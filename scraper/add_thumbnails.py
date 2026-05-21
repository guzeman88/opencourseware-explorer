#!/usr/bin/env python3
"""
add_thumbnails.py
Populates thumbnail_url for courses that currently have none.

Priority:
  1. YouTube playlist oEmbed   (no API key needed)
  2. First linked video's YouTube thumbnail
  3. Coursera public API       (courses with coursera.org URLs)
  4. og:image scrape           (small OCW sites: Tufts, UCI, JHSPH, Utah State, Open Univ)
  5. Subject-based curated Unsplash image
"""

import re
import time

import psycopg2
import requests
from db_utils import get_connection

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (compatible; OCWExplorer/1.0)"})

# ── Subject → stable Unsplash CDN image ───────────────────────────────────────
# Ordered longest-match first so "machine learning" beats "learning"
SUBJECT_MAP = [
    ("machine learning",      "https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=640&q=80"),
    ("artificial intelligence","https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=640&q=80"),
    ("deep learning",         "https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=640&q=80"),
    ("data science",          "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=640&q=80"),
    ("computer science",      "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=640&q=80"),
    ("software",              "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=640&q=80"),
    ("programming",           "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=640&q=80"),
    ("algorithm",             "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=640&q=80"),
    ("web development",       "https://images.unsplash.com/photo-1547658719-da2b51169166?w=640&q=80"),
    ("javascript",            "https://images.unsplash.com/photo-1547658719-da2b51169166?w=640&q=80"),
    ("python",                "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=640&q=80"),
    ("cybersecurity",         "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=640&q=80"),
    ("network",               "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=640&q=80"),
    ("robotics",              "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=640&q=80"),
    ("linear algebra",        "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=640&q=80"),
    ("calculus",              "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=640&q=80"),
    ("mathematics",           "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=640&q=80"),
    ("algebra",               "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=640&q=80"),
    ("statistics",            "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=640&q=80"),
    ("probability",           "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=640&q=80"),
    ("quantum",               "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=640&q=80"),
    ("thermodynamics",        "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=640&q=80"),
    ("astrophysics",          "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=640&q=80"),
    ("astronomy",             "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=640&q=80"),
    ("physics",               "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=640&q=80"),
    ("organic chemistry",     "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=640&q=80"),
    ("chemistry",             "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=640&q=80"),
    ("genetics",              "https://images.unsplash.com/photo-1530026405186-ed1f139313f0?w=640&q=80"),
    ("biology",               "https://images.unsplash.com/photo-1530026405186-ed1f139313f0?w=640&q=80"),
    ("ecology",               "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=640&q=80"),
    ("neuroscience",          "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=640&q=80"),
    ("epidemiology",          "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=640&q=80"),
    ("public health",         "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=640&q=80"),
    ("medicine",              "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=640&q=80"),
    ("medical",               "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=640&q=80"),
    ("nursing",               "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=640&q=80"),
    ("nutrition",             "https://images.unsplash.com/photo-1490818387583-1baba5e638af?w=640&q=80"),
    ("food",                  "https://images.unsplash.com/photo-1490818387583-1baba5e638af?w=640&q=80"),
    ("chemical engineering",  "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=640&q=80"),
    ("electrical engineering","https://images.unsplash.com/photo-1518770660439-4636190af475?w=640&q=80"),
    ("mechanical engineering","https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=640&q=80"),
    ("civil engineering",     "https://images.unsplash.com/photo-1486325212027-8081e485255e?w=640&q=80"),
    ("engineering",           "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=640&q=80"),
    ("materials",             "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=640&q=80"),
    ("architecture",          "https://images.unsplash.com/photo-1486325212027-8081e485255e?w=640&q=80"),
    ("urban",                 "https://images.unsplash.com/photo-1486325212027-8081e485255e?w=640&q=80"),
    ("entrepreneurship",      "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=640&q=80"),
    ("management",            "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=640&q=80"),
    ("marketing",             "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=640&q=80"),
    ("business",              "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=640&q=80"),
    ("finance",               "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=640&q=80"),
    ("accounting",            "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=640&q=80"),
    ("economics",             "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=640&q=80"),
    ("cognitive",             "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=640&q=80"),
    ("psychology",            "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=640&q=80"),
    ("philosophy",            "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=640&q=80"),
    ("ethics",                "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=640&q=80"),
    ("history",               "https://images.unsplash.com/photo-1461360370896-22624d12aa1?w=640&q=80"),
    ("archaeology",           "https://images.unsplash.com/photo-1461360370896-22624d12aa1?w=640&q=80"),
    ("literature",            "https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=640&q=80"),
    ("writing",               "https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=640&q=80"),
    ("linguistics",           "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=640&q=80"),
    ("language",              "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=640&q=80"),
    ("music",                 "https://images.unsplash.com/photo-1507838153414-b4b713384a76?w=640&q=80"),
    ("design",                "https://images.unsplash.com/photo-1559028006-448665bd7c7f?w=640&q=80"),
    ("art",                   "https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=640&q=80"),
    ("climate",               "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=640&q=80"),
    ("environment",           "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=640&q=80"),
    ("legal",                 "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=640&q=80"),
    ("law",                   "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=640&q=80"),
    ("political",             "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=640&q=80"),
    ("sociology",             "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=640&q=80"),
    ("social",                "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=640&q=80"),
    ("geography",             "https://images.unsplash.com/photo-1524661135-423995f22d0b?w=640&q=80"),
]
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=640&q=80"

