"""Generate web/src/data/subject-counts.json using strict_subject_title_condition
(SQL ILIKE matching via strict_subject_phrases).

This matches what fetchStrictSubjectCourses produces — the function the deployed
subject detail page actually uses. Both pages now show the same number.

Run whenever course data changes, then commit subject-counts.json and redeploy.
"""
import json, os, sys

import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

DB = os.environ.get("DATABASE_URL", "")
if not DB:
    print("ERROR: DATABASE_URL not set.")
    sys.exit(1)
DB = DB.replace("postgresql+asyncpg://", "postgresql://")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from app.subject_matching import strict_subject_phrases

conn = psycopg2.connect(DB, connect_timeout=15, sslmode="require")
cur = conn.cursor()

cur.execute("SELECT slug FROM subjects ORDER BY slug")
subjects = [r[0] for r in cur.fetchall()]

counts = {}
for slug in subjects:
    phrases = strict_subject_phrases(slug)
    if not phrases:
        continue
    parts = []
    params = []
    for p in phrases:
        parts.append("(c.title ILIKE %s AND c.title NOT ILIKE %s)")
        params.extend(["%" + p + "%", "% | %" + p + "%"])
    where = " OR ".join(parts)
    cur.execute(
        "SELECT COUNT(*) FROM courses c"
        " WHERE c.is_published = true AND c.has_video_lectures = true"
        " AND c.total_videos > 0 AND c.source_key != 'nptel'"
        " AND EXISTS (SELECT 1 FROM videos WHERE course_id = c.id)"
        " AND (" + where + ")",
        params,
    )
    cnt = cur.fetchone()[0]
    if cnt > 0:
        counts[slug] = cnt

cur.close()
conn.close()

out_dir = os.path.join(os.path.dirname(__file__), "..", "web", "src", "data")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "subject-counts.json")
with open(out_path, "w") as f:
    json.dump(counts, f, indent=2)

print(f"Wrote {len(counts)} subject counts to {out_path}")
print()
for s in ["calculus", "machine-learning", "physics", "algorithms"]:
    print(f"  {s}: {counts.get(s, 0)}")
