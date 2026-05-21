import psycopg2
from db_utils import get_connection
conn = get_connection()
cur = conn.cursor()

# Check videos table for NULL-thumbnail courses that have YouTube video IDs
cur.execute("""
SELECT c.source_key, COUNT(DISTINCT c.id) as courses_with_vid
FROM courses c
JOIN videos v ON v.course_id = c.id AND v.youtube_id IS NOT NULL
WHERE c.thumbnail_url IS NULL
GROUP BY c.source_key
ORDER BY courses_with_vid DESC
""")
print("Sources with NULL thumbs that HAVE videos in videos table:")
for r in cur.fetchall():
    print(f"  {r[0]:20s}: {r[1]} courses")

# Check total NULL courses
cur.execute("SELECT COUNT(*) FROM courses WHERE thumbnail_url IS NULL")
print(f"\nTotal NULL: {cur.fetchone()[0]}")

# Sample: show a few CrashCourse NULL courses and their first video ID
cur.execute("""
SELECT c.id, c.title, c.source_url,
       (SELECT v.youtube_id FROM videos v WHERE v.course_id = c.id ORDER BY v."order" ASC LIMIT 1) as first_yt
FROM courses c
WHERE c.source_key = 'crashcourse' AND c.thumbnail_url IS NULL
LIMIT 5
""")
print("\nSample CrashCourse NULL courses:")
for r in cur.fetchall():
    print(f"  [{r[0]}] {r[1][:40]} | first_yt={r[3]} | url={r[2]}")

conn.close()
