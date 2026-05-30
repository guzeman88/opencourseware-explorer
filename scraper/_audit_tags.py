"""
Audit tag quality - find likely false positives for specific subjects.
"""
import os, psycopg2

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Check real-analysis tagged courses
print("=== REAL-ANALYSIS tagged courses (sample 20) ===")
cur.execute("""
    SELECT c.title FROM courses c
    JOIN course_subjects cs ON cs.course_id = c.id
    JOIN subjects s ON s.id = cs.subject_id
    WHERE s.slug = 'real-analysis' AND c.is_published = TRUE
    ORDER BY c.title LIMIT 20
""")
for row in cur.fetchall(): print(f"  {row[0]}")

print("\n=== CALCULUS tagged courses that look suspicious (sample) ===")
cur.execute("""
    SELECT c.title FROM courses c
    JOIN course_subjects cs ON cs.course_id = c.id
    JOIN subjects s ON s.id = cs.subject_id
    WHERE s.slug = 'calculus' AND c.is_published = TRUE
    AND LOWER(c.title) NOT LIKE '%calculus%'
    AND LOWER(c.title) NOT LIKE '%differentiat%'
    AND LOWER(c.title) NOT LIKE '%integral%'
    AND LOWER(c.title) NOT LIKE '%multivariable%'
    ORDER BY c.title LIMIT 20
""")
for row in cur.fetchall(): print(f"  {row[0]}")

print("\n=== ANALYSIS tagged courses that look suspicious ===")
cur.execute("""
    SELECT c.title FROM courses c
    JOIN course_subjects cs ON cs.course_id = c.id
    JOIN subjects s ON s.id = cs.subject_id
    WHERE s.slug = 'analysis' AND c.is_published = TRUE
    AND LOWER(c.title) NOT LIKE '%real analysis%'
    AND LOWER(c.title) NOT LIKE '%complex analysis%'
    AND LOWER(c.title) NOT LIKE '%mathematical analysis%'
    AND LOWER(c.title) NOT LIKE '%functional analysis%'
    AND LOWER(c.title) NOT LIKE '%advanced calculus%'
    ORDER BY c.title LIMIT 20
""")
for row in cur.fetchall(): print(f"  {row[0]}")

print("\n=== ALGORITHMS tagged but probably just 'computational X' ===")
cur.execute("""
    SELECT c.title FROM courses c
    JOIN course_subjects cs ON cs.course_id = c.id
    JOIN subjects s ON s.id = cs.subject_id
    WHERE s.slug = 'algorithms' AND c.is_published = TRUE
    AND LOWER(c.title) NOT LIKE '%algorithm%'
    AND LOWER(c.title) NOT LIKE '%data structure%'
    AND LOWER(c.title) NOT LIKE '%complexity%'
    AND LOWER(c.title) NOT LIKE '%combinatorics%'
    AND LOWER(c.title) NOT LIKE '%graph theory%'
    AND LOWER(c.title) NOT LIKE '%discrete math%'
    ORDER BY c.title LIMIT 20
""")
for row in cur.fetchall(): print(f"  {row[0]}")

print("\n=== LITERATURE tagged with suspicious titles ===")
cur.execute("""
    SELECT c.title FROM courses c
    JOIN course_subjects cs ON cs.course_id = c.id
    JOIN subjects s ON s.id = cs.subject_id
    WHERE s.slug = 'literature' AND c.is_published = TRUE
    AND LOWER(c.title) NOT LIKE '%literature%'
    AND LOWER(c.title) NOT LIKE '%literary%'
    AND LOWER(c.title) NOT LIKE '%poetry%'
    AND LOWER(c.title) NOT LIKE '%novel%'
    AND LOWER(c.title) NOT LIKE '%fiction%'
    AND LOWER(c.title) NOT LIKE '%writing%'
    AND LOWER(c.title) NOT LIKE '%rhetoric%'
    AND LOWER(c.title) NOT LIKE '%linguistics%'
    ORDER BY c.title LIMIT 20
""")
for row in cur.fetchall(): print(f"  {row[0]}")

print("\n=== NETWORKING tagged but looks like ML/physics ===")
cur.execute("""
    SELECT c.title FROM courses c
    JOIN course_subjects cs ON cs.course_id = c.id
    JOIN subjects s ON s.id = cs.subject_id
    WHERE s.slug = 'networking' AND c.is_published = TRUE
    AND LOWER(c.title) NOT LIKE '%network%'
    AND LOWER(c.title) NOT LIKE '%internet%'
    AND LOWER(c.title) NOT LIKE '%protocol%'
    AND LOWER(c.title) NOT LIKE '%tcp%'
    ORDER BY c.title LIMIT 15
""")
for row in cur.fetchall(): print(f"  {row[0]}")

print("\n=== MACHINE LEARNING tagged non-ML courses (matching 'regression'/'classification' only) ===")
cur.execute("""
    SELECT c.title FROM courses c
    JOIN course_subjects cs ON cs.course_id = c.id
    JOIN subjects s ON s.id = cs.subject_id
    WHERE s.slug = 'machine-learning' AND c.is_published = TRUE
    AND LOWER(c.title) NOT LIKE '%machine learning%'
    AND LOWER(c.title) NOT LIKE '%ml %'
    AND LOWER(c.title) NOT LIKE '%supervised%'
    AND LOWER(c.title) NOT LIKE '%unsupervised%'
    AND LOWER(c.title) NOT LIKE '%neural network%'
    AND LOWER(c.title) NOT LIKE '%deep learning%'
    AND LOWER(c.title) NOT LIKE '%data science%'
    ORDER BY c.title LIMIT 20
""")
for row in cur.fetchall(): print(f"  {row[0]}")

conn.close()
