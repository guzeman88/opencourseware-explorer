import os

import psycopg2

DB = os.environ.get("DATABASE_URL")
if not DB:
    raise SystemExit("DATABASE_URL is required")
conn = psycopg2.connect(DB)
cur = conn.cursor()

cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
print("Tables:", [r[0] for r in cur.fetchall()])

cur.execute("SELECT column_name, data_type, column_default, is_nullable FROM information_schema.columns WHERE table_schema='public' AND table_name='courses' ORDER BY ordinal_position")
print("\nCourses columns:")
for r in cur.fetchall():
    print(f"  {r[0]:<30} {r[1]:<25} nullable={r[3]}")

conn.close()
