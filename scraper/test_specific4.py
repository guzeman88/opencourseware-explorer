"""Test YouTube playlist og:image and NPTEL SvelteKit data."""
import re, requests, json

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
})

print("=== YouTube playlist page - og:image check ===")
for pid in ["PL8dPuuaLjXtKZPLYPEGLHvPUiUcRe6n8h", "PLoROMvodv4rO0raveZzJDfBHMjCJ1wv51"]:
    try:
        r = s.get(f"https://www.youtube.com/playlist?list={pid}", timeout=15)
        html = r.text
        # og:image
        m = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
        if not m:
            m = re.search(r'"og:image",\s*"content":\s*"([^"]+)"', html)
        if not m:
            m = re.search(r'og:image[^>]+content="([^"]+)"', html)
        print(f"  {pid[:30]}: og:image={m.group(1)[:80] if m else 'None'}")
        # Also check meta tags
        metas = re.findall(r'<meta[^>]+og:image[^>]+>', html, re.IGNORECASE)
        print(f"    og:image meta tags: {[m[:100] for m in metas[:2]]}")
        # Look for ytimg in first 5KB
        ytimgs = re.findall(r'"(https://i\.ytimg\.com[^"]+)"', html[:5000])
        print(f"    ytimg in head: {ytimgs[:2]}")
    except Exception as e:
        print(f"  {pid}: error={e}")

print("\n=== YouTube og:image via yt.be ===")
# Try noembed which uses og:image
for pid in ["PL8dPuuaLjXtKZPLYPEGLHvPUiUcRe6n8h"]:
    try:
        r = s.get(f"https://noembed.com/embed?url=https://www.youtube.com/playlist?list={pid}", timeout=10)
        print(f"  noembed status={r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"  error: {e}")

print("\n=== NPTEL SvelteKit listing page - look for JSON data ===")
try:
    r = s.get("https://nptel.ac.in/courses", timeout=25)
    html = r.text
    # Look for SvelteKit's __data scripts
    scripts = re.findall(r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>', html, re.DOTALL)
    print(f"  JSON script blocks: {len(scripts)}")
    for i, sc in enumerate(scripts[:2]):
        print(f"  Script {i} len={len(sc)}: {sc[:200]}")
    # SvelteKit data format
    m = re.search(r'<script\s+id="__SVELTE_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if m: print(f"  SVELTE_DATA: {m.group(1)[:200]}")
    m = re.search(r'window\.__pageData\s*=\s*(\{.*?\})\s*;', html[:100000], re.DOTALL)
    if m: print(f"  pageData: {m.group(1)[:200]}")
    # Look at script tags with any course data
    course_scripts = [s for s in re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL) 
                     if 'course' in s.lower() and len(s) > 100]
    print(f"  Scripts mentioning 'course': {len(course_scripts)}")
    for sc in course_scripts[:2]:
        print(f"    len={len(sc)}: {sc[:200]}")
except Exception as e:
    print(f"  error: {e}")

print("\n=== NPTEL individual course page - look for embedded YouTube ===")
try:
    # Try an NPTEL course with known playlist
    r = s.get("https://nptel.ac.in/courses/106106212", timeout=15)
    html = r.text
    print(f"  status={r.status_code} len={len(html)}")
    # SvelteKit data
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    print(f"  Script blocks: {len(scripts)}")
    for sc in scripts:
        if 'youtube' in sc.lower() or 'playlist' in sc.lower() or 'thumbnail' in sc.lower():
            print(f"  YT-related script (len={len(sc)}): {sc[:300]}")
            break
    # Check head for link rel="image_src"
    m = re.search(r'rel="image_src"\s+href="([^"]+)"', html)
    if m: print(f"  image_src: {m.group(1)}")
    # JSON-LD
    jsonld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    for jl in jsonld[:2]:
        print(f"  JSON-LD: {jl[:300]}")
except Exception as e:
    print(f"  error: {e}")

print("\n=== SWAYAM (NPTEL courses on SWAYAM) ===")
try:
    url = "https://swayam.gov.in/nd2_cec01_cs01/preview"
    r = s.get(url, timeout=15, allow_redirects=True)
    print(f"  status={r.status_code} len={len(r.text)} url={r.url}")
    m = re.search(r'og:image[^>]+content="([^"]+)"', r.text)
    print(f"  og:image: {m.group(1) if m else 'None'}")
except Exception as e:
    print(f"  error: {e}")
