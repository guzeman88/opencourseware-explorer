#!/usr/bin/env python3
"""
_retry_og_image.py

Retry og:image scraping for courses that still have Unsplash fallbacks
and have a non-YouTube source URL.
"""

import re
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import psycopg2
import requests

DB = os.environ.get("DATABASE_URL") or sys.exit("ERROR: DATABASE_URL required")

_tl = threading.local()

def sess() -> requests.Session:
    if not hasattr(_tl, "s"):
        s = requests.Session()
        s.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        _tl.s = s
    return _tl.s


def fetch_og_image(url: str, timeout: int = 15) -> str | None:
    if not url:
        return None
    try:
        resp = sess().get(url, timeout=timeout, allow_redirects=True)
        if not resp.ok:
            return None
        html = resp.text
        for tag in re.findall(r'<meta\s+([^>]+?)(?:/>|>)', html, re.IGNORECASE | re.DOTALL):
            if re.search(r'og:image', tag, re.IGNORECASE):
                m = re.search(r'content=["\']([^"\']+)', tag, re.IGNORECASE)
                if m:
                    img = m.group(1).strip()
                    if img.startswith("http"):
                        return img
        for pat in [
            r'property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
            r'content=["\']([^"\']+)["\'][^>]+property=["\']og:image',
            r'og:image.*?content=["\']([^"\']+)',
            r'"image"\s*:\s*"(https://[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
        ]:
            m = re.search(pat, html, re.IGNORECASE | re.DOTALL)
            if m:
                img = m.group(1).strip()
                if img.startswith("http"):
                    return img
    except Exception:
        pass
    return None


def process(row):
    cid, title, skey, surl = row
    thumb = fetch_og_image(surl)
    return cid, title, skey, thumb


def main():
    conn = psycopg2.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, source_key, source_url
        FROM courses
        WHERE thumbnail_url LIKE '%unsplash%'
          AND source_url IS NOT NULL
          AND source_url NOT LIKE '%youtube%'
        ORDER BY source_key, title
    """)
    rows = cur.fetchall()
    print(f"Courses to retry: {len(rows)}")

    updated = 0
    with ThreadPoolExecutor(max_workers=15) as ex:
        futures = {ex.submit(process, r): r for r in rows}
        for i, fut in enumerate(as_completed(futures)):
            cid, title, skey, thumb = fut.result()
            if thumb:
                cur.execute("UPDATE courses SET thumbnail_url = %s WHERE id = %s", (thumb, cid))
                updated += 1
                print(f"  OK [{skey}] {title[:55]}")
            if (i + 1) % 50 == 0:
                conn.commit()

    conn.commit()
    print(f"\nDone. Fixed: {updated}/{len(rows)}")
    cur.close(); conn.close()


if __name__ == "__main__":
    main()
