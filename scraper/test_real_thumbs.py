"""
Test real thumbnail methods on 5 courses per major source.
"""
import re
import requests
import psycopg2
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

_tl = threading.local()

def get_session():
    if not hasattr(_tl, "session"):
        s = requests.Session()
        s.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        _tl.session = s
    return _tl.session

def fetch_og_image(url, timeout=12):
    if not url:
        return None
    try:
        resp = get_session().get(url, timeout=timeout, allow_redirects=True)
        if not resp.ok:
            return None
        html = resp.text
        for tag in re.findall(r'<meta\s+([^>]+?)(?:/>|>)', html, re.IGNORECASE | re.DOTALL):
            if re.search(r'og:image', tag, re.IGNORECASE):
                m = re.search(r'content=["\']([^"\']+)', tag, re.IGNORECASE)
                if m:
                    img = m.group(1).strip()
                    if img.startswith("http"):
                        return img
        for pat in [
            r'property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
            r'content=["\']([^"\']+)["\'][^>]+property=["\']og:image',
        ]:
            m = re.search(pat, html, re.IGNORECASE | re.DOTALL)
            if m:
                img = m.group(1).strip()
                if img.startswith("http"):
                    return img
    except Exception:
        pass
    return None

def yt_oembed(playlist_id):
    try:
        r = get_session().get("https://www.youtube.com/oembed",
            params={"url": f"https://www.youtube.com/playlist?list={playlist_id}", "format": "json"}, timeout=8)
        if r.ok:
            return r.json().get("thumbnail_url")
    except Exception:
        pass
    return None

def nptel_new_url(source_url):
    m = re.search(r'/courses/(\d+)/(\d+)/(\d+)/', source_url)
    if m:
        return f"https://nptel.ac.in/courses/{m.group(3)}"
    return None

conn = psycopg2.connect(host='127.0.0.1', port=5432, dbname='opencourseware', user='ocw', password='ocwpassword')
cur = conn.cursor()

# Sources to test - pick 5 each
SOURCES = ['nptel', 'harvard', 'stanford', 'berkeley', 'oxford', 'gatech',
           'yale', 'cambridge', 'cmu', 'princeton', 'open_university_uk',
           'utah_state', 'tufts', 'uci', 'jhsph_ocw', 'saylor',
           'edinburgh', 'glasgow', 'anu', 'unsw', 'umelbourne', 'uf',
           'vanderbilt', 'duke', 'uwashington', 'mit_ocw', 'caltech',
           'umich', 'upenn', 'ucsd', 'rice', 'uwashington', 'ut_austin',
           'purdue', 'crashcourse', 'khan', 'freecodecamp', 'simons', '3b1b']

tasks = []  # (source_key, title, source_url, youtube_playlist_id)

for src in SOURCES:
    cur.execute("""
        SELECT title, source_url, youtube_playlist_id
        FROM courses WHERE source_key = %s AND thumbnail_url LIKE '%%unsplash%%'
        LIMIT 3
    """, (src,))
    for row in cur.fetchall():
        tasks.append((src, row[0], row[1], row[2]))

conn.close()

def test_one(src, title, surl, playlist):
    result = None
    method = None
    # 1. YT playlist
    if playlist:
        t = yt_oembed(playlist)
        if t:
            return src, title, "yt_playlist", t

    # 2. NPTEL new URL og:image
    if src == 'nptel' and surl:
        new_url = nptel_new_url(surl)
        if new_url:
            t = fetch_og_image(new_url)
            if t:
                return src, title, "nptel_og", t

    # 3. Coursera page og:image
    if surl and "coursera.org/learn/" in surl:
        t = fetch_og_image(surl)
        if t:
            return src, title, "coursera_og", t

    # 4. edX page og:image
    if surl and "edx.org/course" in surl:
        t = fetch_og_image(surl)
        if t:
            return src, title, "edx_og", t

    # 5. Generic og:image
    if surl:
        t = fetch_og_image(surl)
        if t:
            return src, title, "generic_og", t

    return src, title, "NONE", None

results_by_source = {}

with ThreadPoolExecutor(max_workers=12) as ex:
    futures = {ex.submit(test_one, *t): t for t in tasks}
    for fut in as_completed(futures):
        src, title, method, thumb = fut.result()
        if src not in results_by_source:
            results_by_source[src] = {"ok": 0, "fail": 0, "samples": []}
        if thumb:
            results_by_source[src]["ok"] += 1
            results_by_source[src]["samples"].append((method, thumb[:70]))
        else:
            results_by_source[src]["fail"] += 1

print(f"\n{'source':22s}  ok  fail  sample_method / url")
print("=" * 90)
for src in SOURCES:
    if src not in results_by_source:
        continue
    d = results_by_source[src]
    sample = d["samples"][0] if d["samples"] else ("–", "")
    print(f"{src:22s}  {d['ok']:2d}  {d['fail']:4d}  [{sample[0]}] {sample[1]}")
