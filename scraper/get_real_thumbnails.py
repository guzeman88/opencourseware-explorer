#!/usr/bin/env python3
"""
get_real_thumbnails.py

Replaces ALL Unsplash fallback thumbnails with real course thumbnails.
Uses parallel HTTP requests (ThreadPoolExecutor) for speed.

Confirmed working strategies:
  1. NPTEL      → SvelteKit __data.json endpoint → first lesson youtube_id
                   → https://i.ytimg.com/vi/{id}/hqdefault.jpg
  2. Yale OYC   → Drupal course_detail image from page HTML
  3. Generic    → og:image scraping (MIT OCW, Harvard, Caltech, Simons,
                   FreeCodeCamp, CMU, UW edX, UPenn Coursera, etc.)

Note: YouTube oembed API returns 404 for playlists. YouTube RSS feeds return 404.
Pure YouTube playlist source URLs (CrashCourse, 3b1b etc) have no accessible
thumbnail without the YouTube Data API. Those courses will remain NULL.
"""

import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import psycopg2
import requests
from db_utils import get_connection

# Thread-local HTTP sessions (requests.Session is NOT thread-safe when shared)
_tl = threading.local()

def get_session() -> requests.Session:
    if not hasattr(_tl, "session"):
        s = requests.Session()
        s.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        _tl.session = s
    return _tl.session


# ── og:image extraction ───────────────────────────────────────────────────────

def fetch_og_image(url: str, timeout: int = 12) -> str | None:
    """
    Fetch a web page and extract its og:image meta tag value.
    Handles both attribute orderings and whitespace variations.
    """
    if not url:
        return None
    try:
        resp = get_session().get(url, timeout=timeout, allow_redirects=True)
        if not resp.ok:
            return None
        html = resp.text

        # Strategy 1: Parse each <meta ...> tag individually
        for tag in re.findall(r'<meta\s+([^>]+?)(?:/>|>)', html, re.IGNORECASE | re.DOTALL):
            if re.search(r'og:image', tag, re.IGNORECASE):
                m = re.search(r'content=["\']([^"\']+)', tag, re.IGNORECASE)
                if m:
                    img = m.group(1).strip()
                    if img.startswith("http"):
                        return img

        # Strategy 2: Broad scan for og:image anywhere in document
        for pat in [
            r'property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
            r'content=["\']([^"\']+)["\'][^>]+property=["\']og:image',
            r'og:image.*?content=["\']([^"\']+)',
        ]:
            m = re.search(pat, html, re.IGNORECASE | re.DOTALL)
            if m:
                img = m.group(1).strip()
                if img.startswith("http"):
                    return img
    except Exception:
        pass
    return None


# ── NPTEL: SvelteKit __data.json → youtube_id → ytimg ────────────────────────

def _svelte_resolve(flat: list, idx):
    """Recursively resolve SvelteKit flat-array references."""
    if not isinstance(idx, int) or idx >= len(flat):
        return idx
    val = flat[idx]
    if isinstance(val, dict):
        return {k: _svelte_resolve(flat, v) for k, v in val.items()}
    elif isinstance(val, list):
        return [_svelte_resolve(flat, v) for v in val]
    return val


def nptel_thumb(source_url: str) -> str | None:
    """
    Fetch NPTEL course's SvelteKit __data.json, extract first lesson's
    youtube_id, return https://i.ytimg.com/vi/{id}/hqdefault.jpg
    """
    # Extract course_id from old URL format /courses/dept1/dept2/{course_id}/
    # or new format /courses/{course_id}
    m = re.search(r'/courses/\d+/\d+/(\d+)/?', source_url)
    if not m:
        m = re.search(r'/courses/(\d+)/?$', source_url)
    if not m:
        return None
    course_id = m.group(1)

    try:
        url = f"https://nptel.ac.in/courses/{course_id}/__data.json"
        r = get_session().get(url, timeout=15)
        if not r.ok:
            return None
        data = r.json()
        for node in data.get("nodes", []):
            if not node or node.get("type") != "data":
                continue
            flat = node.get("data", [])
            if not flat or not isinstance(flat[0], dict):
                continue
            resolved = _svelte_resolve(flat, 0)
            # Navigate: courseOutline.units[0].lessons[0].youtube_id
            co = resolved.get("courseOutline") or {}
            units = co.get("units") or []
            if units:
                lessons = (units[0] or {}).get("lessons") or []
                if lessons:
                    yt_id = (lessons[0] or {}).get("youtube_id")
                    if yt_id and len(str(yt_id)) >= 8:
                        # Try maxresdefault first, fall back to hqdefault
                        for size in ("maxresdefault", "hqdefault"):
                            thumb_url = f"https://i.ytimg.com/vi/{yt_id}/{size}.jpg"
                            try:
                                hr = get_session().head(thumb_url, timeout=6)
                                if hr.ok:
                                    return thumb_url
                            except Exception:
                                pass
    except Exception:
        pass
    return None


# ── Yale OYC: Drupal course_detail image ──────────────────────────────────────