# OCW sites where we'll try og:image scraping
OCW_DOMAINS = [
    "ocw.tufts.edu",
    "ocw.usu.edu",
    "ocw.uci.edu",
    "ocw.jhsph.edu",
    "open.edu/openlearn",
    "oyc.yale.edu",
    "podcasts.ox.ac.uk",
    "ocw.saylor.org",
    "learn.saylor.org",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def subject_image(title: str, desc: str = "") -> str:
    text = (title + " " + (desc or "")).lower()
    for kw, url in SUBJECT_MAP:
        if kw in text:
            return url
    return DEFAULT_IMAGE


def yt_playlist_thumb(playlist_id: str) -> str | None:
    """YouTube oEmbed — no API key, returns thumbnail for the playlist."""
    try:
        r = SESSION.get(
            "https://www.youtube.com/oembed",
            params={"url": f"https://www.youtube.com/playlist?list={playlist_id}",
                    "format": "json"},
            timeout=8,
        )
        if r.ok:
            return r.json().get("thumbnail_url")
    except Exception:
        pass
    return None


def yt_video_thumb(video_id: str) -> str:
    """YouTube thumbnail — always available at this URL pattern."""
    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"


def coursera_thumb(slug: str) -> str | None:
    try:
        r = SESSION.get(
            "https://api.coursera.org/api/courses.v1",
            params={"q": "slug", "slug": slug, "fields": "photoUrl"},
            timeout=10,
        )
        if r.ok:
            elems = r.json().get("elements", [])
            if elems:
                return elems[0].get("photoUrl")
    except Exception:
        pass
    return None


_OG_RE = re.compile(
    r'<meta[^>]+(?:property=["\']og:image["\'][^>]+content|content=["\']([^"\']+)["\'][^>]+property=["\']og:image)["\']([^"\']*)',
    re.IGNORECASE,
)
_OG_SIMPLE = re.compile(
    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](https?://[^"\']+)',
    re.IGNORECASE,
)


def og_image(page_url: str) -> str | None:
    try:
        r = SESSION.get(page_url, timeout=8, allow_redirects=True)
        if r.ok:
            m = _OG_SIMPLE.search(r.text)
            if m:
                img = m.group(1)
                if img.startswith("http"):
                    return img
    except Exception:
        pass
    return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.id, c.title, c.source_key, c.source_url, c.description,
               c.youtube_playlist_id,
               (SELECT v.youtube_id FROM videos v
                WHERE v.course_id = c.id ORDER BY v."order" ASC LIMIT 1) AS first_vid
        FROM courses c
        WHERE c.thumbnail_url IS NULL
        ORDER BY c.source_key, c.title
    """)
    rows = cur.fetchall()
    print(f"Courses without thumbnails: {len(rows)}")

    updated = 0
    coursera_reqs = 0

    for i, (cid, title, skey, surl, desc, yt_playlist, first_vid) in enumerate(rows):
        thumb = None

        # ── 1. YouTube playlist oEmbed ─────────────────────────────────────
        if yt_playlist:
            thumb = yt_playlist_thumb(yt_playlist)
            if thumb:
                time.sleep(0.1)

        # ── 2. First video's YouTube thumbnail ────────────────────────────
        if not thumb and first_vid:
            thumb = yt_video_thumb(first_vid)

        # ── 3. Coursera API ───────────────────────────────────────────────
        if not thumb and surl and "coursera.org/learn/" in surl:
            slug = surl.rstrip("/").split("/")[-1]
            thumb = coursera_thumb(slug)
            coursera_reqs += 1
            if thumb:
                time.sleep(0.25)   # gentle rate-limit

        # ── 4. og:image from OCW / open-learning sites ────────────────────
        if not thumb and surl and any(d in surl for d in OCW_DOMAINS):
            thumb = og_image(surl)

        # ── 5. Subject-based curated Unsplash image ───────────────────────
        if not thumb:
            thumb = subject_image(title, desc or "")

        # ── Persist ───────────────────────────────────────────────────────
        if thumb:
            cur.execute(
                "UPDATE courses SET thumbnail_url = %s WHERE id = %s",
                (thumb, cid),
            )
            conn.commit()
            updated += 1

        if (i + 1) % 50 == 0:
            print(f"  [{i+1:4d}/{len(rows)}]  updated={updated}  coursera_api_calls={coursera_reqs}")

    print(f"\nDone. Updated {updated}/{len(rows)} courses.")
    print(f"Coursera API calls made: {coursera_reqs}")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
