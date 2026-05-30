import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM courses WHERE is_published=TRUE')
print('Published:', cur.fetchone()[0])

cur.execute('SELECT COUNT(*) FROM courses WHERE is_published=TRUE AND thumbnail_url IS NOT NULL')
print('Published with thumbnail:', cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM courses WHERE is_published=TRUE AND thumbnail_url LIKE '%unsplash%'")
print('Published with Unsplash fallback:', cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM courses WHERE is_published=TRUE AND thumbnail_url IS NOT NULL AND thumbnail_url NOT LIKE '%unsplash%'")
print('Published with real thumbnail:', cur.fetchone()[0])

cur.execute('SELECT COUNT(*) FROM courses WHERE is_published=TRUE AND youtube_playlist_id IS NOT NULL')
print('Published with youtube_playlist_id:', cur.fetchone()[0])

# Real thumbnails by source
cur.execute("""
    SELECT u.slug, COUNT(*) as real_thumbs
    FROM courses c JOIN universities u ON c.university_id = u.id
    WHERE c.is_published=TRUE
      AND c.thumbnail_url IS NOT NULL
      AND c.thumbnail_url NOT LIKE '%unsplash%'
    GROUP BY u.slug ORDER BY real_thumbs DESC LIMIT 15
""")
print('\nReal thumbnails by source:')
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]}')

conn.close()
