#!/usr/bin/env python
"""Direct loader — uses print(), no logging, hardcoded paths for debugging."""
import csv
import os
import re
import sys
import uuid

print("Starting...", flush=True)

try:
    import psycopg2
    import psycopg2.extras
    print("psycopg2 imported OK", flush=True)
except Exception as e:
    print(f"IMPORT ERROR psycopg2: {e}", flush=True)
    sys.exit(1)

try:
    from slugify import slugify
    print("slugify imported OK", flush=True)
except Exception as e:
    print(f"IMPORT ERROR slugify: {e}", flush=True)
    sys.exit(1)

CSV_PATH = os.environ.get(
    "OCW_MIT_CSV",
    r"C:\Users\Jorge DeGuzeman\Desktop\code-projects\Courses\MIT Course List Master - MIT Course List Master.csv"
)
DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://ocw:ocwpassword@127.0.0.1:5432/opencourseware"
).replace("postgresql+asyncpg://", "postgresql://")

print(f"CSV: {CSV_PATH}", flush=True)
print(f"DB:  {DB_URL}", flush=True)
print(f"CSV exists: {os.path.exists(CSV_PATH)}", flush=True)


def parse_level(raw):
    raw = raw.strip().lower()
    if "grad" in raw:
        return "graduate"
    if "under" in raw or "ug" in raw:
        return "undergraduate"
    if "professional" in raw:
        return "professional"
    return "other"


def extract_year(url):
    m = re.search(r"(\d{4})", url)
    return int(m.group(1)) if m else None


def extract_semester(url):
    for s in ("fall", "spring", "summer", "iap", "january"):
        if s in url.lower():
            return s.capitalize()
    return None


print("Reading CSV...", flush=True)
courses = []
seen_slugs = set()
dept_name = None

try:
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        print(f"CSV columns: {reader.fieldnames}", flush=True)
        for row in reader:
            raw_title  = row.get("Course Title",   "").strip()
            raw_url    = row.get("Course URL",     "").strip()
            raw_level  = row.get("Course Level",   "").strip()
            raw_number = row.get("Course Number",  "").strip()
            raw_video  = row.get("Video Lectures", "").strip()
            raw_notes  = row.get("Lecture Notes",  "").strip()
            raw_exams  = row.get("Exams",          "").strip()

            if not raw_title:
                continue
            if not raw_url and re.match(r"^\d+$", raw_number):
                dept_name = re.sub(r"^Course \d+ - ", "", raw_title)
                continue
            if not raw_url:
                continue

            base_slug = slugify(f"{raw_title} mit")
            slug = base_slug
            counter = 2
            while slug in seen_slugs:
                slug = f"{base_slug}-{counter}"
                counter += 1
            seen_slugs.add(slug)

            courses.append({
                "title":           raw_title,
                "source_url":      raw_url,
                "slug":            slug,
                "course_number":   raw_number or None,
                "level":           parse_level(raw_level),
                "has_video":       bool(raw_video),
                "has_notes":       bool(raw_notes),
                "has_exams":       bool(raw_exams),
                "notes_url":       raw_notes or None,
                "exams_url":       raw_exams or None,
                "year":            extract_year(raw_url),
                "semester":        extract_semester(raw_url),
                "dept_name":       dept_name,
            })
except Exception as e:
    print(f"CSV ERROR: {e}", flush=True)
    import traceback; traceback.print_exc()
    sys.exit(1)

print(f"Parsed {len(courses)} courses", flush=True)

print("Connecting to DB...", flush=True)
try:
    conn = psycopg2.connect(DB_URL, connect_timeout=10)
    conn.autocommit = False
    cur = conn.cursor()
    print("Connected!", flush=True)
except Exception as e:
    print(f"DB CONNECT ERROR: {e}", flush=True)
    sys.exit(1)

try:
    # University
    cur.execute("""
        INSERT INTO universities (id, name, slug, source_key, website, country)
        VALUES (%s, 'Massachusetts Institute of Technology', 'mit', 'mit_ocw',
                'https://ocw.mit.edu', 'US')
        ON CONFLICT (slug) DO NOTHING
    """, (str(uuid.uuid4()),))
    cur.execute("SELECT id FROM universities WHERE slug = 'mit'")
    uni_id = cur.fetchone()[0]
    print(f"University id: {uni_id}", flush=True)

    # Departments
    dept_names = list({c["dept_name"] for c in courses if c["dept_name"]})
    print(f"Inserting {len(dept_names)} departments...", flush=True)
    for dn in dept_names:
        dept_slug = slugify(f"{dn} mit")
        cur.execute("SELECT id FROM departments WHERE slug = %s", (dept_slug,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO departments (id, university_id, name, slug) VALUES (%s,%s,%s,%s)",
                (str(uuid.uuid4()), uni_id, dn, dept_slug)
            )
    cur.execute("SELECT name, id FROM departments WHERE university_id = %s", (uni_id,))
    dept_map = {r[0]: r[1] for r in cur.fetchall()}
    print(f"Departments ready: {len(dept_map)}", flush=True)

    # Courses bulk insert
    rows = [
        (
            str(uuid.uuid4()), uni_id,
            dept_map.get(c["dept_name"]) if c["dept_name"] else None,
            c["course_number"], c["title"], c["slug"],
            c["level"], c["source_url"], "mit_ocw",
            c["has_video"], c["has_notes"], c["has_exams"],
            c["notes_url"], c["exams_url"],
            c["year"], c["semester"],
            0, 0, 0,
        )
        for c in courses
    ]
    print(f"Bulk inserting {len(rows)} courses...", flush=True)
    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO courses (
            id, university_id, department_id, course_number, title, slug,
            level, source_url, source_key,
            has_video_lectures, has_lecture_notes, has_exams,
            lecture_notes_url, exams_url, year, semester,
            total_videos, total_duration_seconds, view_count
        ) VALUES %s ON CONFLICT (slug) DO NOTHING
        """,
        rows,
        template=(
            "(%s,%s,%s,%s,%s,%s,"
            " %s::courselevel,%s,%s,"
            " %s,%s,%s,"
            " %s,%s,%s,%s,"
            " %s,%s,%s)"
        ),
        page_size=500,
    )
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM courses")
    total_courses = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM departments")
    total_depts = cur.fetchone()[0]
    print(f"SUCCESS! Courses: {total_courses} | Departments: {total_depts}", flush=True)

except Exception as e:
    conn.rollback()
    print(f"DB ERROR: {e}", flush=True)
    import traceback; traceback.print_exc()
    sys.exit(1)
finally:
    cur.close()
    conn.close()
