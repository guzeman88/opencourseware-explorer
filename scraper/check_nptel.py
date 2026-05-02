"""Check NPTEL page structure."""
import urllib.request
import re
import json

req = urllib.request.Request('https://nptel.ac.in/courses', headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=30)
html = resp.read().decode('utf-8', errors='ignore')
print(f'Got {len(html)} bytes')

# Look for JSON data 
matches = re.findall(r'window\.__INITIAL_STATE__\s*=\s*(.+?);</script>', html, re.DOTALL)
if matches:
    print('Found __INITIAL_STATE__:', matches[0][:500])

# Look for course data in script tags
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
for s in scripts[:5]:
    if 'course' in s.lower() and len(s) > 100:
        print('Script with course:', s[:300])
        break

# Look for course links
import re
for pat in [r'href="(/courses/[\d/]+)"', r'"courseId":\s*"([^"]+)"', r'"noc\d+[^"]*"']:
    found = re.findall(pat, html)
    if found:
        print(f'Pattern {pat!r} found {len(found)}: {found[:3]}')

# First 3000 chars
print('\n--- First 3000 chars ---')
print(html[:3000])
