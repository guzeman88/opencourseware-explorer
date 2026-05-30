"""Apply schema to Neon and check tables."""
import psycopg2

import os
NEON_URL = os.environ["DATABASE_URL"]

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
