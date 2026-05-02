"""
Test og:image for sources we haven't specifically investigated:
GaTech, Stanford, Berkeley, Cambridge, Princeton
"""
import re, requests, psycopg2

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
})

def fetch_og(url):
    try:
        r = s.get(url, timeout=12, allow_redirects=True)
        if not r.ok:
            return None, r.status_code
        html = r.text
        for tag in re.findall(r'<meta\s+([^>]+?)(?:/>|>)', html, re.IGNORECASE | re.DOTALL):
            if re.search(r'og:image', tag, re.IGNORECASE):
                m = re.search(r'content=["\']([^"\']+)', tag, re.IGNORECASE)
                if m:
                    img = m.group(1).strip()
                    if img.startswith("http"):
                        return img, r.status_code
        return None, r.status_code
    except Exception as e:
        return None, str(e)

conn = psycopg2.connect(host='127.0.0.1',port=5432,dbname='opencourseware',user='ocw',password='ocwpassword')
cur = conn.cursor()

for source in ['gatech', 'stanford', 'cambridge', 'princeton', 'khan', 'unsw', 'ut_austin', 'anu', 'purdue']:
    cur.execute("""
        SELECT source_url FROM courses 
        WHERE source_key = %s AND thumbnail_url IS NULL 
        LIMIT 3
    """, (source,))
    rows = cur.fetchall()
    if not rows:
        continue
    print(f"\n=== {source.upper()} ===")
    for (url,) in rows:
        img, status = fetch_og(url)
        print(f"  [{status}] {url[:70]}")
        if img:
            print(f"         og:image = {img[:80]}")

conn.close()
