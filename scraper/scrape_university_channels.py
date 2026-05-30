#!/usr/bin/env python
"""
Comprehensive university YouTube channel scraper.

Enumerates every playlist from all major English-speaking university
YouTube channels, filters for course-length content, fetches real
video counts, and upserts everything into the database.

After this runs, re-run verify_and_fix_video_courses.py to publish.

Usage:
  py -3.13 scrape_university_channels.py
  DATABASE_URL=postgresql://... py -3.13 scrape_university_channels.py

Progress is checkpointed to channel_scrape_progress.json so the script
can be interrupted and resumed safely.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import psycopg2
import psycopg2.extras
import yt_dlp
from slugify import slugify

# ── Config ─────────────────────────────────────────────────────────────────────
WORKERS = int(os.environ.get("WORKERS", "6"))
DELAY = 0.5
CHECKPOINT_FILE = Path(__file__).parent / "channel_scrape_progress.json"

# Minimum videos for a playlist to count as a "course"
DEFAULT_MIN_VIDEOS = 6

# Title keywords that immediately disqualify a playlist as a course
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
    "inauguration", "state of the university", "convocation",
}

# Positive course indicators — a playlist MUST match at least one of these
# (except for channels in ALWAYS_TRUST_SOURCE_KEYS where every playlist is a course)
COURSE_INDICATOR_PATTERNS = re.compile(
    r"""(?xi)
    \b lecture s? \b |
    \b course s? \b |
    \b class (es)? \b |
    \b seminar s? \b |
    \b tutorial s? \b |
    \b workshop s? \b |   # MIT/Stanford workshops are real courses
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
    # course-code patterns: CS101, CS 101, 6.001, 18.01SC, COS226, 15-721, etc.
    \b [A-Z]{2,5} [\s\-]? \d{2,4} [A-Z]? \b |
    \b \d{1,2} \. \d{2,4} [A-Z]* \b |
    \b \d{2,3} - \d{3} [A-Z]? \b
    """
)

# Source keys where we trust every playlist to be a course (dedicated OCW channels)
ALWAYS_TRUST_SOURCE_KEYS = {
    "mit_ocw", "yale",  # @YaleCourses is purely courses
    "simons", "perimeter", "ias", "ictp",  # research institutes: all are courses
}

# ── University channel definitions ────────────────────────────────────────────
# Each entry can have multiple YouTube channel URLs for the same university.
UNIVERSITIES = [
    {
        "name": "MIT OpenCourseWare",
        "slug": "mit",
        "source_key": "mit_ocw",
        "website": "https://ocw.mit.edu",
        "country": "US",
        "min_videos": 4,
        "channels": [
            "https://www.youtube.com/@mitocw/playlists",
        ],
    },
    {
        "name": "Stanford University",
        "slug": "stanford",
        "source_key": "stanford",
        "website": "https://online.stanford.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@stanfordonline/playlists",
            "https://www.youtube.com/@stanford/playlists",
        ],
    },
    {
        "name": "University of California, Berkeley",
        "slug": "berkeley",
        "source_key": "berkeley",
        "website": "https://berkeley.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@UCBerkeley/playlists",
        ],
    },
    {
        "name": "Yale University",
        "slug": "yale",
        "source_key": "yale",
        "website": "https://oyc.yale.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@Yale/playlists",
            "https://www.youtube.com/@YaleCourses/playlists",
        ],
    },
    {
        "name": "Harvard University",
        "slug": "harvard",
        "source_key": "harvard",
        "website": "https://online-learning.harvard.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@Harvard/playlists",
            "https://www.youtube.com/@HarvardExtension/playlists",
        ],
    },
    {
        "name": "Georgia Institute of Technology",
        "slug": "georgia-tech",
        "source_key": "gatech",
        "website": "https://gatech.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@georgiatech/playlists",
        ],
    },
    {
        "name": "Princeton University",
        "slug": "princeton",
        "source_key": "princeton",
        "website": "https://princeton.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@Princeton/playlists",
        ],
    },
    {
        "name": "Carnegie Mellon University",
        "slug": "carnegie-mellon",
        "source_key": "cmu",
        "website": "https://cmu.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@CarnegieMellonU/playlists",
        ],
    },
    {
        "name": "Columbia University",
        "slug": "columbia",
        "source_key": "columbia",
        "website": "https://columbia.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@Columbia/playlists",
        ],
    },
    {
        "name": "Cornell University",
        "slug": "cornell",
        "source_key": "cornell",
        "website": "https://cornell.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@Cornell/playlists",
            "https://www.youtube.com/@CornellUniversity/playlists",
        ],
    },
    {
        "name": "University of Michigan",
        "slug": "umich",
        "source_key": "umich",
        "website": "https://umich.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@UMich/playlists",
        ],
    },
    {
        "name": "University of California, Los Angeles",
        "slug": "ucla",
        "source_key": "ucla",
        "website": "https://ucla.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@UCLA/playlists",
        ],
    },
    {
        "name": "UC San Diego",
        "slug": "uc-san-diego",
        "source_key": "ucsd",
        "website": "https://ucsd.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@UCSDOfficial/playlists",
            "https://www.youtube.com/@UCSD/playlists",
        ],
    },
    {
        "name": "California Institute of Technology",
        "slug": "caltech",
        "source_key": "caltech",
        "website": "https://caltech.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@caltech/playlists",
        ],
    },
    {
        "name": "University of Oxford",
        "slug": "oxford",
        "source_key": "oxford",
        "website": "https://ox.ac.uk",
        "country": "GB",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@OxfordUniversity/playlists",
        ],
    },
    {
        "name": "University of Cambridge",
        "slug": "cambridge",
        "source_key": "cambridge",
        "website": "https://cam.ac.uk",
        "country": "GB",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@Cambridge/playlists",
            "https://www.youtube.com/@CambridgeUniversity/playlists",
        ],
    },
    {
        "name": "Imperial College London",
        "slug": "imperial-college",
        "source_key": "imperial",
        "website": "https://imperial.ac.uk",
        "country": "GB",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@imperiallondon/playlists",
        ],
    },
    {
        "name": "University College London",
        "slug": "ucl",
        "source_key": "ucl",
        "website": "https://ucl.ac.uk",
        "country": "GB",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@UCLOfficial/playlists",
        ],
    },
    {
        "name": "University of Toronto",
        "slug": "toronto",
        "source_key": "utoronto",
        "website": "https://utoronto.ca",
        "country": "CA",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@UofToronto/playlists",
        ],
    },
    {
        "name": "Simons Institute for the Theory of Computing",
        "slug": "simons-institute",
        "source_key": "simons",
        "website": "https://simons.berkeley.edu",
        "country": "US",
        "min_videos": 4,
        "channels": [
            "https://www.youtube.com/@SimonsInstituteTOC/playlists",
        ],
    },
    {
        "name": "Perimeter Institute for Theoretical Physics",
        "slug": "perimeter-institute",
        "source_key": "perimeter",
        "website": "https://perimeterinstitute.ca",
        "country": "CA",
        "min_videos": 4,
        "channels": [
            "https://www.youtube.com/@PerimeterInstitute/playlists",
        ],
    },
    {
        "name": "Institute for Advanced Study",
        "slug": "ias",
        "source_key": "ias",
        "website": "https://ias.edu",
        "country": "US",
        "min_videos": 4,
        "channels": [
            "https://www.youtube.com/@instituteforadvancedstudy/playlists",
        ],
    },
    {
        "name": "ICTP — International Centre for Theoretical Physics",
        "slug": "ictp",
        "source_key": "ictp",
        "website": "https://ictp.it",
        "country": "IT",
        "min_videos": 4,
        "channels": [
            "https://www.youtube.com/@ICTPmath/playlists",
            "https://www.youtube.com/@ICTP_TV/playlists",
        ],
    },
    {
        "name": "MIT — Massachusetts Institute of Technology",
        "slug": "mit",            # same slug as MIT OCW, same university
        "source_key": "mit_youtube",
        "website": "https://mit.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@MIT/playlists",
        ],
    },
    {
        "name": "University of Washington",
        "slug": "uw",
        "source_key": "uw",
        "website": "https://uw.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@UW/playlists",
        ],
    },
    {
        "name": "Johns Hopkins University",
        "slug": "johns-hopkins",
        "source_key": "jhu",
        "website": "https://jhu.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@JohnsHopkins/playlists",
        ],
    },
    {
        "name": "University of Chicago",
        "slug": "uchicago",
        "source_key": "uchicago",
        "website": "https://uchicago.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@UChicago/playlists",
        ],
    },
    {
        "name": "New York University",
        "slug": "nyu",
        "source_key": "nyu",
        "website": "https://nyu.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@nyuniversity/playlists",
        ],
    },
    {
        "name": "Duke University",
        "slug": "duke",
        "source_key": "duke",
        "website": "https://duke.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@DukeUniversity/playlists",
        ],
    },
    # ── Additional US universities ────────────────────────────────────────────
    {
        "name": "University of Illinois Urbana-Champaign",
        "slug": "uiuc",
        "source_key": "uiuc",
        "website": "https://illinois.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@UIUC/playlists",
            "https://www.youtube.com/@uicseecs/playlists",
        ],
    },
    {
        "name": "University of Texas at Austin",
        "slug": "ut-austin",
        "source_key": "utaustin",
        "website": "https://utexas.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@UTAustinX/playlists",
        ],
    },
    {
        "name": "Purdue University",
        "slug": "purdue",
        "source_key": "purdue",
        "website": "https://purdue.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@PurdueUniversity/playlists",
        ],
    },
    {
        "name": "University of Pennsylvania",
        "slug": "upenn",
        "source_key": "upenn",
        "website": "https://upenn.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@Penn/playlists",
        ],
    },
    {
        "name": "Brown University",
        "slug": "brown",
        "source_key": "brown",
        "website": "https://brown.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@BrownUniversity/playlists",
        ],
    },
    {
        "name": "Dartmouth College",
        "slug": "dartmouth",
        "source_key": "dartmouth",
        "website": "https://dartmouth.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@dartmouth/playlists",
        ],
    },
    {
        "name": "Northwestern University",
        "slug": "northwestern",
        "source_key": "northwestern",
        "website": "https://northwestern.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@northwesternu/playlists",
        ],
    },
    {
        "name": "Vanderbilt University",
        "slug": "vanderbilt",
        "source_key": "vanderbilt",
        "website": "https://vanderbilt.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@vanderbiltu/playlists",
        ],
    },
    {
        "name": "Rice University",
        "slug": "rice",
        "source_key": "rice",
        "website": "https://rice.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@RiceUniversity/playlists",
        ],
    },
    {
        "name": "UC Davis",
        "slug": "uc-davis",
        "source_key": "ucdavis",
        "website": "https://ucdavis.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@ucdavis/playlists",
        ],
    },
    {
        "name": "UC Santa Barbara",
        "slug": "uc-santa-barbara",
        "source_key": "ucsb",
        "website": "https://ucsb.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@ucsantabarbara/playlists",
        ],
    },
    {
        "name": "University of Wisconsin-Madison",
        "slug": "uw-madison",
        "source_key": "uwmadison",
        "website": "https://wisc.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@uwmadison/playlists",
        ],
    },
    # ── UK & international universities ──────────────────────────────────────
    {
        "name": "University of Edinburgh",
        "slug": "edinburgh",
        "source_key": "edinburgh",
        "website": "https://ed.ac.uk",
        "country": "GB",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@EdinburghUniversity/playlists",
        ],
    },
    {
        "name": "University of Manchester",
        "slug": "manchester",
        "source_key": "manchester",
        "website": "https://manchester.ac.uk",
        "country": "GB",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@uomofficial/playlists",
        ],
    },
    {
        "name": "ETH Zurich",
        "slug": "eth-zurich",
        "source_key": "eth",
        "website": "https://ethz.ch",
        "country": "CH",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@ETHZurich/playlists",
        ],
    },
    {
        "name": "EPFL",
        "slug": "epfl",
        "source_key": "epfl",
        "website": "https://epfl.ch",
        "country": "CH",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@epfl/playlists",
        ],
    },
    {
        "name": "Indian Institute of Science (IISc)",
        "slug": "iisc",
        "source_key": "iisc",
        "website": "https://iisc.ac.in",
        "country": "IN",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@IIScBangalore/playlists",
        ],
    },
    {
        "name": "Australian National University",
        "slug": "anu",
        "source_key": "anu",
        "website": "https://anu.edu.au",
        "country": "AU",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@ANUchannel/playlists",
        ],
    },
    # ── Dedicated OCW / lecture channels (always trusted) ─────────────────────
    {
        "name": "MIT OpenCourseWare",   # already in DB; won't re-add dupes
        "slug": "mit",
        "source_key": "mit_ocw",
        "website": "https://ocw.mit.edu",
        "country": "US",
        "min_videos": 4,
        "channels": [
            "https://www.youtube.com/@mitocw/playlists",
        ],
    },
    {
        "name": "Yale Courses",
        "slug": "yale",
        "source_key": "yale",
        "website": "https://oyc.yale.edu",
        "country": "US",
        "min_videos": 4,
        "channels": [
            "https://www.youtube.com/@YaleCourses/playlists",
        ],
    },
    {
        "name": "Brilliant.org",
        "slug": "brilliant",
        "source_key": "brilliant",
        "website": "https://brilliant.org",
        "country": "US",
        "min_videos": 4,
        "channels": [
            "https://www.youtube.com/@BrilliantOrg/playlists",
        ],
    },
    # ── Professor / course-specific channels ─────────────────────────────────
    # These are individual professor or course channels released as OCW
    {
        "name": "Khan Academy",
        "slug": "khan-academy",
        "source_key": "khanacademy",
        "website": "https://khanacademy.org",
        "country": "US",
        "min_videos": 8,
        "channels": [
            "https://www.youtube.com/@khanacademy/playlists",
        ],
    },
    {
        "name": "MIT 18.06 Linear Algebra (Gilbert Strang)",
        "slug": "mit-linear-algebra",
        "source_key": "mit_ocw",
        "website": "https://ocw.mit.edu/18-06",
        "country": "US",
        "min_videos": 4,
        "channels": [
            "https://www.youtube.com/@mitocw/playlists",  # already covered; placeholder
        ],
    },
    {
        "name": "Stanford Engineering Everywhere",
        "slug": "stanford-see",
        "source_key": "stanford",
        "website": "https://see.stanford.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@stanfordonline/playlists",
        ],
    },
    {
        "name": "Berkeley EECS — CS 61A / 61B / 61C",
        "slug": "berkeley-eecs",
        "source_key": "berkeley",
        "website": "https://cs.berkeley.edu",
        "country": "US",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@berkeleyeecs/playlists",
        ],
    },
    {
        "name": "3Blue1Brown",
        "slug": "3blue1brown",
        "source_key": "3b1b",
        "website": "https://3blue1brown.com",
        "country": "US",
        "min_videos": 4,
        "channels": [
            "https://www.youtube.com/@3blue1brown/playlists",
        ],
    },
    {
        "name": "freeCodeCamp.org",
        "slug": "freecodecamp",
        "source_key": "freecodecamp",
        "website": "https://freecodecamp.org",
        "country": "US",
        "min_videos": 1,  # FCC often has single long videos per course
        "channels": [
            "https://www.youtube.com/@freecodecamp/playlists",
        ],
    },
    {
        "name": "Sentdex (Python / ML tutorials)",
        "slug": "sentdex",
        "source_key": "sentdex",
        "website": "https://pythonprogramming.net",
        "country": "US",
        "min_videos": 4,
        "channels": [
            "https://www.youtube.com/@sentdex/playlists",
        ],
    },
    {
        "name": "Andrej Karpathy",
        "slug": "andrej-karpathy",
        "source_key": "karpathy",
        "website": "https://karpathy.ai",
        "country": "US",
        "min_videos": 2,
        "channels": [
            "https://www.youtube.com/@AndrejKarpathy/playlists",
        ],
    },
    {
        "name": "Two Minute Papers",
        "slug": "two-minute-papers",
        "source_key": "twominutepapers",
        "website": "https://www.youtube.com/@TwoMinutePapers",
        "country": "HU",
        "min_videos": 6,
        "channels": [
            "https://www.youtube.com/@TwoMinutePapers/playlists",
        ],
    },
    {
        "name": "Yannic Kilcher (ML Research)",
        "slug": "yannic-kilcher",
        "source_key": "yannickilcher",
        "website": "https://www.youtube.com/@YannicKilcher",
        "country": "CH",
        "min_videos": 4,
        "channels": [
            "https://www.youtube.com/@YannicKilcher/playlists",
        ],
    },
]

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
            host=os.environ.get("POSTGRES_HOST", "127.0.0.1"), port=int(os.environ.get("POSTGRES_PORT", "5432")),
            dbname=os.environ.get("POSTGRES_DB", "opencourseware"), user=os.environ.get("POSTGRES_USER", "ocw"),
            password=os.environ.get("POSTGRES_PASSWORD", ""),
        )

cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# ── Load existing playlist IDs to skip duplicates ────────────────────────────
cur.execute("SELECT youtube_playlist_id FROM courses WHERE youtube_playlist_id IS NOT NULL")
existing_playlist_ids: set[str] = {r["youtube_playlist_id"] for r in cur.fetchall()}
print(f"Existing playlists in DB: {len(existing_playlist_ids)}")

# ── Load checkpoint ───────────────────────────────────────────────────────────
checkpoint: dict = {}
if CHECKPOINT_FILE.exists():
    checkpoint = json.loads(CHECKPOINT_FILE.read_text())
    print(f"Resuming from checkpoint: {len(checkpoint)} channels already done")


def save_checkpoint() -> None:
    CHECKPOINT_FILE.write_text(json.dumps(checkpoint, indent=2))


# ── Subject inference ─────────────────────────────────────────────────────────
SUBJECT_MAP: list[tuple[list[str], list[str]]] = [
    (["machine learning", "deep learning", "neural network", "ai ", "artificial intelligence", "reinforcement learning", "nlp", "natural language", "computer vision", "large language model", "llm"], ["Machine Learning", "Artificial Intelligence"]),
    (["algorithm", "data structure", "competitive programming"], ["Algorithms", "Computer Science"]),
    (["operating system", "systems programming", "computer architecture", "computer system"], ["Computer Systems", "Computer Science"]),
    (["database", "sql", "nosql", "data engineering"], ["Databases", "Computer Science"]),
    (["web development", "javascript", "react", "node", "html", "css", "frontend", "backend", "full stack"], ["Web Development", "Programming"]),
    (["python", "programming", "software engineering", "software development", "object-oriented", "functional programming"], ["Programming", "Computer Science"]),
    (["computer science", "cs50", "cs 1", "cs 2", "intro to cs", "computation"], ["Computer Science"]),
    (["cybersecurity", "security", "cryptography", "network security"], ["Cybersecurity", "Computer Science"]),
    (["computer network", "networking", "distributed system", "cloud computing"], ["Networking", "Computer Science"]),
    (["linear algebra", "calculus", "differential equation", "real analysis", "complex analysis", "number theory", "topology", "abstract algebra", "probability", "statistics", "discrete math", "combinatorics", "graph theory", "optimization"], ["Mathematics"]),
    (["quantum", "quantum mechanics", "quantum computing", "quantum information"], ["Quantum Physics", "Physics"]),
    (["physics", "mechanics", "electromagnetism", "thermodynamics", "optics", "relativity", "classical mechanics", "fluid"], ["Physics"]),
    (["chemistry", "organic chemistry", "biochemistry", "chemical engineering"], ["Chemistry"]),
    (["biology", "genetics", "cell biology", "molecular biology", "neuroscience", "ecology", "evolution"], ["Biology"]),
    (["economics", "microeconomics", "macroeconomics", "econometrics", "finance", "accounting", "financial"], ["Economics", "Finance"]),
    (["electrical engineering", "signal processing", "circuits", "electronics", "semiconductors", "control system"], ["Electrical Engineering"]),
    (["mechanical engineering", "robotics", "materials science", "manufacturing"], ["Mechanical Engineering"]),
    (["civil engineering", "structural engineering", "environmental engineering"], ["Civil Engineering"]),
    (["data science", "data analysis", "data visualization", "big data"], ["Data Science"]),
    (["philosophy", "logic", "ethics"], ["Philosophy"]),
    (["history", "ancient", "medieval", "modern history"], ["History"]),
    (["psychology", "cognitive", "behavioral"], ["Psychology"]),
    (["political science", "government", "international relations", "public policy"], ["Political Science"]),
    (["astronomy", "astrophysics", "cosmology"], ["Astronomy", "Physics"]),
    (["medicine", "medical", "anatomy", "physiology", "clinical", "pharmacology"], ["Medicine", "Biology"]),
    (["law", "legal", "constitutional", "contract"], ["Law"]),
    (["music", "theory of music", "harmony", "composition"], ["Music"]),
    (["literature", "writing", "english literature", "creative writing"], ["Literature"]),
    (["architecture", "urban planning", "design"], ["Architecture"]),
    (["sociology", "anthropology", "social"], ["Social Sciences"]),
    (["blockchain", "cryptocurrency", "web3", "smart contract"], ["Blockchain", "Computer Science"]),
    (["entrepreneurship", "startup", "business", "management", "strategy", "marketing", "leadership"], ["Business", "Entrepreneurship"]),
    (["linguistics", "language"], ["Linguistics"]),
]


def infer_subjects(title: str) -> list[str]:
    t = title.lower()
    for keywords, subjects in SUBJECT_MAP:
        if any(k in t for k in keywords):
            return subjects[:2]
    return ["Education"]


def infer_level(title: str) -> str:
    t = title.lower()
    if any(w in t for w in ["advanced", "graduate", "phd", "doctoral", "research seminar", "grad "]):
        return "graduate"
    if any(w in t for w in ["introduction", "intro ", "intro to", "beginner", "101", "basics", "fundamentals", "getting started", "101", "for beginners"]):
        return "undergraduate"
    return "undergraduate"


def is_course_playlist(title: str, video_count: int, min_videos: int, source_key: str = "") -> bool:
    """Return True if this playlist looks like a full course."""
    if video_count < min_videos:
        return False
    t = title.lower()
    # Hard exclusions first
    for word in EXCLUDE_TITLE_WORDS:
        if word in t:
            return False
    # Trusted dedicated-OCW channels: skip positive check
    if source_key in ALWAYS_TRUST_SOURCE_KEYS:
        return True
    # General university channels: require at least one positive indicator
    return bool(COURSE_INDICATOR_PATTERNS.search(title))


# ── yt-dlp helpers ────────────────────────────────────────────────────────────

def fetch_channel_playlists(channel_url: str) -> list[dict]:
    """Enumerate all playlists from a YouTube channel playlists tab."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "ignoreerrors": True,
        "socket_timeout": 30,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
        if not info:
            return []
        entries = info.get("entries") or []
        playlists = []
        for e in entries:
            if not e:
                continue
            pid = e.get("id") or e.get("playlist_id")
            title = (e.get("title") or "").strip()
            count = e.get("playlist_count") or e.get("n_entries") or 0
            if pid and title:
                playlists.append({"id": pid, "title": title, "count": count})
        return playlists
    except Exception as exc:
        print(f"  [channel ERROR] {channel_url}: {exc}", flush=True)
        return []


