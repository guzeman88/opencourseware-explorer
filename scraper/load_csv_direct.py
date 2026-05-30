#!/usr/bin/env python
"""Ultra-fast loader using asyncpg directly with executemany.

Uses asyncpg's native pipelining — inserts 2563 courses in seconds.
"""
from __future__ import annotations

import asyncio
import csv
import logging
import os
import re
import uuid
from pathlib import Path

from slugify import slugify

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# asyncpg uses plain postgresql:// (not postgresql+asyncpg://)
_RAW_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://ocw:ocwpass@localhost:5432/opencourseware",
)
DATABASE_URL = _RAW_URL.replace("postgresql+asyncpg://", "postgresql://")

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
    courses = []
    seen_slugs: set[str] = set()
    dept_name = None

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_title = row.get("Course Title", "").strip()
            raw_url = row.get("Course URL", "").strip()
            raw_level = row.get("Course Level", "").strip()
            raw_number = row.get("Course Number", "").strip()
            raw_video = row.get("Video Lectures", "").strip()
            raw_notes = row.get("Lecture Notes", "").strip()
            raw_exams = row.get("Exams", "").strip()

            if not raw_title:
                continue

            # Department header rows (number but no URL)
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
                "title": raw_title,
                "source_url": raw_url,
                "slug": slug,
                "course_number": raw_number or None,
                "level": _parse_level(raw_level),
                "has_video_lectures": bool(raw_video),
                "has_lecture_notes": bool(raw_notes),
                "has_exams": bool(raw_exams),
                "lecture_notes_url": raw_notes or None,
                "exams_url": raw_exams or None,
                "year": _extract_year(raw_url),
                "semester": _extract_semester(raw_url),
                "department_name": dept_name,
            })

    logger.info("Parsed %d courses from CSV", len(courses))
    return courses


async def load(csv_path: str) -> None:
    import asyncpg  # type: ignore

    courses = read_csv(csv_path)
    if not courses:
        logger.error("No courses parsed from CSV!")
        return

    logger.info("Connecting to %s", DATABASE_URL)
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        async with conn.transaction():
            # ── University ─────────────────────────────────────────────────
            await conn.execute("""
                INSERT INTO universities (id, name, slug, source_key, website, country)
                VALUES ($1, 'Massachusetts Institute of Technology', 'mit', 'mit_ocw',
                        'https://ocw.mit.edu', 'US')
                ON CONFLICT (slug) DO NOTHING
            """, uuid.uuid4())

            uni_id = await conn.fetchval(
                "SELECT id FROM universities WHERE slug = 'mit'"
            )
            logger.info("University id: %s", uni_id)

            # ── Departments ────────────────────────────────────────────────
            dept_names = list({c["department_name"] for c in courses if c["department_name"]})
            for dept_name in dept_names:
                dept_slug = slugify(f"{dept_name} mit")
                existing = await conn.fetchval(
                    "SELECT id FROM departments WHERE slug = $1", dept_slug
                )
                if not existing:
                    await conn.execute(
                        "INSERT INTO departments (id, university_id, name, slug) "
                        "VALUES ($1, $2, $3, $4)",
                        uuid.uuid4(), uni_id, dept_name, dept_slug,
                    )

            dept_rows = await conn.fetch(
                "SELECT name, id FROM departments WHERE university_id = $1", uni_id
            )
            dept_id_map = {row["name"]: row["id"] for row in dept_rows}
            logger.info("Departments ready: %d", len(dept_id_map))

            # ── Courses (bulk via executemany) ────────────────────────────
            course_params = [
                (
                    uuid.uuid4(),
                    uni_id,
                    dept_id_map.get(c["department_name"]) if c["department_name"] else None,
                    c["course_number"],
                    c["title"],
                    c["slug"],
                    c["level"],       # cast to courselevel enum below
                    c["source_url"],
                    "mit_ocw",
                    c["has_video_lectures"],
                    c["has_lecture_notes"],
                    c["has_exams"],
                    c["lecture_notes_url"],
                    c["exams_url"],
                    c["year"],
                    c["semester"],
                    0,   # total_videos
                    0,   # total_duration_seconds
                    0,   # view_count
                )
                for c in courses
            ]

            await conn.executemany("""
                INSERT INTO courses (
                    id, university_id, department_id, course_number, title, slug,
                    level, source_url, source_key,
                    has_video_lectures, has_lecture_notes, has_exams,
                    lecture_notes_url, exams_url, year, semester,
                    total_videos, total_duration_seconds, view_count
                ) VALUES (
                    $1, $2, $3, $4, $5, $6,
                    $7::courselevel, $8, $9,
                    $10, $11, $12,
                    $13, $14, $15, $16,
                    $17, $18, $19
                )
                ON CONFLICT (slug) DO NOTHING
            """, course_params)

            count = await conn.fetchval("SELECT COUNT(*) FROM courses")
            logger.info("Done! Total courses in DB: %d", count)

    finally:
        await conn.close()


if __name__ == "__main__":
    import sys
    # asyncpg spins on Windows ProactorEventLoop — use SelectorEventLoop instead
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(load(MIT_CSV))
