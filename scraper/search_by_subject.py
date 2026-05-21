#!/usr/bin/env python
"""
Subject-based YouTube playlist search to discover new course channels.

Instead of scraping known channels, this script searches YouTube for specific
academic course titles (e.g. "complex analysis lecture", "abstract algebra course"),
collects qualifying playlists from channels we haven't seen before, inserts them
into the DB, and writes discovered_channels.json for follow-up full-channel scrapes.

Quota cost: ~100 units per search query. With ~70 queries = ~7,000 units.

Usage:
  YOUTUBE_API_KEY=... DATABASE_URL=... python search_by_subject.py
  YOUTUBE_API_KEY=... DATABASE_URL=... python search_by_subject.py --math-only
  YOUTUBE_API_KEY=... DATABASE_URL=... python search_by_subject.py --physics-only
  YOUTUBE_API_KEY=... DATABASE_URL=... python search_by_subject.py --dry-run
"""
from __future__ import annotations

import json
import os
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import psycopg2
import psycopg2.extras
from slugify import slugify

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("ERROR: google-api-python-client not installed.")
    sys.exit(1)

API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
if not API_KEY:
    print("ERROR: YOUTUBE_API_KEY not set.")
    sys.exit(1)

DRY_RUN      = "--dry-run"      in sys.argv
MATH_ONLY    = "--math-only"    in sys.argv
PHYSICS_ONLY = "--physics-only" in sys.argv

youtube = build("youtube", "v3", developerKey=API_KEY)

# ── Search queries ────────────────────────────────────────────────────────────
# Each tuple: (search_string, min_videos_to_qualify)

MATH_QUERIES: list[tuple[str, int]] = [
    # Calculus
    ("calculus 1 lecture full course",           6),
    ("calculus 2 integral lecture course",       6),
    ("multivariable calculus lecture course",    6),
    ("vector calculus lecture course",           6),
    # Linear Algebra
    ("linear algebra lecture course",            6),
    # Differential Equations
    ("ordinary differential equations lecture",  6),
    ("partial differential equations lecture",   6),
    # Analysis
    ("real analysis lecture course",             6),
    ("complex analysis lecture course",          6),
    ("measure theory lecture course",            4),
    ("functional analysis lecture course",       4),
    ("harmonic analysis lecture course",         4),
    # Algebra
    ("abstract algebra lecture course",          6),
    ("modern algebra lecture course",            6),
    ("group theory lecture course",              6),
    ("ring theory lecture course",               4),
    ("galois theory lecture course",             4),
    ("commutative algebra lecture course",       4),
    ("representation theory lecture course",     4),
    ("homological algebra lecture course",       4),
    ("category theory lecture course",           4),
    # Topology and Geometry
    ("point set topology lecture course",        6),
    ("algebraic topology lecture course",        4),
    ("differential topology lecture course",     4),
    ("differential geometry lecture course",     4),
    ("riemannian geometry lecture course",       4),
    ("algebraic geometry lecture course",        4),
    ("symplectic geometry lecture course",       4),
    # Number Theory
    ("number theory lecture course",             6),
    ("analytic number theory lecture course",    4),
    ("algebraic number theory lecture course",   4),
    # Probability and Statistics
    ("probability theory lecture course",        6),
    ("mathematical statistics lecture course",   6),
    ("stochastic processes lecture course",      4),
    ("stochastic calculus lecture course",       4),
    # Other Math
    ("discrete mathematics lecture course",      6),
    ("combinatorics lecture course",             4),
    ("graph theory lecture course",              4),
    ("mathematical logic lecture course",        4),
    ("set theory lecture course",                4),
    ("numerical analysis lecture course",        6),
    ("convex optimization lecture course",       4),
    ("lie groups lie algebras lecture course",   4),
    ("operator algebras lecture course",         4),
]

