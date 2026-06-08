import os

import psycopg2

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise SystemExit("DATABASE_URL is required")

conn = psycopg2.connect(database_url, connect_timeout=15)
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM videos')
print('videos:', cur.fetchone()[0])
cur.execute('SELECT COUNT(*) FROM courses')
print('courses:', cur.fetchone()[0])
cur.execute('SELECT COUNT(*) FROM videos WHERE silence_segments IS NOT NULL')
print('videos with silence:', cur.fetchone()[0])
conn.close()
print('Railway OK')
