#!/usr/bin/env python
"""
MIT OCW direct CSV loader — reads the master CSV and inserts all courses.
Run from scraper/ directory.
Usage: py -3.13 load_mit_csv.py
"""
from __future__ import annotations
import csv
import os
import uuid
import re
import psycopg2
from slugify import slugify
from db_utils import get_connection

CSV_PATH = os.environ.get(
    "OCW_MIT_CSV",
    r"C:\Users\Jorge DeGuzeman\Desktop\code-projects\Courses\MIT Course List Master - MIT Course List Master.csv"
)


def infer_level(level_str: str) -> str:
    s = (level_str or "").lower()
    if "graduate" in s:
        return "graduate"
    if "undergraduate" in s:
        return "undergraduate"
    if "professional" in s:
        return "professional"
    return "undergraduate"


def get_or_create_university(cur) -> str:
    cur.execute("SELECT id FROM universities WHERE source_key='mit_ocw'")
    row = cur.fetchone()
    if row:
        return row[0]
    uid = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO universities (id, name, slug, website, country, source_key, description)
           VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (slug) DO UPDATE SET name=EXCLUDED.name RETURNING id""",
        (uid, "Massachusetts Institute of Technology", "mit",
         "https://ocw.mit.edu", "US", "mit_ocw",
         "MIT OpenCourseWare — free publication of MIT course materials.")
    )
    row = cur.fetchone()
    return row[0] if row else uid


def upsert_subject(cur, name: str, cache: dict) -> str:
    if name in cache:
        return cache[name]
    slug = slugify(name)
    cur.execute("SELECT id FROM subjects WHERE slug=%s", (slug,))
    row = cur.fetchone()
    if row:
        cache[name] = row[0]
        return row[0]
    sid = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO subjects (id, name, slug) VALUES (%s,%s,%s) ON CONFLICT (slug) DO UPDATE SET name=EXCLUDED.name RETURNING id",
        (sid, name, slug)
    )
    row = cur.fetchone()
    cache[name] = row[0] if row else sid
    return cache[name]


def infer_subjects(course_number: str, title: str) -> list[str]:
    """Infer subjects from course number prefix and title."""
    prefix = re.match(r'^(\d+)', course_number or "")
    if prefix:
        n = int(prefix.group(1))
        dept_map = {
            range(1, 3): ["Civil Engineering"],
            range(3, 4): ["Materials Science"],
            range(4, 5): ["Architecture"],
            range(5, 6): ["Chemistry"],
            range(6, 7): ["Electrical Engineering", "Computer Science"],
            range(7, 8): ["Biology"],
            range(8, 9): ["Physics"],
            range(9, 10): ["Neuroscience", "Cognitive Science"],
            range(10, 11): ["Chemical Engineering"],
            range(11, 12): ["Urban Planning"],
            range(12, 14): ["Earth Science"],
            range(14, 15): ["Economics"],
            range(15, 16): ["Management", "Business"],
            range(16, 17): ["Aerospace Engineering"],
            range(17, 18): ["Political Science"],
            range(18, 19): ["Mathematics"],
            range(20, 21): ["Biological Engineering"],
            range(21, 22): ["Humanities"],
            range(22, 23): ["Nuclear Engineering"],
            range(24, 25): ["Philosophy", "Linguistics"],
            range(25, 26): ["Earth Science"],
        }
        for r, subjects in dept_map.items():
            if n in r:
                return subjects
    # Keyword-based fallback
    title_l = title.lower()
    if any(w in title_l for w in ["algorithm", "programming", "software", "python", "java", "code"]):
        return ["Computer Science", "Programming"]
    if any(w in title_l for w in ["machine learning", "neural", "deep learning", "ai", "artificial"]):
        return ["Machine Learning", "Artificial Intelligence"]
    if "math" in title_l or "calculus" in title_l or "algebra" in title_l:
        return ["Mathematics"]
    if "physics" in title_l:
        return ["Physics"]
    if "chemistry" in title_l:
        return ["Chemistry"]
    if "biology" in title_l:
        return ["Biology"]
    return ["Engineering"]


def load_csv():
    print(f"Loading MIT CSV from: {CSV_PATH}", flush=True)
    conn = get_connection()
    cur = conn.cursor()

    uni_id = get_or_create_university(cur)
    conn.commit()

    # Get existing MIT courses
    cur.execute("SELECT source_url FROM courses WHERE university_id=%s", (uni_id,))
    existing_urls = {r[0] for r in cur.fetchall()}
    cur.execute("SELECT slug FROM courses")
    seen_slugs = {r[0] for r in cur.fetchall()}
    print(f"Existing MIT OCW courses in DB: {len(existing_urls)}", flush=True)

    subject_cache: dict = {}
    created = skipped = errors = 0

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"CSV has {len(rows)} rows", flush=True)

    for row in rows:
        # Support both column name patterns
        title = (row.get("Course Title") or row.get("title") or "").strip()
        source_url = (row.get("Course URL") or row.get("url") or "").strip()
        level_str = (row.get("Course Level") or row.get("level") or "").strip()
        course_number = (row.get("Course Number") or row.get("course_number") or "").strip()
        has_video = bool((row.get("Video Lectures") or "").strip())
        has_notes = bool((row.get("Lecture Notes") or "").strip())
        has_exams = bool((row.get("Exams") or "").strip())

        if not title or not source_url:
            skipped += 1
            continue

        if source_url in existing_urls:
            skipped += 1
            continue

        level = infer_level(level_str)
        subjects = infer_subjects(course_number, title)

        # Make unique slug
        base_slug = slugify(f"{title} mit")
        slug = base_slug
        i = 2
        while slug in seen_slugs:
            slug = f"{base_slug}-{i}"
            i += 1
        seen_slugs.add(slug)

        course_id = str(uuid.uuid4())
        description = f"MIT OpenCourseWare: {title}."
        if course_number:
            description += f" Course number: {course_number}."
        if level_str:
            description += f" Level: {level_str}."

        try:
            cur.execute(
                """INSERT INTO courses (
                    id, university_id, title, slug, source_key, source_url,
                    description, level, course_number, has_video_lectures,
                    has_lecture_notes, has_exams
                ) VALUES (%s,%s,%s,%s,'mit_ocw',%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (slug) DO NOTHING""",
                (course_id, uni_id, title, slug, source_url,
                 description, level, course_number or None,
                 has_video, has_notes, has_exams)
            )

            for subj in subjects[:2]:
                subj_id = upsert_subject(cur, subj, subject_cache)
                cur.execute(
                    "INSERT INTO course_subjects (id, course_id, subject_id) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                    (str(uuid.uuid4()), course_id, subj_id)
                )

            existing_urls.add(source_url)
            created += 1

            if created % 100 == 0:
                conn.commit()
                print(f"  Inserted {created} MIT courses...", flush=True)

        except Exception as e:
            conn.rollback()
            errors += 1
            if errors < 5:
                print(f"  Error: {title!r}: {e}", flush=True)

    conn.commit()
    cur.close()
    conn.close()
    print(f"\nDone! Created: {created}, Skipped: {skipped}, Errors: {errors}")


if __name__ == "__main__":
    load_csv()
