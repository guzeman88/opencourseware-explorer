"""Final targeted tests: Coursera URL differences and YouTube deep search."""
import re, requests

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
})

import psycopg2
conn = psycopg2.connect(host='127.0.0.1',port=5432,dbname='opencourseware',user='ocw',password='ocwpassword')
cur = conn.cursor()

print("=== Coursera URLs per failing source (sample) ===")
for src in ['vanderbilt','duke','uf','edinburgh','glasgow','umelbourne','umich','ucsd','rice','purdue']:
    cur.execute("SELECT source_url FROM courses WHERE source_key=%s AND thumbnail_url LIKE '%%unsplash%%' LIMIT 1", (src,))
    row = cur.fetchone()
    if row:
        url = row[0]
        try:
            r = s.get(url, timeout=12, allow_redirects=True)
            m = re.search(r'og:image[^>]+content=["\']([^"\']+)', r.text)
            print(f"  {src:15s}: {r.status_code} final_url={r.url[:60]} og={m.group(1)[:60] if m else 'None'}")
        except Exception as e:
            print(f"  {src:15s}: error={e}")

cur.close()
conn.close()

print("\n=== YouTube playlist - deep video ID search (full page) ===")
try:
    r = s.get("https://www.youtube.com/playlist?list=PL8dPuuaLjXtKZPLYPEGLHvPUiUcRe6n8h", timeout=15)
    html = r.text
    print(f"  Page size: {len(html):,} bytes")
    # Search full page for videoId pattern
    vids = re.findall(r'"videoId":"([A-Za-z0-9_\-]{11})"', html)
    print(f"  videoId matches (full page): {vids[:5]}")
    # Try other patterns
    vids2 = re.findall(r'watch\?v=([A-Za-z0-9_\-]{11})', html)
    print(f"  watch?v= matches: {vids2[:5]}")
    # Any ytimg references in full page
    ytimgs = re.findall(r'https://i\.ytimg\.com/vi/([A-Za-z0-9_\-]{11})/', html)
    print(f"  ytimg video IDs: {ytimgs[:5]}")
    # Check for yt_initial_data structure
    m = re.search(r'ytInitialData\s*=\s*\{', html)
    if m:
        start = m.start() + len(m.group()) - 1
        # Find the matching closing brace (just take 2000 chars to check structure)
        snippet = html[start:start+2000]
        # Look for videoId within first 2KB of ytInitialData
        vids3 = re.findall(r'"videoId"\s*:\s*"([A-Za-z0-9_\-]{11})"', snippet)
        print(f"  videoId in ytInitialData first 2KB: {vids3[:5]}")
        print(f"  ytInitialData first 500 chars: {snippet[:500]}")
except Exception as e:
    print(f"  error: {e}")
