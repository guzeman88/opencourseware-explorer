import psycopg2
import os
conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()
cur.execute("""
  SELECT v.youtube_id, v.title, v.duration_seconds, c.title
  FROM videos v JOIN courses c ON c.id=v.course_id
  WHERE v.duration_seconds IS NOT NULL
  ORDER BY v.duration_seconds
  LIMIT 5
""")
for r in cur.fetchall():
    print(r)
cur.execute("SELECT COUNT(*) FROM videos")
print("total videos:", cur.fetchone()[0])
conn.close()
