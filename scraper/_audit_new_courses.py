import psycopg2, os

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

# Breakdown by source_key for all published courses
cur.execute("""
    SELECT c.source_key, COUNT(*) as cnt,
           u.name as university_name
    FROM courses c
    LEFT JOIN universities u ON c.university_id = u.id
    WHERE c.is_published = TRUE
    GROUP BY c.source_key, u.name
    ORDER BY cnt DESC
""")
print("Published courses by source:")
for r in cur.fetchall():
    print(f"  {r[0]:30s} {r[1]:5d}  [{r[2] or 'no university'}]")

print()

# Sample new courses from non-traditional channels
cur.execute("""
    SELECT c.title, c.source_key, c.total_videos, c.thumbnail_url
    FROM courses c
    WHERE c.is_published = TRUE
    AND c.source_key IN ('math_with_richard','faculty_of_khan','mathmajor','jeffrey_chasnov')
    ORDER BY c.source_key, c.title
    LIMIT 20
""")
print("Sample non-institutional courses:")
for r in cur.fetchall():
    thumb = "ytimg" if r[3] and "ytimg" in r[3] else "other"
    print(f"  [{r[1]}] {r[0][:55]} ({r[2]}v) {thumb}")

print()

# Check if any courses have non-Latin titles (quick check via title length vs ASCII chars)
cur.execute("""
    SELECT source_key, COUNT(*) FROM courses
    WHERE is_published = TRUE
    AND title != convert_from(convert_to(title, 'ASCII'), 'ASCII')
    GROUP BY source_key ORDER BY COUNT(*) DESC
    LIMIT 10
""")
print("Courses with non-ASCII titles by source:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

conn.close()
