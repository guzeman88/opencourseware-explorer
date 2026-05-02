"""Extract NPTEL course titles properly from HTML structure."""
import urllib.request
import re
from bs4 import BeautifulSoup

req = urllib.request.Request('https://nptel.ac.in/courses', headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=30)
html = resp.read().decode('utf-8', errors='ignore')

soup = BeautifulSoup(html, 'html.parser')

# Find the first course card structure
first_link = soup.select_one('a[href^="/courses/1"]')
if first_link:
    print("=== First course link HTML ===")
    print(first_link)
    print("\n=== Parent ===")
    print(first_link.parent)
    print("\n=== Grandparent ===")
    print(first_link.parent.parent if first_link.parent else "")

# Also try to get individual spans
print("\n=== All direct children of first course link ===")
for child in first_link.children:
    print(repr(child))
