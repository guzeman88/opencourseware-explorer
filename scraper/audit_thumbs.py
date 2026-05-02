import psycopg2

conn = psycopg2.connect(host='127.0.0.1', port=5432, dbname='opencourseware', user='ocw', password='ocwpassword')
cur = conn.cursor()

cur.execute("""
SELECT source_key,
  COUNT(*) total,
  COUNT(CASE WHEN thumbnail_url LIKE '%unsplash%' THEN 1 END) unsplash,
  COUNT(CASE WHEN thumbnail_url NOT LIKE '%unsplash%' THEN 1 END) real_thumb
FROM courses
GROUP BY source_key
ORDER BY unsplash DESC, total DESC
""")
rows = cur.fetchall()
print(f"{'source':25s} {'total':>6} {'unsplash':>9} {'real':>6}")
print("-" * 52)
for r in rows:
    print(f"{r[0]:25s} {r[1]:6d} {r[2]:9d} {r[3]:6d}")

print()
# Sample some source_urls per source that still has unsplash
cur.execute("""
SELECT DISTINCT source_key, source_url
FROM courses
WHERE thumbnail_url LIKE '%unsplash%'
ORDER BY source_key
LIMIT 60
""")
print("\nSample URLs per source (unsplash courses):")
last = None
for sk, url in cur.fetchall():
    if sk != last:
        print(f"\n[{sk}]")
        last = sk
    print(f"  {url}")

conn.close()
