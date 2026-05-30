import psycopg2, os

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

# How many published courses have NO subjects
cur.execute("""
    SELECT COUNT(*) FROM courses c
    WHERE c.is_published = TRUE
    AND NOT EXISTS (SELECT 1 FROM course_subjects cs WHERE cs.course_id = c.id)
""")
print("Published courses with NO subjects:", cur.fetchone()[0])

# How many published courses HAVE subjects
cur.execute("""
    SELECT COUNT(DISTINCT c.id) FROM courses c
    JOIN course_subjects cs ON cs.course_id = c.id
    WHERE c.is_published = TRUE
""")
print("Published courses WITH subjects:", cur.fetchone()[0])

# Top 30 subject slugs by course count
cur.execute("""
    SELECT s.slug, s.name, COUNT(cs.course_id) AS n
    FROM subjects s
    JOIN course_subjects cs ON cs.subject_id = s.id
    JOIN courses c ON c.id = cs.course_id AND c.is_published = TRUE
    GROUP BY s.slug, s.name
    ORDER BY n DESC LIMIT 30
""")
print("\nTop 30 subjects (slug / name / count):")
for row in cur.fetchall():
    print(f"  {row[0]:<40} {row[1]:<35} {row[2]}")

# Also check subjects that exist in the DB but with 0 published courses
cur.execute("""
    SELECT s.slug, s.name
    FROM subjects s
    WHERE NOT EXISTS (
        SELECT 1 FROM course_subjects cs
        JOIN courses c ON c.id = cs.course_id AND c.is_published = TRUE
        WHERE cs.subject_id = s.id
    )
    ORDER BY s.name
""")
zero_subjects = cur.fetchall()
print(f"\nSubjects with 0 published courses: {len(zero_subjects)}")
for row in zero_subjects[:20]:
    print(f"  {row[0]}")

conn.close()
