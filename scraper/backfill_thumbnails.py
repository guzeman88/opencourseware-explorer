#!/usr/bin/env python3
"""
backfill_thumbnails.py

Populates thumbnail_url for ALL courses that currently have NULL.

Strategy (per course):
  1. NPTEL      → SvelteKit __data.json → first lesson youtube_id → ytimg
  2. Yale OYC   → Drupal course_detail image
  3. YouTube playlist source URL → scrape playlist page for first video id → ytimg
  4. Videos table → first video youtube_id → ytimg  (for any source)
  5. Generic og:image scrape (MIT OCW, Harvard, Stanford, etc.)
  6. FALLBACK: subject-based Unsplash image (100% coverage guarantee)

Runs 20 parallel workers. Commits in batches of 100.
"""

import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import psycopg2
import requests

DB = "postgresql://neondb_owner:npg_GbATRcy2v8Fo@ep-gentle-cherry-an1c9y9a-pooler.c-6.us-east-1.aws.neon.tech/opencourseware?sslmode=require"

# ── Thread-local sessions ─────────────────────────────────────────────────────
_tl = threading.local()

def session() -> requests.Session:
    if not hasattr(_tl, "s"):
        s = requests.Session()
        s.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        _tl.s = s
    return _tl.s


# ── Subject-based Unsplash fallbacks ─────────────────────────────────────────
SUBJECT_MAP = [
    ("machine learning",       "https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=640&q=80"),
    ("artificial intelligence","https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=640&q=80"),
    ("deep learning",          "https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=640&q=80"),
    ("data science",           "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=640&q=80"),
    ("computer science",       "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=640&q=80"),
    ("software",               "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=640&q=80"),
    ("programming",            "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=640&q=80"),
    ("algorithm",              "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=640&q=80"),
    ("web development",        "https://images.unsplash.com/photo-1547658719-da2b51169166?w=640&q=80"),
    ("javascript",             "https://images.unsplash.com/photo-1547658719-da2b51169166?w=640&q=80"),
    ("python",                 "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=640&q=80"),
    ("cybersecurity",          "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=640&q=80"),
    ("network",                "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=640&q=80"),
    ("robotics",               "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=640&q=80"),
    ("linear algebra",         "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=640&q=80"),
    ("calculus",               "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=640&q=80"),
    ("mathematics",            "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=640&q=80"),
    ("algebra",                "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=640&q=80"),
    ("statistics",             "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=640&q=80"),
    ("probability",            "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=640&q=80"),
    ("quantum",                "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=640&q=80"),
    ("thermodynamics",         "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=640&q=80"),
    ("astrophysics",           "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=640&q=80"),
    ("astronomy",              "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=640&q=80"),
    ("physics",                "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=640&q=80"),
    ("organic chemistry",      "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=640&q=80"),
    ("chemistry",              "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=640&q=80"),
    ("genetics",               "https://images.unsplash.com/photo-1530026405186-ed1f139313f0?w=640&q=80"),
    ("biology",                "https://images.unsplash.com/photo-1530026405186-ed1f139313f0?w=640&q=80"),
    ("ecology",                "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=640&q=80"),
    ("neuroscience",           "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=640&q=80"),
    ("epidemiology",           "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=640&q=80"),
    ("public health",          "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=640&q=80"),
    ("medicine",               "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=640&q=80"),
    ("medical",                "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=640&q=80"),
    ("nursing",                "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=640&q=80"),
    ("nutrition",              "https://images.unsplash.com/photo-1490818387583-1baba5e638af?w=640&q=80"),
    ("chemical engineering",   "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=640&q=80"),
    ("electrical engineering", "https://images.unsplash.com/photo-1518770660439-4636190af475?w=640&q=80"),
    ("mechanical engineering", "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=640&q=80"),
    ("civil engineering",      "https://images.unsplash.com/photo-1486325212027-8081e485255e?w=640&q=80"),
    ("engineering",            "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=640&q=80"),
    ("materials",              "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=640&q=80"),
    ("architecture",           "https://images.unsplash.com/photo-1486325212027-8081e485255e?w=640&q=80"),
    ("urban",                  "https://images.unsplash.com/photo-1486325212027-8081e485255e?w=640&q=80"),
    ("entrepreneurship",       "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=640&q=80"),
    ("management",             "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=640&q=80"),
    ("marketing",              "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=640&q=80"),
    ("business",               "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=640&q=80"),
    ("finance",                "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=640&q=80"),
    ("accounting",             "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=640&q=80"),
    ("economics",              "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=640&q=80"),
    ("cognitive",              "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=640&q=80"),
    ("psychology",             "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=640&q=80"),
    ("philosophy",             "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=640&q=80"),
    ("ethics",                 "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=640&q=80"),
    ("history",                "https://images.unsplash.com/photo-1461360370896-22624d12aa1?w=640&q=80"),
    ("archaeology",            "https://images.unsplash.com/photo-1461360370896-22624d12aa1?w=640&q=80"),
    ("literature",             "https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=640&q=80"),
    ("writing",                "https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=640&q=80"),
    ("linguistics",            "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=640&q=80"),
    ("language",               "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=640&q=80"),
    ("music",                  "https://images.unsplash.com/photo-1507838153414-b4b713384a76?w=640&q=80"),
    ("design",                 "https://images.unsplash.com/photo-1559028006-448665bd7c7f?w=640&q=80"),
    ("art",                    "https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=640&q=80"),
    ("climate",                "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=640&q=80"),
    ("environment",            "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=640&q=80"),
    ("legal",                  "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=640&q=80"),
    ("law",                    "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=640&q=80"),
    ("political",              "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=640&q=80"),
    ("sociology",              "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=640&q=80"),
    ("social",                 "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=640&q=80"),
    ("geography",              "https://images.unsplash.com/photo-1524661135-423995f22d0b?w=640&q=80"),
]
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=640&q=80"