PHYSICS_QUERIES: list[tuple[str, int]] = [
    # Undergrad Physics
    ("classical mechanics lecture course",       6),
    ("lagrangian mechanics lecture course",      4),
    ("electromagnetism lecture course",          6),
    ("electrodynamics lecture course",           4),
    ("quantum mechanics lecture course",         6),
    ("thermodynamics lecture course",            6),
    ("statistical mechanics lecture course",     6),
    ("special relativity lecture course",        6),
    ("optics lecture course",                    6),
    ("modern physics lecture course",            6),
    ("mathematical methods physics lecture",     6),
    ("waves vibrations physics lecture",         4),
    # Graduate Physics
    ("quantum field theory lecture course",      4),
    ("general relativity lecture course",        4),
    ("condensed matter physics lecture course",  4),
    ("solid state physics lecture course",       4),
    ("particle physics lecture course",          4),
    ("astrophysics lecture course",              4),
    ("cosmology lecture course",                 4),
    ("nuclear physics lecture course",           4),
    ("plasma physics lecture course",            4),
    ("quantum optics lecture course",            4),
    ("quantum information lecture course",       4),
    ("string theory lecture course",             4),
    ("advanced quantum mechanics lecture",       4),
    ("many body physics lecture course",         4),
    ("statistical field theory lecture",         4),
]

# ── Filter logic ──────────────────────────────────────────────────────────────
EXCLUDE_TITLE_WORDS = {
    "commencement", "graduation", "ceremony", "convocation", "orientation",
    "alumni", "reunion", "homecoming", "welcome", "tour", "campus life",
    "sports", "athletics", "football", "basketball", "baseball", "soccer",
    "press release", "interview", "announcement",
    "fundrais", "campaign", "gala", "award", "prize", "celebration",
    "concert", "performance", "exhibition", "showcase", "demo day",
    "promo", "promotional", "trailer", "teaser",
    "year in review", "class of 20", "class of 19", "class photos",
    "open day", "open house", "research feature", "faculty spotlight",
    "student spotlight", "research highlights", "community",
    "three minute thesis", "3 minute thesis",
    "climate commitment", "sustainability", "giving", "donation",
    "inauguration", "state of the university",
    "podcast", "podcasts", "christmas lecture", "annual lecture",
    "q&a", "panel discussion", "keynote", "ted talk",
    "luminaries", "myths", "busted", "short", "#short",
    "information session", "program information",
    "conversations with", "talk with", "chat with",
    "family focus", "family weekend", "family day",
    "life lessons", "leadership lessons",
    "symposium", "town hall", "conference proceedings",
    "news", "updates", "highlights", "recap",
    "anniversary", "milestone", "celebration of",
    "job talk", "faculty search", "candidate talk",
}

COURSE_INDICATOR_PATTERNS = re.compile(
    r"""(?xi)
    \b lecture s? \b | \b course s? \b | \b class (es)? \b |
    \b seminar s? \b | \b tutorial s? \b | \b module s? \b |
    \b unit \s+ \d | \b week \s+ \d | \b lesson s? \b |
    \b calculus \b | \b algebra \b | \b analysis \b | \b topology \b |
    \b geometry \b | \b mechanics \b | \b physics \b | \b mathematics \b |
    \b quantum \b | \b relativity \b | \b thermodynamics \b |
    \b electro (magnetism|dynamics|statics) \b |
    \b differential \s+ (equations?|geometry|topology) \b |
    \b linear \s+ algebra \b | \b real \s+ analysis \b |
    \b complex \s+ analysis \b | \b number \s+ theory \b |
    \b group \s+ theory \b | \b ring \s+ theory \b | \b field \s+ theory \b |
    \b abstract \s+ algebra \b | \b modern \s+ algebra \b |
    \b measure \s+ theory \b | \b functional \s+ analysis \b |
    \b harmonic \s+ analysis \b | \b stochastic \b |
    \b combinatorics \b | \b graph \s+ theory \b | \b probability \b |
    \b statistics \b | \b optimization \b | \b numerical \b |
    \b galois \b | \b homological \b | \b representation \b |
    \b algebraic \s+ (topology|geometry|number|group) \b |
    \b riemannian \b | \b symplectic \b | \b operator \s+ algebra \b |
    \b condensed \s+ matter \b | \b solid \s+ state \b |
    \b astrophysics \b | \b cosmology \b | \b particle \s+ physics \b |
    \b quantum \s+ field \s+ theory \b | \b general \s+ relativity \b |
    \b lie \s+ (group|algebra) \b | \b category \s+ theory \b |
    """,
)


