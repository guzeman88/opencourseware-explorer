import os
if not os.environ.get("DATABASE_URL"):
    raise SystemExit("ERROR: DATABASE_URL env var is required")
from db_utils import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM courses WHERE is_published = TRUE')
print('published:', cur.fetchone()[0])

cur.execute('SELECT COUNT(*) FROM courses WHERE is_published = TRUE AND total_videos = 0')
print('published+no_videos:', cur.fetchone()[0])

cur.execute('SELECT COUNT(*) FROM courses WHERE youtube_playlist_id IS NOT NULL')
print('has_playlist_id:', cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM courses WHERE youtube_playlist_id IS NOT NULL AND total_videos = 0")
print('has_playlist_id+no_videos:', cur.fetchone()[0])

cur.execute('SELECT COUNT(*) FROM videos')
print('total_video_rows:', cur.fetchone()[0])

cur.execute("SELECT source_key, COUNT(*) FROM courses WHERE is_published=TRUE GROUP BY source_key ORDER BY 2 DESC LIMIT 10")
print('\nCourses by source_key (published):')
for r in cur.fetchall():
    print(' ', r)

cur.execute("SELECT source_key, COUNT(*) FROM courses WHERE is_published=TRUE AND total_videos=0 GROUP BY source_key ORDER BY 2 DESC LIMIT 10")
print('\nCourses with no videos (published):')
for r in cur.fetchall():
    print(' ', r)

cur.execute("SELECT id, title, source_key, youtube_playlist_id, source_url FROM courses WHERE is_published=TRUE AND youtube_playlist_id IS NOT NULL LIMIT 5")
print('\nSample courses with playlist_id:')
for r in cur.fetchall():
    print(' ', r[2], '|', r[1][:50], '| playlist:', r[3])

conn.close()
