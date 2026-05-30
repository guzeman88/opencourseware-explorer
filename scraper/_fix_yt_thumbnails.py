#!/usr/bin/env python3
"""
_fix_yt_thumbnails.py

Use yt-dlp to get real thumbnails for courses that have youtube_playlist_id
but currently have Unsplash fallback thumbnails.

Runs yt-dlp --flat-playlist --playlist-end 1 for each playlist to get
the first video's thumbnail without downloading anything.
"""

import io
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import psycopg2
import yt_dlp

DB = os.environ.get("DATABASE_URL") or sys.exit("ERROR: DATABASE_URL required")


def yt_thumb(playlist_id: str) -> str | None:
    """Use yt-dlp Python API to get the first video thumbnail from a playlist."""
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "playlistend": 1,
        "skip_download": True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if not info:
            return None
        entries = info.get("entries") or []
        if not entries:
            return None
        entry = entries[0]
        # Get video ID
        vid_id = entry.get("id")
        if not vid_id or len(vid_id) != 11:
            return None
        # Try maxresdefault then hqdefault
        import urllib.request
        for size in ("maxresdefault", "hqdefault"):
            thumb = f"https://i.ytimg.com/vi/{vid_id}/{size}.jpg"
            try:
                req = urllib.request.urlopen(thumb, timeout=6)
                if req.status == 200:
                    return thumb
            except Exception:
                pass
        return f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
    except Exception as e:
        print(f"  yt-dlp error for {playlist_id}: {e}")
    return None


def process(row: tuple) -> tuple:
    cid, title, skey, playlist_id = row
    thumb = yt_thumb(playlist_id)
    return (cid, title, skey, thumb)


def main():
    conn = psycopg2.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, source_key, youtube_playlist_id
        FROM courses
        WHERE youtube_playlist_id IS NOT NULL
          AND thumbnail_url LIKE '%unsplash%'
        ORDER BY source_key, title
    """)
    rows = cur.fetchall()
    total = len(rows)
    print(f"Courses to fix: {total}")
    if total == 0:
        print("Nothing to do.")
        cur.close(); conn.close(); return

    updated = 0
    failed = 0

    # Use 8 workers — yt-dlp is I/O bound but not too many to avoid rate limits
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(process, row): row for row in rows}
        for i, fut in enumerate(as_completed(futures)):
            cid, title, skey, thumb = fut.result()
            status = "✓" if thumb else "✗"
            print(f"  [{i+1:3d}/{total}] {status} [{skey:12s}] {title[:55]}")
            if thumb:
                cur.execute(
                    "UPDATE courses SET thumbnail_url = %s WHERE id = %s",
                    (thumb, cid)
                )
                updated += 1
            else:
                failed += 1
            if (i + 1) % 20 == 0:
                conn.commit()

    conn.commit()
    print(f"\nDone. Fixed: {updated}, Still failed: {failed}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
