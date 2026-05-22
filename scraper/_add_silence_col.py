import psycopg2

conn = psycopg2.connect(
    "postgresql://neondb_owner:npg_GbATRcy2v8Fo@ep-gentle-cherry-an1c9y9a-pooler.c-6.us-east-1.aws.neon.tech/opencourseware?sslmode=require"
)
cur = conn.cursor()
cur.execute("ALTER TABLE videos ADD COLUMN IF NOT EXISTS silence_segments JSONB")
conn.commit()
cur.execute(
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_name='videos' AND column_name='silence_segments'"
)
row = cur.fetchone()
print("Column exists:", row)
conn.close()
