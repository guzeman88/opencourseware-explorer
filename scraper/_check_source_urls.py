import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM courses WHERE is_published=TRUE AND source_url IS NOT NULL AND source_url != ''")
print('Published with source_url:', cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM courses WHERE is_published=TRUE AND source_url IS NULL")
print('Published with NULL source_url:', cur.fetchone()[0])

cur.execute("""
SELECT source_key, COUNT(*) as n, 
  COUNT(CASE WHEN source_url IS NULL THEN 1 END) as no_url
FROM courses WHERE is_published=TRUE
GROUP BY source_key ORDER BY 2 DESC LIMIT 15
""")
print('\nsource_key | total | no_url')
for r in cur.fetchall():
    print(f'  {r[0]:20s} {r[1]:5d} {r[2]:5d}')

conn.close()
