import psycopg2
conn = psycopg2.connect(
    'postgresql://postgres:nfMWCACJCkSCRLgMlDGVSzjCigUIrLHc@tramway.proxy.rlwy.net:11497/railway',
    connect_timeout=15
)
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM videos')
print('videos:', cur.fetchone()[0])
cur.execute('SELECT COUNT(*) FROM courses')
print('courses:', cur.fetchone()[0])
cur.execute('SELECT COUNT(*) FROM videos WHERE silence_segments IS NOT NULL')
print('videos with silence:', cur.fetchone()[0])
conn.close()
print('Railway OK')
