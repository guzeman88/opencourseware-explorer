"""
fetch_thumbnails_5.py
Extract thumbnails from MIT OCW's __NEXT_DATA__ JSON embedded in pages,
plus Yale physics hardcoded video ID.
"""

import asyncio
import json
import re
import time

import aiohttp
import psycopg2

CONN_STR = "postgresql://ocw:ocwpassword@127.0.0.1:5432/opencourseware"
CONCURRENCY = 8

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

BAD = ("mit-logo-250", "placeholder", "/static/img/")

# Yale courses with known first-video IDs
YALE_KNOWN = {
    "https://oyc.yale.edu/physics/phys-200": "WkSXGzxAEXM",  # Fundamentals of Physics I
}


def good(url: str) -> bool:
    return bool(url) and not any(p in url for p in BAD)


def extract_image_from_next_data(html: str) -> str | None:
    """Parse __NEXT_DATA__ from MIT OCW Next.js pages to find course image."""
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
        # Walk the props tree looking for image-like keys
        def walk(obj, depth=0):
            if depth > 12:
                return None
            if isinstance(obj, dict):
                for key in ("image_src", "course_image_url", "imageUrl",
                            "course_feature_url", "thumbnail", "image"):
                    val = obj.get(key)
                    if val and isinstance(val, str) and good(val):
                        return val
                # Also look for og_image
                val = obj.get("og_image") or obj.get("ogImage")
                if val and isinstance(val, str) and good(val):
                    return val
                for v in obj.values():
                    r = walk(v, depth + 1)
                    if r:
                        return r
            elif isinstance(obj, list):
                for item in obj[:5]:
                    r = walk(item, depth + 1)
                    if r:
                        return r
            return None
        return walk(data)
    except Exception:
        return None


async def fetch_and_extract(session: aiohttp.ClientSession, url: str) -> str | None:
    try:
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=25), allow_redirects=True
        ) as resp:
            if resp.status != 200:
                return None
            html = await resp.text(errors="replace")

            # 1. __NEXT_DATA__ JSON
            img = extract_image_from_next_data(html)
            if img and good(img):
                return img

            # 2. og:image / twitter:image
            for pat in (
                r'property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
                r'content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
                r'name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
                r'content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
            ):
                m = re.search(pat, html)
                if m and good(m.group(1)):
                    return m.group(1).strip()

            # 3. MIT CDN image pattern in any attribute
            m = re.search(
                r'(https://ocw\.mit\.edu/courses/[^"\'> ]+?'
                r'\.(jpg|jpeg|png|webp|gif))',
                html, re.IGNORECASE
            )
            if m and good(m.group(1)):
                return m.group(1)

    except Exception as e:
        pass
    return None


async def run():
    conn = psycopg2.connect(CONN_STR)
    cur = conn.cursor()

    cur.execute(
        "SELECT id, source_url, source_key, youtube_playlist_id "
        "FROM courses WHERE thumbnail_url IS NULL ORDER BY source_key, id"
    )
    rows = cur.fetchall()
    print(f"Still missing: {len(rows)}", flush=True)

    updated = 0
    start = time.time()

    # ── Hardcoded Yale ──────────────────────────────────────────────────────
    for course_id, source_url, source_key, playlist_id in rows:
        if source_url in YALE_KNOWN:
            vid = YALE_KNOWN[source_url]
            thumb = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
            cur.execute("UPDATE courses SET thumbnail_url=%s WHERE id=%s", (thumb, course_id))
            updated += 1
            print(f"  ✓ Yale hardcoded: {vid}", flush=True)
    conn.commit()

    # Reload
    cur.execute(
        "SELECT id, source_url, source_key, youtube_playlist_id "
        "FROM courses WHERE thumbnail_url IS NULL ORDER BY source_key, id"
    )
    remaining = cur.fetchall()
    print(f"  After Yale hardcode: {len(remaining)} left", flush=True)

    # ── __NEXT_DATA__ scrape ────────────────────────────────────────────────
    if remaining:
        print(f"\nScraping __NEXT_DATA__ + meta for {len(remaining)} pages...", flush=True)
        sem = asyncio.Semaphore(CONCURRENCY)
        connector = aiohttp.TCPConnector(limit=CONCURRENCY + 5, ssl=False)
        scraped = 0
        seen_urls = set()

        async def proc(course_id, source_url, source_key, playlist_id):
            nonlocal updated, scraped
            if not source_url or source_url in seen_urls:
                return
            seen_urls.add(source_url)
            async with sem:
                img = await fetch_and_extract(session, source_url)
                if img:
                    # Update all courses with this source_url
                    cur.execute(
                        "UPDATE courses SET thumbnail_url=%s "
                        "WHERE source_url=%s AND thumbnail_url IS NULL",
                        (img, source_url),
                    )
                    n = cur.rowcount
                    updated += n
                    scraped += n
                    print(f"  ✓ [{source_key}] {source_url[-55:]}", flush=True)
                    print(f"        → {img[:80]}", flush=True)
                else:
                    print(f"  ✗ [{source_key}] {source_url[-55:]}", flush=True)

        async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
            await asyncio.gather(*[proc(*r) for r in remaining])

        conn.commit()
        print(f"\n  Found {scraped} images", flush=True)

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.0f}s — updated {updated} total", flush=True)

    cur.execute("SELECT COUNT(*) total, COUNT(thumbnail_url) has_thumb FROM courses")
    row = cur.fetchone()
    pct = row[1] / row[0] * 100
    print(f"DB coverage: {row[1]}/{row[0]} = {pct:.1f}%", flush=True)
    conn.close()


if __name__ == "__main__":
    asyncio.run(run())
