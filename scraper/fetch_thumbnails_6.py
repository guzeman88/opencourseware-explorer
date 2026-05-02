"""
fetch_thumbnails_6.py
For the 33 404ing MIT OCW courses:
  1. Try legacy URL: ocw.mit.edu/courses/{department}/{slug}/
  2. Try MIT OCW search JSON: ocw.mit.edu/api/v2/courses/?q=...
  3. Extract og:image or CDN thumbnail from whatever works
"""

import asyncio
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

BAD = ("mit-logo-250", "placeholder")

# Map course number prefix → OCW department slug (legacy URLs)
DEPT_MAP = {
    "1":    "civil-and-environmental-engineering",
    "2":    "mechanical-engineering",
    "3":    "materials-science-and-engineering",
    "4":    "architecture",
    "5":    "chemistry",
    "6":    "electrical-engineering-and-computer-science",
    "7":    "biology",
    "8":    "physics",
    "9":    "brain-and-cognitive-sciences",
    "10":   "chemical-engineering",
    "11":   "urban-studies-and-planning",
    "12":   "earth-atmospheric-and-planetary-sciences",
    "14":   "economics",
    "15":   "sloan-school-of-management",
    "16":   "aeronautics-and-astronautics",
    "17":   "political-science",
    "18":   "mathematics",
    "21":   "humanities",
    "21a":  "anthropology",
    "21g":  "global-languages",
    "21h":  "history",
    "21l":  "literature",
    "21m":  "music-and-theater-arts",
    "21w":  "writing-and-humanistic-studies",
    "22":   "nuclear-engineering",
    "24":   "linguistics-and-philosophy",
    "wgs":  "womens-and-gender-studies",
    "res":  "iap",   # resources — fallback
}

def course_slug_to_number(slug: str) -> str | None:
    """Extract course number from slug like '14-02-principles-...' → '14'"""
    m = re.match(r"^([a-z0-9]+(?:-[a-z0-9]+)?)-", slug)
    if m:
        return m.group(1).replace("-", ".")
    return None

def get_dept(course_slug: str) -> str | None:
    """Map course slug to department string."""
    prefix = re.match(r"^([a-z0-9]+)", course_slug)
    if not prefix:
        return None
    p = prefix.group(1)
    # Try numeric-dotted prefix first (14, 7, 9, etc.)
    return DEPT_MAP.get(p)


def good(url: str) -> bool:
    return bool(url) and not any(p in url for p in BAD)


async def try_url(session: aiohttp.ClientSession, url: str) -> str | None:
    """Try fetching a URL and extract any image from it."""
    try:
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=20), allow_redirects=True
        ) as resp:
            if resp.status != 200:
                return None
            html = await resp.text(errors="replace")
            for pat in (
                r'property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
                r'content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
                r'name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
                r'content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
            ):
                m = re.search(pat, html)
                if m and good(m.group(1)):
                    return m.group(1).strip()
            # CDN image
            m = re.search(
                r'(https://ocw\.mit\.edu/courses/[^"\'> ]+?'
                r'\.(jpg|jpeg|png|webp|gif))',
                html, re.IGNORECASE
            )
            if m and good(m.group(1)):
                return m.group(1)
    except Exception:
        pass
    return None


async def try_mit_search(session: aiohttp.ClientSession, title: str) -> str | None:
    """Use OCW search API to find a course and its image."""
    # MIT OCW search endpoint
    import urllib.parse
    q = urllib.parse.quote(title[:60])
    url = f"https://ocw.mit.edu/search/?q={q}&f_d=Courses"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                return None
            html = await resp.text(errors="replace")
            # Look for the first course result's image
            m = re.search(
                r'<img[^>]+src=["\']('
                r'https://[^"\']+\.(jpg|jpeg|png|webp)'
                r')["\']',
                html
            )
            if m and good(m.group(1)):
                return m.group(1)
    except Exception:
        pass
    return None


async def run():
    conn = psycopg2.connect(CONN_STR)
    cur = conn.cursor()

    cur.execute(
        "SELECT id, source_url, source_key, title FROM courses "
        "WHERE thumbnail_url IS NULL AND source_key='mit_ocw' ORDER BY id"
    )
    rows = cur.fetchall()
    print(f"MIT OCW courses without thumbnails: {len(rows)}", flush=True)

    updated = 0
    start = time.time()
    sem = asyncio.Semaphore(CONCURRENCY)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY + 5, ssl=False)

    async def proc(course_id, source_url, source_key, title):
        nonlocal updated
        async with sem:
            # Extract the course slug from the source_url
            slug_m = re.search(r"/courses/([^/]+)/?$", source_url)
            if not slug_m:
                print(f"  ✗ Can't parse slug: {source_url[-50:]}", flush=True)
                return
            slug = slug_m.group(1)
            dept = get_dept(slug)

            # Try 1: legacy dept URL
            img = None
            if dept:
                legacy_url = f"https://ocw.mit.edu/courses/{dept}/{slug}/"
                img = await try_url(session, legacy_url)
                if img:
                    print(f"  ✓ legacy [{dept}] {slug[:50]}", flush=True)

            # Try 2: OCW search for this title
            if not img:
                img = await try_mit_search(session, title)
                if img:
                    print(f"  ✓ search  [{title[:45]}]", flush=True)

            if img:
                cur.execute(
                    "UPDATE courses SET thumbnail_url=%s WHERE id=%s",
                    (img, course_id),
                )
                updated += 1
            else:
                print(f"  ✗ {slug[:60]}", flush=True)

    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
        await asyncio.gather(*[proc(*r) for r in rows])

    conn.commit()

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.0f}s — updated {updated}/{len(rows)}", flush=True)

    cur.execute("SELECT COUNT(*) total, COUNT(thumbnail_url) has_thumb FROM courses")
    row = cur.fetchone()
    pct = row[1] / row[0] * 100
    print(f"DB coverage: {row[1]}/{row[0]} = {pct:.1f}%", flush=True)
    conn.close()


if __name__ == "__main__":
    asyncio.run(run())
