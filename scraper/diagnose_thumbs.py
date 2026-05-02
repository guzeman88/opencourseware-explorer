import psycopg2
import requests
import re

conn = psycopg2.connect(host='127.0.0.1', port=5432, dbname='opencourseware', user='ocw', password='ocwpassword')
cur = conn.cursor()

# How many unsplash courses have videos stored?
cur.execute("""
SELECT c.source_key,
  COUNT(*) total_unsplash,
  COUNT(CASE WHEN v.youtube_id IS NOT NULL THEN 1 END) has_video
FROM courses c
LEFT JOIN LATERAL (
  SELECT youtube_id FROM videos WHERE course_id = c.id ORDER BY "order" ASC LIMIT 1
) v ON TRUE
WHERE c.thumbnail_url LIKE '%unsplash%'
GROUP BY c.source_key
ORDER BY total_unsplash DESC
""")
rows = cur.fetchall()
print(f"{'source':22s}  {'unsplash':>8}  {'has_video':>9}  {'no_video':>8}")
print("-"*55)
for r in rows:
    no_vid = r[1] - r[2]
    print(f"{r[0]:22s}  {r[1]:8d}  {r[2]:9d}  {no_vid:8d}")

total_unsplash = sum(r[1] for r in rows)
total_has_video = sum(r[2] for r in rows)
print(f"\nTotal unsplash: {total_unsplash}, with video: {total_has_video}, no video: {total_unsplash - total_has_video}")

# Test NPTEL URL formats
print("\n\nTesting NPTEL URL formats:")
s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

cur.execute("SELECT source_url FROM courses WHERE source_key='nptel' LIMIT 3")
nptel_urls = [r[0] for r in cur.fetchall()]
for url in nptel_urls:
    # Try new format: extract course ID
    m = re.search(r'/courses/(\d+)/(\d+)/(\d+)/', url)
    if m:
        new_url = f"https://nptel.ac.in/courses/{m.group(3)}"
        try:
            resp = s.get(new_url, timeout=8, allow_redirects=True)
            print(f"  old: {url}")
            print(f"  new: {new_url} → {resp.status_code}")
            if resp.ok:
                # Check for og:image
                for tag in re.findall(r'<meta\s+([^>]+?)(?:/>|>)', resp.text, re.IGNORECASE | re.DOTALL):
                    if re.search(r'og:image', tag, re.IGNORECASE):
                        m2 = re.search(r'content=["\']([^"\']+)', tag, re.IGNORECASE)
                        if m2:
                            print(f"  og:image: {m2.group(1)[:80]}")
                        break
        except Exception as e:
            print(f"  ERROR: {e}")

# Test if Harvard og:image truncated URL works
print("\n\nFull Harvard og:image:")
cur.execute("SELECT source_url FROM courses WHERE source_key='harvard' AND thumbnail_url LIKE '%unsplash%' LIMIT 1")
hurl = cur.fetchone()[0]
try:
    resp = s.get(hurl, timeout=10, allow_redirects=True)
    print(f"  {hurl} → {resp.status_code}")
    for tag in re.findall(r'<meta\s+([^>]+?)(?:/>|>)', resp.text, re.IGNORECASE | re.DOTALL):
        if re.search(r'og:image', tag, re.IGNORECASE):
            m2 = re.search(r'content=["\']([^"\']+)', tag, re.IGNORECASE)
            if m2:
                print(f"  og:image: {m2.group(1)[:100]}")
            break
except Exception as e:
    print(f"  ERROR: {e}")

# Test img.youtube.com for a known NPTEL video
cur.execute("""
SELECT c.title, v.youtube_id
FROM courses c
JOIN videos v ON v.course_id = c.id
WHERE c.source_key = 'nptel'
LIMIT 3
""")
vids = cur.fetchall()
print(f"\nNPTEL videos in DB:")
for title, yt_id in vids:
    url = f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg"
    try:
        resp = s.head(url, timeout=6)
        print(f"  {title[:40]:40s} → {url[:60]} {resp.status_code}")
    except Exception as e:
        print(f"  ERROR: {e}")

conn.close()
