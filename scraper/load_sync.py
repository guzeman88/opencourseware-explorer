#!/usr/bin/env python
"""Synchronous psycopg2 loader — no asyncio, runs in seconds on Windows."""
from __future__ import annotations

import csv
import logging
import os
import re
import uuid
from pathlib import Path

import psycopg2
import psycopg2.extras
from slugify import slugify

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Accept both asyncpg and plain postgresql:// URLs
_RAW = os.environ.get(
    "DATABASE_URL",
    "postgresql://ocw:ocwpassword@localhost:5432/opencourseware",
)
DATABASE_URL = _RAW.replace("postgresql+asyncpg://", "postgresql://")

MIT_CSV = os.environ.get(
    "OCW_MIT_CSV",
    str(Path(__file__).parent.parent / "MIT Course List Master - MIT Course List Master.csv"),
)


def _parse_level(raw: str) -> str:
    raw = raw.strip().lower()
    if "grad" in raw:
        return "graduate"
    if "under" in raw or "ug" in raw:
        return "undergraduate"
    if "professional" in raw:
        return "professional"
    return "other"


def _extract_year(url: str):
    m = re.search(r"(\d{4})", url)
    return int(m.group(1)) if m else None


def _extract_semester(url: str):
    for season in ("fall", "spring", "summer", "iap", "january"):
        if season in url.lower():
            return season.capitalize()
    return None


def read_csv(csv_path: str) -> list[dict]:
    courses: list[dict] = []
    seen_slugs: set[str] = set()
    dept_name: str | None = None

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_title  = row.get("Course Title",  "").strip()
            raw_url    = row.get("Course URL",    "").strip()
            raw_level  = row.get("Course Level",  "").strip()
            raw_number = row.get("Course Number", "").strip()
            raw_video  = row.get("Video Lectures","").strip()
            raw_notes  = row.get("Lecture Notes", "").strip()
            raw_exams  = row.get("Exams",         "").strip()

            if not raw_title:
                continue

            # Department header rows
            if not raw_url and re.match(r"^\d+$", raw_number):
                dept_name = re.sub(r"^Course \d+ - ", "", raw_title)
                continue

            if not raw_url:
                continue

            base_slug = slugify(f"{raw_title} mit")
            slug = base_slug
            counter = 2
            while slug in seen_slugs:
                year = _extract_year(raw_url)
                slug = f"{base_slug}-{year or counter}"
                counter += 1
            seen_slugs.add(slug)

            courses.append({
                "title":              raw_title,
                "source_url":         raw_url,
                "slug":               slug,
                "course_number":      raw_number or None,
                "level":              _parse_level(raw_level),
                "has_video_lectures": bool(raw_video),
                "has_lecture_notes":  bool(raw_notes),
                "has_exams":          bool(raw_exams),
                "lecture_notes_url":  raw_notes or None,
                "exams_url":          raw_exams or None,
                "year":               _extract_year(raw_url),
                "semester":           _extract_semester(raw_url),
                "department_name":    dept_name,
            })

    logger.info("Parsed %d courses from CSV", len(courses))
    return courses


def load(csv_path: str) -> None:
    courses = read_csv(csv_path)
    if not courses:
        logger.error("No courses parsed!")
        return

    logger.info("Connecting to DB...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # ── University ────────────────────────────────────────────────────
        cur.execute("""
            INSERT INTO universities (id, name, slug, source_key, website, country)
            VALUES (%s, 'Massachusetts Institute of Technology', 'mit', 'mit_ocw',
                    'https://ocw.mit.edu', 'US')
            ON CONFLICT (slug) DO NOTHING
        """, (str(uuid.uuid4()),))

        cur.execute("SELECT id FROM universities WHERE slug = 'mit'")
        uni_id = cur.fetchone()[0]
        logger.info("University id: %s", uni_id)

        # ── Departments ───────────────────────────────────────────────────
        dept_names = list({c["department_name"] for c in courses if c["department_name"]})
        for dept_name in dept_names:
            dept_slug = slugify(f"{dept_name} mit")
            cur.execute("SELECT id FROM departments WHERE slug = %s", (dept_slug,))
            row = cur.fetchone()
            if not row:
                cur.execute(
                    "INSERT INTO departments (id, university_id, name, slug) VALUES (%s, %s, %s, %s)",
                    (str(uuid.uuid4()), uni_id, dept_name, dept_slug),
                )

        cur.execute("SELECT name, id FROM departments WHERE university_id = %s", (uni_id,))
        dept_id_map = {row[0]: row[1] for row in cur.fetchall()}
        logger.info("Departments ready: %d", len(dept_id_map))

        # ── Courses (bulk executemany) ────────────────────────────────────
        course_rows = [
            (
                str(uuid.uuid4()),
                uni_id,
                dept_id_map.get(c["department_name"]) if c["department_name"] else None,
                c["course_number"],
                c["title"],
                c["slug"],
                c["level"],
                c["source_url"],
                "mit_ocw",
                c["has_video_lectures"],
                c["has_lecture_notes"],
                c["has_exams"],
                c["lecture_notes_url"],
                c["exams_url"],
                c["year"],
                c["semester"],
                0, 0, 0,
            )
            for c in courses
        ]

        psycopg2.extras.execute_values(
            cur,
            """
            INSERT INTO courses (
                id, university_id, department_id, course_number, title, slug,
                level, source_url, source_key,
                has_video_lectures, has_lecture_notes, has_exams,
                lecture_notes_url, exams_url, year, semester,
                total_videos, total_duration_seconds, view_count
            ) VALUES %s
            ON CONFLICT (slug) DO NOTHING
            """,
            course_rows,
            template=(
                "(%s, %s, %s, %s, %s, %s,"
                " %s::courselevel, %s, %s,"
                " %s, %s, %s,"
                " %s, %s, %s, %s,"
                " %s, %s, %s)"
            ),
            page_size=500,
        )

        conn.commit()

        cur.execute("SELECT COUNT(*) FROM courses")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM departments")
        dept_total = cur.fetchone()[0]
        logger.info("SUCCESS! Courses: %d | Departments: %d", total, dept_total)

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    load(MIT_CSV)
