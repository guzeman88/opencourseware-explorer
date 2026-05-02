"""
fetch_thumbnails_2.py
Second pass:
  1. YouTube playlists → oEmbed API (no key required)
  2. MIT OCW remaining → retry with redirect-following
"""

import asyncio
import json
import re
import sys
import time

import aiohttp
import psycopg2

CONN_STR = "postgresql://ocw:ocwpassword@127.0.0.1:5432/opencourseware"
MIT_LOGO = "https://ocw.mit.edu/img/mit-logo-250.png"
CONCURRENCY = 10

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


async def yt_oembed_thumb(session: aiohttp.ClientSession, playlist_id: str) -> str | None:
    """YouTube oEmbed API — returns thumbnail_url, no API key needed."""
    url = (
        "https://www.youtube.com/oembed"
        f"?url=https%3A%2F%2Fwww.youtube.com%2Fplaylist%3Flist%3D{playlist_id}"
        "&format=json"
    )
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=12)) as resp:
            if resp.status == 200:
                data = await resp.json(content_type=None)
                thumb = data.get("thumbnail_url")
                if thumb:
                    return thumb
    except Exception as e:
        pass

    # Fallback: scrape the playlist page og:image
    page_url = f"https://www.youtube.com/playlist?list={playlist_id}"
    try:
        async with session.get(page_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 200:
                html = await resp.text(errors="replace")
                m = re.search(
                    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
                    html,
                ) or re.search(
                    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
                    html,
                )
                if m:
                    img = m.group(1).strip()
                    if img and "ytimg" in img:
                        return img
                # Try extracting from initial data JSON
                m2 = re.search(r'"thumbnail"\s*:\s*\{"thumbnails"\s*:\s*\[([^\]]+)\]', html)
                if m2:
                    inner = m2.group(1)
                    mu = re.search(r'"url"\s*:\s*"([^"]+)"', inner)
                    if mu:
                        u = mu.group(1).replace("\\u0026", "&")
                        if u:
                            return u
    except Exception as e:
        pass
    return None


async def fetch_og_image(session: aiohttp.ClientSession, url: str) -> str | None:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=20),
                               allow_redirects=True) as resp:
            if resp.status != 200:
                return None
            html = await resp.text(errors="replace")
            m = re.search(
                r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
                html,
            ) or re.search(
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
                html,
            )
            if m:
                img = m.group(1).strip()
                if img and MIT_LOGO not in img and not img.endswith("mit-logo-250.png"):
                    return img
    except Exception:
        pass
    return None


async def run():
    conn = psycopg2.connect(CONN_STR)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, source_url, source_key, youtube_playlist_id
        FROM courses
        WHERE thumbnail_url IS NULL
        ORDER BY source_key, id
        """
    )
    rows = cur.fetchall()
    total = len(rows)
    print(f"Still missing thumbnails: {total}", flush=True)

    mit_rows = [(r[0], r[1]) for r in rows if r[2] == "mit_ocw"]
    yt_rows  = [(r[0], r[3]) for r in rows if r[2] != "mit_ocw" and r[3]]

    print(f"  MIT OCW remaining  : {len(mit_rows)}", flush=True)
    print(f"  YouTube playlists  : {len(yt_rows)}", flush=True)

    updated = 0
    start = time.time()
    sem = asyncio.Semaphore(CONCURRENCY)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY + 5, ssl=False)

    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:

        # ── YouTube playlists via oEmbed ────────────────────────────────────
        if yt_rows:
            print("\n[1/2] YouTube oEmbed thumbnails...", flush=True)

            async def proc_yt(course_id, playlist_id):
                nonlocal updated
                async with sem:
                    thumb = await yt_oembed_thumb(session, playlist_id)
                    if thumb:
                        cur.execute(
                            "UPDATE courses SET thumbnail_url=%s WHERE id=%s",
                            (thumb, course_id),
                        )
                        updated += 1
                        print(f"  ✓ {playlist_id[:40]}", flush=True)
                    else:
                        print(f"  ✗ {playlist_id[:40]}", flush=True)

            await asyncio.gather(*[proc_yt(r[0], r[1]) for r in yt_rows])
            conn.commit()
            print(f"  YouTube done: {updated} thumbnails", flush=True)

        # ── MIT OCW retry ──────────────────────────────────────────────────
        if mit_rows:
            print(f"\n[2/2] MIT OCW retry ({len(mit_rows)} pages)...", flush=True)
            mit_ok = 0

            async def proc_mit(course_id, source_url):
                nonlocal updated, mit_ok
                async with sem:
                    img = await fetch_og_image(session, source_url)
                    if img:
                        cur.execute(
                            "UPDATE courses SET thumbnail_url=%s WHERE id=%s",
                            (img, course_id),
                        )
                        updated += 1
                        mit_ok += 1
                        print(f"  ✓ {source_url}", flush=True)
                    else:
                        print(f"  ✗ {source_url}", flush=True)

            await asyncio.gather(*[proc_mit(r[0], r[1]) for r in mit_rows])
            conn.commit()
            print(f"  MIT retry done: {mit_ok}/{len(mit_rows)}", flush=True)

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.0f}s — updated {updated}/{total}", flush=True)

    cur.execute("SELECT COUNT(*) total, COUNT(thumbnail_url) has_thumb FROM courses")
    row = cur.fetchone()
    pct = row[1] / row[0] * 100
    print(f"DB coverage: {row[1]}/{row[0]} = {pct:.1f}%", flush=True)
    conn.close()


if __name__ == "__main__":
    asyncio.run(run())
