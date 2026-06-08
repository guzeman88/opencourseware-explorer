import os
import psycopg2
import psycopg2.extras

DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    raise SystemExit("DATABASE_URL is required")
conn = psycopg2.connect(DB_URL)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

NPTEL = "source_key ILIKE '%nptel%' OR source_key ILIKE '%nptelhrd%' OR source_key ILIKE '%iit-%' OR source_key ILIKE '%noc-iitm%'"

cur.execute(f"""
    SELECT COUNT(*) as total,
           COUNT(*) FILTER (WHERE has_video_lectures=TRUE) as has_video,
           COUNT(*) FILTER (WHERE {NPTEL}) as nptel,
           COUNT(*) FILTER (WHERE NOT ({NPTEL})) as non_nptel,
           COUNT(*) FILTER (WHERE NOT ({NPTEL}) AND has_video_lectures=TRUE) as non_nptel_video
    FROM courses
""")
row = dict(cur.fetchone())
print("=== Summary ===")
for k, v in row.items():
    print(f"  {k}: {v}")

print("\n=== Non-NPTEL by source_key (total | video) ===")
cur.execute(f"""
    SELECT source_key, COUNT(*) as n,
           COUNT(*) FILTER (WHERE has_video_lectures=TRUE) as has_video
    FROM courses
    WHERE NOT ({NPTEL})
    GROUP BY source_key ORDER BY has_video DESC, n DESC
""")
for r in cur.fetchall():
    sk = r["source_key"]
    print(f"  {sk:<25} total={r['n']:>4}  video={r['has_video']:>4}")

cur.close()
conn.close()
