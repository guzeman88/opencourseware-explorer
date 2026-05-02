"""
Check if NPTEL non-video course pages have any images in their static HTML.
"""
import re, requests

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
})

# Non-video NPTEL course
url = "https://nptel.ac.in/courses/106105078"
print(f"Fetching: {url}")
r = s.get(url, timeout=15)
print(f"HTTP {r.status_code}, size: {len(r.text)}")

html = r.text

# Look for og:image
for tag in re.findall(r'<meta\s+([^>]+?)(?:/>|>)', html, re.IGNORECASE | re.DOTALL):
    if re.search(r'og:image', tag, re.IGNORECASE):
        print(f"og:image tag: {tag[:200]}")

# Look for any image URL patterns  
img_patterns = [
    r'https?://[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)',
    r'"image":\s*"([^"]+)"',
    r'courseImage["\s:]+([^\s"\']+)',
]
for pat in img_patterns:
    matches = re.findall(pat, html, re.IGNORECASE)
    if matches:
        print(f"\nPattern '{pat[:40]}' found {len(matches)} matches:")
        for m in matches[:5]:
            print(f"  {m[:120]}")

# Also check for any nptel-specific image patterns
nptel_imgs = re.findall(r'nptel[^\s"\'<>]*\.(?:jpg|jpeg|png|webp)', html, re.IGNORECASE)
print(f"\nNPTEL-specific images: {nptel_imgs[:5]}")

# Check for "thumb" or "cover" or "banner"
for keyword in ['thumb', 'cover', 'banner', 'poster', 'course_img', 'courseImg']:
    matches = re.findall(rf'["\'][^"\']*{keyword}[^"\']*["\']', html, re.IGNORECASE)
    if matches:
        print(f"\n'{keyword}' references: {matches[:3]}")
