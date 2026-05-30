"""
Find and fix missing YouTube playlist IDs for courses that have no videos.

Strategy:
1. Crash Course: scrape their current channel playlists and match by title
2. CMU/Berkeley/Stanford/etc: search YouTube for each course's playlist
3. Update youtube_playlist_id in DB, then videos can be backfilled
"""
import psycopg2
import yt_dlp
import re
import time
import json
from difflib import SequenceMatcher

import os as _os; DB = _os.environ.get("DATABASE_URL") or exit("ERROR: DATABASE_URL env var is required")

# Known channel handles/IDs for each source_key
CHANNEL_SOURCES = {
    "crashcourse": "https://www.youtube.com/@crashcourse/playlists",
    # Others we'll do via search
}

# Known specific playlists (manually curated for high-confidence courses)
KNOWN_PLAYLISTS = {
    # CMU
    "15-213: Introduction to Computer Systems": "PLbY-cFJNzq7z_tQGq-rxtq_n2QQDf5vnM",  # Fall 2015
    "15-445: Database Systems": "PLSE8ODhjZXjbj8BMuIrRcacnQh20hmY9g",    # Andy Pavlo Fall 2019
    "15-721: Advanced Database Systems": "PLSE8ODhjZXja7K1hjZ01UTVDnGQdx5v5U",  # Andy Pavlo Spring 2023
    "15-462: Computer Graphics": "PLQ3UicqQtfNuBjzJ-KEuitXkHe0-4-4R5",
    "11-785: Deep Learning": "PLp-0K3kfddPxRmjgjm0P1WT6H-gTqE8j9",      # CMU 11-785
    "11-711: Advanced NLP": "PL8PYTP1V4I8D4BeyjwWczukWq9d8An6QP",       # Neubig 2022
    # Berkeley
    "CS 285: Deep Reinforcement Learning": "PL_iWQOsE6TfX7MaC6C3HcdOf1g337dlC9",  # Sergey Levine
    "CS 186: Introduction to Database Systems": "PLYp4IGUhNFmw8USiYMJvCo6b0C24FNOmW",
    "CS 189: Introduction to Machine Learning": "PL_zMkS6sSMHm-rPmZtCf0mvKL0sLbZqHo",
    "CS 61A: Structure and Interpretation of Computer Programs": "PL6BsET-8jgYVkdaPYJNyvuNga3QA_U1gA",
    "CS 61C: Great Ideas in Computer Architecture": "PLDoI-XvXv0kc0wfIq7ijWVvYEPnJXfgMQ",
    "CS 70: Discrete Mathematics and Probability Theory": "PLkFD6_40KJIx8lkHADvhUjNsI5OaSbVtk",
    "Foundations of Data Science (Data 8)": "PLzFB3E3_Z7dEJYbpUWS_dkxqMWUMYElrz",
    "Physics 10: Physics for Future Presidents": "PLF9BDEBCBE40A9E33",
    "EE 16A: Designing Information Devices and Systems I": "PLkFD6_40KJIx2n2vUlMEPvdDXRaG9wCmh",
    "DATA 100: Principles and Techniques of Data Science": "PLPowWqQP9Q8Tv-iMJX0b4yXRnHLi2WSQT",
    # Stanford
    "Machine Learning (CS229)": "PLoROMvodv4rMiGQp3WXShtMGgzqpfVfbU",
    "Deep Learning (CS230)": "PLoROMvodv4rOABXSygHTsbvUz4G_YQhOb",
    "NLP with Deep Learning (CS224N)": "PLoROMvodv4rOSH4v6133s9LFPRHjEmbmJ",
    "Computer Vision (CS231N)": "PLoROMvodv4rMFqRtEuo6SGjG4XAdein9u",
    "Reinforcement Learning (CS234)": "PLoROMvodv4rOSOc5eO31skAIoSiQLRs22",
    # MIT  
    "Introduction to Deep Learning (6.S191)": "PLtBw6njQRU-rwp5__7C0oIVt26ZgjG9NI",
    # 3Blue1Brown
    "Differential Equations": "PLZHQObOWTQDNPOjrT6KVlfJuKtYTftqH6",
    "Imaginary Numbers and Complex Arithmetic": "PLiaHhY2iBX9g6KIvZ_703G3KJXapKkNaF",
    # Khan Academy series that are standalone
}

