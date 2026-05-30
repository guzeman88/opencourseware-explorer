"""
Full schema sync: add missing columns and create missing tables in Neon.
"""
import psycopg2

import os as _os; DB = _os.environ.get("DATABASE_URL") or exit("ERROR: DATABASE_URL env var is required")
conn = psycopg2.connect(DB)
conn.autocommit = True
cur = conn.cursor()

def tables():
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
    return {r[0] for r in cur.fetchall()}

def cols(table):
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s", (table,))
    return {r[0] for r in cur.fetchall()}

def add(table, col, dtype):
    if col not in cols(table):
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {dtype}")
        print(f"  + {table}.{col}")

existing_tables = tables()

# ── 1. columns on existing tables ────────────────────────────────────────────

# universities — model has is_institution
add("universities", "is_institution", "BOOLEAN NOT NULL DEFAULT FALSE")

# subjects — model has parent_id (optional FK to self)
add("subjects", "parent_id", "UUID REFERENCES subjects(id)")

# ── 2. create missing tables ──────────────────────────────────────────────────

if "roadmaps" not in existing_tables:
    cur.execute("""
    CREATE TABLE roadmaps (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        university_id UUID NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
        slug VARCHAR(300) NOT NULL UNIQUE,
        title VARCHAR(500) NOT NULL,
        degree_type VARCHAR(100),
        major VARCHAR(255),
        department VARCHAR(255),
        description TEXT,
        estimated_years INTEGER,
        website_url VARCHAR(1000)
    )""")
    cur.execute("CREATE INDEX ix_roadmaps_university_id ON roadmaps(university_id)")
    cur.execute("CREATE INDEX ix_roadmaps_slug ON roadmaps(slug)")
    print("  + created table: roadmaps")

if "roadmap_entries" not in existing_tables:
    cur.execute("""
    CREATE TABLE roadmap_entries (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        roadmap_id UUID NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
        course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
        position INTEGER NOT NULL,
        course_number VARCHAR(100),
        course_title VARCHAR(500) NOT NULL,
        category VARCHAR(100),
        semester VARCHAR(50),
        year_in_program INTEGER,
        is_required BOOLEAN NOT NULL DEFAULT TRUE,
        units INTEGER,
        notes VARCHAR(500),
        subject_slug VARCHAR(200)
    )""")
    cur.execute("CREATE INDEX ix_roadmap_entries_roadmap_id ON roadmap_entries(roadmap_id)")
    cur.execute("CREATE INDEX ix_roadmap_entries_course_id ON roadmap_entries(course_id)")
    print("  + created table: roadmap_entries")

if "user_library_courses" not in existing_tables:
    cur.execute("""
    CREATE TABLE user_library_courses (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        CONSTRAINT uq_user_library_course UNIQUE (user_id, course_id)
    )""")
    cur.execute("CREATE INDEX ix_user_library_courses_user_id ON user_library_courses(user_id)")
    cur.execute("CREATE INDEX ix_user_library_courses_course_id ON user_library_courses(course_id)")
    print("  + created table: user_library_courses")

# ── 3. verify ────────────────────────────────────────────────────────────────
print("\n=== Final state ===")
print("Tables:", sorted(tables()))
cur.execute("SELECT COUNT(*) FROM courses WHERE is_published = TRUE")
print(f"Published courses: {cur.fetchone()[0]}")

cur.close()
conn.close()
print("Done.")
