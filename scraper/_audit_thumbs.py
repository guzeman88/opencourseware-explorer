import psycopg2
conn = psycopg2.connect("postgresql://neondb_owner:npg_GbATRcy2v8Fo@ep-gentle-cherry-an1c9y9a-pooler.c-6.us-east-1.aws.neon.tech/opencourseware?sslmode=require")
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM courses")
total = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM courses WHERE thumbnail_url IS NOT NULL")
has_thumb = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM courses WHERE youtube_playlist_id IS NOT NULL")
has_yt = cur.fetchone()[0]
print(f"Total: {total}")
print(f"Has thumbnail: {has_thumb}")
print(f"No thumbnail: {total - has_thumb}")
print(f"Has youtube_playlist_id: {has_yt}")
cur.execute("SELECT source_key, COUNT(*) total, COUNT(thumbnail_url) has_thumb FROM courses GROUP BY source_key ORDER BY total DESC")
for r in cur.fetchall():
    print(f"  {r[0]:30s}  total={r[1]:5d}  thumbs={r[2]:5d}  missing={r[1]-r[2]:5d}")
conn.close()
