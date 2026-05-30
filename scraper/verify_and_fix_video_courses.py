#!/usr/bin/env python
"""
Comprehensive video course verification and fix.

The only reliable signal that a course has playable video on this platform is
total_videos > 0 (videos fetched and counted from YouTube). This script:

  1. Audits current state
  2. Runs yt-dlp on every course that has a youtube_playlist_id but total_videos=0
     to get real video counts and first-video thumbnails
  3. Sets has_video_lectures = TRUE  only where total_videos > 0
           has_video_lectures = FALSE everywhere else (no playlist, or empty/dead playlist)
  4. Sets is_published = TRUE  for confirmed video courses
           is_published = FALSE for previously-published "video" courses that have
                                no real videos (so they drop off the video rows but
                                remain in the database for non-video browsing)
  5. Publishes MIT OCW non-video courses that have lecture notes or exams
  6. Prints a full before/after report

Usage:
  py -3.13 verify_and_fix_video_courses.py
  DATABASE_URL=postgresql://... py -3.13 verify_and_fix_video_courses.py

Workers / rate-limit:
  Set WORKERS env var (default 6) to control parallel yt-dlp threads.
  A 0.4s delay per request is baked in to stay well under YouTube rate limits.
"""
from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import psycopg2
import psycopg2.extras
import yt_dlp

# ── DB connection ──────────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL:
    # Railway or explicit URL
    _ssl = "require" if ("rlwy.net" in DATABASE_URL or "railway" in DATABASE_URL.lower()) else "prefer"
    conn = psycopg2.connect(DATABASE_URL, sslmode="disable")
else:
    try:
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "127.0.0.1"),
            port=int(os.environ.get("POSTGRES_PORT", "5432")),
            dbname=os.environ.get("POSTGRES_DB", "opencourseware"),
            user="postgres",
            password=os.environ.get("POSTGRES_SUPERUSER_PASSWORD", "postgres"),
        )
    except Exception:
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "127.0.0.1"),
            port=int(os.environ.get("POSTGRES_PORT", "5432")),
            dbname=os.environ.get("POSTGRES_DB", "opencourseware"),
            user=os.environ.get("POSTGRES_USER", "ocw"),
            password=os.environ.get("POSTGRES_PASSWORD", ""),
        )

cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
WORKERS = int(os.environ.get("WORKERS", "6"))
DELAY = 0.4  # seconds between yt-dlp calls per thread


# ── Helpers ───────────────────────────────────────────────────────────────────

def audit(label: str) -> None:
    cur.execute("SELECT COUNT(*) FROM courses")
    total = cur.fetchone()["count"]
    cur.execute("SELECT COUNT(*) FROM courses WHERE is_published=TRUE AND has_video_lectures=TRUE")
    pub_video = cur.fetchone()["count"]
    cur.execute("SELECT COUNT(*) FROM courses WHERE total_videos > 0")
    real_video = cur.fetchone()["count"]
    cur.execute("SELECT COUNT(*) FROM courses WHERE youtube_playlist_id IS NOT NULL")
    has_pid = cur.fetchone()["count"]
    cur.execute("SELECT COUNT(*) FROM courses WHERE is_published=TRUE")
    published = cur.fetchone()["count"]
    print(f"\n=== {label} ===")
    print(f"  Total courses               : {total}")
    print(f"  Published                   : {published}")
    print(f"  Published + video           : {pub_video}  <- frontend video rows")
    print(f"  total_videos > 0 (verified) : {real_video}")
    print(f"  youtube_playlist_id set     : {has_pid}")


def yt_info(playlist_id: str, timeout: int = 30) -> dict | None:
    """Return {video_count, first_video_id, thumbnail_url} or None on failure."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "ignoreerrors": True,
        "socket_timeout": timeout,
        "retries": 2,
    }
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if not info:
            return None
        entries = [e for e in (info.get("entries") or []) if e]
        first_vid = entries[0].get("id") if entries else None
        return {
            "video_count": len(entries),
            "first_video_id": first_vid,
            "thumbnail_url": (
                f"https://i.ytimg.com/vi/{first_vid}/hqdefault.jpg" if first_vid else None
            ),
        }
    except Exception as exc:
        print(f"  [yt-dlp FAIL] {playlist_id}: {exc}", flush=True)
        return None


def verify_playlist(row: dict) -> dict:
    """Worker fn: verify one course's playlist and return result dict."""
    time.sleep(DELAY)
    info = yt_info(row["youtube_playlist_id"])
    return {
        "id": row["id"],
        "title": row["title"],
        "playlist_id": row["youtube_playlist_id"],
        "video_count": info["video_count"] if info else 0,
        "thumbnail_url": info["thumbnail_url"] if info else None,
        "ok": bool(info and info["video_count"] > 0),
    }


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Audit before
# ══════════════════════════════════════════════════════════════════════════════
audit("BEFORE")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Verify all playlists that have an ID but no video count yet
# ══════════════════════════════════════════════════════════════════════════════
cur.execute("""
    SELECT id, title, source_key, youtube_playlist_id
    FROM courses
    WHERE youtube_playlist_id IS NOT NULL AND total_videos = 0
    ORDER BY source_key, title
""")
to_verify = cur.fetchall()
print(f"\n--- Step 2: Verifying {len(to_verify)} playlists with yt-dlp ({WORKERS} workers) ---")

