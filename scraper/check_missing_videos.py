"""Check video counts and source URLs for courses missing videos."""
import psycopg2

import os as _os; DB = _os.environ.get("DATABASE_URL") or exit("ERROR: DATABASE_URL env var is required")
conn = psycopg2.connect(DB)
cur = conn.cursor()

# Courses with has_video_lectures=true but 0 videos
cur.execute("""
    SELECT c.id, c.title, c.source_key, c.source_url, c.youtube_playlist_id,
           COUNT(v.id) AS video_count
    FROM courses c
    LEFT JOIN videos v ON v.course_id = c.id
    WHERE c.has_video_lectures = true
    GROUP BY c.id, c.title, c.source_key, c.source_url, c.youtube_playlist_id
    HAVING COUNT(v.id) = 0
    ORDER BY c.source_key, c.title
""")
rows = cur.fetchall()
print(f"Courses with has_video_lectures=true but 0 videos: {len(rows)}\n")

from collections import Counter
by_source = Counter(r[2] for r in rows)
for src, cnt in by_source.most_common():
    print(f"  {cnt:3d}  {src}")

print("\n--- Sample: first 20 courses missing videos ---")
for id_, title, src, source_url, playlist_id, _ in rows[:20]:
    print(f"  [{src}] {title}")
    print(f"    playlist_id: {playlist_id}")
    print(f"    source_url: {(source_url or '')[:80]}")

# Total video count overall
cur.execute("SELECT COUNT(*) FROM videos")
total = cur.fetchone()[0]
print(f"\nTotal videos in DB: {total}")

# Videos per source_key
cur.execute("""
    SELECT c.source_key, COUNT(v.id) AS vids
    FROM videos v JOIN courses c ON c.id = v.course_id
    GROUP BY c.source_key ORDER BY vids DESC
""")
print("\nVideos by source:")
for src, cnt in cur.fetchall():
    print(f"  {cnt:5d}  {src}")

conn.close()
