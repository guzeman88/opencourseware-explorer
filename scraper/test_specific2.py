"""Test alternative strategies for playlist thumbnails and NPTEL."""
import re, requests, json

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
})

def scrape_yt_playlist_thumb(playlist_id):
    """Scrape YouTube playlist page to get first video thumbnail."""
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    try:
        r = s.get(url, timeout=15)
        print(f"  yt playlist page status={r.status_code} len={len(r.text)}")
        html = r.text
        # extract first video ID from ytInitialData
        m = re.search(r'"videoId"\s*:\s*"([A-Za-z0-9_\-]{11})"', html)
        if m:
            vid_id = m.group(1)
            return f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
        # try og:image from playlist page
        m = re.search(r'property="og:image"\s+content="([^"]+)"', html)
        if m: return m.group(1)
    except Exception as e:
        print(f"  yt_scrape error: {e}")
    return None

print("=== YouTube playlist page scraping ===")
for pid in ["PL8dPuuaLjXtKZPLYPEGLHvPUiUcRe6n8h", "PLoROMvodv4rO0raveZzJDfBHMjCJ1wv51", "PLRe7s5JtDsYRPd3USSYQFIYMbPtEBbHsL"]:
    t = scrape_yt_playlist_thumb(pid)
    print(f"  {pid[:30]}: {t}")

print("\n=== NPTEL API endpoints ===")
for url in [
    "https://nptel.ac.in/api/v2/auth/courses/search?searchQuery=106106212",
    "https://nptel.ac.in/api/v2/course/detail?courseId=106106212",
    "https://nptel.ac.in/api/v1/courses/details?courseId=106106212",
]:
    try:
        r = s.get(url, timeout=10)
        print(f"  {url[-50:]}: status={r.status_code} len={len(r.text)}")
        if r.ok and r.text.strip().startswith('{'):
            data = r.json()
            print(f"    keys: {list(data.keys())[:5]}")
    except Exception as e:
        print(f"  {url[-50:]}: error={e}")

print("\n=== NPTEL page - look for YouTube embeds and noc_images ===")
try:
    r = s.get("https://nptel.ac.in/courses/106106212", timeout=15)
    html = r.text
    # Look for youtube video/playlist in page
    yt_matches = re.findall(r'(?:youtube\.com/|youtu\.be/)(?:watch\?v=|embed/|playlist\?list=)([A-Za-z0-9_\-]{11,})', html)
    print(f"  YouTube refs found: {yt_matches[:5]}")
    # Look for noc_images pattern
    noc = re.findall(r'noc_images[^"\']*', html)
    print(f"  noc_images refs: {noc[:3]}")
    # Look for any img src
    imgs = re.findall(r'src=["\']([^"\']+\.(?:jpg|png|webp)[^"\']*)["\']', html, re.IGNORECASE)
    print(f"  img srcs found: {imgs[:5]}")
    # Check for JSON data containing thumbnail
    thumbnails = re.findall(r'"(?:thumbnail|image|poster|cover)[^"]*"\s*:\s*"(https?://[^"]+)"', html, re.IGNORECASE)
    print(f"  thumbnail-like URLs: {thumbnails[:5]}")
except Exception as e:
    print(f"  error: {e}")

print("\n=== Khan Academy correct check ===")
try:
    r = s.get("https://www.khanacademy.org/math/algebra2", timeout=15)
    print(f"  status={r.status_code} len={len(r.text)} url={r.url}")
    html = r.text
    m = re.search(r'og:image[^>]*content=["\']([^"\']+)', html)
    if m: print(f"  og:image = {m.group(1)}")
    else: print("  No og:image, checking first 200 chars:", html[:200])
except Exception as e:
    print(f"  error: {e}")

print("\n=== Yale OYC - check page source ===")
try:
    r = s.get("https://oyc.yale.edu/spanish-and-portuguese/span-300", timeout=15)
    print(f"  status={r.status_code} len={len(r.text)}")
    html = r.text
    # Check all meta tags
    metas = re.findall(r'<meta[^>]+>', html, re.IGNORECASE)
    for m in metas[:10]: print(f"  meta: {m[:100]}")
    # Check for og:image in different formats
    imgs = re.findall(r'src=["\']([^"\']+\.(?:jpg|png|webp)[^"\']*)["\']', html, re.IGNORECASE)
    print(f"  img srcs: {imgs[:3]}")
except Exception as e:
    print(f"  error: {e}")
