import psycopg2

from mutation_guard import require_explicit_apply


DATABASE_URL = require_explicit_apply("Add the legacy silence_segments column.")
conn = psycopg2.connect(DATABASE_URL)
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
