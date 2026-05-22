import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:nfMWCACJCkSCRLgMlDGVSzjCigUIrLHc@tramway.proxy.rlwy.net:11497/railway'
from db_utils import get_connection
conn = get_connection()
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM videos')
print('videos:', cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM courses WHERE is_published=TRUE AND NOT EXISTS (SELECT 1 FROM videos WHERE course_id=courses.id) AND (youtube_playlist_id IS NOT NULL OR source_url ILIKE '%list=%')")
print('remaining:', cur.fetchone()[0])
conn.close()
print('DB OK')
