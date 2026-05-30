import psycopg2
import urllib.request

import os as _os; DB = _os.environ.get("DATABASE_URL") or exit("ERROR: DATABASE_URL env var is required")
conn = psycopg2.connect(DB)
cur = conn.cursor()

# Get specific CMU and other courses that might have wrong thumbnails
cur.execute("""
    SELECT title, source_key, thumbnail_url
    FROM courses
    WHERE has_video_lectures = true
      AND (title ILIKE '%15-213%' OR title ILIKE '%intro%computer systems%' OR title ILIKE '%sailing%')
    ORDER BY source_key, title
""")
rows = cur.fetchall()
print("Specific courses:")
for title, src, thumb in rows:
    print(f"  [{src}] {title}")
    print(f"    {thumb}")

# Check which thumbnail domains have broken URLs - sample a few from each domain
print("\n--- Checking MIT OCW thumbnail URLs (sample) ---")
cur.execute("""
    SELECT title, thumbnail_url
    FROM courses
    WHERE has_video_lectures = true
      AND thumbnail_url LIKE '%ocw.mit.edu%'
    LIMIT 5
""")
for title, thumb in cur.fetchall():
    print(f"  {title[:50]}: {thumb}")

print("\n--- Checking i.ibb.co thumbnails ---")
cur.execute("""
    SELECT title, source_key, thumbnail_url
    FROM courses
    WHERE has_video_lectures = true
      AND thumbnail_url LIKE '%i.ibb.co%'
""")
for title, src, thumb in cur.fetchall():
    print(f"  [{src}] {title}: {thumb}")

print("\n--- Checking simons.berkeley.edu thumbnails ---")
cur.execute("""
    SELECT title, source_key, thumbnail_url
    FROM courses
    WHERE has_video_lectures = true
      AND thumbnail_url LIKE '%simons.berkeley.edu%'
""")
for title, src, thumb in cur.fetchall():
    print(f"  [{src}] {title}: {thumb}")

conn.close()
