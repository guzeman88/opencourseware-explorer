#!/usr/bin/env python
"""
Full-channel playlist enumeration using the YouTube Data API v3.

yt-dlp caps at 30 playlists per channel (YouTube's first-page limit).
The YouTube Data API has no such cap — it paginates through ALL playlists.

For each university channel, this script:
  1. Resolves the channel handle to a channelId via the API
  2. Pages through ALL playlists (no cap)
  3. Applies the same course filter as scrape_university_channels.py
  4. Verifies playlist video counts via the API (playlistItems.list)
  5. Upserts new courses into the database

Requirements:
  pip install google-api-python-client

Setup:
  1. Go to https://console.cloud.google.com
  2. Create a project -> Enable "YouTube Data API v3"
  3. Credentials -> Create API Key
  4. Set: YOUTUBE_API_KEY=AIza...

Usage:
  YOUTUBE_API_KEY=AIza... py -3.13 scrape_all_playlists_api.py
  YOUTUBE_API_KEY=AIza... DATABASE_URL=postgresql://... py -3.13 scrape_all_playlists_api.py

  # Re-scrape only specific universities:
  YOUTUBE_API_KEY=AIza... ONLY=mit_ocw,stanford py -3.13 scrape_all_playlists_api.py

Quota notes:
  - channels.list:       1 unit/call
  - playlists.list:      1 unit/call  (50 playlists/page)
  - playlistItems.list:  1 unit/call  (50 items/page, we only need count)
  Default daily quota:   10,000 units
  MIT OCW ~900 playlists = ~18 pages + ~900 item-count calls = ~920 units
  All channels combined: roughly 3,000-5,000 units (safe for one day)
"""
from __future__ import annotations

import os
import re
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import psycopg2
import psycopg2.extras
from slugify import slugify

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("ERROR: google-api-python-client not installed.")
    print("  pip install google-api-python-client")
    sys.exit(1)

API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
if not API_KEY:
    print("ERROR: YOUTUBE_API_KEY environment variable not set.")
    print("  Get a free key at https://console.cloud.google.com")
    print("  Enable YouTube Data API v3, then create an API Key under Credentials.")
    sys.exit(1)

ONLY_SOURCES = set(os.environ.get("ONLY", "").split(",")) - {""}
WORKERS = int(os.environ.get("WORKERS", "8"))

youtube = build("youtube", "v3", developerKey=API_KEY)

