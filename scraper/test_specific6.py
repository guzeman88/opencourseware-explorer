"""Test SvelteKit __data.json endpoints for NPTEL and check what CDN images exist."""
import re, requests

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html",
    "Accept-Language": "en-US,en;q=0.9",
})

print("=== NPTEL SvelteKit __data.json endpoints ===")
for url in [
    "https://nptel.ac.in/courses/106106212/__data.json",
    "https://nptel.ac.in/courses/106106212.json",
    "https://nptel.ac.in/api/courses/106106212",
    "https://nptel.ac.in/api/course/106106212",
    "https://nptel.ac.in/courses/106106212?__data=true",
    "https://nptel.ac.in/_api/courses/106106212",
]:
    try:
        r = s.get(url, timeout=10)
        print(f"  {url[-50:]}: status={r.status_code} len={len(r.text)}")
        if r.ok:
            print(f"    content: {r.text[:200]}")
    except Exception as e:
        print(f"  {url[-50:]}: error={e}")

print("\n=== NPTEL archive CDN thumbnail patterns ===")
# Try common NPTEL thumbnail CDN patterns
course_id = "106106212"
dept1, dept2 = "106", "106"
for url in [
    f"https://archive.nptel.ac.in/noc_images/{course_id}.jpg",
    f"https://archive.nptel.ac.in/content/noc/NOC21_CS100/Pdfs/thumbnail.jpg",
    f"https://archive.nptel.ac.in/content/storage2/courses/downloads_new/noc/noc21_cs100/Pdfs/thumbnail.jpg",
]:
    try:
        r = s.head(url, timeout=8)
        print(f"  {url[-60:]}: status={r.status_code}")
    except Exception as e:
        print(f"  {url[-50:]}: error={e}")

print("\n=== NPTEL listing page - look in 838KB script block for course thumbnails ===")
try:
    r = s.get("https://nptel.ac.in/courses", timeout=25)
    html = r.text
    print(f"  Page len: {len(html):,}")
    # Find the big script block
    m = re.search(r'__sveltekit_iq2jui[^<]{100,}', html)
    if m:
        script_content = m.group(0)
        print(f"  SvelteKit script len: {len(script_content):,}")
        # Look for any image URLs in this script
        img_urls = re.findall(r'https?://[^"\']+\.(?:jpg|png|webp)', script_content)
        print(f"  Image URLs in script: {img_urls[:10]}")
        # Look for nptel CDN patterns
        nptel_imgs = re.findall(r'nptel[^"\']{0,100}\.(?:jpg|png)', script_content)
        print(f"  NPTEL img patterns: {nptel_imgs[:5]}")
    
    # Look for any ytimg.com in the FULL page
    ytimgs = re.findall(r'https?://i\.ytimg\.com[^"\']+', html)
    print(f"  ytimg URLs in full page: {ytimgs[:5]}")
    
    # Look for any image URL near a course ID pattern
    pairs = re.findall(r'courses[/\\](\d{9})[^<]{0,200}https?://[^"\']*\.(?:jpg|png)', html, re.DOTALL)
    print(f"  Course ID + image pairs: {pairs[:3]}")
    
    # look for data-sveltekit-prefetch page with JSON 
    sveltekit_data = re.search(r'<script[^>]*data-sveltekit[^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
    if sveltekit_data:
        print(f"  SvelteKit data script: {sveltekit_data.group(1)[:200]}")
except Exception as e:
    print(f"  error: {e}")

print("\n=== Try NPTEL API via xhr-like request ===")
for url in [
    "https://nptel.ac.in/api/v1/course/detail?courseId=106106212",
    "https://nptel.ac.in/api/v2/course/list?dept=CS&page=1",
    "https://nptel.ac.in/courses.json",
]:
    try:
        r = s.get(url, timeout=8, headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"})
        print(f"  {url[-50:]}: status={r.status_code} len={len(r.text)}")
        if r.ok and 'json' in r.headers.get('content-type', ''):
            print(f"    JSON: {r.text[:200]}")
    except Exception as e:
        print(f"  {url[-50:]}: error={e}")
