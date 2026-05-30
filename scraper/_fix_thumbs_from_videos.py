"""
Fix thumbnails for published courses that:
1. Still have Unsplash fallback thumbnails
2. Now have videos in the videos table (added by backfill_videos.py)

Uses the first video's YouTube ID to construct a real thumbnail URL.
"""
import psycopg2, os, urllib.request

DB = os.environ['DATABASE_URL']
conn = psycopg2.connect(DB)
cur = conn.cursor()

# Find published courses with Unsplash thumbnails that have videos
cur.execute("""
    SELECT c.id, c.title, c.source_key, MIN(v.youtube_id) as first_vid
    FROM courses c
    JOIN videos v ON v.course_id = c.id
    WHERE c.is_published = TRUE
      AND c.thumbnail_url LIKE '%unsplash%'
      AND v.youtube_id IS NOT NULL
    GROUP BY c.id, c.title, c.source_key
    ORDER BY c.source_key, c.title
""")
rows = cur.fetchall()
print(f"Courses to fix: {len(rows)}")

updated = 0
for cid, title, skey, vid_id in rows:
    # Try maxresdefault, then hqdefault
    thumb = None
    for size in ("maxresdefault", "hqdefault"):
        url = f"https://i.ytimg.com/vi/{vid_id}/{size}.jpg"
        try:
            req = urllib.request.urlopen(url, timeout=8)
            if req.status == 200:
                thumb = url
                break
        except Exception:
            pass
    if thumb:
        cur.execute("UPDATE courses SET thumbnail_url=%s WHERE id=%s", (thumb, cid))
        updated += 1
        print(f"  OK [{skey}] {title[:55]}")

conn.commit()
print(f"\nDone. Fixed: {updated}/{len(rows)}")
cur.close()
conn.close()
