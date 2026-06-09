import psycopg2

from mutation_guard import require_explicit_apply


DATABASE_URL = require_explicit_apply(
    "Permanently delete NPTEL courses.",
    require_delete_confirmation=True,
)
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
    SELECT source_key, COUNT(*) FROM courses
    WHERE source_key ILIKE '%nptel%'
       OR source_key ILIKE '%nptelhrd%'
       OR source_key ILIKE '%iit-bombay%'
       OR source_key ILIKE '%iit-kanpur%'
       OR source_key ILIKE '%iit-guwahati%'
       OR source_key ILIKE '%iit-madras%'
       OR source_key ILIKE '%noc-iitm%'
    GROUP BY source_key ORDER BY COUNT(*) DESC
""")
rows = cur.fetchall()
print("NPTEL source_keys found:")
for r in rows:
    print(f"  {r[0]}: {r[1]}")

cur.execute("""
    DELETE FROM courses
    WHERE source_key ILIKE '%nptel%'
       OR source_key ILIKE '%nptelhrd%'
       OR source_key ILIKE '%iit-bombay%'
       OR source_key ILIKE '%iit-kanpur%'
       OR source_key ILIKE '%iit-guwahati%'
       OR source_key ILIKE '%iit-madras%'
       OR source_key ILIKE '%noc-iitm%'
""")
print(f"Deleted {cur.rowcount} NPTEL courses")
conn.commit()

cur.execute("SELECT COUNT(*) FROM courses WHERE is_published=TRUE AND has_video_lectures=TRUE")
print(f"Published video courses remaining: {cur.fetchone()[0]}")
conn.close()
