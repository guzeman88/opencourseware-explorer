"""Fix HTML-encoded &amp; in thumbnail_url values in the DB."""
import psycopg2

import os as _os; DB = _os.environ.get("DATABASE_URL") or exit("ERROR: DATABASE_URL env var is required")
conn = psycopg2.connect(DB)
cur = conn.cursor()

# Find all courses whose thumbnail_url contains the HTML entity &amp;
cur.execute("""
    SELECT id, title, source_key, thumbnail_url
    FROM courses
    WHERE thumbnail_url LIKE '%&amp;%'
""")
rows = cur.fetchall()
print(f"Found {len(rows)} courses with &amp; in thumbnail_url:\n")

fixed = 0
for id_, title, src, thumb in rows:
    new_thumb = thumb.replace("&amp;", "&")
    print(f"  [{src}] {title}")
    print(f"    Before: {thumb[:100]}")
    print(f"    After:  {new_thumb[:100]}")
    cur.execute("UPDATE courses SET thumbnail_url = %s WHERE id = %s", (new_thumb, id_))
    fixed += 1

conn.commit()
print(f"\nFixed {fixed} thumbnail URLs.")
conn.close()
