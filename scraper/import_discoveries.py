"""
Import cleaned course code discoveries into the database.

For each validated course:
1. Map to existing university (or create if needed)
2. Create course record with proper fields
3. Tag with subjects based on course code + title
4. Update subject counts after import
"""
import json, os, re, sys, uuid
from datetime import datetime, timezone
from slugify import slugify

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Register UUID adapter for psycopg2
psycopg2.extras.register_uuid()

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

DB = os.environ.get("DATABASE_URL", "")
if not DB:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)
DB = DB.replace("postgresql+asyncpg://", "postgresql://")

# Add backend to path for subject matching
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from app.subject_matching import strict_subject_phrases, strict_subject_matches_title

# Load clean discoveries
clean_path = os.path.join(
    os.path.dirname(__file__), "..", "course_code_discoveries_clean.json"
)
with open(clean_path, encoding="utf-8") as f:
    discoveries = json.load(f)

conn = psycopg2.connect(DB, connect_timeout=15, sslmode="require")
cur = conn.cursor()

# ═══════════════════════════════════════════════════════════════════════════
# University mapping: discovery name → DB source_key
# ═══════════════════════════════════════════════════════════════════════════
UNI_MAP = {
    "MIT": "mit_ocw",
    "Stanford": "stanford",
    "Harvard": "harvard",
    "UC Berkeley": "berkeley",
    "Carnegie Mellon": "cmu",
    "Caltech": "caltech",
    "Princeton": "princeton",
    "Yale": "yale",
    "Columbia": "columbia",
    "Cornell": "cornell",
    "Duke": "duke",
    "Georgia Tech": "gatech",
    "Oxford": "oxford",
    "Cambridge": "cambridge",
    "Imperial College London": "imperial",
    "University College London": "ucl",
    "University of Edinburgh": "edinburgh",
    "University of Toronto": "utoronto",
    "UBC": "ubc",
    "University of Waterloo": "waterloo",
    "McGill": "mcgill",
    "University of Michigan": "umich",
    "UT Austin": "ut_austin",
    "UCLA": "ucla",
    "UC San Diego": "ucsd",
    "UIUC": "uiuc",
    "Purdue": "purdue",
    "NYU": "nyu",
    "ETH Zurich": "eth",
    "EPFL": "epfl",
    "NUS": "nus",
    "UNSW": "unsw",
    "University of Melbourne": "umelbourne",
}

# Load university IDs from DB
cur.execute("SELECT id, source_key, name FROM universities")
uni_rows = cur.fetchall()
uni_by_source = {r[1]: {"id": r[0], "name": r[2]} for r in uni_rows}
uni_by_name = {r[2].lower(): {"id": r[0], "source_key": r[1]} for r in uni_rows}

print(f"Universities in DB: {len(uni_rows)}")

# ═══════════════════════════════════════════════════════════════════════════
# Load existing playlists to skip dupes
# ═══════════════════════════════════════════════════════════════════════════
cur.execute("SELECT youtube_playlist_id FROM courses WHERE youtube_playlist_id IS NOT NULL")
existing_pids = {r[0] for r in cur.fetchall()}
print(f"Existing playlists: {len(existing_pids)}")

# ═══════════════════════════════════════════════════════════════════════════
# Load subjects for tagging
# ═══════════════════════════════════════════════════════════════════════════
cur.execute("SELECT id, slug, name FROM subjects")
subjects = {r[1]: {"id": r[0], "name": r[2]} for r in cur.fetchall()}
print(f"Subjects: {len(subjects)}")

# ═══════════════════════════════════════════════════════════════════════════
# Import
# ═══════════════════════════════════════════════════════════════════════════
imported = 0
skipped_dupe = 0
skipped_no_uni = 0
tagged = 0

