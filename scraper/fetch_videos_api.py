#!/usr/bin/env python
"""
Backfill course videos using the YouTube Data API v3.

Fetches playlist items for every published course that has a youtube_playlist_id
but zero rows in the videos table.  Much more reliable than yt-dlp (no bot
detection / rate-limit bans) and consumes ~1 API unit per 50 videos.

Quota budget estimate (default 10,000 units/day):
  playlistItems.list: 1 unit per call, 50 items per page
  5,500 playlists × avg 1.5 pages = ~8,250 units  (well under limit)

Usage:
  cd opencourseware/scraper
  $env:DATABASE_URL  = "postgresql://..."
  $env:YOUTUBE_API_KEY = "AIza..."
  python fetch_videos_api.py

  # Dry run – shows what would be inserted without writing:
  $env:DRY_RUN = "1"  ;  python fetch_videos_api.py

  # Process specific universities only:
  $env:ONLY = "mit_ocw,stanford"  ;  python fetch_videos_api.py

  # Re-process courses that already have videos:
  $env:FORCE = "1"  ;  python fetch_videos_api.py

  # Limit how many courses to process (for testing):
  $env:LIMIT = "20"  ;  python fetch_videos_api.py
"""
from __future__ import annotations

import os
import sys
import time
import uuid
from urllib.parse import urlparse

# Force UTF-8 output on Windows so non-ASCII course titles don't crash the script
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import psycopg2
import psycopg2.extras

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import requests
except ImportError:
    print("ERROR: requests not installed.  pip install requests")
    sys.exit(1)

# ── Config ─────────────────────────────────────────────────────────────────────

DATABASE_URL  = os.environ.get("DATABASE_URL", "")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
DRY_RUN       = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")
FORCE         = os.environ.get("FORCE", "").lower() in ("1", "true", "yes")
ONLY_SOURCES  = set(filter(None, os.environ.get("ONLY", "").split(",")))
LIMIT         = int(os.environ.get("LIMIT", "0") or 0)   # 0 = no limit
# Stop when remaining quota budget is below this threshold
QUOTA_SAFETY  = int(os.environ.get("QUOTA_SAFETY", "500"))

if not DATABASE_URL:
    DATABASE_URL = "postgresql://ocw:ocwpass@localhost:5432/opencourseware"
    print(f"[warn] DATABASE_URL not set — using local default: {DATABASE_URL}")

if not YOUTUBE_API_KEY:
    print("ERROR: YOUTUBE_API_KEY not set.")
    sys.exit(1)

# ── DB helpers ─────────────────────────────────────────────────────────────────

def get_connection():
    url = DATABASE_URL
    for prefix in ("postgresql+asyncpg://", "postgres+asyncpg://", "postgresql+psycopg://"):
        if url.startswith(prefix):
            url = "postgresql://" + url[len(prefix):]
            break
    parsed = urlparse(url)
    return psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        dbname=parsed.path.lstrip("/"),
        user=parsed.username,
        password=parsed.password,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5,
        connect_timeout=30,
        sslmode="require",
    )


# ── YouTube API helpers ────────────────────────────────────────────────────────

API_BASE = "https://www.googleapis.com/youtube/v3"
quota_used = 0   # track units consumed this run


def yt_get(endpoint: str, params: dict) -> dict | None:
    """Call a YouTube Data API endpoint, return parsed JSON or None on error."""
    global quota_used
    params["key"] = YOUTUBE_API_KEY
    try:
        r = requests.get(f"{API_BASE}/{endpoint}", params=params, timeout=30)
        quota_used += 1
        if r.status_code == 403:
            data = r.json()
            reason = data.get("error", {}).get("errors", [{}])[0].get("reason", "")
            if reason in ("quotaExceeded", "dailyLimitExceeded"):
                print(f"\n[QUOTA] Daily quota exceeded after {quota_used} units. "
                      "Re-run tomorrow or use a different API key.")
                sys.exit(2)
            print(f"    [api-error] 403 {reason}: {data.get('error', {}).get('message', '')}")
            return None
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    except requests.RequestException as exc:
        print(f"    [api-error] {exc}")
        return None


