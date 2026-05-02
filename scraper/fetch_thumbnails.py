"""
fetch_thumbnails.py
Fetches real thumbnail images for all courses missing them.

Strategy:
  - MIT OCW: async scrape og:image from each source_url page
  - Non-MIT (all have youtube_playlist_id): yt-dlp to get first video thumbnail
"""

import asyncio
import re
import sys
import time

import aiohttp
import psycopg2
import yt_dlp

CONN_STR = "postgresql://ocw:ocwpassword@127.0.0.1:5432/opencourseware"
MIT_LOGO = "https://ocw.mit.edu/img/mit-logo-250.png"
CONCURRENCY = 20          # parallel OCW page fetches
YT_CONCURRENCY = 5        # parallel yt-dlp calls


# ── helpers ────────────────────────────────────────────────────────────────────

def ytimg(video_id: str) -> str:
    return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"


async def fetch_og_image(session: aiohttp.ClientSession, url: str) -> str | None:
    """Fetch og:image from an HTML page. Returns None if not found or generic."""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                return None
            html = await resp.text(errors="replace")
            # Try property="og:image" content="..." (both attribute orders)
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


def yt_first_video_thumb(playlist_id: str) -> str | None:
    """Use yt-dlp to get the first video's thumbnail from a YouTube playlist."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,   # don't download, just list entries
        "playlist_items": "1",  # only first entry
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/playlist?list={playlist_id}",
                download=False,
            )
            entries = info.get("entries") or []
            if entries:
                vid = entries[0]
                # Prefer explicit thumbnail, fall back to constructing from id
                thumb = vid.get("thumbnail") or vid.get("thumbnails", [{}])[-1].get("url")
                if thumb:
                    return thumb
                vid_id = vid.get("id")
                if vid_id:
                    return ytimg(vid_id)
    except Exception as e:
        print(f"    yt-dlp error for {playlist_id}: {e}", flush=True)
    return None


# ── main ───────────────────────────────────────────────────────────────────────

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
    print(f"Courses without thumbnails: {total}", flush=True)

    mit_rows = [(r[0], r[1]) for r in rows if r[2] == "mit_ocw"]
    yt_rows  = [(r[0], r[3]) for r in rows if r[2] != "mit_ocw" and r[3]]

    print(f"  MIT OCW to scrape : {len(mit_rows)}", flush=True)
    print(f"  YouTube playlists : {len(yt_rows)}", flush=True)

    updated = 0
    start = time.time()

    # ── 1. Non-MIT via yt-dlp (small set, run synchronously in thread pool) ──
    if yt_rows:
        print("\n[1/2] Fetching YouTube playlist thumbnails...", flush=True)
        sem_yt = asyncio.Semaphore(YT_CONCURRENCY)

        async def process_yt(course_id, playlist_id):
            nonlocal updated
            async with sem_yt:
                loop = asyncio.get_running_loop()
                thumb = await loop.run_in_executor(
                    None, yt_first_video_thumb, playlist_id
                )
                if thumb:
                    cur.execute(
                        "UPDATE courses SET thumbnail_url=%s WHERE id=%s",
                        (thumb, course_id),
                    )
                    updated += 1
                    print(f"    ✓ {playlist_id[:30]}  →  {thumb[:60]}", flush=True)
                else:
                    print(f"    ✗ {playlist_id[:30]}  (no thumb found)", flush=True)

        await asyncio.gather(*[process_yt(r[0], r[1]) for r in yt_rows])
        conn.commit()
        print(f"  YouTube done: {updated} thumbnails", flush=True)

    # ── 2. MIT OCW via async HTTP ──────────────────────────────────────────────
    if mit_rows:
        print(f"\n[2/2] Scraping {len(mit_rows)} MIT OCW pages (concurrency={CONCURRENCY})...", flush=True)
        sem = asyncio.Semaphore(CONCURRENCY)
        mit_updated = 0
        batch_start = updated

        async def process_mit(session, course_id, source_url):
            nonlocal updated, mit_updated
            async with sem:
                img = await fetch_og_image(session, source_url)
                if img:
                    cur.execute(
                        "UPDATE courses SET thumbnail_url=%s WHERE id=%s",
                        (img, course_id),
                    )
                    updated += 1
                    mit_updated += 1
                    if mit_updated % 100 == 0:
                        conn.commit()
                        elapsed = time.time() - start
                        pct = (updated / total) * 100
                        print(
                            f"  {mit_updated}/{len(mit_rows)} MIT pages scraped"
                            f"  ({updated} total, {pct:.1f}% of missing)  [{elapsed:.0f}s]",
                            flush=True,
                        )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        connector = aiohttp.TCPConnector(limit=CONCURRENCY + 5, ssl=False)
        async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
            tasks = [process_mit(session, r[0], r[1]) for r in mit_rows]
            await asyncio.gather(*tasks)

        conn.commit()
        print(
            f"  MIT OCW done: {mit_updated}/{len(mit_rows)} thumbnails found"
            f"  ({mit_updated/len(mit_rows)*100:.1f}% hit rate)",
            flush=True,
        )

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.0f}s — updated {updated}/{total} missing thumbnails", flush=True)

    # ── Summary ───────────────────────────────────────────────────────────────
    cur.execute(
        "SELECT COUNT(*) total, COUNT(thumbnail_url) has_thumb FROM courses"
    )
    row = cur.fetchone()
    pct = row[1] / row[0] * 100
    print(f"DB coverage: {row[1]}/{row[0]} = {pct:.1f}%", flush=True)

    conn.close()


if __name__ == "__main__":
    asyncio.run(run())
