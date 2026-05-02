"""Extract NPTEL course titles and metadata from the courses listing page."""
import urllib.request
import re
from bs4 import BeautifulSoup

req = urllib.request.Request('https://nptel.ac.in/courses', headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=30)
html = resp.read().decode('utf-8', errors='ignore')

soup = BeautifulSoup(html, 'html.parser')

# Find all course links with their text
courses = []
seen_urls = set()
for a in soup.select('a[href^="/courses/"]'):
    href = a.get('href', '')
    # Only numbered course IDs
    if not re.match(r'^/courses/\d+$', href):
        continue
    if href in seen_urls:
        continue
    seen_urls.add(href)
    
    # Get title from the anchor or surrounding elements
    title = a.get_text(strip=True)
    if not title:
        # Try parent elements
        parent = a.parent
        if parent:
            title = parent.get_text(strip=True)
    
    url = f"https://nptel.ac.in{href}"
    courses.append({'url': url, 'title': title, 'id': href.split('/')[-1]})

print(f"Found {len(courses)} courses")
for c in courses[:5]:
    print(c)
