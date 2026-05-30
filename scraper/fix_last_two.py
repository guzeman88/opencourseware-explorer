"""Find and fix thumbnails for the 2 remaining Unsplash courses."""
import psycopg2
import subprocess
import json

import os as _os; DB = _os.environ.get("DATABASE_URL") or exit("ERROR: DATABASE_URL env var is required")

SEARCHES = [
    # (course_id_pattern, search_query)
    ("Justice (PLSC 141)", "Justice Michael Sandel Harvard lecture full course"),
    ("Foundations of Causal Inference (CS236G)", "causal inference Stanford lecture full course"),
]

def yt_search_thumbnail(query):
    cmd = [
        "yt-dlp",
        "--no-download",
        "--skip-download",
        "--print", "thumbnail",
        "--playlist-items", "1",
        f"ytsearch5:{query}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    thumbs = [line.strip() for line in result.stdout.strip().splitlines() if line.strip().startswith("http")]
    return thumbs[0] if thumbs else None

conn = psycopg2.connect(DB)
cur = conn.cursor()

for title_match, query in SEARCHES:
    print(f"\nSearching for: {title_match}")
    print(f"  Query: {query}")
    thumb = yt_search_thumbnail(query)
    if thumb:
        print(f"  Found: {thumb}")
        cur.execute(
            "UPDATE courses SET thumbnail_url = %s WHERE title = %s",
            (thumb, title_match)
        )
        if cur.rowcount:
            print(f"  Updated {cur.rowcount} row(s)")
        else:
            print(f"  WARNING: No row matched title '{title_match}'")
    else:
        print(f"  FAILED: No thumbnail found")

conn.commit()
conn.close()
print("\nDone.")
