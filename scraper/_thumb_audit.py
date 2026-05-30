import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

cur.execute("""
SELECT c.source_key, 
  COUNT(*) as total,
  COUNT(CASE WHEN c.thumbnail_url NOT LIKE '%unsplash%' THEN 1 END) as real,
  COUNT(CASE WHEN c.thumbnail_url LIKE '%unsplash%' THEN 1 END) as fallback,
  SUBSTRING(MAX(CASE WHEN c.thumbnail_url NOT LIKE '%unsplash%' THEN c.thumbnail_url END), 1, 60) as sample_real
FROM courses c
WHERE c.is_published=TRUE
GROUP BY c.source_key
ORDER BY fallback DESC
""")
print(f"{'source_key':20s} {'total':6s} {'real':6s} {'fallback':8s}")
print("-" * 45)
for r in cur.fetchall():
    print(f"  {r[0]:20s} {r[1]:5d} {r[2]:5d} {r[3]:5d}   {r[4] or ''[:50]}")

conn.close()