for uni_name, items in discoveries.items():
    source_key = UNI_MAP.get(uni_name)
    if not source_key:
        print(f"  SKIP {uni_name}: no source_key mapping")
        skipped_no_uni += len(items)
        continue

    uni = uni_by_source.get(source_key)
    if not uni:
        # Try to find by name
        uni = uni_by_name.get(uni_name.lower())
        if not uni:
            print(f"  SKIP {uni_name}: university not found in DB (source_key={source_key})")
            skipped_no_uni += len(items)
            continue
        source_key = uni["source_key"]

    uni_id = uni["id"]
    print(f"\n--- {uni_name} ({len(items)} courses) ---")

    for item in items:
        pid = item.get("playlist_id")
        if pid in existing_pids:
            skipped_dupe += 1
            continue

        title = item.get("display_title") or item.get("title", "")
        if not title:
            continue

        # Generate slug
        base_slug = slugify(title[:80])
        slug = base_slug[:200]
        # Ensure unique slug
        cur.execute("SELECT id FROM courses WHERE slug = %s", (slug,))
        if cur.fetchone():
            slug = f"{base_slug[:180]}-{uuid.uuid4().hex[:8]}"

        course_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        # Determine level from course code
        code = item.get("course_code", "")
        level = "undergraduate"
        if re.search(r'[WS]\d{4}', code):  # Columbia grad courses like W4111
            level = "graduate"
        elif re.search(r'\b[5-9]\d{2}\b', code):  # 500+ level
            level = "graduate"
        elif re.search(r'\b[4]\d{2}\b', code):  # 400 level
            level = "undergraduate"

        cur.execute("""
            INSERT INTO courses (id, title, slug, description, level,
                source_key, source_url, youtube_playlist_id,
                thumbnail_url, total_videos, is_published,
                has_video_lectures, university_id, view_count,
                created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            course_id, title, slug,
            item.get("description", "") or "",
            level, source_key,
            f"https://www.youtube.com/playlist?list={pid}",
            pid,
            item.get("thumbnail", ""),
            item.get("video_count", 0),
            True,  # is_published
            True,  # has_video_lectures
            uni_id,
            0,  # view_count
            now, now,
        ))

        # Tag with subjects based on title + course code
        subject_ids = set()
        title_lower = title.lower()

        # Match by strict subject matching
        for subj_slug, subj_data in subjects.items():
            if strict_subject_matches_title(title, subj_slug):
                subject_ids.add(subj_data["id"])

        # Also tag by course code patterns
        code_upper = code.upper()
        if any(c in code_upper for c in ["CS", "COMP", "CPSC", "COS", "CSC", "CMS"]):
            cs_id = subjects.get("computer-science", {}).get("id")
            if cs_id:
                subject_ids.add(cs_id)
        if any(c in code_upper for c in ["MATH", "MAT", "MA"]):
            math_id = subjects.get("mathematics", {}).get("id")
            if math_id:
                subject_ids.add(math_id)
        if any(c in code_upper for c in ["PHYS", "PH", "PHY"]):
            phys_id = subjects.get("physics", {}).get("id")
            if phys_id:
                subject_ids.add(phys_id)
        if any(c in code_upper for c in ["CHEM", "CH"]):
            chem_id = subjects.get("chemistry", {}).get("id")
            if chem_id:
                subject_ids.add(chem_id)
        if any(c in code_upper for c in ["BIO", "BIOL", "MCB", "BI"]):
            bio_id = subjects.get("biology", {}).get("id")
            if bio_id:
                subject_ids.add(bio_id)
        if any(c in code_upper for c in ["ECON", "ECO"]):
            econ_id = subjects.get("economics", {}).get("id")
            if econ_id:
                subject_ids.add(econ_id)
        if any(c in code_upper for c in ["STAT", "STA", "ST"]):
            stat_id = subjects.get("statistics", {}).get("id")
            if stat_id:
                subject_ids.add(stat_id)
        if any(c in code_upper for c in ["EE", "ECE", "ELEC", "EECS", "ELE"]):
            ee_id = subjects.get("electrical-engineering", {}).get("id")
            if ee_id:
                subject_ids.add(ee_id)
        if any(c in code_upper for c in ["ME", "MECH", "MAE"]):
            me_id = subjects.get("mechanical-engineering", {}).get("id")
            if me_id:
                subject_ids.add(me_id)
        if any(c in code_upper for c in ["CE", "CIV", "CEE"]):
            ce_id = subjects.get("civil-engineering", {}).get("id")
            if ce_id:
                subject_ids.add(ce_id)

        # Insert course_subjects
        for sid in subject_ids:
            cur.execute("""
                INSERT INTO course_subjects (course_id, subject_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (course_id, sid))
            tagged += 1

        existing_pids.add(pid)
        imported += 1

        if imported % 25 == 0:
            conn.commit()
            print(f"  ... {imported} imported, {tagged} tags")

    conn.commit()
    print(f"  Done: {len(items)} processed")

# ═══════════════════════════════════════════════════════════════════════════
# Final commit and summary
# ═══════════════════════════════════════════════════════════════════════════
conn.commit()

print("\n" + "=" * 60)
print(f"Imported: {imported}")
print(f"Skipped (duplicate): {skipped_dupe}")
print(f"Skipped (no university): {skipped_no_uni}")
print(f"Subject tags added: {tagged}")

# ═══════════════════════════════════════════════════════════════════════════
# Regenerate subject counts
# ═══════════════════════════════════════════════════════════════════════════
print("\nRegenerating subject counts JSON...")
from app.subject_matching import strict_subject_matches_title

# Get all catalog-ready course titles
fragments = [
    "about ", "#short", "admissions", "alumni", "anniversary", "annual review",
    "apply to", "around campus", "best of", "campus life", "centenary lectures",
    "challenge", "ceremony", "colloquium", "commencement", "competition",
    "conference", "congregation", "convocation", "conversation with", "covid",
    "departmental day", "election", "episode", "event recordings", "events",
    "family weekend", "forum", "graduation", "groupe calcul", "help sessions",
    "heures avec", "highlights", "homework, exams", "homecoming",
    "information session", "interview", "lecture series", "live clips",
    "meeting", "minutes to change", "orientation", "playlist", "programme",
    "programs", "promo", "promotional", "recap", "research at", "reunion",
    "season ", "seminar", "special talks", "stories", "student life",
    "student spotlight", "student lectures", "symposium", "teaser", "trailer",
    "video series", "workshop", "year in review", "\" series",
    "colóquio", "comunauté", "conferência", "conférence", "encuentro",
]
frag_clause = " AND ".join([f"c.title NOT ILIKE '%{f}%'" for f in fragments])

cur.execute(f"""
    SELECT c.title FROM courses c
    WHERE c.is_published = TRUE
      AND c.has_video_lectures = TRUE
      AND c.total_videos > 0
      AND c.source_key != 'nptel'
      AND EXISTS (SELECT 1 FROM videos v WHERE v.course_id = c.id)
      AND c.title NOT LIKE '#%'
      AND c.title NOT LIKE '@%'
      AND ({frag_clause})
""")
titles = [r[0] for r in cur.fetchall()]

cur.execute("SELECT slug FROM subjects ORDER BY slug")
all_subjects = [r[0] for r in cur.fetchall()]

counts = {}
for slug in all_subjects:
    cnt = sum(1 for t in titles if t and strict_subject_matches_title(t, slug))
    if cnt > 0:
        counts[slug] = cnt

out_dir = os.path.join(os.path.dirname(__file__), "..", "web", "src", "data")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "subject-counts.json")
with open(out_path, "w") as f:
    json.dump(counts, f, indent=2)