def subject_fallback(title: str) -> str:
    low = title.lower()
    for keyword, url in SUBJECT_MAP:
        if keyword in low:
            return url
    return DEFAULT_IMAGE


# ── og:image extraction ───────────────────────────────────────────────────────
def fetch_og_image(url: str, timeout: int = 12) -> str | None:
    if not url:
        return None
    try:
        resp = session().get(url, timeout=timeout, allow_redirects=True)
        if not resp.ok:
            return None
        html = resp.text
        # Parse each <meta ...> tag
        for tag in re.findall(r'<meta\s+([^>]+?)(?:/>|>)', html, re.IGNORECASE | re.DOTALL):
            if re.search(r'og:image', tag, re.IGNORECASE):
                m = re.search(r'content=["\']([^"\']+)', tag, re.IGNORECASE)
                if m:
                    img = m.group(1).strip()
                    if img.startswith("http"):
                        return img
        # Broad scan
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


# ── NPTEL: __data.json → first lesson youtube_id ─────────────────────────────
def _svelte_resolve(flat, idx):
    if not isinstance(idx, int) or idx >= len(flat):
        return idx
    val = flat[idx]
    if isinstance(val, dict):
        return {k: _svelte_resolve(flat, v) for k, v in val.items()}
    elif isinstance(val, list):
        return [_svelte_resolve(flat, v) for v in val]
    return val

def nptel_thumb(source_url: str) -> str | None:
    m = re.search(r'/courses/\d+/\d+/(\d+)/?', source_url)
    if not m:
        m = re.search(r'/courses/(\d+)/?$', source_url)
    if not m:
        return None
    course_id = m.group(1)
    try:
        url = f"https://nptel.ac.in/courses/{course_id}/__data.json"
        r = session().get(url, timeout=15)
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
            co = resolved.get("courseOutline") or {}
            units = co.get("units") or []
            if units:
                lessons = (units[0] or {}).get("lessons") or []
                if lessons:
                    yt_id = (lessons[0] or {}).get("youtube_id")
                    if yt_id and len(str(yt_id)) >= 8:
                        for size in ("maxresdefault", "hqdefault"):
                            thumb = f"https://i.ytimg.com/vi/{yt_id}/{size}.jpg"
                            try:
                                hr = session().head(thumb, timeout=6)
                                if hr.ok:
                                    return thumb
                            except Exception:
                                pass
    except Exception:
        pass
    return None


# ── Yale OYC: Drupal image ────────────────────────────────────────────────────
def yale_thumb(source_url: str) -> str | None:
    if not source_url or "oyc.yale.edu" not in source_url:
        return None
    try:
        r = session().get(source_url, timeout=12)
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


# ── YouTube playlist page scrape → first video thumbnail ─────────────────────
def youtube_playlist_thumb(playlist_id: str) -> str | None:
    """
    Scrape YouTube playlist page for first video id, then return ytimg URL.
    Only uses publicly available HTML (no API key).
    """
    if not playlist_id:
        return None
    try:
        url = f"https://www.youtube.com/playlist?list={playlist_id}"
        r = session().get(url, timeout=12)
        if not r.ok:
            return None
        html = r.text
        # Look for videoId in the initial data JSON
        m = re.search(r'"videoId"\s*:\s*"([A-Za-z0-9_\-]{11})"', html)
        if m:
            vid = m.group(1)
            for size in ("maxresdefault", "hqdefault"):
                thumb = f"https://i.ytimg.com/vi/{vid}/{size}.jpg"
                try:
                    hr = session().head(thumb, timeout=6)
                    if hr.ok:
                        return thumb
                except Exception:
                    pass
    except Exception:
        pass
    return None


