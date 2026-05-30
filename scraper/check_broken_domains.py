import psycopg2
import urllib.request
import ssl

import os as _os; DB = _os.environ.get("DATABASE_URL") or exit("ERROR: DATABASE_URL env var is required")
conn = psycopg2.connect(DB)
cur = conn.cursor()

# Domains NOT in next.config.js remotePatterns:
# video.udacity-data.com, prod-discovery.edx-cdn.org, i.ibb.co, cdn.sanity.io, s3.amazonaws.com
# Also check simons.berkeley.edu &amp; bug and Georgia Tech

cur.execute("""
    SELECT id, title, source_key, thumbnail_url
    FROM courses
    WHERE has_video_lectures = true
      AND thumbnail_url IS NOT NULL
      AND (
        thumbnail_url LIKE '%video.udacity-data.com%'
        OR thumbnail_url LIKE '%prod-discovery.edx-cdn.org%'
        OR thumbnail_url LIKE '%i.ibb.co%'
        OR thumbnail_url LIKE '%cdn.sanity.io%'
        OR thumbnail_url LIKE '%s3.amazonaws.com%'
        OR thumbnail_url LIKE '%&amp;%'
        OR thumbnail_url LIKE '%unsplash.com%'
      )
    ORDER BY source_key, title
""")
rows = cur.fetchall()
print(f"Courses with potentially broken/missing-domain thumbnails: {len(rows)}\n")
for id_, title, src, thumb in rows:
    print(f"  [{src}] {title}")
    print(f"    {thumb[:100]}")
    print()

# Also check Georgia Tech courses
print("\n--- Georgia Tech courses ---")
cur.execute("""
    SELECT id, title, source_key, thumbnail_url
    FROM courses
    WHERE has_video_lectures = true
      AND source_key = 'gatech'
    ORDER BY title
""")
for id_, title, src, thumb in cur.fetchall():
    print(f"  {title}: {(thumb or 'NULL')[:80]}")

conn.close()
