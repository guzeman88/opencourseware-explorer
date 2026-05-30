"""Diagnose and run backfill for courses missing videos."""
import psycopg2

import os as _os; DB = _os.environ.get("DATABASE_URL") or exit("ERROR: DATABASE_URL env var is required")
conn = psycopg2.connect(DB)
cur = conn.cursor()

# Check published status and playlist availability for zero-video courses
cur.execute("""
    SELECT c.source_key, c.title, c.is_published, c.youtube_playlist_id,
           c.source_url
    FROM courses c
    LEFT JOIN videos v ON v.course_id = c.id
    WHERE c.has_video_lectures = true
    GROUP BY c.id
    HAVING COUNT(v.id) = 0
    ORDER BY c.source_key, c.title
""")
rows = cur.fetchall()

print("Zero-video courses breakdown:\n")
has_playlist_published = []
has_playlist_unpublished = []
has_yt_in_url_published = []
no_playlist = []

import re
from urllib.parse import urlparse, parse_qs

def extract_pl(url):
    if not url: return None
    m = re.search(r'[?&]list=([A-Za-z0-9_-]+)', url)
    return m.group(1) if m else None

for src, title, published, pl_id, source_url in rows:
    extracted = extract_pl(source_url or '')
    effective_pl = pl_id or extracted
    if effective_pl and published:
        has_playlist_published.append((src, title, effective_pl))
    elif effective_pl and not published:
        has_playlist_unpublished.append((src, title, effective_pl, published))
    elif 'youtube.com' in (source_url or '') and published:
        has_yt_in_url_published.append((src, title, source_url))
    else:
        no_playlist.append((src, title, published, source_url))

print(f"Has playlist & published: {len(has_playlist_published)}")
for src, title, pl in has_playlist_published[:10]:
    print(f"  [{src}] {title} -> {pl}")
if len(has_playlist_published) > 10:
    print(f"  ... and {len(has_playlist_published)-10} more")

print(f"\nHas YouTube URL in source_url but published: {len(has_yt_in_url_published)}")
for src, title, url in has_yt_in_url_published[:5]:
    print(f"  [{src}] {title}: {url[:80]}")

print(f"\nHas playlist but NOT published: {len(has_playlist_unpublished)}")
for src, title, pl, pub in has_playlist_unpublished[:5]:
    print(f"  [{src}] {title} (published={pub})")

print(f"\nNo playlist at all: {len(no_playlist)}")
from collections import Counter
by_src = Counter(r[0] for r in no_playlist)
for s, c in by_src.most_common(10):
    print(f"  {c:3d}  [{s}]")

# Specifically: CMU courses
print("\nCMU courses detail:")
cur.execute("""
    SELECT id, title, is_published, youtube_playlist_id, source_url
    FROM courses WHERE source_key = 'cmu' ORDER BY title
""")
for id_, title, pub, pl, url in cur.fetchall():
    print(f"  {title} (published={pub})")
    print(f"    playlist_id={pl}, source_url={url}")

conn.close()