def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def get_channel_playlists(channel_url):
    """Get all playlists from a YouTube channel."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "ignoreerrors": True,
    }
    playlists = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
        if info and "entries" in info:
            for entry in (info["entries"] or []):
                if not entry:
                    continue
                pl_id = entry.get("id") or entry.get("url", "")
                pl_title = entry.get("title") or ""
                if pl_id and pl_title:
                    playlists.append({"id": pl_id, "title": pl_title})
    except Exception as e:
        print(f"  [error] channel scrape failed: {e}")
    return playlists

def search_youtube_playlist(query, course_title):
    """Search YouTube for a course playlist. Returns (playlist_id, playlist_title) or None."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "ignoreerrors": True,
    }
    search_query = f"ytsearch5:{query}"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
        if not info or not info.get("entries"):
            return None
        for entry in info["entries"]:
            if not entry:
                continue
            # Look for playlist entries (not individual videos)
            url = entry.get("url") or entry.get("webpage_url") or ""
            if "playlist" in url.lower() or entry.get("_type") == "playlist":
                pl_id = entry.get("id")
                if pl_id:
                    return pl_id, entry.get("title", "")
    except Exception as e:
        print(f"  [error] search failed: {e}")
    return None

def main():
    conn = psycopg2.connect(DB)
    cur = conn.cursor()

    # Get all zero-video published courses
    cur.execute("""
        SELECT c.id, c.title, c.source_key, c.source_url, c.youtube_playlist_id
        FROM courses c
        LEFT JOIN videos v ON v.course_id = c.id
        WHERE c.has_video_lectures = true AND c.is_published = true
        GROUP BY c.id
        HAVING COUNT(v.id) = 0
        ORDER BY c.source_key, c.title
    """)
    courses = cur.fetchall()
    print(f"Courses needing playlist IDs: {len(courses)}\n")

    updated = 0

    # === STEP 1: Known playlists ===
    print("=== Step 1: Applying known playlist IDs ===")
    for id_, title, src, source_url, existing_pl in courses:
        if title in KNOWN_PLAYLISTS:
            new_pl = KNOWN_PLAYLISTS[title]
            cur.execute(
                "UPDATE courses SET youtube_playlist_id = %s WHERE id = %s",
                (new_pl, str(id_))
            )
            print(f"  [{src}] {title} -> {new_pl}")
            updated += 1
    conn.commit()
    print(f"  Applied {updated} known playlist IDs\n")

    # === STEP 2: Crash Course channel scrape ===
    print("=== Step 2: Scraping Crash Course channel ===")
    cc_url = "https://www.youtube.com/@crashcourse/playlists"
    cc_playlists = get_channel_playlists(cc_url)
    print(f"  Found {len(cc_playlists)} playlists on Crash Course channel")

    if cc_playlists:
        # Re-fetch zero-video crashcourse courses
        cur.execute("""
            SELECT c.id, c.title FROM courses c
            LEFT JOIN videos v ON v.course_id = c.id
            WHERE c.source_key = 'crashcourse' AND c.has_video_lectures = true
            GROUP BY c.id HAVING COUNT(v.id) = 0
        """)
        cc_courses = cur.fetchall()
        print(f"  Matching {len(cc_courses)} Crash Course courses...")
        for id_, title in cc_courses:
            best_match = None
            best_score = 0
            for pl in cc_playlists:
                score = similar(title, pl["title"])
                if score > best_score:
                    best_score = score
                    best_match = pl
            if best_match and best_score > 0.6:
                cur.execute(
                    "UPDATE courses SET youtube_playlist_id = %s WHERE id = %s",
                    (best_match["id"], str(id_))
                )
                print(f"  [{best_score:.2f}] {title} -> {best_match['title']} ({best_match['id']})")
                updated += 1
            else:
                print(f"  [no match] {title} (best: {best_match['title'] if best_match else 'none'}, score: {best_score:.2f})")
        conn.commit()

    print(f"\nTotal playlist IDs set: {updated}")
    print("Run backfill_videos.py to import the actual videos.")
    conn.close()

if __name__ == "__main__":
    main()
