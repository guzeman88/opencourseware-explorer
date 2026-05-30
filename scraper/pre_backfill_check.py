import psycopg2
import os as _os; DB = _os.environ.get("DATABASE_URL") or exit("ERROR: DATABASE_URL env var is required")
conn = psycopg2.connect(DB)
cur = conn.cursor()
cur.execute("UPDATE courses SET youtube_playlist_id = NULL WHERE title = 'Sociology' AND source_key = 'crashcourse'")
print("Cleared Sociology bad match:", cur.rowcount)
cur.execute("SELECT title, youtube_playlist_id FROM courses WHERE title = '15-213: Introduction to Computer Systems'")
print("CMU 15-213:", cur.fetchone())
# Show all courses that now have playlist IDs but no videos
cur.execute("""
    SELECT c.source_key, c.title, c.youtube_playlist_id
    FROM courses c
    LEFT JOIN videos v ON v.course_id = c.id
    WHERE c.has_video_lectures = true AND c.is_published = true
      AND c.youtube_playlist_id IS NOT NULL
    GROUP BY c.id HAVING COUNT(v.id) = 0
    ORDER BY c.source_key, c.title
""")
rows = cur.fetchall()
print(f"\nCourses ready for backfill: {len(rows)}")
for src, title, pl in rows[:25]:
    print(f"  [{src}] {title} -> {pl}")
conn.commit()
conn.close()
