import psycopg2, os

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()
cur.execute("""
    SELECT c.source_key, u.name,
           COUNT(*) FILTER (WHERE c.is_published=TRUE)  AS pub,
           COUNT(*) FILTER (WHERE c.is_published=FALSE) AS unpub
    FROM courses c
    JOIN universities u ON c.university_id = u.id
    GROUP BY c.source_key, u.name
    ORDER BY pub DESC
""")
rows = cur.fetchall()
conn.close()

total_pub = sum(r[2] for r in rows)
total_unpub = sum(r[3] for r in rows)

print(f"{'source_key':<32} {'university':<42} {'visible':>7}  {'hidden':>7}")
print("-" * 95)
for sk, name, pub, unpub in rows:
    if pub > 0 or unpub > 0:
        print(f"{sk:<32} {name:<42} {pub:>7}  {unpub:>7}")
print("-" * 95)
print(f"{'TOTAL':<75} {total_pub:>7}  {total_unpub:>7}")