print(f"Updated subject-counts.json: {len(counts)} subjects")

# Also update subject_catalog_counts table
from app.subject_counts import STRICT_COUNT_POLICY_VERSION

cur.execute("SELECT id, slug FROM subjects")
db_subjects = cur.fetchall()

for sid, slug in db_subjects:
    phrases = strict_subject_phrases(slug)
    if not phrases:
        cnt = 0
    else:
        parts = []
        params = []
        for p in phrases:
            parts.append("(c.title ILIKE %s AND c.title NOT ILIKE %s)")
            params.extend([f"%{p}%", f"% | %{p}%"])
        where = " OR ".join(parts)
        cur.execute(f"""
            SELECT COUNT(*) FROM courses c
            WHERE c.is_published = true AND c.has_video_lectures = true
            AND c.total_videos > 0 AND c.source_key != 'nptel'
            AND EXISTS (SELECT 1 FROM videos WHERE course_id = c.id)
            AND ({where})
        """, params)
        cnt = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO subject_catalog_counts (id, subject_id, course_count, policy_version)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (subject_id) DO UPDATE
        SET course_count = %s, policy_version = %s
    """, (str(uuid.uuid4()), sid, cnt, STRICT_COUNT_POLICY_VERSION, cnt, STRICT_COUNT_POLICY_VERSION))

conn.commit()
print(f"Updated subject_catalog_counts: {len(db_subjects)} subjects")

cur.close()
conn.close()
print("\nDone!")
