import os, psycopg2
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute("SELECT id, slug FROM subjects WHERE slug='education'")
r = cur.fetchone()
print("education slug:", r)
conn.close()
