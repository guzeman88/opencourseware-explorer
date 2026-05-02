import psycopg2
conn = psycopg2.connect(host='127.0.0.1',port=5432,dbname='opencourseware',user='ocw',password='ocwpassword')
cur = conn.cursor()

# How did CrashCourse/3b1b get thumbnails?
for src in ['crashcourse', '3b1b', 'gatech']:
    cur.execute("""
        SELECT title, source_url, thumbnail_url FROM courses 
        WHERE source_key = %s AND thumbnail_url IS NOT NULL
        LIMIT 3
    """, (src,))
    rows = cur.fetchall()
    print(f"\n=== {src.upper()} with thumbnails ===")
    for r in rows:
        print(f"  title: {r[0][:50]}")
        print(f"  url:   {r[1]}")
        print(f"  thumb: {r[2][:80]}")
        print()

# Count edX sources that are 404
cur.execute("""
    SELECT source_key, COUNT(*) FROM courses 
    WHERE thumbnail_url IS NULL 
    AND source_url LIKE '%edx.org%'
    GROUP BY source_key
""")
print("=== edX 404 sources ===")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]} courses")
    
conn.close()