def yale_thumb(source_url: str) -> str | None:
    """
    Extract course thumbnail from oyc.yale.edu Drupal pages.
    The course image is at /sites/default/files/...jpg in the page HTML.
    """
    if not source_url or "oyc.yale.edu" not in source_url:
        return None
    try:
        r = get_session().get(source_url, timeout=12)
        if not r.ok:
            return None
        html = r.text
        m = re.search(
            r'(/sites/default/files/[^"\']+\.(?:jpg|jpeg|png|webp)[^"\']*)',
            html, re.IGNORECASE
        )
        if m:
            path = m.group(1).replace("&amp;", "&")
            return f"https://oyc.yale.edu{path}"
    except Exception:
        pass
    return None


# ── Main per-course resolver ──────────────────────────────────────────────────

def get_thumb_for_course(row: tuple) -> tuple:
    """Returns (course_id, thumbnail_url_or_None). Runs in a worker thread."""
    cid, title, skey, surl, yt_playlist, first_vid = row
    surl = (surl or "").strip()

    # ── 1. NPTEL: __data.json → youtube_id → ytimg ──
    if skey == "nptel":
        t = nptel_thumb(surl)
        return (cid, t)

    # ── 2. Yale OYC: Drupal image ──
    if skey == "yale" or (surl and "oyc.yale.edu" in surl):
        t = yale_thumb(surl)
        if t:
            return (cid, t)
        # Fall through to og:image

    # ── 3. Skip pure YouTube playlist source URLs (no accessible thumbnail
    #       without YouTube Data API — oembed and RSS both return 404) ──
    if surl and re.match(r'https?://(?:www\.)?youtube\.com/playlist', surl):
        return (cid, None)

    # ── 4. Generic og:image (handles MIT OCW, Harvard, Caltech, FreeCodeCamp,
    #       Simons, CMU, edX sources, Coursera sources, Stanford dept pages…) ──
    if surl:
        t = fetch_og_image(surl, timeout=14)
        if t:
            return (cid, t)

    return (cid, None)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.id, c.title, c.source_key, c.source_url,
               c.youtube_playlist_id,
               (SELECT v.youtube_id FROM videos v
                WHERE v.course_id = c.id ORDER BY v."order" ASC LIMIT 1) AS first_vid
        FROM courses c
        WHERE c.thumbnail_url LIKE '%unsplash%'
        ORDER BY c.source_key, c.title
    """)
    rows = cur.fetchall()
    total = len(rows)
    print(f"Courses with Unsplash fallback thumbnails: {total}")
    if total == 0:
        print("Nothing to do.")
        cur.close()
        conn.close()
        return

    # Clear all unsplash thumbnails to NULL before fetching real ones
    cur.execute("UPDATE courses SET thumbnail_url = NULL WHERE thumbnail_url LIKE '%unsplash%'")
    conn.commit()
    print(f"Cleared {total} Unsplash thumbnails → NULL.")
    print("Starting real thumbnail fetch with 20 parallel workers...\n")

    updated = 0
    failed = 0
    source_stats: dict[str, dict] = {}
    results: dict[str, str | None] = {}

    t0 = time.time()

    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_row = {executor.submit(get_thumb_for_course, row): row for row in rows}

        for i, future in enumerate(as_completed(future_to_row)):
            row = future_to_row[future]
            skey = row[2]
            try:
                cid, thumb = future.result()
            except Exception as exc:
                cid = row[0]
                thumb = None
                print(f"  ERROR [{skey}] {row[1][:40]}: {exc}")

            results[cid] = thumb

            if skey not in source_stats:
                source_stats[skey] = {"ok": 0, "fail": 0}
            if thumb:
                source_stats[skey]["ok"] += 1
                updated += 1
            else:
                source_stats[skey]["fail"] += 1
                failed += 1

            if (i + 1) % 100 == 0:
                elapsed = time.time() - t0
                rate = (i + 1) / elapsed
                remaining = (total - i - 1) / rate if rate > 0 else 0
                print(f"  [{i+1:4d}/{total}] real={updated} null={failed} "
                      f"rate={rate:.1f}/s eta={remaining:.0f}s")

    # Write all results to DB
    print(f"\nWriting {updated} thumbnail URLs to database ...")
    for row in rows:
        cid = row[0]
        thumb = results.get(cid)
        if thumb:
            cur.execute("UPDATE courses SET thumbnail_url = %s WHERE id = %s", (thumb, cid))
    conn.commit()

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"Done in {elapsed:.0f}s.")
    print(f"Real thumbnails set: {updated}/{total}")
    print(f"Still NULL (no accessible thumbnail): {failed}")
    print(f"\nPer-source breakdown:")
    print(f"  {'source':24s}  {'ok':>5}  {'fail':>5}")
    print(f"  {'-'*40}")
    for src, stats in sorted(source_stats.items(), key=lambda x: -(x[1]['ok'] + x[1]['fail'])):
        if stats['ok'] + stats['fail'] > 0:
            print(f"  {src:24s}  {stats['ok']:5d}  {stats['fail']:5d}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
