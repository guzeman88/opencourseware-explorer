#!/usr/bin/env python
"""
Fast catalogue loader — inserts all courses from load_all_courses.CATALOGUE
WITHOUT calling yt-dlp. Sets has_video_lectures=True for courses that have
a playlist_id; video backfill can run later.

Usage:
    python _load_catalogue_fast.py
"""
import os, sys, uuid
import psycopg2
import psycopg2.extras
from slugify import slugify

# Import the catalogue and helpers from load_all_courses
sys.path.insert(0, os.path.dirname(__file__))
from load_all_courses import (
    CATALOGUE,
    DATABASE_URL,
    LEVEL_MAP,
    upsert_university,
    upsert_department,
    upsert_subject,
    connect,
)

def make_slug(title: str, source: str, seen: set) -> str:
    base = slugify(f"{title} {source}")
    slug = base
    counter = 2
    while slug in seen:
        slug = f"{base}-{counter}"
        counter += 1
    seen.add(slug)
    return slug


def insert_course(cur, course: dict, uni_id: str, dept_id: str, slug: str):
    course_id = str(uuid.uuid4())
    level_raw = course.get("level", "other")
    level = LEVEL_MAP.get(level_raw, "other")
    playlist_id = course.get("playlist_id")

    try:
        cur.execute(
            """
            INSERT INTO courses (
                id, title, slug, level, source_key, source_url,
                thumbnail_url, instructor, year, semester,
                has_video_lectures, total_videos, youtube_playlist_id,
                university_id, department_id, course_number, description
            ) VALUES (
                %s, %s, %s, %s::courselevel, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s
            )
            ON CONFLICT (slug) DO UPDATE SET
                thumbnail_url       = COALESCE(EXCLUDED.thumbnail_url, courses.thumbnail_url),
                youtube_playlist_id = COALESCE(EXCLUDED.youtube_playlist_id, courses.youtube_playlist_id),
                has_video_lectures  = EXCLUDED.has_video_lectures OR courses.has_video_lectures,
                description         = COALESCE(EXCLUDED.description, courses.description)
            RETURNING id
            """,
            (
                course_id,
                course["title"],
                slug,
                level,
                course.get("source_key", "unknown"),
                course.get("source_url", ""),
                course.get("thumbnail_url"),
                course.get("instructor"),
                course.get("year"),
                course.get("semester"),
                bool(playlist_id),
                0,  # video_count — backfill later
                playlist_id,
                uni_id, dept_id,
                course.get("course_number"),
                course.get("description"),
            ),
        )
        row = cur.fetchone()
        return str(row[0]) if row else None
    except Exception as exc:
        print(f"  [WARN] {course['title']}: {exc}", flush=True)
        return None


def main():
    db_url = os.environ.get("DATABASE_URL", DATABASE_URL)
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    # Pre-load slugs
    cur.execute("SELECT slug FROM courses")
    seen_slugs = {r[0] for r in cur.fetchall()}

    total_inserted = 0
    total_skipped = 0

    for uni_key, uni_data in CATALOGUE.items():
        print(f"\n→ {uni_data['name']}", flush=True)
        uni_id = upsert_university(cur, uni_data)
        conn.commit()

        dept_cache = {}
        for course in uni_data["courses"]:
            course["source_key"] = uni_data.get("source_key", uni_key)
            dept_name = course.get("dept", "General")
            if dept_name not in dept_cache:
                dept_cache[dept_name] = upsert_department(cur, dept_name, uni_id)
            dept_id = dept_cache[dept_name]

            slug = make_slug(course["title"], uni_data["slug"], seen_slugs)
            c_id = insert_course(cur, course, uni_id, dept_id, slug)

            if c_id:
                # Link subjects
                for name in course.get("subjects", []):
                    if name:
                        subj_id = upsert_subject(cur, name)
                        cur.execute(
                            "INSERT INTO course_subjects (course_id, subject_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            (c_id, subj_id)
                        )
                total_inserted += 1
                print(f"  ✓ {course['title'][:60]}", flush=True)
            else:
                total_skipped += 1

        conn.commit()

    cur.close()
    conn.close()
    print(f"\nDone! Inserted: {total_inserted}, Skipped: {total_skipped}", flush=True)


if __name__ == "__main__":
    main()
