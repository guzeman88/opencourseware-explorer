import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute("SELECT source_key, COUNT(*) FROM courses WHERE is_published=TRUE AND thumbnail_url LIKE '%unsplash%' GROUP BY source_key ORDER BY COUNT(*) DESC")
rows = cur.fetchall()
total = sum(r[1] for r in rows)
print(f"Total published with Unsplash: {total}")
print()
for sk, cnt in rows:
    print(f"  {sk}: {cnt}")
cur.execute("SELECT COUNT(*) FROM courses WHERE is_published=TRUE AND thumbnail_url LIKE '%unsplash%' AND youtube_playlist_id IS NOT NULL")
print(f"\nWith youtube_playlist_id: {cur.fetchone()[0]}")
conn.close()