results: list[dict] = []
done = 0
with ThreadPoolExecutor(max_workers=WORKERS) as pool:
    futures = {pool.submit(verify_playlist, dict(row)): row for row in to_verify}
    for fut in as_completed(futures):
        result = fut.result()
        results.append(result)
        done += 1
        status = f"OK ({result['video_count']} videos)" if result["ok"] else "EMPTY/DEAD"
        print(f"  [{done}/{len(to_verify)}] {result['title'][:50]:<50} {status}", flush=True)

# Bulk-update total_videos and thumbnail_url from yt-dlp results
good = [r for r in results if r["ok"]]
dead = [r for r in results if not r["ok"]]

if good:
    psycopg2.extras.execute_batch(
        cur,
        """UPDATE courses
              SET total_videos   = %s,
                  thumbnail_url  = COALESCE(%s, thumbnail_url)
            WHERE id = %s""",
        [(r["video_count"], r["thumbnail_url"], r["id"]) for r in good],
        page_size=100,
    )
    conn.commit()
    print(f"\n  Updated {len(good)} courses with real video counts.")

if dead:
    # Null out the playlist ID for playlists that returned 0 videos (dead/private/removed)
    psycopg2.extras.execute_batch(
        cur,
        "UPDATE courses SET youtube_playlist_id = NULL WHERE id = %s",
        [(r["id"],) for r in dead],
        page_size=100,
    )
    conn.commit()
    print(f"  Cleared playlist_id for {len(dead)} dead/empty playlists.")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Set has_video_lectures using total_videos as the single source of truth
# ══════════════════════════════════════════════════════════════════════════════
print("\n--- Step 3: Setting has_video_lectures = (total_videos > 0) for ALL courses ---")

cur.execute("""
    UPDATE courses
       SET has_video_lectures = TRUE
     WHERE total_videos > 0
       AND has_video_lectures = FALSE
""")
promoted = cur.rowcount
conn.commit()

cur.execute("""
    UPDATE courses
       SET has_video_lectures = FALSE
     WHERE total_videos = 0
       AND has_video_lectures = TRUE
""")
demoted = cur.rowcount
conn.commit()
print(f"  Promoted {promoted} courses to has_video_lectures=TRUE")
print(f"  Demoted  {demoted} courses to has_video_lectures=FALSE (no verified videos)")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Republish based on corrected flags
# ══════════════════════════════════════════════════════════════════════════════
print("\n--- Step 4: Republishing based on verified data ---")

# Unpublish anything that was "video" but now has no verified videos
cur.execute("""
    UPDATE courses
       SET is_published = FALSE
     WHERE is_published = TRUE
       AND has_video_lectures = FALSE
       AND (has_lecture_notes = FALSE AND has_exams = FALSE)
""")
unpublished = cur.rowcount
conn.commit()
print(f"  Unpublished {unpublished} courses (no video, no lecture notes, no exams)")

# Publish confirmed video courses
cur.execute("""
    UPDATE courses
       SET is_published = TRUE
     WHERE has_video_lectures = TRUE
       AND is_published = FALSE
""")
published_video = cur.rowcount
conn.commit()
print(f"  Published {published_video} confirmed video courses")

# Keep MIT OCW non-video courses that have lecture notes or exams published
cur.execute("""
    UPDATE courses
       SET is_published = TRUE
     WHERE source_key = 'mit_ocw'
       AND has_video_lectures = FALSE
       AND (has_lecture_notes = TRUE OR has_exams = TRUE)
       AND is_published = FALSE
""")
published_ocw = cur.rowcount
conn.commit()
print(f"  Published {published_ocw} MIT OCW non-video courses (have notes/exams)")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Final breakdown by source
# ══════════════════════════════════════════════════════════════════════════════
print("\n--- Published video courses by source ---")
cur.execute("""
    SELECT source_key,
           COUNT(*) FILTER (WHERE has_video_lectures=TRUE)  AS video,
           COUNT(*) FILTER (WHERE has_video_lectures=FALSE) AS non_video,
           SUM(total_videos) AS total_vids
    FROM courses
    WHERE is_published = TRUE
    GROUP BY source_key
    ORDER BY video DESC
""")
for r in cur.fetchall():
    if r["video"] > 0:
        print(f"  {r['source_key']:<20} video={r['video']}  total_vids={r['total_vids']}")

audit("AFTER")

cur.close()
conn.close()
print("\nDone.")
