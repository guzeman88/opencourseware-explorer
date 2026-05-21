import psycopg2
from db_utils import get_connection
conn = get_connection()
cur = conn.cursor()

cur.execute("""
SELECT c.source_key, c.title, c.source_url, c.youtube_playlist_id,
    (SELECT v.youtube_id FROM videos v WHERE v.course_id = c.id ORDER BY v."order" ASC LIMIT 1) AS first_vid
FROM courses c
WHERE c.thumbnail_url IS NULL
ORDER BY c.source_key, c.title
LIMIT 20
""")
for r in cur.fetchall():
    sk, title, url, playlist, vid = r
    print(f"[{sk}] {title[:60]}")
    print(f"  url={url}")
    print(f"  playlist={playlist}  first_vid={vid}")

cur.close()
conn.close()
