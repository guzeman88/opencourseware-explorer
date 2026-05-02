"""Quick targeted tests for specific source strategies."""
import re, requests

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
})

def yt_oembed(playlist_id):
    try:
        r = s.get("https://www.youtube.com/oembed",
            params={"url": f"https://www.youtube.com/playlist?list={playlist_id}", "format": "json"}, timeout=10)
        print(f"  yt_oembed status={r.status_code}")
        if r.ok: return r.json().get("thumbnail_url")
    except Exception as e:
        print(f"  yt_oembed error: {e}")
    return None

def fetch_og(url):
    try:
        r = s.get(url, timeout=15, allow_redirects=True)
        print(f"  og status={r.status_code} len={len(r.text)}")
        if not r.ok: return None
        html = r.text
        # og:image
        for pat in [
            r'property=["\']og:image["\'][^>]*content=["\']([^"\']+)',
            r'content=["\']([^"\']+)["\'][^>]*property=["\']og:image',
            r'name=["\']og:image["\'][^>]*content=["\']([^"\']+)',
        ]:
            m = re.search(pat, html, re.IGNORECASE)
            if m and m.group(1).startswith('http'):
                return m.group(1)
        # Also look for __NEXT_DATA__ thumbnail
        m = re.search(r'"thumbnail[_\-]?[uU]rl"\s*:\s*"([^"]+)"', html)
        if m: return m.group(1)
        return None
    except Exception as e:
        print(f"  og error: {e}")
    return None

print("=== CrashCourse YouTube oembed ===")
t = yt_oembed("PL8dPuuaLjXtKZPLYPEGLHvPUiUcRe6n8h")
print(f"  Result: {t}")

print("\n=== Stanford YouTube oembed ===")
t = yt_oembed("PLoROMvodv4rO0raveZzJDfBHMjCJ1wv51")
print(f"  Result: {t}")

print("\n=== NPTEL new URL og:image ===")
t = fetch_og("https://nptel.ac.in/courses/106106212")
print(f"  Result: {t}")

print("\n=== NPTEL new URL check __NEXT_DATA__ ===")
try:
    r = s.get("https://nptel.ac.in/courses/106106212", timeout=15)
    html = r.text
    # Look for any image reference in next data
    m = re.search(r'"coverImageMedium"\s*:\s*"([^"]+)"', html)
    if m: print(f"  coverImageMedium: {m.group(1)}")
    m = re.search(r'"thumbnail"\s*:\s*"([^"]+)"', html)
    if m: print(f"  thumbnail: {m.group(1)}")
    m = re.search(r'"image"\s*:\s*"([^"]+)"', html)
    if m: print(f"  image: {m.group(1)}")
    m = re.search(r'"poster"\s*:\s*"([^"]+)"', html)
    if m: print(f"  poster: {m.group(1)}")
    # print first og tags found
    ogs = re.findall(r'<meta[^>]+og:[^>]+>', html, re.IGNORECASE)
    for og in ogs[:5]:
        print(f"  og tag: {og[:120]}")
except Exception as e:
    print(f"  error: {e}")

print("\n=== Yale OYC og:image ===")
t = fetch_og("https://oyc.yale.edu/spanish-and-portuguese/span-300")
print(f"  Result: {t}")

print("\n=== Khan Academy og:image ===")
t = fetch_og("https://www.khanacademy.org/math/algebra2")
print(f"  Result: {t}")

print("\n=== Saylor og:image ===")
t = fetch_og("https://learn.saylor.org/course/bus104")
print(f"  Result: {t}")

print("\n=== Open University UK og:image ===")
t = fetch_og("https://www.open.edu/openlearn/digital-computing/introduction-cybersecurity")
print(f"  Result: {t}")

print("\n=== Oxford podcasts og:image ===")
t = fetch_og("https://podcasts.ox.ac.uk/series/philosophy-mind-and-action")
print(f"  Result: {t}")
