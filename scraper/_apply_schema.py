"""Apply schema to Neon and check tables."""
import psycopg2

NEON_URL = "postgresql://neondb_owner:npg_GbATRcy2v8Fo@ep-gentle-cherry-an1c9y9a-pooler.c-6.us-east-1.aws.neon.tech/opencourseware?channel_binding=require&sslmode=require"

conn = psycopg2.connect(NEON_URL, connect_timeout=15)
conn.autocommit = True
cur = conn.cursor()

with open("../schema_only.sql", "r", encoding="utf-8") as f:
    sql = f.read()

# Remove GRANT lines that reference the 'ocw' role (doesn't exist on Neon)
import re
sql = re.sub(r'GRANT .+ TO ocw;\n?', '', sql)

cur.execute(sql)
print("Schema applied successfully")

cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
tables = [r[0] for r in cur.fetchall()]
print(f"Tables ({len(tables)}):", tables)

cur.close()
conn.close()
