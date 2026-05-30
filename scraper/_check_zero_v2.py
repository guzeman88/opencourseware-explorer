import os, psycopg2
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

cur.execute("SELECT title FROM courses WHERE is_published=TRUE AND LOWER(title) LIKE '%asic%' LIMIT 10")
print('ASIC courses:', [r[0] for r in cur.fetchall()])

cur.execute("SELECT title FROM courses WHERE is_published=TRUE AND LOWER(title) LIKE '%wave%' LIMIT 10")
print('Wave courses:', [r[0] for r in cur.fetchall()])

cur.execute("SELECT title FROM courses WHERE is_published=TRUE AND LOWER(title) LIKE '%oscillation%' LIMIT 10")
print('Oscillation courses:', [r[0] for r in cur.fetchall()])

cur.execute("SELECT title FROM courses WHERE is_published=TRUE AND LOWER(title) LIKE '%photon%' LIMIT 5")
print('Photon courses:', [r[0] for r in cur.fetchall()])

cur.execute("SELECT title FROM courses WHERE is_published=TRUE AND LOWER(title) LIKE '%vlsi%' LIMIT 5")
print('VLSI courses:', [r[0] for r in cur.fetchall()])

cur.execute("SELECT title FROM courses WHERE is_published=TRUE AND LOWER(title) LIKE '%stochastic%' LIMIT 5")
print('Stochastic courses:', [r[0] for r in cur.fetchall()])

conn.close()