def is_course_playlist(title: str, count: int, min_videos: int) -> bool:
    t = title.lower()
    if count < min_videos:
        return False
    for word in EXCLUDE_TITLE_WORDS:
        if word in t:
            return False
    return bool(COURSE_INDICATOR_PATTERNS.search(title))


# ── Subject / level inference ─────────────────────────────────────────────────
SUBJECT_MAP = [
    (["calculus", "integral", "derivative", "multivariable", "vector calculus"], ["Mathematics"]),
    (["linear algebra"], ["Mathematics"]),
    (["differential equation"], ["Mathematics"]),
    (["real analysis", "measure theory", "functional analysis", "harmonic analysis"], ["Mathematics"]),
    (["complex analysis"], ["Mathematics"]),
    (["abstract algebra", "modern algebra", "group theory", "ring theory", "galois",
      "commutative algebra", "homological", "representation theory", "category theory",
      "lie group", "lie algebra", "operator algebra"], ["Mathematics"]),
    (["topology", "algebraic topology", "differential topology", "manifold"], ["Mathematics"]),
    (["geometry", "riemannian", "symplectic", "algebraic geometry",
      "differential geometry"], ["Mathematics"]),
    (["number theory", "analytic number theory", "algebraic number theory"], ["Mathematics"]),
    (["probability", "stochastic", "statistics"], ["Mathematics"]),
    (["combinatorics", "graph theory", "discrete math"], ["Mathematics"]),
    (["optimization", "convex", "numerical"], ["Mathematics"]),
    (["quantum field theory", "quantum mechanics", "quantum optics",
      "quantum information"], ["Quantum Physics", "Physics"]),
    (["general relativity", "special relativity"], ["Physics"]),
    (["classical mechanics", "lagrangian", "hamiltonian"], ["Physics"]),
    (["electromagnetism", "electrodynamics", "electrostatics"], ["Physics"]),
    (["thermodynamics", "statistical mechanics"], ["Physics"]),
    (["condensed matter", "solid state"], ["Physics"]),
    (["particle physics", "nuclear physics"], ["Physics"]),
    (["astrophysics", "cosmology", "string theory", "plasma physics"], ["Physics", "Astronomy"]),
    (["optics"], ["Physics"]),
]


def infer_subjects(title: str) -> list[str]:
    t = title.lower()
    for keywords, subjects in SUBJECT_MAP:
        if any(k in t for k in keywords):
            return subjects[:2]
    return ["Mathematics"]


def infer_level(title: str) -> str:
    t = title.lower()
    if any(w in t for w in ["advanced", "graduate", "phd", "doctoral",
                             "grad ", "second course", "part ii", "part 2"]):
        return "graduate"
    return "undergraduate"


# ── YouTube API helpers ───────────────────────────────────────────────────────
quota_used = 0


def search_playlists(query: str, max_results: int = 50) -> list[dict]:
    global quota_used
    results = []
    try:
        resp = youtube.search().list(
            q=query,
            type="playlist",
            part="snippet",
            maxResults=max_results,
            relevanceLanguage="en",
            safeSearch="none",
        ).execute()
        quota_used += 100
        for item in resp.get("items", []):
            snip = item["snippet"]
            results.append({
                "playlist_id":    item["id"]["playlistId"],
                "playlist_title": snip.get("title", "").strip(),
                "channel_id":     snip.get("channelId", ""),
                "channel_title":  snip.get("channelTitle", "").strip(),
                "thumbnail":      (snip.get("thumbnails", {}).get("high", {}).get("url")
                                   or snip.get("thumbnails", {}).get("default", {}).get("url")),
            })
    except HttpError as e:
        print(f"  [API ERROR] search '{query}': {e}", flush=True)
    return results


