#!/usr/bin/env python
"""
Backfill individual lecture videos for courses that already have a
youtube_playlist_id (or one extractable from source_url) but have
no rows in the videos table yet.

Uses yt-dlp to fetch playlist metadata — no YouTube API key required.

Usage:
    cd opencourseware/scraper
    $env:DATABASE_URL = "postgresql://user:pass@host:port/dbname"
    python backfill_videos.py

    # Dry run (see what would be fetched without writing):
    $env:DRY_RUN = "1"  ;  python backfill_videos.py

    # Only process a specific university (by source_key):
    $env:ONLY = "mit_ocw,stanford"  ;  python backfill_videos.py

    # Re-process courses that already have videos (force refresh):
    $env:FORCE = "1"  ;  python backfill_videos.py
"""
from __future__ import annotations

import os
import re
import sys
import time
import uuid
from urllib.parse import urlparse, parse_qs

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

# ── Config ─────────────────────────────────────────────────────────────────────

DATABASE_URL = os.environ.get("DATABASE_URL", "")
DRY_RUN = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")
FORCE = os.environ.get("FORCE", "").lower() in ("1", "true", "yes")
ONLY_SOURCES = set(filter(None, os.environ.get("ONLY", "").split(",")))

if not DATABASE_URL:
    DATABASE_URL = "postgresql://ocw:ocwpass@localhost:5432/opencourseware"
    print(f"[warn] DATABASE_URL not set — using local default: {DATABASE_URL}")

try:
    import yt_dlp
except ImportError:
    print("ERROR: yt-dlp is not installed.  pip install yt-dlp")
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
        # Keep connection alive through Railway's load balancer
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5,
        connect_timeout=30,
    )


# ── Playlist helpers ───────────────────────────────────────────────────────────

def extract_playlist_id(url: str) -> str | None:
    """Extract a YouTube playlist ID from a URL."""
    if not url:
        return None
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if "list" in qs:
        pid = qs["list"][0]
        if re.match(r"^(PL|FL|UU|RD|OL)[A-Za-z0-9_-]+$", pid):
            return pid
    m = re.search(r"[?&]list=([A-Za-z0-9_-]+)", url)
    if m:
        return m.group(1)
    return None


