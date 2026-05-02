"""Test NPTEL listing page for thumbnails + YouTube proper extraction + Yale."""
import re, requests, json

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
})

print("=== NPTEL listing page - checking for thumbnails ===")
try:
    r = s.get("https://nptel.ac.in/courses", timeout=20)
    print(f"  status={r.status_code} len={len(r.text)}")
    html = r.text
    # Look for thumbnail/img inside course cards
    card_imgs = re.findall(r'href=["\'](?:/courses/\d+)["\'][^<]*?<img[^>]+src=["\']([^"\']+)["\']', html, re.DOTALL)
    print(f"  card imgs: {card_imgs[:3]}")
    # Broader: any img src near a /courses/ link
    sections = re.findall(r'href=["\'][^"\']*courses/(\d+)["\'][^<]{0,500}', html[:200000], re.DOTALL)
    print(f"  first 3 section snippets: {[s[:100] for s in sections[:3]]}")
    # Look for data-src or src attributes near course IDs 
    course_with_img = re.findall(r'courses/(\d+)["\'][^<]{0,300}<img[^>]+(?:src|data-src)=["\']([^"\']+)["\']', html[:200000], re.DOTALL)
    print(f"  course→img pairs: {course_with_img[:3]}")
    # Look for noc images pattern
    noc_imgs = re.findall(r'(?:archive\.nptel\.ac\.in|nptel\.ac\.in)[^"\']*(?:jpg|png|webp)[^"\']*', html)
    print(f"  NPTEL image URLs in page: {noc_imgs[:5]}")
    # Look for any ytimg references (YouTube thumbnails embedded)
    ytimgs = re.findall(r'ytimg\.com[^"\']*', html)
    print(f"  ytimg refs: {ytimgs[:3]}")
    # Check page structure around course cards
    idx = html.find('/courses/')
    if idx > 0:
        print(f"  context around first /courses/ link: {html[max(0,idx-200):idx+300]}")
except Exception as e:
    print(f"  error: {e}")

print("\n=== YouTube playlist page - ytInitialData extraction ===")
try:
    r = s.get("https://www.youtube.com/playlist?list=PL8dPuuaLjXtKZPLYPEGLHvPUiUcRe6n8h", timeout=15)
    html = r.text
    # Find ytInitialData JSON
    m = re.search(r'var ytInitialData\s*=\s*(\{.+?\});</script>', html, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(1))
            # Navigate to first video
            tabs = data.get('contents',{}).get('twoColumnBrowseResultsRenderer',{}).get('tabs',[])
            print(f"  ytInitialData found, tabs count: {len(tabs)}")
        except:
            print(f"  ytInitialData found but JSON parse failed, len={len(m.group(1))}")
    else:
        print("  ytInitialData NOT found")
    # Try simpler: look for videoId in first 50KB
    vids = re.findall(r'"videoId":"([A-Za-z0-9_\-]{11})"', html[:100000])
    print(f"  videoId pattern matches in first 100KB: {vids[:3]}")
    # Also check without quotes around colon
    vids2 = re.findall(r'videoId["\s:]+([A-Za-z0-9_\-]{11})', html[:50000])
    print(f"  videoId loose matches: {vids2[:3]}")
    # Check for thumbnails directly
    thumb_urls = re.findall(r'"(https://i\.ytimg\.com/vi/[^"]{20,60})"', html[:200000])
    print(f"  ytimg thumb URLs found: {thumb_urls[:3]}")
except Exception as e:
    print(f"  error: {e}")

print("\n=== Yale OYC course image extraction ===")
try:
    r = s.get("https://oyc.yale.edu/spanish-and-portuguese/span-300", timeout=15)
    html = r.text
    # Find course detail style image
    m = re.search(r'(https?://[^"\']+/styles/course_detail/[^"\']+)', html)
    if m:
        print(f"  course_detail img: {m.group(1)}")
    else:
        # Find any /sites/default/files/ image
        m = re.search(r'(/sites/default/files/[^"\']+\.(?:jpg|png|webp)[^"\']*)', html)
        if m:
            print(f"  sites/default/files img: https://oyc.yale.edu{m.group(1)}")
        else:
            print("  no image found")
    # Check all field-name--field-image classes
    imgs = re.findall(r'class="[^"]*field[^"]*image[^"]*"[^>]*>[^<]*<img[^>]+src=["\']([^"\']+)["\']', html, re.DOTALL)
    print(f"  field image imgs: {imgs[:3]}")
except Exception as e:
    print(f"  error: {e}")

print("\n=== Princeton CS page og:image ===")
try:
    r = s.get("https://www.cs.princeton.edu/courses/archive/spring14/cos511/", timeout=15)
    print(f"  status={r.status_code} len={len(r.text)}")
    html = r.text
    m = re.search(r'og:image[^>]*content=["\']([^"\']+)', html)
    imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
    print(f"  og:image: {m.group(1) if m else 'None'}")
    print(f"  img srcs: {imgs[:3]}")
except Exception as e:
    print(f"  error: {e}")
