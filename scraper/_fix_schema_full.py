"""
Fix ALL schema gaps between SQLAlchemy models and the Neon database.
Run once to bring Neon in sync with the backend models.
"""
import psycopg2

DB = "postgresql://neondb_owner:npg_GbATRcy2v8Fo@ep-gentle-cherry-an1c9y9a-pooler.c-6.us-east-1.aws.neon.tech/opencourseware?sslmode=require"

conn = psycopg2.connect(DB)
conn.autocommit = True
cur = conn.cursor()

def get_columns(table):
    cur.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name=%s",
        (table,)
    )
    return {r[0] for r in cur.fetchall()}

def add_col(table, col, dtype, default=None, not_null=False):
    if col in existing[table]:
        return
    constraint = f"DEFAULT {default}" if default is not None else ""
    null_clause = "NOT NULL" if not_null else ""
    sql = f"ALTER TABLE {table} ADD COLUMN {col} {dtype} {null_clause} {constraint}".strip()
    cur.execute(sql)
    print(f"  + {table}.{col}")

tables = ["courses", "universities", "departments", "subjects", "videos",
          "roadmaps", "roadmap_courses", "scraper_jobs", "users", "library_items"]
existing = {}
for t in tables:
    try:
        existing[t] = get_columns(t)
    except Exception:
        existing[t] = set()

print("=== Fixing schema gaps ===")

# ── courses ──────────────────────────────────────────────────────────────────
add_col("courses", "is_published",    "BOOLEAN", "TRUE",  not_null=True)
# Mark all existing courses as published
if "is_published" not in get_columns("courses"):
    pass  # just added above
cur.execute("UPDATE courses SET is_published = TRUE WHERE is_published IS NULL OR is_published = FALSE")

# ── universities ─────────────────────────────────────────────────────────────
add_col("universities", "is_institution", "BOOLEAN", "FALSE", not_null=True)

# ── subjects ─────────────────────────────────────────────────────────────────
add_col("subjects", "parent_id", "UUID", default=None)

# ── roadmaps ─────────────────────────────────────────────────────────────────
add_col("roadmaps", "degree_type",      "VARCHAR(100)")
add_col("roadmaps", "major",            "VARCHAR(255)")
add_col("roadmaps", "department",       "VARCHAR(255)")
add_col("roadmaps", "description",      "TEXT")
add_col("roadmaps", "estimated_years",  "INTEGER")
add_col("roadmaps", "website_url",      "VARCHAR(1000)")

# ── roadmap_courses ──────────────────────────────────────────────────────────
add_col("roadmap_courses", "category",        "VARCHAR(100)")
add_col("roadmap_courses", "semester",        "VARCHAR(50)")
add_col("roadmap_courses", "year_in_program", "INTEGER")
add_col("roadmap_courses", "is_required",     "BOOLEAN", "TRUE", not_null=True)
add_col("roadmap_courses", "units",           "INTEGER")
add_col("roadmap_courses", "notes",           "VARCHAR(500)")
add_col("roadmap_courses", "subject_slug",    "VARCHAR(200)")

print("\n=== Verification ===")
for t in ["courses", "universities"]:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    n = cur.fetchone()[0]
    print(f"  {t}: {n} rows")

cur.execute("SELECT COUNT(*) FROM courses WHERE is_published = TRUE")
print(f"  published courses: {cur.fetchone()[0]}")

cur.close()
conn.close()
print("\nDone.")