def fetch_playlist_videos(playlist_id: str) -> list[dict]:
    """
    Fetch all video metadata from a YouTube playlist using yt-dlp.
    Returns a list of dicts with: youtube_id, title, description,
    thumbnail_url, duration_seconds, published_at.
    """
    playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "ignoreerrors": True,
        "skip_download": True,
    }

    videos = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
    except Exception as e:
        print(f"    [error] yt-dlp failed for {playlist_id}: {e}")
        return []

    if not info or "entries" not in info:
        return []

    for entry in (info.get("entries") or []):
        if not entry:
            continue
        vid_id = entry.get("id") or entry.get("url", "").split("v=")[-1]
        if not vid_id:
            continue

        # Pick best thumbnail
        thumb = None
        thumbs = entry.get("thumbnails") or []
        if thumbs:
            # yt-dlp orders thumbnails from lowest to highest quality
            thumb = thumbs[-1].get("url") if isinstance(thumbs[-1], dict) else None
        if not thumb:
            thumb = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"

        duration = entry.get("duration")  # seconds (int or None)
        published = entry.get("upload_date")  # "YYYYMMDD" or None
        published_iso = None
        if published and len(published) == 8:
            published_iso = f"{published[:4]}-{published[4:6]}-{published[6:8]}T00:00:00Z"

        videos.append({
            "youtube_id": vid_id,
            "title": (entry.get("title") or "")[:500],
            "description": entry.get("description") or "",
            "thumbnail_url": thumb,
            "duration_seconds": int(duration) if duration else None,
            "view_count": entry.get("view_count"),
            "published_at": published_iso,
        })

    return videos


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

    cur.execute(f"""
        SELECT
            c.id,
            c.title,
            c.source_key,
            c.source_url,
            c.youtube_playlist_id,
            c.total_videos
        FROM courses c
        WHERE (
              c.youtube_playlist_id IS NOT NULL
              OR c.source_url ILIKE '%%list=%%'
          )
          {video_filter}
          {source_filter}
        ORDER BY c.source_key, c.title
    """, filter_args)

    courses = cur.fetchall()
    total = len(courses)
    flags = " ".join(filter(None, [
        "(FORCE)" if FORCE else "",
        "(DRY RUN)" if DRY_RUN else "",
        f"(only: {', '.join(sorted(ONLY_SOURCES))})" if ONLY_SOURCES else "",
    ]))
    print(f"Found {total} courses to backfill {flags}".strip())

    if total == 0:
        print("Nothing to do — all courses already have videos, or no playlist IDs found.")
        conn.close()
        return

    videos_inserted = 0
    courses_updated = 0
    skipped = 0

    for idx, course in enumerate(courses, 1):
        course_id = course["id"]
        title = course["title"][:60]
        source_key = course["source_key"]

        playlist_id = course["youtube_playlist_id"] or extract_playlist_id(course["source_url"] or "")
        if not playlist_id:
            skipped += 1
            continue

        print(f"\n[{idx}/{total}] {source_key} | {title}")
        print(f"    playlist: {playlist_id}")

        items = fetch_playlist_videos(playlist_id)
        if not items:
            print("    [skip] No videos returned")
            skipped += 1
            continue

        total_duration = sum(v.get("duration_seconds") or 0 for v in items)
        print(f"    {len(items)} videos, ~{total_duration // 60}min total")

        if DRY_RUN:
            for i, v in enumerate(items[:3]):
                print(f"      {i+1}. {v['title'][:70]}")
            if len(items) > 3:
                print(f"      ... and {len(items)-3} more")
            continue

        # Retry loop for dropped DB connections
        for attempt in range(3):
            try:
                insert_cur = conn.cursor()
                inserted_count = 0
                for order, item in enumerate(items):
                    insert_cur.execute("""
                        INSERT INTO videos
                            (id, course_id, youtube_id, title, description,
                             thumbnail_url, duration_seconds, view_count, "order", published_at)
                        SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        WHERE NOT EXISTS (
                            SELECT 1 FROM videos
                            WHERE course_id = %s AND youtube_id = %s
                        )
                    """, (
                        str(uuid.uuid4()),
                        str(course_id),
                        item["youtube_id"],
                        item["title"],
                        item.get("description", ""),
                        item.get("thumbnail_url"),
                        item.get("duration_seconds"),
                        item.get("view_count"),
                        order,
                        item.get("published_at"),
                        str(course_id),
                        item["youtube_id"],
                    ))
                    inserted_count += insert_cur.rowcount

                insert_cur.execute("""
                    UPDATE courses
                    SET total_videos = %s,
                        total_duration_seconds = %s,
                        has_video_lectures = TRUE,
                        youtube_playlist_id = COALESCE(youtube_playlist_id, %s)
                    WHERE id = %s
                """, (len(items), total_duration, playlist_id, str(course_id)))

                conn.commit()
                insert_cur.close()
                break  # success

            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                print(f"    [warn] DB connection lost (attempt {attempt+1}/3): {e}")
                try:
                    conn.close()
                except Exception:
                    pass
                time.sleep(5)
                conn = get_connection()
                cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            except Exception as e:
                print(f"    [warn] Insert error: {e}")
                try:
                    conn.rollback()
                except Exception:
                    pass
                break

        print(f"    inserted {inserted_count} new videos")
        videos_inserted += inserted_count
        courses_updated += 1

    cur.close()
    conn.close()

    print()
    print("=" * 60)
    print(f"Done. {courses_updated} courses updated | {videos_inserted} videos inserted | {skipped} skipped")
    if DRY_RUN:
        print("(DRY RUN — nothing was written to the database)")


if __name__ == "__main__":
    main()
