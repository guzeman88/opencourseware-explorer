import psycopg2
conn = psycopg2.connect(host='127.0.0.1',port=5432,dbname='opencourseware',user='ocw',password='ocwpassword')
cur = conn.cursor()

cur.execute("SELECT source_url FROM courses WHERE source_key='berkeley' AND thumbnail_url IS NULL LIMIT 10")
print("=== BERKELEY NULL (first 10) ===")
for r in cur.fetchall(): print(" ", r[0])

cur.execute("SELECT source_url FROM courses WHERE source_key='caltech' AND thumbnail_url IS NULL LIMIT 10")
print("\n=== CALTECH NULL ===")
for r in cur.fetchall(): print(" ", r[0])

cur.execute("SELECT source_url, thumbnail_url FROM courses WHERE source_key='berkeley' AND thumbnail_url IS NOT NULL LIMIT 5")
print("\n=== BERKELEY SUCCEEDED (first 5) ===")
for r in cur.fetchall(): print(" ", r[0], "->", r[1][:80])

cur.execute("SELECT source_url, thumbnail_url FROM courses WHERE source_key='caltech' AND thumbnail_url IS NOT NULL LIMIT 5")
print("\n=== CALTECH SUCCEEDED ===")
for r in cur.fetchall(): print(" ", r[0], "->", r[1][:80])

# Overall stats
cur.execute("""
SELECT source_key, 
  COUNT(*) FILTER(WHERE thumbnail_url IS NOT NULL) as ok,
  COUNT(*) FILTER(WHERE thumbnail_url IS NULL) as null_
FROM courses GROUP BY source_key
HAVING COUNT(*) FILTER(WHERE thumbnail_url IS NULL) > 0
ORDER BY null_ DESC
""")
print("\n=== ALL SOURCES WITH NULL THUMBNAILS ===")
print(f"  {'source':24s}  {'ok':>5}  {'null':>5}")
for r in cur.fetchall():
    print(f"  {r[0]:24s}  {r[1]:>5}  {r[2]:>5}")

conn.close()
