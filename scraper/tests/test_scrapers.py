from __future__ import annotations

import csv
import io
import os
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from scrapers.mit_ocw import MITOCWScraper, _parse_level, _extract_year, _extract_semester
from scrapers.yale_ocw import YaleOCWScraper
from scrapers.stanford import StanfordScraper
from scrapers.nptel import NPTELScraper
from scrapers.berkeley import BerkeleyScraper
from scrapers.harvard import HarvardScraper
from scrapers.youtube_api import _iso8601_to_seconds


# ─── Unit helpers ──────────────────────────────────────────────────────────────

class TestHelpers:
    def test_parse_level_undergraduate(self):
        assert _parse_level("Undergraduate") == "undergraduate"
        assert _parse_level("UG") == "undergraduate"

    def test_parse_level_graduate(self):
        assert _parse_level("Graduate") == "graduate"

    def test_parse_level_other(self):
        assert _parse_level("") == "other"
        assert _parse_level("Professional") == "professional"

    def test_extract_year(self):
        assert _extract_year("https://ocw.mit.edu/courses/18-06-fall-2011/") == 2011
        assert _extract_year("https://example.com/no-year/") is None

    def test_extract_semester(self):
        assert _extract_semester("fall-2011") == "Fall"
        assert _extract_semester("spring-2020") == "Spring"
        assert _extract_semester("no-season-here") is None

    def test_iso8601_to_seconds(self):
        assert _iso8601_to_seconds("PT1H2M3S") == 3723
        assert _iso8601_to_seconds("PT30M") == 1800
        assert _iso8601_to_seconds("PT45S") == 45
        assert _iso8601_to_seconds("") == 0
        assert _iso8601_to_seconds("INVALID") == 0


# ─── CSV loader ──────────────────────────────────────────────────────────────

class TestMITCSVLoader:
    def _make_csv(self, rows: list[dict]) -> str:
        buf = io.StringIO()
        fieldnames = ["Course Number", "Course Title", "Course Level", "Course URL",
                      "Video Lectures", "Lecture Notes", "Exams"]
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        return buf.getvalue()

    def test_basic_course(self, tmp_path: Path):
        csv_content = self._make_csv([
            {
                "Course Number": "6.006",
                "Course Title": "Introduction to Algorithms",
                "Course Level": "Undergraduate",
                "Course URL": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/",
                "Video Lectures": "https://ocw.mit.edu/courses/6-006/pages/lecture-videos",
                "Lecture Notes": "https://ocw.mit.edu/courses/6-006/pages/lecture-notes",
                "Exams": "",
            }
        ])
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)

        scraper = MITOCWScraper(csv_path=str(csv_file))
        result = scraper.load_from_csv(str(csv_file))

        assert len(result.courses) == 1
        course = result.courses[0]
        assert course.title == "Introduction to Algorithms"
        assert course.course_number == "6.006"
        assert course.level == "undergraduate"
        assert course.has_video_lectures is True
        assert course.has_lecture_notes is True
        assert course.has_exams is False
        assert course.year == 2011
        assert course.semester == "Fall"
        assert course.source_key == "mit_ocw"

    def test_department_header_skipped(self, tmp_path: Path):
        csv_content = self._make_csv([
            {
                "Course Number": "6",
                "Course Title": "Course 6 - Electrical Engineering",
                "Course Level": "",
                "Course URL": "",
                "Video Lectures": "",
                "Lecture Notes": "",
                "Exams": "",
            },
            {
                "Course Number": "6.001",
                "Course Title": "Structure and Interpretation of Computer Programs",
                "Course Level": "Undergraduate",
                "Course URL": "https://ocw.mit.edu/courses/6-001-fall-2005/",
                "Video Lectures": "",
                "Lecture Notes": "",
                "Exams": "",
            },
        ])
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)

        scraper = MITOCWScraper()
        result = scraper.load_from_csv(str(csv_file))

        # Department header row should not be included
        assert len(result.courses) == 1
        assert result.courses[0].department_name == "Electrical Engineering"

    def test_duplicate_slugs_disambiguated(self, tmp_path: Path):
        rows = [
            {
                "Course Number": "1.04",
                "Course Title": "Project Management",
                "Course Level": "Undergraduate",
                "Course URL": "https://ocw.mit.edu/courses/1-040-project-management-spring-2004/",
                "Video Lectures": "",
                "Lecture Notes": "",
                "Exams": "",
            },
            {
                "Course Number": "1.04",
                "Course Title": "Project Management",
                "Course Level": "Undergraduate",
                "Course URL": "https://ocw.mit.edu/courses/1-040-project-management-spring-2009/",
                "Video Lectures": "",
                "Lecture Notes": "",
                "Exams": "",
            },
        ]
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(self._make_csv(rows))

        scraper = MITOCWScraper()
        result = scraper.load_from_csv(str(csv_file))

        slugs = [c.slug for c in result.courses]
        assert len(set(slugs)) == len(slugs), "Duplicate slugs found!"

    def test_empty_csv(self, tmp_path: Path):
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("Course Number,Course Title,Course Level,Course URL,Video Lectures,Lecture Notes,Exams\n")
        scraper = MITOCWScraper()
        result = scraper.load_from_csv(str(csv_file))
        assert len(result.courses) == 0


