#!/usr/bin/env python
"""
Fast backfill of total_videos and description for courses that have a
youtube_playlist_id. Uses yt-dlp flat extraction (no per-video API calls).

Usage:
    cd opencourseware/scraper
    $env:DATABASE_URL = "postgresql://..."
    python _backfill_counts.py

    # Only specific source keys:
    $env:ONLY = "crashcourse,mit_ocw"  ;  python _backfill_counts.py

    # Force re-process all (even those already updated):
    $env:FORCE = "1"  ;  python _backfill_counts.py
"""
from __future__ import annotations

import os
import sys
import time
from urllib.parse import urlparse

import psycopg2
import psycopg2.extras

try:
    import yt_dlp
except ImportError:
    print("ERROR: yt-dlp not installed. pip install yt-dlp")
    sys.exit(1)

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

FORCE = os.environ.get("FORCE", "").lower() in ("1", "true", "yes")
ONLY_SOURCES = set(filter(None, os.environ.get("ONLY", "").split(",")))
DELAY = 0.8  # seconds between yt-dlp calls


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
        connect_timeout=30,
    )


def fetch_playlist_meta(playlist_id: str) -> tuple[int, str | None]:
    """
    Fetch video count and playlist description via flat extraction.
    Returns (count, description).
    """
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
        "ignoreerrors": True,
        "skip_download": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        print(f"    [error] {playlist_id}: {e}")
        return 0, None

    if not info:
        return 0, None

    entries = info.get("entries") or []
    count = len([e for e in entries if e])  # skip None entries

    # Get description from playlist-level info
    description = info.get("description") or info.get("title") or None
    if description:
        description = description.strip()
        if len(description) > 2000:
            description = description[:2000]

    return count, description


def main():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    where_extra = ""
    args = []
    if ONLY_SOURCES:
        placeholders = ",".join(["%s"] * len(ONLY_SOURCES))
        where_extra += f" AND source_key IN ({placeholders})"
        args.extend(ONLY_SOURCES)
    if not FORCE:
        where_extra += " AND (total_videos = 0 OR total_videos IS NULL)"

    cur.execute(
        f"""
        SELECT id, title, source_key, youtube_playlist_id
        FROM courses
        WHERE youtube_playlist_id IS NOT NULL {where_extra}
        ORDER BY source_key, title
        """,
        args,
    )
    rows = cur.fetchall()
    print(f"Courses to process: {len(rows)}")

    updated = 0
    failed = 0

    for i, row in enumerate(rows, 1):
        pid = row["youtube_playlist_id"]
        title = row["title"]
        skey = row["source_key"]
        print(f"  [{i}/{len(rows)}] [{skey}] {title[:55]}")

        count, description = fetch_playlist_meta(pid)

        if count > 0:
            cur.execute(
                """
                UPDATE courses
                SET total_videos = %s,
                    description = COALESCE(NULLIF(%s, ''), description),
                    updated_at = now()
                WHERE id = %s
                """,
                (count, description, row["id"]),
            )
            conn.commit()
            print(f"      -> {count} videos")
            updated += 1
        else:
            print(f"      -> 0 videos (skipped/private/deleted)")
            failed += 1

        time.sleep(DELAY)

    print(f"\nDone. Updated: {updated}/{len(rows)}, failed/empty: {failed}")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
