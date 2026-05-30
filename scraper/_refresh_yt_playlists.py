#!/usr/bin/env python3
"""
_refresh_yt_playlists.py

For YouTube channel sources (crashcourse, khan, 3b1b, mit_youtube, freecodecamp,
berkeley, etc.), fetch the current playlists from the channel, match them to
our courses by title similarity, update youtube_playlist_id in DB, then fetch
a thumbnail from the first video.

Does NOT re-scrape courses that already have real (non-Unsplash) thumbnails.
"""

import os
import re
import sys
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor, as_completed

import psycopg2
import yt_dlp
import urllib.request

DB = os.environ.get("DATABASE_URL") or sys.exit("ERROR: DATABASE_URL required")

# Known YouTube channel URLs for each source key
# Use /playlists to get list of playlists, or use channel handle
CHANNEL_PLAYLIST_URLS = {
    "cmu": "https://www.youtube.com/@cmu/playlists",
    "gatech": "https://www.youtube.com/@GeorgiaTech/playlists",
    "cambridge": "https://www.youtube.com/@cambridgeuniversity/playlists",
}

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def fetch_channel_playlists(channel_url: str) -> list[dict]:
    """Return list of {id, title} for all playlists on a channel."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "ignoreerrors": True,
    }
    playlists = []
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
        if not info:
            return playlists
        entries = info.get("entries") or []
        for entry in entries:
            if not entry:
                continue
            pl_id = entry.get("id")
            pl_title = entry.get("title")
            if pl_id and pl_title:
                playlists.append({"id": pl_id, "title": pl_title})
    except Exception as e:
        print(f"  Error fetching {channel_url}: {e}")
    return playlists


def get_first_video_thumb(playlist_id: str) -> str | None:
    """Get thumbnail of first video in a playlist via yt-dlp."""
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "playlistend": 1,
        "skip_download": True,
        "ignoreerrors": True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if not info:
            return None
        entries = info.get("entries") or []
        if not entries or not entries[0]:
            return None
        vid_id = entries[0].get("id")
        if not vid_id or len(vid_id) != 11:
            return None
        for size in ("maxresdefault", "hqdefault"):
            thumb = f"https://i.ytimg.com/vi/{vid_id}/{size}.jpg"
            try:
                req = urllib.request.urlopen(thumb, timeout=6)
                if req.status == 200:
                    return thumb
            except Exception:
                pass
        return f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
    except Exception:
        return None


def main():
    conn = psycopg2.connect(DB)
    cur = conn.cursor()

    # Get courses needing thumbnails, grouped by source_key
    source_keys = list(CHANNEL_PLAYLIST_URLS.keys())
    placeholders = ",".join(["%s"] * len(source_keys))
    cur.execute(f"""
        SELECT id, title, source_key, youtube_playlist_id
        FROM courses
        WHERE thumbnail_url LIKE '%%unsplash%%'
          AND source_key IN ({placeholders})
        ORDER BY source_key, title
    """, source_keys)
    rows = cur.fetchall()
    print(f"Courses to fix: {len(rows)}")
    if not rows:
        print("Nothing to do.")
        cur.close(); conn.close(); return

    # Group by source_key
    by_source = {}
    for row in rows:
        sk = row[2]
        by_source.setdefault(sk, []).append(row)

    total_fixed = 0

    for source_key, channel_url in CHANNEL_PLAYLIST_URLS.items():
        courses = by_source.get(source_key, [])
        if not courses:
            continue

        print(f"\n[{source_key}] Fetching playlists from {channel_url} ...")
        playlists = fetch_channel_playlists(channel_url)
        print(f"  Found {len(playlists)} playlists")

        if not playlists:
            print(f"  Skipping — no playlists found")
            continue

        for cid, title, skey, old_pid in courses:
            # Find best matching playlist by title similarity
            best_score = 0.0
            best_pl = None
            for pl in playlists:
                score = similarity(title, pl["title"])
                if score > best_score:
                    best_score = score
                    best_pl = pl

            if not best_pl or best_score < 0.45:
                print(f"  ✗ [{best_score:.2f}] No match for: {title[:55]}")
                continue

            print(f"  ~ [{best_score:.2f}] {title[:40]!r} → {best_pl['title'][:40]!r} ({best_pl['id']})")

            # Get thumbnail from first video in playlist
            thumb = get_first_video_thumb(best_pl["id"])
            if not thumb:
                print(f"    ✗ Couldn't get thumbnail for playlist {best_pl['id']}")
                continue

            print(f"    ✓ {thumb}")
            cur.execute(
                "UPDATE courses SET youtube_playlist_id = %s, thumbnail_url = %s WHERE id = %s",
                (best_pl["id"], thumb, cid)
            )
            total_fixed += 1

        conn.commit()

    print(f"\n{'='*60}")
    print(f"Total courses fixed: {total_fixed}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
