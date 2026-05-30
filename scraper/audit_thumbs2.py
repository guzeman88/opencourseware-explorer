import psycopg2
from urllib.parse import urlparse
from collections import Counter

import os as _os; DB = _os.environ.get("DATABASE_URL") or exit("ERROR: DATABASE_URL env var is required")
conn = psycopg2.connect(DB)
cur = conn.cursor()

# First check column names
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='courses' ORDER BY ordinal_position")
cols = [r[0] for r in cur.fetchall()]
print("Columns:", cols[:15])

# Get all has_video_lectures courses
cur.execute("""
    SELECT id, title, source_key, thumbnail_url
    FROM courses
    WHERE has_video_lectures = true
    ORDER BY source_key, title
""")
rows = cur.fetchall()
print(f"\nTotal has_video_lectures courses: {len(rows)}\n")

domain_counts = Counter()
unsplash_courses = []
null_courses = []

for id_, title, source_key, thumb in rows:
    if not thumb:
        domain_counts["NULL"] += 1
        null_courses.append((title, source_key or "?"))
    elif "unsplash.com" in thumb:
        domain_counts["UNSPLASH"] += 1
        unsplash_courses.append((title, source_key or "?", thumb))
    elif "ytimg.com" in thumb or "img.youtube.com" in thumb:
        domain_counts["YouTube (ytimg)"] += 1
    elif "ocw.mit.edu" in thumb:
        domain_counts["MIT OCW"] += 1
    else:
        host = urlparse(thumb).hostname or "unknown"
        domain_counts[host] += 1

for k, v in domain_counts.most_common():
    print(f"{v:5d}  {k}")

print("\nUNSPLASH courses still remaining:")
for title, src, thumb in unsplash_courses:
    print(f"  [{src}] {title}")

print(f"\nNULL thumbnail courses: {len(null_courses)}")
for title, src in null_courses[:10]:
    print(f"  [{src}] {title}")

conn.close()