def get_playlist_video_count(playlist_id: str) -> int:
    global quota_used
    count = 0
    page_token = None
    while True:
        try:
            resp = youtube.playlistItems().list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=page_token,
            ).execute()
            quota_used += 1
        except Exception:
            break
        count += len(resp.get("items", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return count


# ── DB connection ─────────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set.")
    sys.exit(1)

conn = psycopg2.connect(DATABASE_URL, sslmode="disable")
cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("SELECT youtube_playlist_id FROM courses WHERE youtube_playlist_id IS NOT NULL")
existing_pids: set[str] = {r["youtube_playlist_id"] for r in cur.fetchall()}
print(f"Existing playlists in DB: {len(existing_pids)}", flush=True)

cur.execute("SELECT slug FROM courses")
seen_slugs: set[str] = {r["slug"] for r in cur.fetchall()}

subject_cache: dict[str, str] = {}


def upsert_university_for_channel(channel_id: str, channel_title: str) -> tuple[str, str, str]:
    source_key = slugify(channel_title)[:40]
    slug       = source_key
    cur.execute("SELECT id FROM universities WHERE slug = %s", (slug,))
    row = cur.fetchone()
    if row:
        return str(row["id"]), slug, source_key
    uid = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO universities (id, name, slug, source_key, website, country)
           VALUES (%s, %s, %s, %s, %s, %s)
           ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name RETURNING id""",
        (uid, channel_title, slug, source_key,
         f"https://www.youtube.com/channel/{channel_id}", "US"),
    )
    row = cur.fetchone()
    conn.commit()
    return str(row["id"]), slug, source_key


def upsert_subject(name: str) -> str:
    if name in subject_cache:
        return subject_cache[name]
    sl = slugify(name)
    cur.execute("SELECT id FROM subjects WHERE slug = %s", (sl,))
    row = cur.fetchone()
    if row:
        subject_cache[name] = str(row["id"])
        return subject_cache[name]
    sid = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO subjects (id, name, slug) VALUES (%s,%s,%s) "
        "ON CONFLICT (slug) DO NOTHING RETURNING id",
        (sid, name, sl),
    )
    row = cur.fetchone()
    if not row:
        cur.execute("SELECT id FROM subjects WHERE slug = %s", (sl,))
        row = cur.fetchone()
    subject_cache[name] = str(row["id"])
    conn.commit()
    return subject_cache[name]


def insert_course(playlist_id: str, title: str, count: int, thumbnail: str | None,
                  uni_id: str, source_key: str) -> bool:
    subjects = infer_subjects(title)
    level    = infer_level(title)
    base     = slugify(f"{title} {source_key}")
    slug     = base
    n = 2
    while slug in seen_slugs:
        slug = f"{base}-{n}"
        n += 1
    seen_slugs.add(slug)
    cid = str(uuid.uuid4())
    try:
        cur.execute(
            """INSERT INTO courses (
                   id, university_id, title, slug, source_key,
                   level, youtube_playlist_id, total_videos, thumbnail_url,
                   has_video_lectures, is_published
               ) VALUES (%s,%s,%s,%s,%s, %s,%s,%s,%s, TRUE,TRUE)
               ON CONFLICT (slug) DO UPDATE SET
                   youtube_playlist_id = EXCLUDED.youtube_playlist_id,
                   total_videos        = GREATEST(EXCLUDED.total_videos, courses.total_videos),
                   thumbnail_url       = COALESCE(EXCLUDED.thumbnail_url, courses.thumbnail_url),
                   has_video_lectures  = TRUE,
                   is_published        = TRUE""",
            (cid, uni_id, title, slug, source_key,
             level, playlist_id, count, thumbnail),
        )
        for subj_name in subjects:
            subj_id = upsert_subject(subj_name)
            cur.execute(
                """INSERT INTO course_subjects (id, course_id, subject_id)
                   VALUES (%s, (SELECT id FROM courses WHERE slug=%s LIMIT 1), %s)
                   ON CONFLICT DO NOTHING""",
                (str(uuid.uuid4()), slug, subj_id),
            )
        existing_pids.add(playlist_id)
        return True
    except Exception as exc:
        conn.rollback()
        print(f"  [DB ERROR] {title[:60]}: {exc}", flush=True)
        return False


# ── Main ──────────────────────────────────────────────────────────────────────
queries: list[tuple[str, int]] = []
if not PHYSICS_ONLY:
    queries += MATH_QUERIES
if not MATH_ONLY:
    queries += PHYSICS_QUERIES

print(f"Running {len(queries)} subject searches "
      f"(estimated ~{len(queries) * 100} quota units)\n", flush=True)

# channel_id -> info dict
discovered_channels: dict[str, dict] = {}

total_inserted = 0
total_skipped  = 0

for query, min_v in queries:
    print(f"\n-- {query} --", flush=True)
    results = search_playlists(query, max_results=50)
    print(f"   {len(results)} results", flush=True)

    new_this_query = 0
    for r in results:
        pid    = r["playlist_id"]
        title  = r["playlist_title"]
        cid    = r["channel_id"]
        ctitle = r["channel_title"]

        if cid not in discovered_channels:
            discovered_channels[cid] = {
                "channel_id":      cid,
                "channel_title":   ctitle,
                "queries_matched": [],
                "playlists_added": 0,
                "already_in_db":   False,
            }
        if query not in discovered_channels[cid]["queries_matched"]:
            discovered_channels[cid]["queries_matched"].append(query)

        if pid in existing_pids:
            discovered_channels[cid]["already_in_db"] = True
            continue

        count = get_playlist_video_count(pid)
        if not is_course_playlist(title, count, min_v):
            total_skipped += 1
            continue

        safe = title.encode("ascii", "replace").decode("ascii")
        print(f"   + [{ctitle[:28]}] {safe[:52]} ({count}v)", flush=True)

        if not DRY_RUN:
            uni_id, _, source_key = upsert_university_for_channel(cid, ctitle)
            if insert_course(pid, title, count, r["thumbnail"], uni_id, source_key):
                discovered_channels[cid]["playlists_added"] += 1
                new_this_query += 1
                total_inserted += 1
                if total_inserted % 30 == 0:
                    conn.commit()

    print(f"   -> {new_this_query} new (quota so far: ~{quota_used})", flush=True)

conn.commit()

# ── Save discovered channels JSON ─────────────────────────────────────────────
new_channels   = {cid: info for cid, info in discovered_channels.items()
                  if not info["already_in_db"] or info["playlists_added"] > 0}
known_channels = {cid: info for cid, info in discovered_channels.items()
                  if info["already_in_db"] and info["playlists_added"] == 0}

output = {
    "generated_at":    datetime.utcnow().isoformat(),
    "queries_run":     len(queries),
    "total_inserted":  total_inserted,
    "quota_used":      quota_used,
    "new_channels": sorted(
        new_channels.values(),
        key=lambda x: len(x["queries_matched"]), reverse=True,
    ),
    "already_scraped_channels": sorted(
        known_channels.values(),
        key=lambda x: len(x["queries_matched"]), reverse=True,
    ),
}

out_path = Path(__file__).parent / "discovered_channels.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

# ── Final report ──────────────────────────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM courses WHERE is_published=TRUE AND has_video_lectures=TRUE")
pub_total = cur.fetchone()["count"]

print(f"\n{'=' * 60}")
print(f"COMPLETE")
print(f"  Queries run              : {len(queries)}")
print(f"  New courses inserted     : {total_inserted}")
print(f"  Playlists skipped        : {total_skipped}")
print(f"  Quota used               : ~{quota_used} units")
print(f"  Total published video    : {pub_total}")
print(f"  New channels discovered  : {len(new_channels)}")
print(f"  Channels already in DB   : {len(known_channels)}")
print(f"  Channel log              : {out_path}")
print(f"{'=' * 60}")

cur.close()
conn.close()
