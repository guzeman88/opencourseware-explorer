import psycopg2

DB = "postgresql://neondb_owner:npg_O1SmkveyKXw2@ep-blue-leaf-aq4lk4jf.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require"
conn = psycopg2.connect(DB)
cur = conn.cursor()

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='courses' AND column_name='is_published'")
if cur.fetchone():
    print("Column already exists")
else:
    cur.execute("ALTER TABLE courses ADD COLUMN is_published BOOLEAN NOT NULL DEFAULT FALSE")
    print("Column is_published added")

cur.execute("UPDATE courses SET is_published = TRUE WHERE has_video_lectures = TRUE OR youtube_playlist_id IS NOT NULL OR total_videos > 0")
print(f"Published: {cur.rowcount} video courses")

cur.execute("SELECT COUNT(*) FROM courses WHERE is_published = FALSE")
print(f"Pending (non-video OCW): {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM courses WHERE is_published = TRUE AND has_video_lectures = TRUE")
print(f"Published + has_video: {cur.fetchone()[0]}")

conn.commit()
conn.close()
print("Done.")