# ── Same filter logic as scrape_university_channels.py ─────────────────────────
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
    # additional non-course content
    "podcast", "podcasts", "christmas lecture", "annual lecture",
    "q&a", "panel discussion", "keynote", "ted talk", "commencement",
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
    \b \d{2,3} - \d{3} [A-Z]? \b |
    \b linear \s+ algebra \b |
    \b differential \s+ equations? \b |
    \b real \s+ analysis \b |
    \b complex \s+ analysis \b |
    \b abstract \s+ algebra \b |
    \b topology \b |
    \b number \s+ theory \b |
    \b combinatorics \b |
    \b discrete \s+ math \b |
    \b graph \s+ theory \b |
    \b thermodynamics \b |
    \b electromagnetism \b |
    \b electrodynamics \b |
    \b fluid \s+ mechanics \b |
    \b solid \s+ state \b |
    \b relativity \b |
    \b astrophysics \b |
    \b astronomy \b |
    \b genetics \b |
    \b neuroscience \b |
    \b organic \s+ chemistry \b |
    \b biochemistry \b |
    \b cell \s+ biology \b |
    \b molecular \s+ biology \b |
    \b microeconomics \b |
    \b macroeconomics \b |
    \b econometrics \b |
    \b game \s+ theory \b |
    \b signal \s+ processing \b |
    \b control \s+ systems? \b |
    \b circuits \b |
    \b electronics \b |
    \b robotics \b |
    \b compiler s? \b |
    \b distributed \s+ systems? \b |
    \b parallel \s+ computing \b |
    \b reinforcement \s+ learning \b |
    \b time \s+ series \b |
    \b bayesian \b |
    \b stochastic \b |
    \b optimization \b |
    \b convex \b |
    \b full \s+ course \b |
    \b complete \s+ course \b |
    \b bootcamp \b |
    \b masterclass \b |
    \b philosophy \b |
    \b history \s+ of \b |
    \b psychology \b |
    \b cognitive \s+ science \b |
    \b sociology \b |
    \b anthropology \b |
    \b linguistics \b |
    \b political \s+ science \b |
    \b international \s+ relations \b |
    \b public \s+ policy \b |
    \b law \s+ (of|and|for) \b |
    \b constitutional \b |
    \b jurisprudence \b |
    \b medicine \b |
    \b anatomy \b |
    \b physiology \b |
    \b immunology \b |
    \b pharmacology \b |
    \b epidemiology \b |
    \b neurology \b |
    \b psychiatry \b |
    \b genomics \b |
    \b proteomics \b |
    \b astronomy \b |
    \b astrophysics \b |
    \b cosmology \b |
    \b geophysics \b |
    \b earth \s+ science \b |
    \b climate \s+ science \b |
    \b environmental \s+ science \b |
    \b ecology \b |
    \b evolution \b |
    \b bioinformatics \b |
    \b music \s+ theory \b |
    \b art \s+ history \b |
    \b literature \b |
    \b writing \s+ (program|workshop|seminar) \b |
    \b architecture \b |
    \b urban \s+ planning \b |
    \b accounting \b |
    \b microeconomics \b |
    \b macroeconomics \b |
    \b econometrics \b |
    \b game \s+ theory \b |
    \b supply \s+ chain \b |
    \b operations \s+ research \b |
    \b financial \s+ (mathematics|engineering|modeling|economics|markets) \b |
    \b quantum \s+ (information|chemistry|optics) \b |
    \b nuclear \b |
    \b plasma \b |
    \b semiconductor s? \b |
    \b photonics \b |
    \b nanotechnology \b |
    \b aerospace \b |
    \b aerodynamics \b |
    \b thermodynamics \b
    """
)

ALWAYS_TRUST_SOURCE_KEYS = {
    # University OCW channels (curated playlists only)
    "mit_ocw", "yale", "simons", "perimeter", "ias", "ictp",
    "gatech", "tudelft", "cs50", "fields", "newton", "slmath", "ihp", "hausdorff",
    # Educator channels — all playlists are structured courses
    "prof_leonard", "drtefor", "neso_academy", "eigensteve", "statquest",
    "brian_douglas", "michelvanbiezen", "octutor", "prof_dave",
    "ben_eater", "fastai", "reducible", "jacob_sorber", "patrickjmt",
    # Major research universities — playlists are mostly academic content
    # (exclusion filter still applies, but no positive indicator required)
    "oxford", "cambridge", "harvard", "princeton", "columbia",
    "caltech", "jhu", "uchicago", "duke", "cornell",
    "ubc", "mcgill", "waterloo", "utoronto",
    "melbourne", "unsw", "anu",
    "nus", "hkust", "hku",
    "kcl", "lse", "bristol", "warwick", "manchester", "glasgow", "edinburgh",
    "tum", "eth", "epfl", "kth",
    # Note: stanford has non-course playlists on @stanfordonline so we apply the filter
    # Newly discovered educator channels
    "borcherds", "schuller", "bright_side_math", "walter_lewin",
    "prof_macauley", "bill_kinney", "james_cook_math", "ictp_diploma",
    "ictp_math", "impa", "zewail_ocw", "aims_south_africa",
    "math_at_hse", "oxford_mathematics", "uppsala_algebra",
}


def is_course_playlist(title: str, video_count: int, min_videos: int, source_key: str) -> bool:
    if video_count < min_videos:
        return False
    t = title.lower()
    for word in EXCLUDE_TITLE_WORDS:
        if word in t:
            return False
    if source_key in ALWAYS_TRUST_SOURCE_KEYS:
        return True
    return bool(COURSE_INDICATOR_PATTERNS.search(title))


# ── University definitions ─────────────────────────────────────────────────────
# handles: YouTube channel handle (without @), OR channel ID (UC...)
def _u(name, slug, source_key, website, country, min_videos, handles, channel_ids=None):
    """Shorthand constructor for university entries."""
    return {
        "name": name, "slug": slug, "source_key": source_key,
        "website": website, "country": country, "min_videos": min_videos,
        "handles": handles,
        "channel_ids": channel_ids or [],  # direct IDs skip channels.list
    }


UNIVERSITIES = [
    # channel_ids are used directly (no channels.list call) for handles that fail API lookup
    _u("MIT OpenCourseWare",        "mit",              "mit_ocw",      "https://ocw.mit.edu",               "US", 4, ["mitocw"],                    ["UCEBb1b_L6zDS3xTUrIALZOw"]),
    _u("Stanford University",       "stanford",         "stanford",     "https://online.stanford.edu",        "US", 6, ["stanfordonline", "stanford"], ["UCBa5G_ESCn8Yd4vw5U-gIcg"]),  # stanfordonline known; @stanford fallback
    _u("UC Berkeley",               "berkeley",         "berkeley",     "https://berkeley.edu",               "US", 6, ["UCBerkeley", "berkeleyeecs"]),
    _u("Yale University",           "yale",             "yale",         "https://oyc.yale.edu",               "US", 4, ["Yale", "YaleCourses"]),
    _u("Harvard University",        "harvard",          "harvard",      "https://online-learning.harvard.edu","US", 6, ["Harvard", "HarvardExtension"]),
    _u("Georgia Tech",              "georgia-tech",     "gatech",       "https://gatech.edu",                 "US", 6, ["georgiatech"]),
    _u("Princeton University",      "princeton",        "princeton",    "https://princeton.edu",              "US", 6, ["Princeton"]),
    _u("Carnegie Mellon Univ.",     "carnegie-mellon",  "cmu",          "https://cmu.edu",                    "US", 6, ["CarnegieMellonU"]),
    _u("Columbia University",       "columbia",         "columbia",     "https://columbia.edu",               "US", 6, ["Columbia"]),
    _u("Cornell University",        "cornell",          "cornell",      "https://cornell.edu",                "US", 6, ["Cornell", "CornellUniversity"]),
    _u("Univ. of Michigan",         "umich",            "umich",        "https://umich.edu",                  "US", 6, ["UofMichigan", "UMich", "universityofmichigan"]),
    _u("UCLA",                      "ucla",             "ucla",         "https://ucla.edu",                   "US", 6, ["UCLA"]),
    _u("UC San Diego",              "uc-san-diego",     "ucsd",         "https://ucsd.edu",                   "US", 6, ["UCSDOfficial", "UCSD"]),
    _u("Caltech",                   "caltech",          "caltech",      "https://caltech.edu",                "US", 6, ["caltech"]),
    _u("Univ. of Oxford",           "oxford",           "oxford",       "https://ox.ac.uk",                   "GB", 6, ["OxfordUniversity"]),
    _u("Univ. of Cambridge",        "cambridge",        "cambridge",    "https://cam.ac.uk",                  "GB", 6, ["Cambridge", "CambridgeUniversity"]),
    _u("Imperial College London",   "imperial-college", "imperial",     "https://imperial.ac.uk",             "GB", 6, ["ImperialCollegeLondon", "imperiallondon"]),
    _u("University College London", "ucl",              "ucl",          "https://ucl.ac.uk",                  "GB", 6, ["UCLOfficial", "UCL"]),
    _u("Univ. of Toronto",          "toronto",          "utoronto",     "https://utoronto.ca",                "CA", 6, ["UniversityofToronto", "UofToronto"]),
    _u("Simons Institute",          "simons-institute", "simons",       "https://simons.berkeley.edu",        "US", 4, ["SimonsInstitute", "SimonsInstituteTOC"], ["UC64CNjm_kBUqNJwF7DtY5yg"]),
    _u("Perimeter Institute",       "perimeter-institute","perimeter",  "https://perimeterinstitute.ca",      "CA", 4, ["perimeterinstitute", "PerimeterInstitute"]),
    _u("Institute for Advanced Study","ias",            "ias",          "https://ias.edu",                    "US", 4, ["iaspas", "instituteforadvancedstudy"]),
    _u("ICTP",                      "ictp",             "ictp",         "https://ictp.it",                    "IT", 4, ["ICTPmath", "ICTP_TV", "ICTPonline"]),
    _u("MIT (main channel)",        "mit",              "mit_youtube",  "https://mit.edu",                    "US", 6, ["MIT"],                       ["UCcgTxFR-w1pN1A1fvXK53Dw"]),
    _u("Univ. of Washington",       "uw",               "uw",           "https://uw.edu",                     "US", 6, ["UW"]),
    _u("Johns Hopkins Univ.",       "johns-hopkins",    "jhu",          "https://jhu.edu",                    "US", 6, ["JohnsHopkins"]),
    _u("Univ. of Chicago",          "uchicago",         "uchicago",     "https://uchicago.edu",               "US", 6, ["UChicago"]),
    _u("New York University",       "nyu",              "nyu",          "https://nyu.edu",                    "US", 6, ["NewYorkUniversity", "nyuniversity", "NYU"]),
    _u("Duke University",           "duke",             "duke",         "https://duke.edu",                   "US", 6, ["DukeUniversity"]),
    _u("UIUC",                      "uiuc",             "uiuc",         "https://illinois.edu",               "US", 6, ["UIUC"]),
    _u("Purdue University",         "purdue",           "purdue",       "https://purdue.edu",                 "US", 6, ["PurdueUniversity"]),
    _u("Univ. of Pennsylvania",     "upenn",            "upenn",        "https://upenn.edu",                  "US", 6, ["Penn"]),
    _u("Northwestern University",   "northwestern",     "northwestern", "https://northwestern.edu",           "US", 6, ["northwesternu"]),
    _u("ETH Zurich",                "eth-zurich",       "eth",          "https://ethz.ch",                    "CH", 6, ["ETHZurich"]),
    _u("EPFL",                      "epfl",             "epfl",         "https://epfl.ch",                    "CH", 6, ["epfl"]),
    _u("Khan Academy",              "khan-academy",     "khanacademy",  "https://khanacademy.org",            "US", 8, ["khanacademy"],               ["UC4a-Gbdw7vOaccHmFo40b9g"]),
    _u("freeCodeCamp",              "freecodecamp",     "freecodecamp", "https://freecodecamp.org",           "US", 1, ["freecodecamp"],              ["UC8butISFwT-Wl7EV0hUK0BQ"]),
    _u("3Blue1Brown",               "3blue1brown",      "3b1b",         "https://3blue1brown.com",            "US", 4, ["3blue1brown"],               ["UCYO_jab_esuFRV4b17AJtAg"]),
    _u("Andrej Karpathy",           "andrej-karpathy",  "karpathy",     "https://karpathy.ai",                "US", 2, ["AndrejKarpathy"]),
    _u("Crash Course",              "crash-course",     "crashcourse",  "https://thecrashcourse.com",         "US", 8, ["crashcourse"],               ["UCX6b17PVsYBQ0ip5gyeme-Q"]),
    _u("Computerphile",             "computerphile",    "computerphile","https://www.youtube.com/@Computerphile","GB",4,["Computerphile"]),
    _u("Numberphile",               "numberphile",      "numberphile",  "https://www.numberphile.com",        "GB", 4, ["numberphile"]),
    _u("MIT CSAIL",                 "mit-csail",        "mit_ocw",      "https://csail.mit.edu",              "US", 4, ["MITCSAIL"]),
    _u("UC Davis",                  "uc-davis",         "ucdavis",      "https://ucdavis.edu",                "US", 6, ["ucdavis"]),
    _u("Univ. of Edinburgh",        "edinburgh",        "edinburgh",    "https://ed.ac.uk",                   "GB", 6, ["EdinburghUniversity"]),
    _u("Rice University",           "rice",             "rice",         "https://rice.edu",                   "US", 6, ["RiceUniversity"]),
    _u("Brown University",          "brown",            "brown",        "https://brown.edu",                  "US", 6, ["BrownUniversity"]),

    # ── More US Universities ──────────────────────────────────────────────────
    _u("UT Austin",                 "ut-austin",        "ut_austin",    "https://utexas.edu",                 "US", 6, ["UTAustin", "utaustinx"]),
    _u("UC Santa Barbara",          "ucsb",             "ucsb",         "https://ucsb.edu",                   "US", 6, ["UCSantaBarbara"]),
    _u("UC Irvine",                 "uc-irvine",        "uci",          "https://uci.edu",                    "US", 6, ["UCIrvine", "UCIOpenCourseWare"]),
    _u("UC Santa Cruz",             "uc-santa-cruz",    "ucsc",         "https://ucsc.edu",                   "US", 6, ["UCSantaCruz"]),
    _u("Arizona State University",  "asu",              "asu",          "https://asu.edu",                    "US", 6, ["ASU"]),
    _u("Ohio State University",     "ohio-state",       "osu",          "https://osu.edu",                    "US", 6, ["OhioStateUniversity"]),
    _u("Michigan State University", "michigan-state",   "msu",          "https://msu.edu",                    "US", 6, ["MichiganState"]),
    _u("Penn State University",     "penn-state",       "psu",          "https://psu.edu",                    "US", 6, ["PennState"]),
    _u("University of Minnesota",   "minnesota",        "umn",          "https://umn.edu",                    "US", 6, ["UMNNews"]),
    _u("University of Wisconsin",   "wisconsin",        "uwisconsin",   "https://wisc.edu",                   "US", 6, ["UWMadison"]),
    _u("University of Florida",     "uf",               "uf",           "https://ufl.edu",                    "US", 6, ["UniversityofFlorida"]),
    _u("Rutgers University",        "rutgers",          "rutgers",      "https://rutgers.edu",                "US", 6, ["RutgersU"]),
    _u("Vanderbilt University",     "vanderbilt",       "vanderbilt",   "https://vanderbilt.edu",             "US", 6, ["VanderbiltUniversity"]),
    _u("Notre Dame",                "notre-dame",       "notredame",    "https://nd.edu",                     "US", 6, ["NotreDame"]),
    _u("USC",                       "usc",              "usc",          "https://usc.edu",                    "US", 6, ["USC"]),
    _u("Boston University",         "bu",               "bu",           "https://bu.edu",                     "US", 6, ["BostonUniversity"]),
    _u("Northeastern University",   "northeastern",     "northeastern", "https://northeastern.edu",           "US", 6, ["NortheasternU"]),
    _u("Virginia Tech",             "virginia-tech",    "vt",           "https://vt.edu",                     "US", 6, ["VirginiaTech"]),
    _u("University of Virginia",    "uva",              "uva",          "https://virginia.edu",               "US", 6, ["UVACollegeEngineer"]),
    _u("University of Colorado Boulder", "cu-boulder",  "cu_boulder",   "https://colorado.edu",               "US", 6, ["CUBoulder"]),
    _u("University of Utah",        "utah",             "utah",         "https://utah.edu",                   "US", 6, ["UofUtah"]),
    _u("Indiana University",        "indiana",          "iu",           "https://iu.edu",                     "US", 6, ["IndianaUniversity"]),
    _u("Harvey Mudd College",       "harvey-mudd",      "harvey_mudd",  "https://hmc.edu",                    "US", 4, ["HarveyMuddCollege"]),
    _u("Stony Brook University",    "stony-brook",      "stony_brook",  "https://stonybrook.edu",             "US", 6, ["StonyBrookU"]),
    _u("University of Maryland",    "umd",              "umd",          "https://umd.edu",                    "US", 6, ["UMD"]),
    _u("UC Riverside",              "uc-riverside",     "ucr",          "https://ucr.edu",                    "US", 6, ["UCRiverside"]),
    _u("Tufts University",          "tufts",            "tufts",        "https://tufts.edu",                  "US", 6, ["TuftsUniversity"]),
    _u("Carnegie Mellon SCS",       "cmu-scs",          "cmu",          "https://cs.cmu.edu",                 "US", 4, ["CMUSCS"]),
    _u("Stanford HAI",              "stanford-hai",     "stanford",     "https://hai.stanford.edu",           "US", 4, ["StanfordHAI"]),
    _u("MIT LIDS",                  "mit-lids",         "mit_ocw",      "https://lids.mit.edu",               "US", 4, ["MITLIDS"]),
    _u("Caltech Online",            "caltech-online",   "caltech",      "https://caltech.edu",                "US", 4, ["CaltechCourses"]),

    # ── UK Universities ────────────────────────────────────────────────────────
    _u("University of Manchester",  "manchester",       "manchester",   "https://manchester.ac.uk",           "GB", 6, ["UoMOfficial"]),
    _u("King's College London",     "kcl",              "kcl",          "https://kcl.ac.uk",                  "GB", 6, ["KingsCollegeLondon"]),
    _u("London School of Economics","lse",              "lse",          "https://lse.ac.uk",                  "GB", 6, ["londonschoolofeconomics"]),
    _u("University of Bristol",     "bristol",          "bristol",      "https://bristol.ac.uk",              "GB", 6, ["BristolUniversity"]),
    _u("University of Warwick",     "warwick",          "warwick",      "https://warwick.ac.uk",              "GB", 6, ["WarwickMaths", "UniversityofWarwick"]),
    _u("University of Southampton", "southampton",      "southampton",  "https://soton.ac.uk",                "GB", 6, ["SouthamptonUniversity"]),
    _u("Durham University",         "durham",           "durham_uk",    "https://dur.ac.uk",                  "GB", 6, ["DurhamUniversity"]),
    _u("University of Birmingham",  "birmingham",       "birmingham",   "https://birmingham.ac.uk",           "GB", 6, ["unibirmingham"]),
    _u("University of Leeds",       "leeds",            "leeds",        "https://leeds.ac.uk",                "GB", 6, ["leedsuniversity"]),
    _u("University of Glasgow",     "glasgow",          "glasgow",      "https://gla.ac.uk",                  "GB", 6, ["UniversityofGlasgow"]),
    _u("Royal Institution",         "royal-institution","ri",           "https://rigb.org",                   "GB", 4, ["RoyalInstitution"]),

    # ── Canadian Universities ──────────────────────────────────────────────────
    _u("University of British Columbia", "ubc",         "ubc",          "https://ubc.ca",                     "CA", 6, ["UBC"]),
    _u("University of Waterloo",    "waterloo",         "waterloo",     "https://uwaterloo.ca",               "CA", 6, ["uwaterloo"]),
    _u("McGill University",         "mcgill",           "mcgill",       "https://mcgill.ca",                  "CA", 6, ["McGillU"]),
    _u("University of Alberta",     "alberta",          "alberta",      "https://ualberta.ca",                "CA", 6, ["UAlberta"]),
    _u("McMaster University",       "mcmaster",         "mcmaster",     "https://mcmaster.ca",                "CA", 6, ["McMasterUniversity"]),
    _u("University of Ottawa",      "ottawa",           "uottawa",      "https://uottawa.ca",                 "CA", 6, ["uOttawa"]),

    # ── Australian Universities ────────────────────────────────────────────────
    _u("Univ. of New South Wales",  "unsw",             "unsw",         "https://unsw.edu.au",                "AU", 6, ["UNSW"]),
    _u("University of Melbourne",   "melbourne",        "melbourne",    "https://unimelb.edu.au",             "AU", 6, ["UniMelb"]),
    _u("University of Sydney",      "sydney",           "usyd",         "https://sydney.edu.au",              "AU", 6, ["sydney_uni"]),
    _u("University of Queensland",  "uq",               "uq",           "https://uq.edu.au",                  "AU", 6, ["UQueensland"]),
    _u("Monash University",         "monash",           "monash",       "https://monash.edu",                 "AU", 6, ["MonashUniversity"]),

    # ── European Universities ──────────────────────────────────────────────────
    _u("TU Delft",                  "tu-delft",         "tudelft",      "https://tudelft.nl",                 "NL", 4, ["TUDelft"]),
    _u("TU Munich",                 "tu-munich",        "tum",          "https://tum.de",                     "DE", 6, ["TUMunich"]),
    _u("KTH Royal Institute",       "kth",              "kth",          "https://kth.se",                     "SE", 6, ["kthswe"], channel_ids=["UC8F0qdOBryEyjg4HgTIjRQA"]),
    _u("University of Amsterdam",   "uva-nl",           "uva_nl",       "https://uva.nl",                     "NL", 6, ["uva_amsterdam"], channel_ids=["UC3i2K9G-s3NcOjabgYlDkOA"]),
    _u("University of Helsinki",    "helsinki",         "helsinki",     "https://helsinki.fi",                "FI", 6, ["UniversityofHelsinki"]),
    _u("Eindhoven University",      "tue",              "tue",          "https://tue.nl",                     "NL", 6, ["TUeindhoven"]),

    # ── Asian / Singapore / HK ────────────────────────────────────────────────
    _u("National Univ. of Singapore","nus",             "nus",          "https://nus.edu.sg",                 "SG", 6, ["nus_singapore", "NUSComputing"]),
    _u("HKUST",                     "hkust",            "hkust",        "https://ust.hk",                     "HK", 4, ["hkust"], channel_ids=["UCdRnXk2yE-4olVkgz0tECvw"]),
    _u("University of Hong Kong",   "hku",              "hku",          "https://hku.hk",                     "HK", 4, ["HKUniversity"], channel_ids=["UCvZ4seZaqaO_A_WPfL-d9WQ"]),
    _u("Nanyang Tech University",   "ntu",              "ntu",          "https://ntu.edu.sg",                 "SG", 4, ["NanyangTechU"], channel_ids=["UC7ggK2wDrW6pIbKmvOrA_Kw"]),

    # ── Research Institutes ───────────────────────────────────────────────────
    _u("Fields Institute",          "fields-institute", "fields",       "https://fields.utoronto.ca",         "CA", 4, ["fieldsInstitute"]),
    _u("Newton Institute",          "newton-institute", "newton",       "https://newton.ac.uk",               "GB", 4, ["newtoninstitutevideos"], channel_ids=["UCrIzp-iUXd7YL4PacS2Qt4A"]),
    _u("MSRI / SLMath",             "slmath",           "slmath",       "https://slmath.org",                 "US", 4, ["MSRIvideo"], channel_ids=["UCj8bVrwNrIGAQlC_xceQaPA", "UCv1cOp6hkXdqeI92x1pW33Q"]),
    _u("Institut Henri Poincaré",   "ihp",              "ihp",          "https://ihp.fr",                     "FR", 4, ["InstitutHenriPoincare"]),
    _u("Hausdorff Center",          "hausdorff",        "hausdorff",    "https://hausdorff-center.de",        "DE", 4, ["HausdorffCenter"], channel_ids=["UC2F-j2KMho0zVWIPFKWoXoA"]),
    _u("MPI Mathematics Sciences",  "mpi-mis",          "mpi_mis",      "https://mis.mpg.de",                 "DE", 4, ["MPIMathSci"], channel_ids=["UC80kiZNWGR-nlLD1nCYFw0Q"]),
    _u("Santa Fe Institute",        "santa-fe",         "sfi",          "https://santafe.edu",                "US", 4, ["SantaFeInstitute"], channel_ids=["UC9rHXgUE9pikzYcGrAujMXQ"]),

    # ── Educator / Professor Channels ─────────────────────────────────────────
    _u("Professor Leonard",         "professor-leonard","prof_leonard",  "https://www.youtube.com/@ProfessorLeonard","US", 8, ["ProfessorLeonard"]),
    _u("Dr. Trefor Bazett",         "dr-trefor",        "drtefor",       "https://www.youtube.com/@DrTrefor",       "CA", 6, ["DrTrefor"]),
    _u("Michael Penn (Math)",       "michael-penn",     "michael_penn",  "https://www.youtube.com/@MichaelPennMath","US", 4, ["MichaelPennMath"]),
    _u("Neso Academy",              "neso-academy",     "neso_academy",  "https://nesoacademy.org",                 "IN", 6, ["nesoacademy"]),
    _u("Steve Brunton (Eigensteve)","eigensteve",       "eigensteve",    "https://eigensteve.com",                  "US", 4, ["Eigensteve"]),
    _u("StatQuest",                 "statquest",        "statquest",     "https://www.youtube.com/@statquest",      "US", 4, ["statquest"]),
    _u("Brian Douglas",             "brian-douglas",    "brian_douglas", "https://www.youtube.com/@BrianBDouglas",  "US", 4, ["BrianBDouglas"]),
    _u("Michel van Biezen",         "michel-van-biezen","michelvanbiezen","https://www.youtube.com/@MichelvanBiezen","US", 6, ["MichelvanBiezen"]),
    _u("PatrickJMT",                "patrickjmt",       "patrickjmt",    "https://patrickjmt.com",                  "US", 4, ["patrickjmt"]),
    _u("Organic Chemistry Tutor",   "organic-chem-tutor","octutor",      "https://www.youtube.com/@TheOrganicChemistryTutor","US", 6, ["TheOrganicChemistryTutor"]),
    _u("Professor Dave Explains",   "professor-dave",   "prof_dave",     "https://www.youtube.com/@ProfessorDaveExplains","US", 6, ["ProfessorDaveExplains"]),
    _u("Ben Eater",                 "ben-eater",        "ben_eater",     "https://eater.net",                       "US", 4, ["beneater"]),
    _u("CS50 (Harvard)",            "cs50",             "cs50",          "https://cs50.harvard.edu",                "US", 2, ["cs50", "cs50tv"], channel_ids=["UCcabW7890RKJzL968QWEykA"]),
    _u("fast.ai",                   "fastai",           "fastai",        "https://fast.ai",                         "US", 2, ["fastai", "fastdotai"], channel_ids=["UCUE6BorphFmAyNud6ONRvMg"]),
    _u("Reducible",                 "reducible",        "reducible",     "https://www.youtube.com/@Reducible",      "US", 4, ["Reducible"]),
    _u("The Coding Train",          "coding-train",     "coding_train",  "https://thecodingtrain.com",              "US", 4, ["TheCodingTrain"]),
    _u("Yannic Kilcher",            "yannic-kilcher",   "yannic_kilcher","https://www.youtube.com/@YannicKilcher",  "DE", 4, ["YannicKilcher"]),
    _u("Zach Star",                 "zach-star",        "zach_star",     "https://www.youtube.com/@zachstar",       "US", 4, ["zachstar"]),
    _u("Jacob Sorber",              "jacob-sorber",     "jacob_sorber",  "https://www.youtube.com/@JacobSorber",   "US", 4, ["JacobSorber"]),
    _u("Mathologer",                "mathologer",       "mathologer",    "https://www.youtube.com/@Mathologer",    "AU", 4, ["Mathologer"]),
    _u("Physics Videos by Eugene",  "eugene-physics",   "eugene_physics","https://www.youtube.com/@EugeneKhutoryansky","US",4,["EugeneKhutoryansky"]),
    _u("Two Minute Papers",         "two-minute-papers","two_min_papers", "https://www.youtube.com/@TwoMinutePapers","AT", 4, ["TwoMinutePapers"]),
    _u("Sentdex",                   "sentdex",          "sentdex",       "https://pythonprogramming.net",           "US", 6, ["sentdex"]),
    _u("DeepMind",                  "deepmind",         "deepmind",      "https://deepmind.com",                    "GB", 4, ["googledeepmind"]),
    _u("Weights & Biases",          "wandb",            "wandb",         "https://wandb.ai",                        "US", 4, ["WeightsBiases"]),
    _u("MIT OpenLearning",          "mit-openlearning", "mit_ocw",       "https://openlearning.mit.edu",            "US", 4, ["MITOpenLearning"]),
    _u("Stanford Engineering",      "stanford-engineering","stanford",   "https://engineering.stanford.edu",        "US", 6, ["StanfordEngineering"]),
    _u("Lex Fridman",               "lex-fridman",      "lex_fridman",   "https://lexfridman.com",                  "US", 4, ["lexfridman"]),

    # ── Discovered via subject search ─────────────────────────────────────────
    _u("Richard E Borcherds",       "borcherds",        "borcherds",     "https://www.youtube.com/@richarde.borcherds7998", "US", 4, ["richarde.borcherds7998"], channel_ids=["UCIyDqfi_cbkp-RU20aBF-MQ"]),
    _u("Frederic Schuller",         "frederic-schuller","schuller",      "https://www.youtube.com/@FredericSchuller",       "DE", 4, ["FredericSchuller"],        channel_ids=["UC6SaWe7xeOp31Vo8cQG1oXw"]),
    _u("Bright Side of Mathematics","bright-side-math", "bright_side_math","https://www.youtube.com/@brightsideofmaths",   "DE", 4, ["brightsideofmaths"],      channel_ids=["UCdwo4k1RQHTcq_-WS7Cazqg"]),
    _u("Walter Lewin Lectures",     "walter-lewin",     "walter_lewin",  "https://www.youtube.com/channel/UCiEHVhv0SBMpP75JbzJShqw", "US", 6, [], channel_ids=["UCiEHVhv0SBMpP75JbzJShqw"]),
    _u("Professor Macauley",        "prof-macauley",    "prof_macauley", "https://www.youtube.com/@ProfessorMacauley",      "US", 4, ["ProfessorMacauley"],      channel_ids=["UCH1cV4RtgI_N97M8jepiUzw"]),
    _u("Bill Kinney Math",          "bill-kinney",      "bill_kinney",   "https://www.youtube.com/@billkinneymath",         "US", 4, ["billkinneymath"],         channel_ids=["UCzLIrCdw8yBcknEf5kt6jnw"]),
    _u("James Cook Math",           "james-cook-math",  "james_cook_math","https://www.youtube.com/@jamescookmath",         "US", 4, ["jamescookmath"],          channel_ids=["UCfYSpKDLTjNDcoOyPoMFIsA"]),
    _u("ICTP Diploma Programme",    "ictp-diploma",     "ictp_diploma",  "https://www.ictp.it",                             "IT", 4, [],                         channel_ids=["UCBlqfZZYQWKyr6qLAB7LINw"]),
    _u("ICTP Mathematics",          "ictp-math",        "ictp_math",     "https://www.ictp.it",                             "IT", 4, [],                         channel_ids=["UC-akozxNLMPcMcs0qVvS1VQ"]),
    _u("IMPA",                      "impa",             "impa",          "https://impa.br",                                 "BR", 4, ["impa_br"],                channel_ids=["UCpuZUX_IyMPXiqlkwrxCbNA"]),
    _u("Zewail City OCW",           "zewail-ocw",       "zewail_ocw",    "https://zewailcity.edu.eg",                       "EG", 4, [],                         channel_ids=["UCGNOEBp7AZaY4XPNoagpv8w"]),
    _u("AIMS South Africa",         "aims-south-africa","aims_south_africa","https://aims.ac.za",                           "ZA", 4, [],                         channel_ids=["UCetimk8fNERHoir_zKQbwiQ"]),
    _u("Mathematics at HSE",        "math-at-hse",      "math_at_hse",   "https://www.hse.ru",                              "RU", 4, [],                         channel_ids=["UCASlwNxf7mHBUEPr1s6fsDg"]),
    _u("Oxford Mathematics",        "oxford-mathematics","oxford_mathematics","https://www.maths.ox.ac.uk",                 "GB", 4, ["OxfordMathematics"],      channel_ids=["UCLnGGRG__uGSPLBLzyhg8dQ"]),
    _u("Uppsala Algebra",           "uppsala-algebra",  "uppsala_algebra","https://www.uu.se",                              "SE", 4, [],                         channel_ids=["UCPWnhR29VHTAk7rZUEDQdDQ"]),
    _u("Kimberly Brehm",            "kimberly-brehm",   "kimberly_brehm","https://www.youtube.com/@KimberlyBrehm",          "US", 6, ["KimberlyBrehm"],          channel_ids=["UCcbu9qaBn3MNFYr96mbg72w"]),
    _u("Math With Richard",         "math-with-richard","math_with_richard","https://www.youtube.com/@MathWithRichard",     "US", 6, ["MathWithRichard"],        channel_ids=["UCX1Fp8GbfbdIguUjGatQu6g"]),
    _u("Jeffrey Chasnov",           "jeffrey-chasnov",  "jeffrey_chasnov","https://www.math.hkust.edu.hk",                  "HK", 4, ["jeffreychasnov"],         channel_ids=["UClqK6PQ-aYbftRLlMWVuE0g"]),
    _u("Faculty of Khan",           "faculty-of-khan",  "faculty_of_khan","https://www.youtube.com/@FacultyOfKhan",         "US", 4, ["FacultyOfKhan"],          channel_ids=["UCGDanWUzNMbIV11lcNi-yBg"]),
    _u("MathMajor",                 "mathmajor",        "mathmajor",     "https://www.youtube.com/@MathMajor",              "US", 4, ["MathMajor"],              channel_ids=["UCC6Wl-xnWVS9FP0k-Hj5aiw"]),
]


# ── YouTube API helpers ────────────────────────────────────────────────────────

def resolve_handle_to_channel_id(handle: str) -> str | None:
    """Convert a YouTube handle to a channelId."""
    try:
        resp = youtube.channels().list(
            part="id",
            forHandle=handle,
        ).execute()
        items = resp.get("items", [])
        if items:
            return items[0]["id"]
    except HttpError as e:
        print(f"    [API] channels.list({handle}) error: {e}", flush=True)
    return None


def get_all_playlists(channel_id: str) -> list[dict]:
    """Return ALL playlists for a channel using pagination."""
    playlists = []
    page_token = None
    while True:
        try:
            resp = youtube.playlists().list(
                part="snippet,contentDetails",
                channelId=channel_id,
                maxResults=50,
                pageToken=page_token,
            ).execute()
        except HttpError as e:
            print(f"    [API] playlists.list error: {e}", flush=True)
            break

        for item in resp.get("items", []):
            pid = item["id"]
            title = (item["snippet"].get("title") or "").strip()
            # itemCount from contentDetails is approximate but fast (no extra call needed)
            count = item.get("contentDetails", {}).get("itemCount", 0) or 0
            thumbnail = (
                item["snippet"].get("thumbnails", {}).get("high", {}).get("url")
                or item["snippet"].get("thumbnails", {}).get("default", {}).get("url")
            )
            playlists.append({
                "id": pid,
                "title": title,
                "count": int(count),
                "thumbnail_url": thumbnail,
            })

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return playlists


def get_playlist_video_count(playlist_id: str) -> int:
    """Get exact video count for a playlist by paging through playlistItems."""
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
        except Exception:
            break
        count += len(resp.get("items", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return count


# ── Subject / level inference (same as other scrapers) ────────────────────────
SUBJECT_MAP: list[tuple[list[str], list[str]]] = [
    (["machine learning", "deep learning", "neural network", "ai ", "artificial intelligence", "reinforcement learning", "nlp", "natural language", "computer vision", "large language model", "llm"], ["Machine Learning", "Artificial Intelligence"]),
    (["algorithm", "data structure", "competitive programming"], ["Algorithms", "Computer Science"]),
    (["operating system", "systems programming", "computer architecture", "computer system"], ["Computer Systems", "Computer Science"]),
    (["database", "sql", "nosql", "data engineering"], ["Databases", "Computer Science"]),
    (["web development", "javascript", "react", "node", "html", "css", "frontend", "backend", "full stack"], ["Web Development", "Programming"]),
    (["python", "programming", "software engineering", "software development", "object-oriented", "functional programming"], ["Programming", "Computer Science"]),
    (["computer science", "cs50", "computation"], ["Computer Science"]),
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
    (["blockchain", "cryptocurrency", "web3", "smart contract"], ["Blockchain", "Computer Science"]),
    (["entrepreneurship", "startup", "business", "management", "strategy", "marketing", "leadership"], ["Business", "Entrepreneurship"]),
]


def infer_subjects(title: str) -> list[str]:
    t = title.lower()
    for keywords, subjects in SUBJECT_MAP:
        if any(k in t for k in keywords):
            return subjects[:2]
    return ["Education"]


def infer_level(title: str) -> str:
    t = title.lower()
    if any(w in t for w in ["advanced", "graduate", "phd", "doctoral", "grad "]):
        return "graduate"
    return "undergraduate"


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

cur.execute("SELECT youtube_playlist_id FROM courses WHERE youtube_playlist_id IS NOT NULL")
existing_pids: set[str] = {r["youtube_playlist_id"] for r in cur.fetchall()}
print(f"Existing playlists in DB: {len(existing_pids)}")

subject_cache: dict[str, str] = {}


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
        "INSERT INTO subjects (id, name, slug) VALUES (%s,%s,%s) ON CONFLICT (slug) DO NOTHING RETURNING id",
        (sid, name, sl),
    )
    row = cur.fetchone()
    if not row:
        cur.execute("SELECT id FROM subjects WHERE slug = %s", (sl,))
        row = cur.fetchone()
    subject_cache[name] = str(row["id"])
    conn.commit()
    return subject_cache[name]


# ── Slug dedup ────────────────────────────────────────────────────────────────
cur.execute("SELECT slug FROM courses")
seen_slugs: set[str] = {r["slug"] for r in cur.fetchall()}

# ── Main loop ─────────────────────────────────────────────────────────────────
total_inserted = 0
quota_used = 0  # rough unit estimate

for uni in UNIVERSITIES:
    source_key = uni["source_key"]
    if ONLY_SOURCES and source_key not in ONLY_SOURCES:
        continue

    print(f"\n{'='*60}")
    print(f"  {uni['name']} [{source_key}]")
    print(f"{'='*60}")

    uni_id = upsert_university(uni["name"], uni["slug"], source_key, uni["website"], uni["country"])
    min_v = uni.get("min_videos", 6)

    all_playlists: dict[str, dict] = {}
    resolved_ids: list[str] = []

    # Prefer hardcoded channel IDs (skip channels.list entirely)
    for cid in uni.get("channel_ids", []):
        resolved_ids.append(cid)

    # Then try handle-based resolution for any not already covered
    for handle in uni["handles"]:
        print(f"  Resolving @{handle} ...", flush=True)
        channel_id = resolve_handle_to_channel_id(handle)
        quota_used += 1
        if not channel_id:
            print(f"    Could not resolve @{handle}", flush=True)
            continue
        if channel_id not in resolved_ids:
            resolved_ids.append(channel_id)
        print(f"    channelId = {channel_id}", flush=True)

    for channel_id in resolved_ids:
        playlists = get_all_playlists(channel_id)
        quota_used += max(1, (len(playlists) + 49) // 50)
        print(f"    {channel_id}: {len(playlists)} playlists", flush=True)

        for p in playlists:
            if p["id"] not in all_playlists:
                all_playlists[p["id"]] = p

    new_playlists = [p for p in all_playlists.values() if p["id"] not in existing_pids]
    print(f"  New playlists (not in DB): {len(new_playlists)}", flush=True)

    if not new_playlists:
        continue

    # For playlists where itemCount=0 (private/API anomaly), verify with playlistItems
    # For the rest, trust the API count (it's accurate for public playlists)
    need_exact_count = [p for p in new_playlists if p["count"] == 0]

    if need_exact_count:
        print(f"  Getting exact counts for {len(need_exact_count)} playlists with count=0...", flush=True)
        def _get_count(p: dict) -> dict:
            c = get_playlist_video_count(p["id"])
            return {**p, "count": c}

        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futures = {pool.submit(_get_count, p): p for p in need_exact_count}
            for fut in as_completed(futures):
                result = fut.result()
                all_playlists[result["id"]]["count"] = result["count"]
                quota_used += max(1, (result["count"] + 49) // 50)

        new_playlists = [all_playlists[p["id"]] for p in new_playlists]

    # Filter for course playlists
    verified = [
        p for p in new_playlists
        if is_course_playlist(p["title"], p["count"], min_v, source_key)
    ]
    skipped = len(new_playlists) - len(verified)
    print(f"  Kept {len(verified)} course playlists, skipped {skipped}", flush=True)

    # Upsert
    inserted_this_uni = 0
    for p in verified:
        title = p["title"]
        subjects = infer_subjects(title)
        level = infer_level(title)

        base_slug = slugify(f"{title} {source_key}")
        slug = base_slug
        counter = 2
        while slug in seen_slugs:
            slug = f"{base_slug}-{counter}"
            counter += 1
        seen_slugs.add(slug)

        safe = title.encode("ascii", "replace").decode("ascii")
        print(f"    + {safe[:65]:<65} ({p['count']}v)", flush=True)

        cid = str(uuid.uuid4())
        try:
            cur.execute(
                """INSERT INTO courses (
                       id, university_id, title, slug, source_key,
                       level, youtube_playlist_id,
                       total_videos, thumbnail_url,
                       has_video_lectures, is_published
                   ) VALUES (%s,%s,%s,%s,%s, %s,%s, %s,%s, TRUE,TRUE)
                   ON CONFLICT (slug) DO UPDATE SET
                       youtube_playlist_id = EXCLUDED.youtube_playlist_id,
                       total_videos        = GREATEST(EXCLUDED.total_videos, courses.total_videos),
                       thumbnail_url       = COALESCE(EXCLUDED.thumbnail_url, courses.thumbnail_url),
                       has_video_lectures  = TRUE,
                       is_published        = TRUE""",
                (cid, uni_id, title, slug, source_key,
                 level, p["id"],
                 p["count"], p.get("thumbnail_url")),
            )

            for subj_name in subjects:
                subj_id = upsert_subject(subj_name)
                cur.execute(
                    """INSERT INTO course_subjects (id, course_id, subject_id)
                       VALUES (%s, (SELECT id FROM courses WHERE slug=%s LIMIT 1), %s)
                       ON CONFLICT DO NOTHING""",
                    (str(uuid.uuid4()), slug, subj_id),
                )

            existing_pids.add(p["id"])
            inserted_this_uni += 1

            if inserted_this_uni % 30 == 0:
                conn.commit()
                print(f"    ... committed {inserted_this_uni}", flush=True)

        except Exception as exc:
            conn.rollback()
            print(f"  [DB ERROR] {safe}: {exc}", flush=True)

    conn.commit()
    total_inserted += inserted_this_uni
    print(f"  Done: {inserted_this_uni} new courses (quota used so far: ~{quota_used} units)", flush=True)

# ── Final report ──────────────────────────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM courses WHERE is_published=TRUE AND has_video_lectures=TRUE")
pub_video = cur.fetchone()["count"]

print(f"\n{'='*60}")
print(f"COMPLETE")
print(f"  New courses inserted     : {total_inserted}")
print(f"  Estimated API quota used : ~{quota_used} units (of 10,000/day)")
print(f"  Total published video    : {pub_video}")
print(f"{'='*60}")

cur.close()
conn.close()
