"""
fetch_thumbnails_4.py
Final pass: broader image extraction for the last 35 stubborn courses.
- Adds 2 missing known video IDs (Crash Course + Yale)
- For MIT OCW: tries twitter:image, json-ld, and direct image URL patterns
"""

import asyncio
import json
import re
import time

import aiohttp
import psycopg2

CONN_STR = "postgresql://ocw:ocwpassword@127.0.0.1:5432/opencourseware"
MIT_LOGO = "https://ocw.mit.edu/img/mit-logo-250.png"
CONCURRENCY = 10

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Final known video IDs not covered in pass 3
EXTRA_KNOWN = {
    # Crash Course Biology (PL8dPuuaLjXtMJ-AfB_7J1538YKZkEjJsN)
    "PL8dPuuaLjXtMJ-AfB_7J1538YKZkEjJsN": "P3FxS3A4Hdg",
    # Simons Institute
    "PLgKuh-lKre11GbZx3fRAsQEDmOKNIuVKP": "FeNkDr7p6zU",
}

BAD_IMG_PATTERNS = (
    "mit-logo-250",
    "default_thumbnail",
    "placeholder",
    "/static/img/og",
)


def is_good_img(url: str) -> bool:
    if not url:
        return False
    low = url.lower()
    return not any(p in low for p in BAD_IMG_PATTERNS)


async def extract_image(session: aiohttp.ClientSession, url: str) -> str | None:
    """Try multiple strategies to find a meaningful image URL from a page."""
    try:
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=20), allow_redirects=True
        ) as resp:
            if resp.status != 200:
                return None
            html = await resp.text(errors="replace")

            # 1. og:image
            for pat in (
                r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
            ):
                m = re.search(pat, html)
                if m and is_good_img(m.group(1)):
                    return m.group(1).strip()

            # 2. twitter:image
            for pat in (
                r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
            ):
                m = re.search(pat, html)
                if m and is_good_img(m.group(1)):
                    return m.group(1).strip()

            # 3. JSON-LD image
            ld_blocks = re.findall(
                r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                html, re.DOTALL
            )
            for block in ld_blocks:
                try:
                    data = json.loads(block.strip())
                    # Handle single object or list
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        img = item.get("image") or item.get("thumbnailUrl")
                        if isinstance(img, dict):
                            img = img.get("url")
                        if isinstance(img, list):
                            img = img[0] if img else None
                            if isinstance(img, dict):
                                img = img.get("url")
                        if img and is_good_img(str(img)):
                            return str(img)
                except Exception:
                    pass

            # 4. MIT OCW specific: look for course image in page content
            # Pattern: <img ... src="https://ocw.mit.edu/courses/.../images/..."
            m = re.search(
                r'<img[^>]+src=["\']('
                r'https://ocw\.mit\.edu/courses/[^/]+/images/[^"\']+\.(jpg|jpeg|png|webp)'
                r')["\']',
                html, re.IGNORECASE
            )
            if m and is_good_img(m.group(1)):
                return m.group(1)

            # 5. Any reasonable thumbnail-looking ytimg.com URL in the page
            m = re.search(r'(https://i\.ytimg\.com/vi/[A-Za-z0-9_-]+/hqdefault\.jpg)', html)
            if m:
                return m.group(1)

    except Exception:
        pass
    return None


async def run():
    conn = psycopg2.connect(CONN_STR)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, source_url, source_key, youtube_playlist_id
        FROM courses WHERE thumbnail_url IS NULL
        ORDER BY source_key, id
        """
    )
    rows = cur.fetchall()
    print(f"Still missing: {len(rows)}", flush=True)

    updated = 0
    start = time.time()

    # ── 1. Extra known video IDs ────────────────────────────────────────────
    extra_hits = 0
    for course_id, source_url, source_key, playlist_id in rows:
        if playlist_id and playlist_id in EXTRA_KNOWN:
            vid_id = EXTRA_KNOWN[playlist_id]
            thumb = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
            cur.execute("UPDATE courses SET thumbnail_url=%s WHERE id=%s", (thumb, course_id))
            extra_hits += 1
            updated += 1
            print(f"  ✓ {playlist_id[:40]} → {vid_id}", flush=True)
    if extra_hits:
        conn.commit()
        print(f"  Applied {extra_hits} extra known IDs", flush=True)

    # Reload
    cur.execute(
        "SELECT id, source_url, source_key, youtube_playlist_id "
        "FROM courses WHERE thumbnail_url IS NULL ORDER BY source_key, id"
    )
    remaining = cur.fetchall()
    print(f"  Remaining after known IDs: {len(remaining)}", flush=True)

    # ── 2. Broader scrape for all remaining ────────────────────────────────
    if remaining:
        print(f"\nBroadly scraping {len(remaining)} pages...", flush=True)
        sem = asyncio.Semaphore(CONCURRENCY)
        connector = aiohttp.TCPConnector(limit=CONCURRENCY + 5, ssl=False)
        scraped = 0

        async def proc(course_id, source_url, source_key, playlist_id):
            nonlocal updated, scraped
            if not source_url:
                return
            async with sem:
                img = await extract_image(session, source_url)
                if img:
                    cur.execute(
                        "UPDATE courses SET thumbnail_url=%s WHERE id=%s",
                        (img, course_id),
                    )
                    updated += 1
                    scraped += 1
                    print(f"  ✓ [{source_key}] {source_url[-60:]}", flush=True)
                    print(f"        → {img[:80]}", flush=True)
                else:
                    print(f"  ✗ [{source_key}] {source_url[-60:]}", flush=True)

        async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
            await asyncio.gather(*[proc(*r) for r in remaining])

        conn.commit()
        print(f"\n  Scraped {scraped} additional thumbnails", flush=True)

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.0f}s — updated {updated} total in this pass", flush=True)

    cur.execute("SELECT COUNT(*) total, COUNT(thumbnail_url) has_thumb FROM courses")
    row = cur.fetchone()
    pct = row[1] / row[0] * 100
    print(f"DB coverage: {row[1]}/{row[0]} = {pct:.1f}%", flush=True)
    conn.close()


if __name__ == "__main__":
    asyncio.run(run())
