import os

import psycopg2

DB = os.environ.get("DATABASE_URL")
if not DB:
    raise SystemExit("DATABASE_URL is required")
if os.environ.get("APPLY") != "1":
    raise SystemExit("Refusing to mutate the database. Set APPLY=1 after taking a backup.")
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
