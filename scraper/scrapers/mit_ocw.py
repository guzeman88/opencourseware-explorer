"""MIT OpenCourseWare scraper.

Reads the CSV export (which you already have) AND can live-scrape new courses
from the OCW site to pick up any courses added since the CSV was generated.

CSV columns: Course Number, Course Title, Course Level, Course URL,
             Video Lectures, Lecture Notes, Exams
"""
from __future__ import annotations

import csv
import logging
import re
from pathlib import Path
from typing import Optional

from slugify import slugify

from scrapers.base import BaseScraper, ScrapedCourse, ScraperResult

logger = logging.getLogger(__name__)

OCW_BASE = "https://ocw.mit.edu"
OCW_COURSE_LIST = f"{OCW_BASE}/search/?t=&l=&f=Lecture+Videos"


def _parse_level(raw: str) -> str:
    raw = raw.strip().lower()
    if "under" in raw or "ug" in raw:
        return "undergraduate"
    if "grad" in raw:
        return "graduate"
    if "professional" in raw:
        return "professional"
    return "other"


def _extract_year(url: str) -> Optional[int]:
    m = re.search(r"(\d{4})", url)
    if m:
        return int(m.group(1))
    return None


def _extract_semester(url: str) -> Optional[str]:
    for season in ("fall", "spring", "summer", "iap", "january"):
        if season in url.lower():
            return season.capitalize()
    return None


def _extract_subjects_from_url(url: str) -> list[str]:
    """Best-effort subject extraction from OCW URL slug."""
    # e.g. /courses/18-06-linear-algebra-fall-2011/
    m = re.search(r"/courses/([^/]+)/", url)
    if not m:
        return []
    slug_part = m.group(1)
    # Remove number prefix and year/semester suffix
    slug_part = re.sub(r"^\d+[-\d]*-", "", slug_part)
    slug_part = re.sub(r"-(fall|spring|summer|january|iap)-\d{4}$", "", slug_part, flags=re.I)
    # Convert slug to human-readable
    words = slug_part.replace("-", " ").title()
    return [words] if words else []


class MITOCWScraper(BaseScraper):
    source_key = "mit_ocw"
    university_name = "Massachusetts Institute of Technology"
    university_slug = "mit"
    university_website = "https://ocw.mit.edu"
    university_country = "US"

    def __init__(self, csv_path: Optional[str] = None, delay: float = 0.5):
        super().__init__(delay=delay)
        self.csv_path = csv_path

    # ─── CSV loader (fast, offline) ───────────────────────────────────────────

    def load_from_csv(self, csv_path: str) -> ScraperResult:
        """Parse the provided MIT OCW CSV export."""
        result = ScraperResult()
        seen_slugs: set[str] = set()
        dept_name: Optional[str] = None

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

                # Department header rows (no URL, number like "1", "2", etc.)
                if not raw_url and re.match(r"^\d+$", raw_number):
                    dept_name = raw_title
                    # Strip "Course N - " prefix
                    dept_name = re.sub(r"^Course \d+ - ", "", dept_name)
                    continue

                if not raw_url:
                    continue

                # Build slug: title + source to ensure uniqueness
                base_slug = slugify(f"{raw_title} mit")
                slug = base_slug
                counter = 2
                while slug in seen_slugs:
                    # Disambiguate with year
                    year = _extract_year(raw_url)
                    slug = f"{base_slug}-{year or counter}"
                    counter += 1
                seen_slugs.add(slug)

                subjects = _extract_subjects_from_url(raw_url)

                course = ScrapedCourse(
                    title=raw_title,
                    source_key=self.source_key,
                    source_url=raw_url,
                    slug=slug,
                    course_number=raw_number if raw_number else None,
                    level=_parse_level(raw_level),
                    has_video_lectures=bool(raw_video),
                    has_lecture_notes=bool(raw_notes),
                    has_exams=bool(raw_exams),
                    video_lectures_url=raw_video or None,
                    lecture_notes_url=raw_notes or None,
                    exams_url=raw_exams or None,
                    year=_extract_year(raw_url),
                    semester=_extract_semester(raw_url),
                    university_name=self.university_name,
                    university_slug=self.university_slug,
                    department_name=dept_name,
                    subjects=subjects,
                )
                result.courses.append(course)

        logger.info("MIT OCW CSV: loaded %d courses", len(result.courses))
        return result

    # ─── Live scrape (supplemental) ───────────────────────────────────────────

    async def scrape(self) -> ScraperResult:
        """If a CSV path is provided, load from it. Otherwise live-scrape."""
        if self.csv_path and Path(self.csv_path).exists():
            return self.load_from_csv(self.csv_path)
        return await self._live_scrape()

    async def _live_scrape(self) -> ScraperResult:
        """Scrape the OCW course catalogue live (for updates / new courses)."""
        result = ScraperResult()
        page = 1
        seen_slugs: set[str] = set()

        while True:
            url = f"{OCW_BASE}/search/?q=&page={page}&f=Lecture+Videos"
            try:
                html = await self.fetch(url)
            except Exception as exc:
                logger.error("OCW live scrape failed at page %d: %s", page, exc)
                break

            soup = self.parse_html(html)
            cards = soup.select(".card, article.course-card, .learning-resource-card")
            if not cards:
                break

            for card in cards:
                link = card.select_one("a[href*='/courses/']")
                if not link:
                    continue
                href = link.get("href", "")
                course_url = href if href.startswith("http") else f"{OCW_BASE}{href}"

                title_el = card.select_one("h3, h2, .course-title, .title")
                title = title_el.get_text(strip=True) if title_el else ""
                if not title:
                    continue

                slug = slugify(f"{title} mit")
                counter = 2
                while slug in seen_slugs:
                    slug = f"{slug}-{counter}"
                    counter += 1
                seen_slugs.add(slug)

                course = ScrapedCourse(
                    title=title,
                    source_key=self.source_key,
                    source_url=course_url,
                    slug=slug,
                    year=_extract_year(course_url),
                    semester=_extract_semester(course_url),
                    has_video_lectures=True,  # we filtered for video lectures
                    university_name=self.university_name,
                    university_slug=self.university_slug,
                    subjects=_extract_subjects_from_url(course_url),
                )
                result.courses.append(course)

            logger.info("OCW live page %d: %d courses so far", page, len(result.courses))
            page += 1

            # Safety: stop at 50 pages (~1500 courses)
            if page > 50:
                break

        return result
