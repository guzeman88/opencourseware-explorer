import os, psycopg2
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute("SELECT slug FROM subjects WHERE slug LIKE '%measure%' OR slug LIKE '%calcul%'")
print('Matching subjects:', cur.fetchall())
conn.close()
