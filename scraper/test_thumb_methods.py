"""Quick test: verify og:image extraction works on a few representative URLs."""
import sys
sys.path.insert(0, r'C:\Users\Jorge DeGuzeman\Desktop\code-projects\Courses\opencourseware\scraper')

import re
import requests

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
})

def fetch_og_image(url, timeout=12):
    try:
        resp = s.get(url, timeout=timeout, allow_redirects=True)
        if not resp.ok:
            return f"HTTP {resp.status_code}"
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
        return "NO og:image found"
    except Exception as e:
        return f"ERROR: {e}"

def coursera_api(slug):
    try:
        r = s.get("https://api.coursera.org/api/courses.v1",
                  params={"q": "slug", "slug": slug, "fields": "photoUrl"}, timeout=10)
        if r.ok:
            elems = r.json().get("elements", [])
            if elems and elems[0].get("photoUrl"):
                return elems[0]["photoUrl"]
        return f"API empty (status={r.status_code})"
    except Exception as e:
        return f"ERROR: {e}"

def yt_oembed(playlist_id):
    try:
        r = s.get("https://www.youtube.com/oembed",
                  params={"url": f"https://www.youtube.com/playlist?list={playlist_id}", "format": "json"}, timeout=8)
        if r.ok:
            return r.json().get("thumbnail_url", "no thumbnail_url in response")
        return f"HTTP {r.status_code}"
    except Exception as e:
        return f"ERROR: {e}"

tests = [
    ("NPTEL",          "og",       "https://nptel.ac.in/courses/108/106/108106098/"),
    ("Harvard PLL",    "og",       "https://pll.harvard.edu/course/opioid-crisis-america"),
    ("Oxford podcast", "og",       "https://podcasts.ox.ac.uk/series/general-relativity"),
    ("Utah State OCW", "og",       "https://ocw.usu.edu/course/general-physics-i-usu/"),
    ("Tufts OCW",      "og",       "https://ocw.tufts.edu/courses/chemistry/organic-chemistry-i/"),
    ("UCI OCW",        "og",       "https://ocw.uci.edu/courses/genetics_uci.html"),
    ("JHSPH OCW",      "og",       "https://ocw.jhsph.edu/courses/InfectiousDiseaseEpi/"),
    ("Saylor",         "og",       "https://learn.saylor.org/course/bus104"),
    ("Open Univ UK",   "og",       "https://www.open.edu/openlearn/digital-computing/introduction-cybersecurity"),
    ("edX ANU",        "og",       "https://www.edx.org/course/machine-learning-anu"),
    ("Coursera Angular","coursera","angular"),
    ("Coursera Duke",  "coursera", "biology-dna"),
    ("Berkeley archive","yt",      "PLRe7s5JtDsYRPd3USSYQFIYMbPtEBbHsL"),
    ("Stanford YT",    "yt",       "PLoROMvodv4rO0raveZzJDfBHMjCJ1wv51"),
]

print(f"\n{'Source':22s}  {'Method':8s}  Result")
print("-" * 100)
for name, method, arg in tests:
    if method == "og":
        result = fetch_og_image(arg)
    elif method == "coursera":
        result = coursera_api(arg)
    elif method == "yt":
        result = yt_oembed(arg)
    else:
        result = "unknown"
    print(f"{name:22s}  {method:8s}  {str(result)[:80]}")
