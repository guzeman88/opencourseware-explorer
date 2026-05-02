#!/usr/bin/env python
"""Fast bulk-load of MIT OCW CSV into PostgreSQL.

Reads the CSV and inserts all data in a single transaction using
SQLAlchemy core bulk operations — much faster than the ORM ingester.
"""
from __future__ import annotations

import asyncio
import csv
import logging
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from slugify import slugify
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://ocw:ocwpass@localhost:5432/opencourseware",
)
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
    engine = create_async_engine(DATABASE_URL, echo=False)

    courses = read_csv(csv_path)
    if not courses:
        logger.error("No courses parsed from CSV!")
        return

    async with engine.begin() as conn:
        # ── Upsert university ──────────────────────────────────────────────
        await conn.execute(text("""
            INSERT INTO universities (id, name, slug, source_key, website, country)
            VALUES (gen_random_uuid(), 'Massachusetts Institute of Technology', 'mit', 'mit_ocw',
                    'https://ocw.mit.edu', 'US')
            ON CONFLICT (slug) DO NOTHING
        """))
        result = await conn.execute(text("SELECT id FROM universities WHERE slug = 'mit'"))
        uni_id = result.scalar()
        logger.info("University id: %s", uni_id)

        # ── Collect unique departments ─────────────────────────────────────
        dept_names = list({c["department_name"] for c in courses if c["department_name"]})
        dept_id_map: dict[str, int] = {}
        for dept_name in dept_names:
            dept_slug = slugify(f"{dept_name} mit")
            # Check if already exists
            r = await conn.execute(text("SELECT id FROM departments WHERE slug = :slug"), {"slug": dept_slug})
            existing = r.scalar()
            if existing:
                dept_id_map[dept_name] = existing
            else:
                r2 = await conn.execute(
                    text("INSERT INTO departments (id, university_id, name, slug) VALUES (gen_random_uuid(), :uni_id, :name, :slug) RETURNING id"),
                    {"uni_id": uni_id, "name": dept_name, "slug": dept_slug}
                )
                dept_id_map[dept_name] = r2.scalar()
        logger.info("Upserted %d departments", len(dept_id_map))

        # ── Bulk insert courses ────────────────────────────────────────────
        inserted = 0
        skipped = 0
        for c in courses:
            dept_id = dept_id_map.get(c["department_name"]) if c["department_name"] else None
            try:
                await conn.execute(text("""
                    INSERT INTO courses (
                        id, university_id, department_id, course_number, title, slug,
                        level, source_url, source_key,
                        has_video_lectures, has_lecture_notes, has_exams,
                        lecture_notes_url, exams_url, year, semester,
                        total_videos, total_duration_seconds, view_count
                    ) VALUES (
                        gen_random_uuid(), :uni_id, :dept_id, :course_number, :title, :slug,
                        :level, :source_url, 'mit_ocw',
                        :has_video_lectures, :has_lecture_notes, :has_exams,
                        :lecture_notes_url, :exams_url, :year, :semester,
                        0, 0, 0
                    )
                    ON CONFLICT (slug) DO NOTHING
                """), {
                    "uni_id": uni_id,
                    "dept_id": dept_id,
                    "course_number": c["course_number"],
                    "title": c["title"],
                    "slug": c["slug"],
                    "level": c["level"],
                    "source_url": c["source_url"],
                    "has_video_lectures": c["has_video_lectures"],
                    "has_lecture_notes": c["has_lecture_notes"],
                    "has_exams": c["has_exams"],
                    "lecture_notes_url": c["lecture_notes_url"],
                    "exams_url": c["exams_url"],
                    "year": c["year"],
                    "semester": c["semester"],
                })
                inserted += 1
            except Exception as exc:
                logger.warning("Skip course '%s': %s", c["slug"], exc)
                skipped += 1

        logger.info("Done: %d inserted, %d skipped", inserted, skipped)

    await engine.dispose()


if __name__ == "__main__":
    csv_path = MIT_CSV
    if not Path(csv_path).exists():
        logger.error("CSV not found: %s", csv_path)
        sys.exit(1)
    asyncio.run(load(csv_path))