# ─── Seed course scrapers ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_yale_scraper_returns_courses():
    # No network call needed — uses curated data
    async with YaleOCWScraper() as scraper:
        # Override _live_scrape to avoid real HTTP
        async def mock_live(seen):
            from scrapers.base import ScraperResult
            return ScraperResult()
        scraper._live_scrape = mock_live
        result = await scraper.scrape()
    assert len(result.courses) >= 10
    titles = [c.title for c in result.courses]
    assert any("Death" in t for t in titles)
    assert all(c.has_video_lectures for c in result.courses)


@pytest.mark.asyncio
async def test_stanford_scraper_returns_courses():
    async with StanfordScraper() as scraper:
        result = await scraper.scrape()
    assert len(result.courses) >= 5
    assert all(c.source_key == "stanford" for c in result.courses)


@pytest.mark.asyncio
async def test_nptel_scraper_returns_courses():
    async with NPTELScraper() as scraper:
        async def mock_live(seen):
            from scrapers.base import ScraperResult
            return ScraperResult()
        scraper._live_scrape = mock_live
        result = await scraper.scrape()
    assert len(result.courses) >= 10
    assert all(c.university_slug == "nptel" for c in result.courses)


@pytest.mark.asyncio
async def test_berkeley_scraper_returns_courses():
    async with BerkeleyScraper() as scraper:
        result = await scraper.scrape()
    assert len(result.courses) >= 5
    assert all(c.has_video_lectures for c in result.courses)


@pytest.mark.asyncio
async def test_harvard_scraper_returns_courses():
    async with HarvardScraper() as scraper:
        result = await scraper.scrape()
    assert len(result.courses) >= 5
    assert any("CS50" in c.title for c in result.courses)


def test_all_seeded_courses_have_slugs():
    from scrapers import SCRAPER_MAP
    import asyncio

    async def collect_all():
        all_courses = []
        for key, cls in SCRAPER_MAP.items():
            if key == "mit_ocw":
                continue
            async with cls() as scraper:
                # Stub out live scrapes
                if hasattr(scraper, "_live_scrape"):
                    async def noop(*a, **kw):
                        from scrapers.base import ScraperResult
                        return ScraperResult()
                    scraper._live_scrape = noop
                result = await scraper.scrape()
                all_courses.extend(result.courses)
        return all_courses

    courses = asyncio.run(collect_all())
    for c in courses:
        assert c.slug, f"Course '{c.title}' has no slug"
        assert c.title, "Course has empty title"
        assert c.source_key, f"Course '{c.title}' has no source_key"
