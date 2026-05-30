"""
Find the specific keyword causing each false positive tag.
"""
import os, psycopg2, re

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

def check_keyword_false_positives(slug, keywords, bad_terms, limit=15):
    """Find courses tagged with `slug` where title doesn't look related."""
    print(f"\n=== {slug.upper()} - suspicious tags ===")
    for kw in keywords:
        cur.execute("""
            SELECT c.title, c.description FROM courses c
            JOIN course_subjects cs ON cs.course_id = c.id
            JOIN subjects s ON s.id = cs.subject_id
            WHERE s.slug = %s AND c.is_published = TRUE
            AND LOWER(c.title || ' ' || COALESCE(c.description,'')) LIKE %s
        """, (slug, f'%{kw}%'))
        rows = cur.fetchall()
        suspicious = [(t, d) for t, d in rows 
                      if not any(bt in t.lower() for bt in [slug.replace('-',' ')] + 
                                  [s.replace('-',' ') for s in slug.split('-')])]
        if suspicious:
            print(f"  Keyword '{kw}' matches {len(suspicious)} potentially wrong courses:")
            for t, d in suspicious[:5]:
                print(f"    - {t}")

# Check analysis i / analysis ii problem
print("=== KEYWORD 'analysis i' matches (first 15) ===")
cur.execute("""
    SELECT title FROM courses WHERE is_published=TRUE 
    AND LOWER(title) LIKE '%analysis i%'
    AND LOWER(title) NOT LIKE '%real analysis%'
    AND LOWER(title) NOT LIKE '%mathematical analysis%'
    AND LOWER(title) NOT LIKE '%complex analysis%'
    AND LOWER(title) NOT LIKE '%functional analysis%'
    LIMIT 15
""")
for row in cur.fetchall(): print(f"  {row[0]}")

print("\n=== KEYWORD 'analysis ii' matches (first 15) ===")
cur.execute("""
    SELECT title FROM courses WHERE is_published=TRUE 
    AND LOWER(title) LIKE '%analysis ii%'
    AND LOWER(title) NOT LIKE '%real analysis%'
    AND LOWER(title) NOT LIKE '%mathematical analysis%'
    LIMIT 15
""")
for row in cur.fetchall(): print(f"  {row[0]}")

print("\n=== KEYWORD 'computational' in algorithms - suspicious matches ===")
cur.execute("""
    SELECT title FROM courses WHERE is_published=TRUE 
    AND LOWER(title) LIKE '%computational%'
    AND LOWER(title) NOT LIKE '%algorithm%'
    AND LOWER(title) NOT LIKE '%complexity%'
    AND LOWER(title) NOT LIKE '%data structure%'
    LIMIT 20
""")
for row in cur.fetchall(): print(f"  {row[0]}")

print("\n=== KEYWORD 'language' in literature - suspicious matches ===")
cur.execute("""
    SELECT title FROM courses WHERE is_published=TRUE 
    AND LOWER(title) LIKE '%language%'
    AND LOWER(title) NOT LIKE '%linguistics%'
    AND LOWER(title) NOT LIKE '%literature%'
    LIMIT 20
""")
for row in cur.fetchall(): print(f"  {row[0]}")

print("\n=== KEYWORD 'integration' in calculus - suspicious matches ===")
cur.execute("""
    SELECT title FROM courses WHERE is_published=TRUE 
    AND LOWER(title) LIKE '%integration%'
    AND LOWER(title) NOT LIKE '%calculus%'
    AND LOWER(title) NOT LIKE '%integral%'
    AND LOWER(title) NOT LIKE '%math%'
    LIMIT 15
""")
for row in cur.fetchall(): print(f"  {row[0]}")

print("\n=== KEYWORD 'differentiation' in calculus - suspicious matches ===")
cur.execute("""
    SELECT title FROM courses WHERE is_published=TRUE 
    AND LOWER(title) LIKE '%differentiat%'
    AND LOWER(title) NOT LIKE '%calculus%'
    AND LOWER(title) NOT LIKE '%differential%'
    LIMIT 10
""")
for row in cur.fetchall(): print(f"  {row[0]}")

print("\n=== KEYWORD 'development' in sociology broad - suspicious matches ===")
cur.execute("""
    SELECT title FROM courses WHERE is_published=TRUE 
    AND LOWER(title) LIKE '%development%'
    AND LOWER(title) NOT LIKE '%social%'
    AND LOWER(title) NOT LIKE '%community%'
    AND LOWER(title) NOT LIKE '%urban%'
    LIMIT 15
""")
for row in cur.fetchall(): print(f"  {row[0]}")

print("\n=== KEYWORD 'planning' in AI rule - suspicious matches ===")
cur.execute("""
    SELECT title FROM courses WHERE is_published=TRUE 
    AND LOWER(title) LIKE '%planning%'
    AND LOWER(title) NOT LIKE '%artificial intelligence%'
    AND LOWER(title) NOT LIKE '% ai %'
    LIMIT 10
""")
for row in cur.fetchall(): print(f"  {row[0]}")

conn.close()
