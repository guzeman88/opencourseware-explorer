"""
fetch_thumbnails_3.py
Third pass: scrape og:image from source_url for ALL remaining courses
(both MIT retry and non-MIT university pages).
Also hardcodes known YouTube video IDs for popular courses where playlist lookup fails.
"""

import asyncio
import re
import time

import aiohttp
import psycopg2

CONN_STR = "postgresql://ocw:ocwpassword@127.0.0.1:5432/opencourseware"
MIT_LOGO = "https://ocw.mit.edu/img/mit-logo-250.png"
CONCURRENCY = 15

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Known first-video IDs for playlists that YouTube blocks
# Format: { playlist_id: youtube_video_id }
KNOWN_VIDEO_IDS = {
    # 3Blue1Brown
    "PLZHQObOWTQDNPOjrT6KVlfJuKtYTftqH1": "p_di4Zn4wz4",  # DE series
    # Berkeley CS61A
    "PLhMnuBfGeCDNgVzLPxF9o5UNKG7LeZyng": "0jljZxf95fo",
    # Berkeley CS61C
    "PLDoI-XvXX0kUoMBIWKGwfAlZmq3K8Q7Gu": "9y89TTBnBuk",
    # Berkeley CS70
    "PLkFD6_40KJIxJMR9fbkuu7grHoxfu30_y": "vaUEQDBJaIs",
    # Berkeley CS285
    "PL_iWQOsE6TfVYGEGiAf6h9tnVMsKX5dAX": "ue9aS17d5iI",
    # Berkeley CS189
    "PLOOm2AoWNCHh04aPJHi0l4xrgTz8jqsNp": "slGitmCIqMs",
    # Berkeley EE16A
    "PLkFD6_40KJIwoOHJ2UMBjBGnZkLl4DAnS": "FRXDJ_2xBQU",
    # Berkeley Physics10
    "PLF5B7F21FB98E3620": "M1OFMtgpzAU",
    # Crash Course World History
    "PLBDA2A52596754C17": "Yocja_N5s1I",
    # Crash Course Economics
    "PL1oDmcs0xTD-dJN1PL2N1urX0EKupBJkQ": "bu56jHbILio",
    # Crash Course Artificial Intelligence
    "PLH2l6uzC4UEW0s7-KewFLBC1D0l6XRttC": "a0_lo_GDcFw",
    # Crash Course Statistics
    "PL8dPuuaLjXtNM_Y-bUAhblSAdWRnmdfZ3": "zouPoc49xbk",
    # Crash Course Philosophy
    "PLtKNX4SfUs73gvH4B6OsJI8Hl9DV62_WT": "1A_CAkYt3GY",
    # Crash Course Computer Science
    "PL8dPuuaLjXtNgK6MoafmfgiXTZRyrr0iB": "O5nskjLLeJg",
    # Crash Course Biology
    "PL3EED4C1D684D3ADF": "QnQe0xW_JY4",
    # Harvard CS50
    "PLhQjrBD2T380KNMCECLKrFfbxLbPTDQtS": "IDDmrzzB14M",
    # Harvard CS50 Python
    "PLhQjrBD2T381VAFMSVCJa5od_i0dmhvMx": "nLRL_NcnK-4",
    # Harvard Data Science
    "PLhQjrBD2T380El0MdL9dBHniqSFJiZWMa": "AvgB8-lEDYo",
    # Harvard CS50 AI
    "PLhQjrBD2T381Q-lRkm40LBJGHPAy1YhKv": "WbzNRTTrX0g",
    # Harvard Justice
    "PLQyPl6C7EwMCuFNntnbFBYIJHIHl0M7j7": "kBdfcR-8hEY",
    # Harvard Introduction to Game Development
    "PLhQjrBD2T3812tj4cjP2pZbsE37fj_gZ6": "jZqYXSmgDuM",
    # Khan Academy Linear Algebra
    "PLFD0EB975BA0CC1E0": "xyAuNHPsq-g",
    # Khan Academy Multivariable Calculus
    "PLSQl0a2vh4HCfSaDSsM7KBmFPaGimqGDP": "TrcCbdWwCBc",
    # Khan Academy Differential Equations
    "PLSQl0a2vh4HDs9KofCMrBO2sCrCHWmFRe": "6o7b9yyhH7k",
    # Khan Academy Statistics
    "PLSQl0a2vh4HCFkp0HVDxe3LJPHXlUqB43": "uhxtUt_-GyM",
    # Yale ECON159
    "PLqOZ6FD_RQ7ln1ge6L8cTnNKFHe2A1D0b": "nM3rTU927io",
    # Yale Financial Markets
    "PLFDbGp5YzjqXQ4oE4w9GVWdiokWB9gEpm": "WQpJAGGZIh0",
    # Yale PSYC110
    "PL6A08EB4EEFF3E91F": "P3FSKV3IHmA",
    # Yale PHIL181
    "PLh9mgdi4rNewYDaK2gDC7aWzV5iJreSoQ": "9YiMBGCM3bY",
    # Stanford ML (Andrew Ng)
    "PLoROMvodv4rMIJ-TvblAIkw28Wxi27B1h": "jGwO_UgTS7I",
    # Stanford NLP
    "PLoROMvodv4rOSOPzxUAZed-Ce8r-KiT3m": "rmVRLeJRkl4",
    # Stanford CNN
    "PLE323F3B6B6B03A5A": "vT1JzLTH4G4",
    # Stanford Reinforcement Learning
    "PLoROMvodv4rOABXSygHTsbvUz4G_YQhOb": "FgzM3zpZ55o",
    # freeCodeCamp Machine Learning
    "PLWKjhJtqVAbl5SlE1osOoaRanch1kavSRI": "NWONeJKn9Kc",
    # freeCodeCamp Deep Learning
    "PLWKjhJtqVAbknyJ7hSrf1WKh_Xnv9RL1E": "6g4O5UOH304",
    # NPTEL courses
    "PLbRMhDVUMngcxHBcuIqPvqHN1qomWPQj0": "K8Pyp4p6J_s",
    "PLbRMhDVUMngcwMTyYkHt9VRsJRDSCaP7K": "2PyFMp1EGUY",
    "PLF706D4C8B6F0EDE2": "GTPn7c2HHXQ",
    "PL46ED3BF40EDB2D23": "1nMFdkKbsxg",
    "PLC64BEFBE84598658": "VJrEBTz7RRQ",
    "PLF7CBA45AEBAD18B8": "igJgL6hra8w",
    "PLgKuh-lKre12y4gzh0bBNGH0MMchfTxJD": "6P08c0a_MLk",
    "PLEAYkSg4uSQ0OVMb6ux5RpqBRhpCKmYCj": "9THN0QxM0Vs",
    "PLEAYkSg4uSQ3Hi5n7ejSFa1ReHFVFiGKS": "pQ6XCZTlm1E",
    "PLEAYkSg4uSQ3s1RFoFwzOVfxBNXi-RSTW": "RBSGKlAvoiM",
    "PLBF3763AF2452C8C6": "rCxFoXVBGzk",
    # Simons Institute
    "PLgKuh-lKre11GbZx3fRAsQEDmOKNIuVKP": "FeNkDr7p6zU",
    # Georgia Tech
    "PLAwxTw4SYaPkNAtqsKcFkUGpf4j67NBef": "2wl4Jf1mNDo",
    # freeCodeCamp 
    "PLfeEvEPtX_0S6vxxiiNPrJbLu9aK1UyoiV": "rfscVS0vtbw",
    "PLh9mgdi4rNeznMykHj5aEcFX6ySlAKjWx": "zOjov-2OZ0E",
    "PLh9mgdi4rNewbMX8FNrFOoLHzqECXMflt": "8hly31xKli0",
    "PLh9mgdi4rNewMbr3x-fAm7zcmOVOlVoT4": "rfscVS0vtbw",
    "PLh9mgdi4rNeSXcggwbSNEAqNIGpFe5i3S": "aircAruvnKk",
    "PLfVCJZxvQA2j-BRHpCDQIWrI5sZoJKPfk": "u6QfIXgjwGQ",
    "PLyqSpQzTE6M_bB7XwBVq5UAphMGrMutMV": "Xvg00sklIAA",
    "PL7UrpuFGb5Zp6ULGGEAyeYI3LbKhYHkrB": "kBdfcR-8hEY",
    "PLkXkbxA6dkVQZ7MeX5grFiR_tUvniOBhv": "rfscVS0vtbw",
}


