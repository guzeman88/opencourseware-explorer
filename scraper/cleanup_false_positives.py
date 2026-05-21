#!/usr/bin/env python
"""
Remove false-positive "courses" inserted by scrape_university_channels.py.

General university YouTube channels (Harvard, Yale, Duke, etc.) contain many
non-course playlists (class photos, research highlights, year-in-review, etc.)
that slipped through the old exclusion-only filter.

This script:
  1. Audits the current state
  2. Identifies published video courses that have NO positive course indicator
     in their title (uses the same regex as the fixed scraper)
  3. Sets is_published = FALSE for those courses (keeps them in the DB)
  4. Reports what was cleaned up, grouped by source_key

Usage:
  py -3.13 cleanup_false_positives.py
  DATABASE_URL=postgresql://... py -3.13 cleanup_false_positives.py
"""
from __future__ import annotations

import os
import re

import psycopg2
import psycopg2.extras

# ── DB connection ──────────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL:
    conn = psycopg2.connect(DATABASE_URL, sslmode="disable")
else:
    try:
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "127.0.0.1"),
            port=int(os.environ.get("POSTGRES_PORT", "5432")),
            dbname=os.environ.get("POSTGRES_DB", "opencourseware"),
            user="postgres",
            password=os.environ.get("POSTGRES_SUPERUSER_PASSWORD", "postgres"),
        )
    except Exception:
        conn = psycopg2.connect(
            host="127.0.0.1", port=5432,
            dbname="opencourseware", user="ocw", password="ocwpassword",
        )

cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# ── Patterns (must match scrape_university_channels.py) ───────────────────────

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
}

COURSE_INDICATOR_PATTERNS = re.compile(
    r"""(?xi)
    \b lecture s? \b |
    \b course s? \b |
    \b class (es)? \b |
    \b seminar s? \b |
    \b tutorial s? \b |
    \b workshop s? \b |
    \b module s? \b |
    \b lesson s? \b |
    introduction \s+ to \b |
    intro \s+ to \b |
    \b intro \s+ \d |
    \b foundations? \s+ of \b |
    \b principles? \s+ of \b |
    \b theory \s+ of \b |
    \b mathematics \b |
    \b calculus \b |
    \b algebra \b |
    \b geometry \b |
    \b statistics \b |
    \b probability \b |
    \b physics \b |
    \b chemistry \b |
    \b biology \b |
    \b economics \b |
    \b engineering \b |
    \b programming \b |
    \b algorithm s? \b |
    \b computation \b |
    \b neuroscience \b |
    \b machine \s+ learning \b |
    \b deep \s+ learning \b |
    \b artificial \s+ intelligence \b |
    \b blockchain \b |
    \b cryptography \b |
    \b zero \s+ knowledge \b |
    \b fundamentals? \b |
    \b boot \s* camp \b |
    \b data \s+ science \b |
    \b data \s+ structures? \b |
    \b operating \s+ systems? \b |
    \b computer \s+ vision \b |
    \b natural \s+ language \b |
    \b [A-Z]{2,5} [\s\-]? \d{2,4} [A-Z]? \b |
    \b \d{1,2} \. \d{2,4} [A-Z]* \b |
    \b \d{2,3} - \d{3} [A-Z]? \b
    """
)

# Source keys where EVERY playlist is trusted as a real course
ALWAYS_TRUST_SOURCE_KEYS = {
    "mit_ocw", "yale", "simons", "perimeter", "ias", "ictp",
    "stanford",   # @stanfordonline is pure courses
    "gatech",
}

# Source keys that came from general university channels — apply strict check
GENERAL_CHANNEL_SOURCE_KEYS = {
    "harvard", "duke", "cambridge", "columbia", "cornell",
    "caltech", "oxford", "jhu", "uchicago", "nyu", "umich",
    "ucla", "ucsd", "uw", "princeton", "imperial", "ucl",
    "utoronto", "mit_youtube", "cmu", "berkeley",
}


def is_false_positive(title: str, source_key: str) -> bool:
    if source_key in ALWAYS_TRUST_SOURCE_KEYS:
        return False
    if source_key not in GENERAL_CHANNEL_SOURCE_KEYS:
        return False  # unknown source, leave alone

    t = title.lower()
    # Hard exclusion
    for word in EXCLUDE_TITLE_WORDS:
        if word in t:
            return True  # definitely non-course
    # Require positive indicator
    if not COURSE_INDICATOR_PATTERNS.search(title):
        return True  # no indicator = likely non-course
    return False


# ── Audit before ──────────────────────────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM courses WHERE is_published=TRUE AND has_video_lectures=TRUE")
before_pub = cur.fetchone()["count"]
print(f"Published video courses before cleanup: {before_pub}")

# ── Fetch all published video courses from general university channels ─────────
cur.execute("""
    SELECT id, title, source_key, youtube_playlist_id
    FROM courses
    WHERE is_published = TRUE
      AND has_video_lectures = TRUE
      AND source_key = ANY(%s)
    ORDER BY source_key, title
""", (list(GENERAL_CHANNEL_SOURCE_KEYS),))
candidates = cur.fetchall()
print(f"Checking {len(candidates)} published video courses from general channels...")

false_positives = [r for r in candidates if is_false_positive(r["title"], r["source_key"])]

# Group by source_key for reporting
by_source: dict[str, list] = {}
for r in false_positives:
    by_source.setdefault(r["source_key"], []).append(r["title"])

print(f"\nFalse positives found: {len(false_positives)}")
for sk, titles in sorted(by_source.items()):
    print(f"\n  [{sk}] {len(titles)} to unpublish:")
    for t in sorted(titles)[:20]:
        safe = t.encode("ascii", "replace").decode("ascii")
        print(f"    - {safe[:80]}")
    if len(titles) > 20:
        print(f"    ... and {len(titles)-20} more")

# ── Unpublish false positives ─────────────────────────────────────────────────
if false_positives:
    fp_ids = [r["id"] for r in false_positives]
    psycopg2.extras.execute_batch(
        cur,
        "UPDATE courses SET is_published = FALSE WHERE id = %s",
        [(fid,) for fid in fp_ids],
        page_size=200,
    )
    conn.commit()
    print(f"\nUnpublished {len(false_positives)} false-positive courses.")
else:
    print("\nNo false positives found.")

# ── Audit after ───────────────────────────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM courses WHERE is_published=TRUE AND has_video_lectures=TRUE")
after_pub = cur.fetchone()["count"]
print(f"\nPublished video courses after cleanup : {after_pub}")
print(f"Removed from published               : {before_pub - after_pub}")

# ── Breakdown by source ───────────────────────────────────────────────────────
print("\n--- Published video courses by source ---")
cur.execute("""
    SELECT source_key, COUNT(*) AS n
    FROM courses
    WHERE is_published=TRUE AND has_video_lectures=TRUE
    GROUP BY source_key
    ORDER BY n DESC
""")
for r in cur.fetchall():
    print(f"  {r['source_key']:<20} {r['n']}")

cur.close()
conn.close()
print("\nDone.")