def fetch_playlist_items(playlist_id: str) -> list[dict]:
    """
    Fetch all items in a YouTube playlist via the Data API.
    Returns list of dicts with keys: youtube_id, title, description,
    thumbnail_url, published_at, order.
    """
    items: list[dict] = []
    page_token: str | None = None

    while True:
        params: dict = {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": 50,
        }
        if page_token:
            params["pageToken"] = page_token

        data = yt_get("playlistItems", params)
        if data is None:
            break   # private / deleted playlist or quota error

        for item in data.get("items", []):
            snip = item.get("snippet", {})
            resource = snip.get("resourceId", {})
            vid_id = resource.get("videoId", "")
            if not vid_id or vid_id == "Private video":
                continue

            # Best available thumbnail (prefer high quality)
            thumbs = snip.get("thumbnails", {})
            thumb_url = (
                thumbs.get("maxres", {}).get("url")
                or thumbs.get("high",   {}).get("url")
                or thumbs.get("medium", {}).get("url")
                or thumbs.get("default",{}).get("url")
                or f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
            )

            published_at = snip.get("publishedAt")  # ISO-8601 or None
            position = snip.get("position", len(items))

            items.append({
                "youtube_id":    vid_id[:20],
                "title":         (snip.get("title") or "")[:500],
                "description":   snip.get("description") or "",
                "thumbnail_url": thumb_url[:500] if thumb_url else None,
                "published_at":  published_at,
                "order":         position,
            })

        page_token = data.get("nextPageToken")
        if not page_token:
            break
        time.sleep(0.05)   # be polite

    return items


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    source_filter = ""
    filter_args: list = []
    if ONLY_SOURCES:
        placeholders = ", ".join(["%s"] * len(ONLY_SOURCES))
        source_filter = f"AND c.source_key IN ({placeholders})"
        filter_args = list(ONLY_SOURCES)

    video_filter = "" if FORCE else "AND NOT EXISTS (SELECT 1 FROM videos WHERE course_id = c.id)"

    limit_clause = f"LIMIT {LIMIT}" if LIMIT > 0 else ""

    cur.execute(f"""
        SELECT
            c.id,
            c.title,
            c.source_key,
            c.youtube_playlist_id
        FROM courses c
        WHERE c.is_published = TRUE
          AND c.youtube_playlist_id IS NOT NULL
          {video_filter}
          {source_filter}
        ORDER BY c.source_key, c.title
        {limit_clause}
    """, filter_args)

    courses = cur.fetchall()
    total = len(courses)

    flags = " ".join(filter(None, [
        "(FORCE)" if FORCE else "",
        "(DRY RUN)" if DRY_RUN else "",
        f"(only: {', '.join(sorted(ONLY_SOURCES))})" if ONLY_SOURCES else "",
        f"(limit: {LIMIT})" if LIMIT > 0 else "",
    ]))
    print(f"Found {total} courses to backfill {flags}".strip())
    if total == 0:
        print("Nothing to do — all courses already have videos or no playlist IDs.")
        conn.close()
        return

    videos_inserted   = 0
    courses_updated   = 0
    courses_skipped   = 0   # playlist returned 0 videos (private/deleted)
    courses_empty     = 0   # playlist returned items but all were private

    for idx, course in enumerate(courses, 1):
        course_id  = str(course["id"])
        title      = (course["title"] or "")[:60]
        source_key = course["source_key"] or ""
        playlist_id = course["youtube_playlist_id"]

        print(f"\n[{idx}/{total}] {source_key} | {title}")
        print(f"    playlist: {playlist_id}  (quota used so far: {quota_used})")

        items = fetch_playlist_items(playlist_id)
        if not items:
            print("    [skip] Playlist empty, private, or deleted")
            courses_skipped += 1
            continue

        print(f"    {len(items)} videos found")
        if DRY_RUN:
            for i, v in enumerate(items[:3]):
                print(f"      {i+1}. {v['title'][:70]}")
            if len(items) > 3:
                print(f"      ... and {len(items) - 3} more")
            continue

        # Insert all videos for this course (skip duplicates)
        insert_cur = conn.cursor()
        inserted_this_course = 0
        for item in items:
            insert_cur.execute("""
                INSERT INTO videos
                    (id, course_id, youtube_id, title, description,
                     thumbnail_url, "order", published_at)
                SELECT %s, %s, %s, %s, %s, %s, %s, %s
                WHERE NOT EXISTS (
                    SELECT 1 FROM videos
                    WHERE course_id = %s AND youtube_id = %s
                )
            """, (
                str(uuid.uuid4()),
                course_id,
                item["youtube_id"],
                item["title"],
                item["description"],
                item["thumbnail_url"],
                item["order"],
                item["published_at"],
                course_id,
                item["youtube_id"],
            ))
            inserted_this_course += insert_cur.rowcount

        # Update courses.total_videos
        insert_cur.execute("""
            UPDATE courses
               SET total_videos = (SELECT COUNT(*) FROM videos WHERE course_id = %s),
                   updated_at   = now()
             WHERE id = %s
        """, (course_id, course_id))

        conn.commit()
        videos_inserted += inserted_this_course
        courses_updated += 1
        print(f"    inserted {inserted_this_course} videos (running total: {videos_inserted})")

        # Brief pause every 100 courses to stay well under rate limits
        if idx % 100 == 0:
            time.sleep(1)

    cur.close()
    conn.close()

    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Done!
  Courses processed : {courses_updated}
  Videos inserted   : {videos_inserted}
  Playlists skipped : {courses_skipped}
  API quota used    : {quota_used} units
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━""")


if __name__ == "__main__":
    main()
