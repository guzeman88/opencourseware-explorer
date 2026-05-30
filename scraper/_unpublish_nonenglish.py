import psycopg2, os

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

# Find and unpublish all courses with non-English (non-ASCII-Latin) titles
cur.execute("""
    UPDATE courses
    SET is_published = FALSE
    WHERE is_published = TRUE
    AND (title ~ '[\\u0400-\\u04FF]'   -- Cyrillic
      OR title ~ '[\\u0600-\\u06FF]'   -- Arabic
      OR title ~ '[\\u4E00-\\u9FFF]'   -- CJK Unified
      OR title ~ '[\\u3040-\\u30FF]'   -- Hiragana/Katakana
      OR title ~ '[\\uAC00-\\uD7AF]'   -- Korean Hangul
    )
    RETURNING source_key, title
""")
unpublished = cur.fetchall()

print(f"Unpublished {len(unpublished)} non-English courses:")
from collections import Counter
by_source = Counter(r[0] for r in unpublished)
for src, cnt in sorted(by_source.items(), key=lambda x: -x[1]):
    print(f"  {src}: {cnt}")

print("\nSample titles unpublished:")
for sk, title in unpublished[:10]:
    print(f"  [{sk}] {title[:70]}")

conn.commit()
conn.close()
print("\nDone.")
