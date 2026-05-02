"""
Test Khan Academy API and MIT YouTube for NULL-thumbnail courses.
"""
import re, requests, psycopg2

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
})

conn = psycopg2.connect(host='127.0.0.1',port=5432,dbname='opencourseware',user='ocw',password='ocwpassword')
cur = conn.cursor()

# Test Khan Academy API
cur.execute("SELECT id, title, source_url FROM courses WHERE source_key='khan' AND thumbnail_url IS NULL LIMIT 5")
khan_rows = cur.fetchall()

print("=== KHAN ACADEMY API ===")
for cid, title, surl in khan_rows:
    # Extract slug from URL: https://www.khanacademy.org/math/algebra2
    m = re.search(r'khanacademy\.org/(.+?)/?$', surl)
    if not m:
        print(f"  NO SLUG: {surl}")
        continue
    slug = m.group(1).strip('/')
    api_url = f"https://www.khanacademy.org/api/v1/topic/{slug}"
    print(f"\n  {title[:40]}")
    print(f"  API: {api_url}")
    try:
        r = s.get(api_url, timeout=12)
        print(f"  HTTP {r.status_code}")
        if r.ok:
            data = r.json()
            # Look for image fields
            for key in ['thumbnail_url', 'image_url', 'icon_url', 'author_avatar']:
                if key in data:
                    print(f"  {key}: {data[key]}")
            # Also look recursively for image
            def find_img(obj, depth=0):
                if depth > 2: return
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if 'image' in k.lower() or 'thumb' in k.lower() or 'icon' in k.lower():
                            if isinstance(v, str) and v.startswith('http'):
                                print(f"  {k}: {v[:100]}")
                        find_img(v, depth+1)
            find_img(data)
    except Exception as e:
        print(f"  ERROR: {e}")

# Test MIT YouTube
cur.execute("SELECT id, title, source_url FROM courses WHERE source_key='mit_youtube' AND thumbnail_url IS NULL LIMIT 5")
mit_rows = cur.fetchall()

print("\n\n=== MIT YOUTUBE ===")
for cid, title, surl in mit_rows:
    print(f"\n  {title[:50]}")
    print(f"  URL: {surl}")
    try:
        r = s.get(surl, timeout=12, allow_redirects=True)
        print(f"  HTTP {r.status_code}")
        html = r.text
        for tag in re.findall(r'<meta\s+([^>]+?)(?:/>|>)', html, re.IGNORECASE | re.DOTALL):
            if re.search(r'og:image', tag, re.IGNORECASE):
                m = re.search(r'content=["\']([^"\']+)', tag, re.IGNORECASE)
                if m:
                    print(f"  og:image: {m.group(1)[:100]}")
    except Exception as e:
        print(f"  ERROR: {e}")

# Check Simons NULL
cur.execute("SELECT id, title, source_url FROM courses WHERE source_key='simons' AND thumbnail_url IS NULL LIMIT 5")
si_rows = cur.fetchall()
print("\n\n=== SIMONS NULL ===")
for cid, title, surl in si_rows:
    print(f"\n  {title[:50]}")
    print(f"  URL: {surl}")
    try:
        r = s.get(surl, timeout=12, allow_redirects=True)
        print(f"  HTTP {r.status_code}")
        html = r.text
        for tag in re.findall(r'<meta\s+([^>]+?)(?:/>|>)', html, re.IGNORECASE | re.DOTALL):
            if re.search(r'og:image', tag, re.IGNORECASE):
                m = re.search(r'content=["\']([^"\']+)', tag, re.IGNORECASE)
                if m:
                    print(f"  og:image: {m.group(1)[:100]}")
    except Exception as e:
        print(f"  ERROR: {e}")

conn.close()
