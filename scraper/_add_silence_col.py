import psycopg2

conn = psycopg2.connect(
    "os.environ.get("DATABASE_URL") or exit("ERROR: DATABASE_URL env var is required")"
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
