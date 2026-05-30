#!/usr/bin/env python
"""
Ingest courses from publicly curated GitHub lists of free university courses.

Sources:
  - Developer-Y/cs-video-courses  — CS video courses with YouTube playlists
  - prakhar1989/awesome-courses   — broader awesome-courses list
  - ossu/computer-science         — open-source CS degree curriculum
  - ForrestKnight/open-source-cs  — open-source CS path

Each README is parsed for YouTube playlist URLs. For each playlist found:
  1. The section heading is used as course title
  2. The university/institution is inferred from context
  3. yt-dlp verifies the playlist is alive and gets video count + thumbnail
  4. Course is upserted into the database

Usage:
  py -3.13 scrape_github_courses.py
  DATABASE_URL=postgresql://... py -3.13 scrape_github_courses.py
"""
from __future__ import annotations

import os
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import psycopg2
import psycopg2.extras
import urllib.request
import urllib.error
from slugify import slugify

WORKERS = int(os.environ.get("WORKERS", "6"))
DELAY = 0.4

# ── GitHub source definitions ─────────────────────────────────────────────────
GITHUB_SOURCES = [
    {
        "url": "https://raw.githubusercontent.com/Developer-Y/cs-video-courses/master/README.md",
        "default_source_key": "curated",
        "name": "Developer-Y CS Video Courses",
    },
    {
        "url": "https://raw.githubusercontent.com/prakhar1989/awesome-courses/master/README.md",
        "default_source_key": "curated",
        "name": "prakhar1989 Awesome Courses",
    },
    {
        "url": "https://raw.githubusercontent.com/ossu/computer-science/master/README.md",
        "default_source_key": "curated",
        "name": "OSSU Computer Science",
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

# ── Load existing playlist IDs ─────────────────────────────────────────────────
cur.execute("SELECT youtube_playlist_id FROM courses WHERE youtube_playlist_id IS NOT NULL")
existing_pids: set[str] = {r["youtube_playlist_id"] for r in cur.fetchall()}
print(f"Existing playlists in DB: {len(existing_pids)}")

# ── Subject inference (same as channel scraper) ────────────────────────────────
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
    (["blockchain", "cryptocurrency", "web3", "smart contract"], ["Blockchain", "Computer Science"]),
    (["entrepreneurship", "startup", "business", "management", "strategy", "marketing", "leadership"], ["Business", "Entrepreneurship"]),
]


def infer_subjects(title: str) -> list[str]:
    t = title.lower()
    for keywords, subjects in SUBJECT_MAP:
        if any(k in t for k in keywords):
            return subjects[:2]
    return ["Computer Science"]


def infer_level(title: str) -> str:
    t = title.lower()
    if any(w in t for w in ["advanced", "graduate", "phd", "doctoral", "grad "]):
        return "graduate"
    return "undergraduate"


# ── University name → slug/source_key mapping ─────────────────────────────────
UNI_NAME_MAP: dict[str, tuple[str, str]] = {
    "mit": ("mit", "mit_ocw"),
    "massachusetts institute of technology": ("mit", "mit_ocw"),
    "stanford": ("stanford", "stanford"),
    "stanford university": ("stanford", "stanford"),
    "uc berkeley": ("berkeley", "berkeley"),
    "university of california, berkeley": ("berkeley", "berkeley"),
    "berkeley": ("berkeley", "berkeley"),
    "yale": ("yale", "yale"),
    "yale university": ("yale", "yale"),
    "harvard": ("harvard", "harvard"),
    "harvard university": ("harvard", "harvard"),
    "cmu": ("carnegie-mellon", "cmu"),
    "carnegie mellon": ("carnegie-mellon", "cmu"),
    "georgia tech": ("georgia-tech", "gatech"),
    "princeton": ("princeton", "princeton"),
    "columbia": ("columbia", "columbia"),
    "cornell": ("cornell", "cornell"),
    "caltech": ("caltech", "caltech"),
    "oxford": ("oxford", "oxford"),
    "cambridge": ("cambridge", "cambridge"),
    "michigan": ("umich", "umich"),
    "university of michigan": ("umich", "umich"),
    "ucsd": ("uc-san-diego", "ucsd"),
    "uc san diego": ("uc-san-diego", "ucsd"),
    "ucla": ("ucla", "ucla"),
    "duke": ("duke", "duke"),
    "nyu": ("nyu", "nyu"),
    "johns hopkins": ("johns-hopkins", "jhu"),
    "epfl": ("epfl", "epfl"),
    "eth zurich": ("eth-zurich", "eth"),
    "imperial": ("imperial-college", "imperial"),
    "ucl": ("ucl", "ucl"),
    "toronto": ("toronto", "utoronto"),
    "uw": ("uw", "uw"),
    "washington": ("uw", "uw"),
    "illinois": ("uiuc", "uiuc"),
    "purdue": ("purdue", "purdue"),
}

# ── Ensure universities exist in DB ───────────────────────────────────────────
UNI_SLUG_TO_ID: dict[str, str] = {}


def get_or_create_university(slug: str, name: str, source_key: str) -> str:
    if slug in UNI_SLUG_TO_ID:
        return UNI_SLUG_TO_ID[slug]
    cur.execute("SELECT id FROM universities WHERE slug = %s", (slug,))
    row = cur.fetchone()
    if row:
        UNI_SLUG_TO_ID[slug] = str(row["id"])
        return UNI_SLUG_TO_ID[slug]
    uid = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO universities (id, name, slug, source_key, website, country)
           VALUES (%s, %s, %s, %s, %s, %s)
           ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name RETURNING id""",
        (uid, name, slug, source_key, f"https://{slug}.edu", "US"),
    )
    row = cur.fetchone()
    conn.commit()
    UNI_SLUG_TO_ID[slug] = str(row["id"])
    return UNI_SLUG_TO_ID[slug]


subject_cache: dict[str, str] = {}


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


# ── Fetch raw README ──────────────────────────────────────────────────────────
def fetch_readme(url: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        print(f"  [fetch ERROR] {url}: {exc}")
        return None


# ── Parse YouTube playlist IDs from Markdown ─────────────────────────────────
# Matches lines like:
#   [Video Lectures](https://www.youtube.com/playlist?list=PLxxx)
#   [Lecture Videos](https://youtube.com/playlist?list=PLxxx)
#   [Course](https://www.youtube.com/watch?v=xxx&list=PLxxx)
YT_PLAYLIST_RE = re.compile(
    r"https?://(?:www\.)?youtube\.com/(?:playlist\?list=|watch\?[^)]*list=)(PL[A-Za-z0-9_\-]{10,})"
)
# Heading immediately before or as context: ## Title, ### Title, **Title**
HEADING_RE = re.compile(r"^#{1,4}\s+(.+)$", re.MULTILINE)
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
LINK_TEXT_RE = re.compile(r"\[([^\]]+)\]\(https?://(?:www\.)?youtube\.com/playlist")


def parse_courses_from_markdown(text: str) -> list[dict]:
    """Extract {title, playlist_id, university_name} records from README."""
    courses: list[dict] = []
    lines = text.splitlines()

    current_heading = "Unknown Course"
    current_university = ""

    for i, line in enumerate(lines):
        # Track headings as potential course titles
        h_match = HEADING_RE.match(line)
        if h_match:
            heading_text = h_match.group(1).strip()
            # Strip markdown links from heading
            heading_text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", heading_text)
            heading_text = heading_text.strip()
            if heading_text:
                current_heading = heading_text

        # Look for YouTube playlist links on this line
        yt_matches = YT_PLAYLIST_RE.findall(line)
        if not yt_matches:
            continue

        # Get link text as course title
        link_match = LINK_TEXT_RE.search(line)
        link_text = link_match.group(1) if link_match else None

        # Try to infer university from context (look up to 10 lines back)
        uni_name = ""
        context = "\n".join(lines[max(0, i - 10):i + 1]).lower()

        # Look for university names in context
        for uni_key in UNI_NAME_MAP:
            if uni_key in context:
                uni_name = uni_key
                break

        for pid in yt_matches:
            if pid in existing_pids:
                continue

            # Prefer link text, fall back to current heading
            title = link_text or current_heading
            # If link text is something generic like "Video Lectures", use heading
            generic = {"video lectures", "lecture videos", "course", "lectures", "videos",
                       "video", "playlist", "youtube", "watch", "click here", "here"}
            if title.lower().strip() in generic:
                title = current_heading

            courses.append({
                "playlist_id": pid,
                "title": title,
                "university_name": uni_name,
            })

    # Deduplicate by playlist_id
    seen: set[str] = set()
    unique = []
    for c in courses:
        if c["playlist_id"] not in seen:
            seen.add(c["playlist_id"])
            unique.append(c)
    return unique


# ── yt-dlp verification ────────────────────────────────────────────────────────
def verify_playlist(playlist_id: str) -> dict | None:
    """Return {video_count, thumbnail_url} or None if dead."""
    time.sleep(DELAY)
    import yt_dlp
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
            "thumbnail_url": (
                f"https://i.ytimg.com/vi/{first_vid}/hqdefault.jpg" if first_vid else None
            ),
            "title": info.get("title") or "",
        }
    except Exception:
        return None


# ── Main ──────────────────────────────────────────────────────────────────────
all_candidates: list[dict] = []

for source in GITHUB_SOURCES:
    print(f"\n--- Fetching {source['name']} ---")
    text = fetch_readme(source["url"])
    if not text:
        continue
    parsed = parse_courses_from_markdown(text)
    # Tag with source
    for c in parsed:
        c["list_source"] = source["name"]
        c["default_source_key"] = source["default_source_key"]
    all_candidates.extend(parsed)
    print(f"  Found {len(parsed)} unique new playlist IDs")

print(f"\nTotal candidates to verify: {len(all_candidates)}")

if not all_candidates:
    print("Nothing to do.")
    cur.close()
    conn.close()
    raise SystemExit(0)

# ── Verify playlists in parallel ──────────────────────────────────────────────
print(f"\nVerifying {len(all_candidates)} playlists with yt-dlp ({WORKERS} workers)...")

verified_map: dict[str, dict] = {}  # playlist_id -> yt-dlp info
done = 0

with ThreadPoolExecutor(max_workers=WORKERS) as pool:
    fut_to_cand = {pool.submit(verify_playlist, c["playlist_id"]): c for c in all_candidates}
    for fut in as_completed(fut_to_cand):
        cand = fut_to_cand[fut]
        info = fut.result()
        done += 1
        pid = cand["playlist_id"]
        safe = cand["title"].encode("ascii", "replace").decode("ascii")
        if info and info["video_count"] > 0:
            verified_map[pid] = info
            print(f"  [{done}/{len(all_candidates)}] OK  {safe[:55]:<55} ({info['video_count']} videos)", flush=True)
        else:
            print(f"  [{done}/{len(all_candidates)}] DEAD {safe[:55]}", flush=True)

print(f"\n{len(verified_map)} playlists verified alive. Upserting...")

# ── Fetch existing slugs ───────────────────────────────────────────────────────
cur.execute("SELECT slug FROM courses")
seen_slugs: set[str] = {r["slug"] for r in cur.fetchall()}

inserted = 0
skipped = 0

for cand in all_candidates:
    pid = cand["playlist_id"]
    if pid not in verified_map:
        skipped += 1
        continue

    info = verified_map[pid]

    # Use yt-dlp title if it's more descriptive than what we parsed
    yt_title = (info.get("title") or "").strip()
    title = cand["title"]
    # If yt-dlp returned a real playlist title and ours is generic, prefer it
    generic = {"unknown course", "video lectures", "lecture videos", "course", "lectures"}
    if title.lower() in generic and yt_title:
        title = yt_title
    if not title or title.lower() in generic:
        title = yt_title or f"Course {pid}"

    # Resolve university
    uni_name_key = cand.get("university_name", "").lower()
    if uni_name_key in UNI_NAME_MAP:
        uni_slug, source_key = UNI_NAME_MAP[uni_name_key]
        uni_display_name = uni_name_key.title()
    else:
        # Fallback: put under a "Curated" institution
        uni_slug = "curated-courses"
        source_key = "curated"
        uni_display_name = "Open University (Curated)"

    uni_id = get_or_create_university(uni_slug, uni_display_name, source_key)
    subjects = infer_subjects(title)
    level = infer_level(title)

    base_slug = slugify(f"{title} {source_key}")
    slug = base_slug
    counter = 2
    while slug in seen_slugs:
        slug = f"{base_slug}-{counter}"
        counter += 1
    seen_slugs.add(slug)

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
             level, pid,
             info["video_count"], info.get("thumbnail_url")),
        )

        for subj_name in subjects:
            subj_id = upsert_subject(subj_name)
            cur.execute(
                """INSERT INTO course_subjects (id, course_id, subject_id)
                   VALUES (%s,
                           (SELECT id FROM courses WHERE slug=%s LIMIT 1),
                           %s)
                   ON CONFLICT DO NOTHING""",
                (str(uuid.uuid4()), slug, subj_id),
            )

        existing_pids.add(pid)
        inserted += 1

        if inserted % 25 == 0:
            conn.commit()
            print(f"  ... committed {inserted}", flush=True)

    except Exception as exc:
        conn.rollback()
        safe = title.encode("ascii", "replace").decode("ascii")
        print(f"  [DB ERROR] {safe}: {exc}", flush=True)

conn.commit()

# ── Report ────────────────────────────────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM courses WHERE is_published=TRUE AND has_video_lectures=TRUE")
total_pub = cur.fetchone()["count"]

print(f"\n{'='*60}")
print(f"GITHUB CURATED SOURCES COMPLETE")
print(f"  Inserted : {inserted}")
print(f"  Skipped  : {skipped} (dead playlists)")
print(f"  Total published video: {total_pub}")
print(f"{'='*60}")

cur.close()
conn.close()
