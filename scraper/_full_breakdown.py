import psycopg2, os, unicodedata

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

# Full breakdown: published vs unpublished by source
cur.execute("""
    SELECT c.source_key, u.name,
           COUNT(*) FILTER (WHERE c.is_published=TRUE)  AS pub,
           COUNT(*) FILTER (WHERE c.is_published=FALSE) AS unpub,
           COUNT(*) AS total
    FROM courses c
    JOIN universities u ON c.university_id = u.id
    GROUP BY c.source_key, u.name
    ORDER BY pub DESC, total DESC
""")
rows = cur.fetchall()

print(f"{'source_key':<32} {'university':<40} {'pub':>5} {'unpub':>6} {'total':>6}")
print("-" * 93)
total_pub = total_unpub = 0
for sk, name, pub, unpub, total in rows:
    total_pub += pub
    total_unpub += unpub
    print(f"{sk:<32} {name:<40} {pub:>5} {unpub:>6} {total:>6}")

print("-" * 93)
print(f"{'TOTAL':<73} {total_pub:>5} {total_unpub:>6} {total_pub+total_unpub:>6}")

# Non-English (Cyrillic or CJK) published courses by source
print("\n\nNon-English published courses (Cyrillic / Arabic / CJK in title):")
cur.execute("""
    SELECT c.source_key, COUNT(*) FROM courses c
    WHERE c.is_published = TRUE
    AND (title ~ '[\\u0400-\\u04FF]'   -- Cyrillic
      OR title ~ '[\\u0600-\\u06FF]'   -- Arabic
      OR title ~ '[\\u4E00-\\u9FFF]'   -- CJK
      OR title ~ '[\\u3040-\\u30FF]'   -- Japanese
    )
    GROUP BY c.source_key ORDER BY COUNT(*) DESC
""")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

# Sample non-English
cur.execute("""
    SELECT c.source_key, c.title FROM courses c
    WHERE c.is_published = TRUE
    AND (title ~ '[\\u0400-\\u04FF]'
      OR title ~ '[\\u0600-\\u06FF]'
      OR title ~ '[\\u4E00-\\u9FFF]'
      OR title ~ '[\\u3040-\\u30FF]'
    )
    ORDER BY c.source_key, c.title
    LIMIT 10
""")
print("\nSample non-English titles:")
for r in cur.fetchall():
    print(f"  [{r[0]}] {r[1][:70]}")

conn.close()