def ytimg(video_id: str) -> str | None:
    """Get thumbnail for a known youtube video ID."""
    if not video_id:
        return None
    for size in ("maxresdefault", "hqdefault"):
        thumb = f"https://i.ytimg.com/vi/{video_id}/{size}.jpg"
        try:
            hr = session().head(thumb, timeout=6)
            if hr.ok:
                return thumb
        except Exception:
            pass
    return None


# ── Per-course resolver ───────────────────────────────────────────────────────
def resolve(row: tuple) -> tuple:
    """Returns (course_id, thumbnail_url). Always returns a non-None URL."""
    cid, title, skey, surl, yt_playlist_id, first_vid_id = row
    surl = (surl or "").strip()

    # 1. NPTEL
    if skey == "nptel":
        t = nptel_thumb(surl)
        if t:
            return (cid, t)

    # 2. Yale
    if skey == "yale" or "oyc.yale.edu" in surl:
        t = yale_thumb(surl)
        if t:
            return (cid, t)
        # fall through to og:image

    # 3. YouTube playlist source URL → scrape for first video
    if re.match(r'https?://(?:www\.)?youtube\.com/playlist', surl) and yt_playlist_id:
        t = youtube_playlist_thumb(yt_playlist_id)
        if t:
            return (cid, t)

    # 4. First video from videos table → ytimg
    if first_vid_id:
        t = ytimg(first_vid_id)
        if t:
            return (cid, t)

    # 5. og:image (works for MIT OCW, Stanford, Harvard, CMU, Oxford, etc.)
    if surl and not re.match(r'https?://(?:www\.)?youtube\.com', surl):
        t = fetch_og_image(surl, timeout=14)
        if t:
            return (cid, t)

    # 6. YouTube playlist scrape for any course with a playlist_id
    if yt_playlist_id:
        t = youtube_playlist_thumb(yt_playlist_id)
        if t:
            return (cid, t)

    # 7. Unsplash subject fallback (100% guarantee)
    return (cid, subject_fallback(title))


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    conn = psycopg2.connect(DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT c.id, c.title, c.source_key, c.source_url,
               c.youtube_playlist_id,
               (SELECT v.youtube_id FROM videos v
                WHERE v.course_id = c.id ORDER BY v."order" ASC LIMIT 1) AS first_vid
        FROM courses c
        WHERE c.thumbnail_url IS NULL
        ORDER BY c.source_key, c.title
    """)
    rows = cur.fetchall()
    total = len(rows)
    print(f"Courses needing thumbnails: {total}")
    if total == 0:
        print("Nothing to do.")
        cur.close()
        conn.close()
        return

    print(f"Starting fetch with 20 parallel workers...\n")

    results: dict = {}
    source_stats: dict = {}
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(resolve, row): row for row in rows}
        for i, future in enumerate(as_completed(futures)):
            row = futures[future]
            skey = row[2]
            try:
                cid, thumb = future.result()
            except Exception as exc:
                cid = row[0]
                thumb = subject_fallback(row[1])
                print(f"  ERROR [{skey}] {row[1][:50]}: {exc}")

            results[cid] = thumb
            is_real = "unsplash" not in thumb
            if skey not in source_stats:
                source_stats[skey] = {"real": 0, "fallback": 0}
            if is_real:
                source_stats[skey]["real"] += 1
            else:
                source_stats[skey]["fallback"] += 1

            if (i + 1) % 100 == 0:
                elapsed = time.time() - t0
                rate = (i + 1) / elapsed
                eta = (total - i - 1) / rate if rate > 0 else 0
                real_total = sum(v["real"] for v in source_stats.values())
                print(f"  [{i+1:4d}/{total}] real={real_total} "
                      f"rate={rate:.1f}/s eta={eta:.0f}s")

    # Commit in batches
    print(f"\nWriting {len(results)} thumbnails to database...")
    batch = []
    for cid, thumb in results.items():
        batch.append((thumb, cid))
        if len(batch) >= 200:
            cur.executemany("UPDATE courses SET thumbnail_url = %s WHERE id = %s", batch)
            conn.commit()
            batch.clear()
    if batch:
        cur.executemany("UPDATE courses SET thumbnail_url = %s WHERE id = %s", batch)
        conn.commit()

    elapsed = time.time() - t0
    real_total = sum(v["real"] for v in source_stats.values())
    fallback_total = sum(v["fallback"] for v in source_stats.values())

    print(f"\n{'='*60}")
    print(f"Done in {elapsed:.0f}s.")
    print(f"Real thumbnails:     {real_total}/{total}")
    print(f"Unsplash fallbacks:  {fallback_total}/{total}")
    print(f"\nPer-source breakdown:")
    print(f"  {'source':26s}  {'real':>5}  {'fallback':>8}")
    print(f"  {'-'*44}")
    for src, st in sorted(source_stats.items(), key=lambda x: -(x[1]["real"] + x[1]["fallback"])):
        print(f"  {src:26s}  {st['real']:5d}  {st['fallback']:8d}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
