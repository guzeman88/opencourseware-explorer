import psycopg2

import os as _os; DB = _os.environ.get("DATABASE_URL") or exit("ERROR: DATABASE_URL env var is required")

conn = psycopg2.connect(DB)
conn.autocommit = True
cur = conn.cursor()

# Show existing columns
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='courses' ORDER BY column_name")
cols = cur.fetchall()
print("Existing columns:")
for c in cols:
    print(f"  {c[0]:40s} {c[1]}")

existing = {c[0] for c in cols}

# Add missing columns that the backend model expects
fixes = []

if "is_published" not in existing:
    cur.execute("ALTER TABLE courses ADD COLUMN is_published BOOLEAN NOT NULL DEFAULT TRUE")
    # Set all existing rows to published=true
    cur.execute("UPDATE courses SET is_published = TRUE")
    fixes.append("added is_published (all rows set to TRUE)")

if "has_video_lectures" not in existing:
    cur.execute("ALTER TABLE courses ADD COLUMN has_video_lectures BOOLEAN NOT NULL DEFAULT FALSE")
    fixes.append("added has_video_lectures (all rows set to FALSE)")

if "view_count" not in existing:
    cur.execute("ALTER TABLE courses ADD COLUMN view_count INTEGER NOT NULL DEFAULT 0")
    fixes.append("added view_count")

if fixes:
    print("\nFixed:")
    for f in fixes:
        print(f"  {f}")
else:
    print("\nNo fixes needed - all columns exist")

# Verify
cur.execute("SELECT COUNT(*) FROM courses WHERE is_published = TRUE")
count = cur.fetchone()[0]
print(f"\nPublished courses: {count}")

cur.close()
conn.close()
print("Done.")
