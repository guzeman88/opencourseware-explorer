"""
Check why Caltech and NPTEL failed, and test a few URLs directly.
"""
import re, requests, time

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})

def fetch_og(url):
    try:
        r = s.get(url, timeout=14, allow_redirects=True)
        print(f"  HTTP {r.status_code} ({len(r.text)} chars)")
        html = r.text
        for tag in re.findall(r'<meta\s+([^>]+?)(?:/>|>)', html, re.IGNORECASE | re.DOTALL):
            if re.search(r'og:image', tag, re.IGNORECASE):
                m = re.search(r'content=["\']([^"\']+)', tag, re.IGNORECASE)
                if m:
                    return m.group(1).strip()
        return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

# Test Caltech URLs
caltech_urls = [
    "https://www.cms.caltech.edu/academics/courses/cs151",
    "https://www.bbe.caltech.edu/courses/bi114",
    "https://www.cms.caltech.edu/academics/courses/cds110",
    "https://ee.caltech.edu/courses/ee126",
    "https://pma.caltech.edu/courses/ay1",
]
print("=== CALTECH ===")
for url in caltech_urls:
    print(f"\n  {url}")
    og = fetch_og(url)
    print(f"  og:image = {og}")

# Test a few NPTEL NULL ones
import psycopg2
conn = psycopg2.connect(host='127.0.0.1',port=5432,dbname='opencourseware',user='ocw',password='ocwpassword')
cur = conn.cursor()
cur.execute("SELECT id, source_url FROM courses WHERE source_key='nptel' AND thumbnail_url IS NULL LIMIT 5")
nptel_rows = cur.fetchall()
conn.close()

print("\n\n=== NPTEL NULL SAMPLES ===")
for cid, surl in nptel_rows:
    print(f"\n  {surl}")
    m = re.search(r'/courses/\d+/\d+/(\d+)/?', surl)
    if not m:
        m = re.search(r'/courses/(\d+)/?$', surl)
    if m:
        course_id = m.group(1)
        data_url = f"https://nptel.ac.in/courses/{course_id}/__data.json"
        print(f"  data_url = {data_url}")
        try:
            r = s.get(data_url, timeout=15)
            print(f"  HTTP {r.status_code}")
            if r.ok:
                data = r.json()
                # Try to find units/lessons
                for node in data.get("nodes", []):
                    if not node or node.get("type") != "data":
                        continue
                    flat = node.get("data", [])
                    if not flat or not isinstance(flat[0], dict):
                        continue
                    # Quick check - look for youtube_id string anywhere in flat
                    yt_ids = [v for v in flat if isinstance(v, str) and len(v) == 11 and re.match(r'^[A-Za-z0-9_-]{11}$', v)]
                    print(f"  Possible YT IDs in flat: {yt_ids[:5]}")
                    # Check if courseOutline exists at all
                    keys_at_0 = list(flat[0].keys()) if isinstance(flat[0], dict) else []
                    print(f"  Keys at flat[0]: {keys_at_0[:10]}")
                    break
        except Exception as e:
            print(f"  ERROR: {e}")
    else:
        print(f"  NO COURSE_ID MATCH")