async def fetch_og_image(session: aiohttp.ClientSession, url: str) -> str | None:
    """Scrape og:image from any web page."""
    try:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=20),
            allow_redirects=True,
        ) as resp:
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
    print(f"Still missing: {len(rows)}", flush=True)

    updated = 0
    start = time.time()

    # ── 1. Apply known video ID → thumbnail URL directly ─────────────────────
    print("\n[1/2] Applying known YouTube video IDs...", flush=True)
    for course_id, source_url, source_key, playlist_id in rows:
        if playlist_id and playlist_id in KNOWN_VIDEO_IDS:
            vid_id = KNOWN_VIDEO_IDS[playlist_id]
            thumb = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
            cur.execute(
                "UPDATE courses SET thumbnail_url=%s WHERE id=%s",
                (thumb, course_id),
            )
            updated += 1
            print(f"  ✓ {playlist_id[:40]:40s} → {vid_id}", flush=True)
    conn.commit()
    print(f"  Applied {updated} known thumbnails", flush=True)

    # Reload remaining
    cur.execute(
        """
        SELECT id, source_url, source_key, youtube_playlist_id
        FROM courses
        WHERE thumbnail_url IS NULL
        ORDER BY source_key, id
        """
    )
    remaining = cur.fetchall()
    print(f"  Still missing after known IDs: {len(remaining)}", flush=True)

    # ── 2. Scrape source_url og:image for all remaining ───────────────────────
    if remaining:
        print(f"\n[2/2] Scraping source_url og:image for {len(remaining)} courses...", flush=True)
        sem = asyncio.Semaphore(CONCURRENCY)
        connector = aiohttp.TCPConnector(limit=CONCURRENCY + 5, ssl=False)
        scraped = 0

        async def proc(course_id, source_url, source_key, playlist_id):
            nonlocal updated, scraped
            if not source_url:
                return
            async with sem:
                img = await fetch_og_image(session, source_url)
                if img:
                    cur.execute(
                        "UPDATE courses SET thumbnail_url=%s WHERE id=%s",
                        (img, course_id),
                    )
                    updated += 1
                    scraped += 1
                    print(f"  ✓ [{source_key}] {source_url[:70]}", flush=True)
                else:
                    print(f"  ✗ [{source_key}] {source_url[:70]}", flush=True)

        async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
            await asyncio.gather(*[proc(*r) for r in remaining])

        conn.commit()
        print(f"  Scraped {scraped} thumbnails from source pages", flush=True)

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.0f}s — updated {updated} total", flush=True)

    cur.execute("SELECT COUNT(*) total, COUNT(thumbnail_url) has_thumb FROM courses")
    row = cur.fetchone()
    pct = row[1] / row[0] * 100
    print(f"DB coverage: {row[1]}/{row[0]} = {pct:.1f}%", flush=True)
    conn.close()


if __name__ == "__main__":
    asyncio.run(run())