def fetch_playlist_info(playlist_id: str) -> dict | None:
    """Get video count + first-video thumbnail for a playlist."""
    time.sleep(DELAY)
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "ignoreerrors": True,
        "socket_timeout": 30,
        "retries": 2,
    }
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if not info:
            return None
        entries = [e for e in (info.get("entries") or []) if e]
        if not entries:
            return None
        first_vid = entries[0].get("id")
        return {
            "video_count": len(entries),
            "thumbnail_url": f"https://i.ytimg.com/vi/{first_vid}/hqdefault.jpg" if first_vid else None,
            "title": info.get("title") or "",
        }
    except Exception:
        return None


def upsert_university(name: str, slug: str, source_key: str, website: str, country: str) -> str:
    cur.execute("SELECT id FROM universities WHERE slug = %s", (slug,))
    row = cur.fetchone()
    if row:
        return str(row["id"])
    uid = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO universities (id, name, slug, source_key, website, country)
           VALUES (%s, %s, %s, %s, %s, %s)
           ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name RETURNING id""",
        (uid, name, slug, source_key, website, country),
    )
    row = cur.fetchone()
    conn.commit()
    return str(row["id"])


def upsert_subject(name: str, cache: dict) -> str:
    if name in cache:
        return cache[name]
    sl = slugify(name)
    cur.execute("SELECT id FROM subjects WHERE slug = %s", (sl,))
    row = cur.fetchone()
    if row:
        cache[name] = str(row["id"])
        return cache[name]
    sid = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO subjects (id, name, slug) VALUES (%s,%s,%s) ON CONFLICT (slug) DO NOTHING RETURNING id",
        (sid, name, sl),
    )
    row = cur.fetchone()
    if not row:
        cur.execute("SELECT id FROM subjects WHERE slug = %s", (sl,))
        row = cur.fetchone()
    cache[name] = str(row["id"])
    conn.commit()
    return cache[name]


# ══════════════════════════════════════════════════════════════════════════════
# Main loop
# ══════════════════════════════════════════════════════════════════════════════
total_inserted = 0
total_skipped = 0
subject_cache: dict = {}

for uni in UNIVERSITIES:
    uni_key = uni["source_key"]
    print(f"\n{'='*60}")
    print(f"  {uni['name']} [{uni_key}]")
    print(f"{'='*60}")

    uni_id = upsert_university(
        uni["name"], uni["slug"], uni_key, uni["website"], uni["country"]
    )

    all_playlists: dict[str, dict] = {}  # playlist_id -> {title, count}

    for channel_url in uni["channels"]:
        if channel_url in checkpoint:
            print(f"  [skip] {channel_url} (already processed)")
            continue
        print(f"  Fetching playlists from {channel_url} ...", flush=True)
        playlists = fetch_channel_playlists(channel_url)
        print(f"    Found {len(playlists)} playlists", flush=True)
        for p in playlists:
            if p["id"] not in all_playlists:
                all_playlists[p["id"]] = p
        checkpoint[channel_url] = len(playlists)
        save_checkpoint()
        time.sleep(1)

    # Filter out already-in-DB and fetch video counts for unknowns
    new_playlists = [
        p for p in all_playlists.values()
        if p["id"] not in existing_playlist_ids
    ]
    print(f"  New playlists (not in DB): {len(new_playlists)}", flush=True)

    if not new_playlists:
        continue

    # Fetch video counts in parallel
    min_v = uni.get("min_videos", DEFAULT_MIN_VIDEOS)
    verified: list[dict] = []

    def _verify(p: dict) -> dict:
        if p["count"] >= min_v:
            # Already have enough info from channel listing
            return {**p, "needs_fetch": False, "video_count": p["count"], "thumbnail_url": None}
        info = fetch_playlist_info(p["id"])
        if info:
            return {**p, "needs_fetch": True, "video_count": info["video_count"], "thumbnail_url": info["thumbnail_url"]}
        return {**p, "needs_fetch": True, "video_count": 0, "thumbnail_url": None}

    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(_verify, p): p for p in new_playlists}
        for fut in as_completed(futures):
            res = fut.result()
            done += 1
            safe_title = res["title"].encode("ascii", "replace").decode("ascii")
            if is_course_playlist(res["title"], res["video_count"], min_v, uni_key):
                verified.append(res)
                print(f"  [{done}/{len(new_playlists)}] OK  {safe_title[:55]:<55} ({res['video_count']} videos)", flush=True)
            else:
                print(f"  [{done}/{len(new_playlists)}] SKIP {safe_title[:55]:<55} (count={res['video_count']})", flush=True)

    print(f"  Upserting {len(verified)} new courses ...", flush=True)
    inserted_this_uni = 0

    # For playlists that passed the count filter but we don't have a thumbnail yet,
    # we need one more fetch to get the first-video thumbnail.
    def _get_thumb(p: dict) -> dict:
        if p.get("thumbnail_url"):
            return p
        info = fetch_playlist_info(p["id"])
        if info:
            p["thumbnail_url"] = info["thumbnail_url"]
            p["video_count"] = info["video_count"]
        return p

    # Only re-fetch thumbs for those that didn't need a count fetch
    need_thumb = [p for p in verified if not p.get("thumbnail_url") and not p.get("needs_fetch")]
    if need_thumb:
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futures = {pool.submit(_get_thumb, p): p for p in need_thumb}
            for fut in as_completed(futures):
                fut.result()

    seen_slugs_set: set[str] = set()
    cur.execute("SELECT slug FROM courses")
    for r in cur.fetchall():
        seen_slugs_set.add(r["slug"])

    for p in verified:
        title = p["title"]
        subjects = infer_subjects(title)
        level = infer_level(title)

        base_slug = slugify(f"{title} {uni_key}")
        slug = base_slug
        counter = 2
        while slug in seen_slugs_set:
            slug = f"{base_slug}-{counter}"
            counter += 1
        seen_slugs_set.add(slug)

        cid = str(uuid.uuid4())
        try:
            cur.execute(
                """INSERT INTO courses (
                       id, university_id, title, slug, source_key,
                       level, youtube_playlist_id,
                       total_videos, has_video_lectures, is_published
                   ) VALUES (%s,%s,%s,%s,%s, %s,%s, %s,TRUE,TRUE)
                   ON CONFLICT (slug) DO UPDATE SET
                       youtube_playlist_id = EXCLUDED.youtube_playlist_id,
                       total_videos        = GREATEST(EXCLUDED.total_videos, courses.total_videos),
                       has_video_lectures  = TRUE,
                       is_published        = TRUE""",
                (cid, uni_id, title, slug, uni_key,
                 level, p["id"],
                 p.get("video_count", 0)),
            )
            if p.get("thumbnail_url"):
                cur.execute(
                    "UPDATE courses SET thumbnail_url = %s WHERE slug = %s AND thumbnail_url IS NULL",
                    (p["thumbnail_url"], slug),
                )

            # Link subjects
            for subj_name in subjects:
                subj_id = upsert_subject(subj_name, subject_cache)
                cur.execute(
                    """INSERT INTO course_subjects (id, course_id, subject_id)
                       VALUES (%s,
                               (SELECT id FROM courses WHERE slug=%s LIMIT 1),
                               %s)
                       ON CONFLICT DO NOTHING""",
                    (str(uuid.uuid4()), slug, subj_id),
                )

            existing_playlist_ids.add(p["id"])
            inserted_this_uni += 1

            if inserted_this_uni % 20 == 0:
                conn.commit()
                print(f"    ... committed {inserted_this_uni}", flush=True)

        except Exception as exc:
            conn.rollback()
            safe = title.encode("ascii", "replace").decode("ascii")
            print(f"  [DB ERROR] {safe}: {exc}", flush=True)

    conn.commit()
    total_inserted += inserted_this_uni
    total_skipped += len(new_playlists) - inserted_this_uni
    print(f"  Done: inserted {inserted_this_uni} new courses", flush=True)

# ── Final report ──────────────────────────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM courses WHERE has_video_lectures=TRUE AND is_published=TRUE")
pub_video = cur.fetchone()["count"]

print(f"\n{'='*60}")
print(f"COMPLETE")
print(f"  New courses inserted : {total_inserted}")
print(f"  Playlists skipped    : {total_skipped}")
print(f"  Total published video: {pub_video}")
print(f"{'='*60}")

cur.close()
conn.close()
