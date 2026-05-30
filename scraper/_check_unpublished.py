import psycopg2, os

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

cur.execute("SELECT source_key, COUNT(*) FROM courses WHERE is_published=FALSE GROUP BY source_key ORDER BY COUNT(*) DESC")
print("Unpublished by source:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

cur.execute("SELECT title, source_key, source_url, thumbnail_url FROM courses WHERE is_published=FALSE LIMIT 15")
print("\nSample unpublished:")
for r in cur.fetchall():
    url = r[2][:80] if r[2] else "no url"
    thumb = "unsplash" if r[3] and "unsplash" in r[3] else ("ytimg" if r[3] and "ytimg" in r[3] else "other")
    print(f"  [{r[1]}] {r[0][:55]} | thumb:{thumb}")
    print(f"         {url}")

# Check if unpublished courses have content (videos)
cur.execute("""
    SELECT COUNT(DISTINCT c.id) FROM courses c
    JOIN videos v ON v.course_id = c.id
    WHERE c.is_published = FALSE
""")
print(f"\nUnpublished courses WITH videos: {cur.fetchone()[0]}")

# Check for duplicates among unpublished
cur.execute("""
    SELECT title, COUNT(*) FROM courses WHERE is_published=FALSE GROUP BY title HAVING COUNT(*) > 1 LIMIT 5
""")
dupes = cur.fetchall()
print(f"Unpublished with duplicate titles: {len(dupes)}")

conn.close()
