"""Yale Open Courses scraper (oyc.yale.edu + Yale YouTube channel)."""
from __future__ import annotations

import logging
import re
from typing import Optional

from slugify import slugify

from scrapers.base import BaseScraper, ScrapedCourse, ScraperResult

logger = logging.getLogger(__name__)

YALE_OYC_BASE = "https://oyc.yale.edu"
YALE_YOUTUBE_CHANNEL = "UCcmAom-Fwdn1OhNPTI_GCJQ"  # Yale Courses channel


def _extract_year(text: str) -> Optional[int]:
    m = re.search(r"(20\d{2}|19\d{2})", text)
    return int(m.group(1)) if m else None


YALE_COURSES = [
    {
        "title": "Introduction to the Old Testament (Hebrew Bible)",
        "instructor": "Christine Hayes",
        "dept": "Religious Studies",
        "source_url": "https://oyc.yale.edu/religious-studies/rlst-145",
        "youtube_playlist_id": "PLh9mgdi4rNew731mjIZn43G_Y5otqKzJA",
        "level": "undergraduate",
        "year": 2006,
        "semester": "Fall",
    },
    {
        "title": "Introduction to the New Testament History and Literature",
        "instructor": "Dale B. Martin",
        "dept": "Religious Studies",
        "source_url": "https://oyc.yale.edu/religious-studies/rlst-152",
        "youtube_playlist_id": "PLh9mgdi4rNcWDRQUKcpzJkGCJxhZcrqeT",
        "level": "undergraduate",
        "year": 2009,
        "semester": "Spring",
    },
    {
        "title": "Death",
        "instructor": "Shelly Kagan",
        "dept": "Philosophy",
        "source_url": "https://oyc.yale.edu/philosophy/phil-176",
        "youtube_playlist_id": "PLh9mgdi4rNewbMX8FNrFOoLHzqECXMflt",
        "level": "undergraduate",
        "year": 2007,
        "semester": "Spring",
    },
    {
        "title": "Fundamentals of Physics I",
        "instructor": "Ramamurti Shankar",
        "dept": "Physics",
        "source_url": "https://oyc.yale.edu/physics/phys-200",
        "youtube_playlist_id": "PLFeEvEPtX_0S6vxxiiNPrJbLu9aK1UyoiV",
        "level": "undergraduate",
        "year": 2006,
        "semester": "Fall",
    },
    {
        "title": "Fundamentals of Physics II",
        "instructor": "Ramamurti Shankar",
        "dept": "Physics",
        "source_url": "https://oyc.yale.edu/physics/phys-201",
        "youtube_playlist_id": "PLFeEvEPtX_0S6vxxiiNPrJbLu9aK1UyoiV",
        "level": "undergraduate",
        "year": 2010,
        "semester": "Spring",
    },
    {
        "title": "Financial Markets",
        "instructor": "Robert J. Shiller",
        "dept": "Economics",
        "source_url": "https://oyc.yale.edu/economics/econ-252",
        "youtube_playlist_id": "PL8FB14A2200B87185",
        "level": "undergraduate",
        "year": 2011,
        "semester": "Spring",
    },
    {
        "title": "Introduction to Psychology",
        "instructor": "Paul Bloom",
        "dept": "Psychology",
        "source_url": "https://oyc.yale.edu/psychology/psyc-110",
        "youtube_playlist_id": "PLE323F3B6B6B03A5A",
        "level": "undergraduate",
        "year": 2007,
        "semester": "Spring",
    },
    {
        "title": "Game Theory",
        "instructor": "Ben Polak",
        "dept": "Economics",
        "source_url": "https://oyc.yale.edu/economics/econ-159",
        "youtube_playlist_id": "PL6EF60E1027E1A10B",
        "level": "undergraduate",
        "year": 2007,
        "semester": "Fall",
    },
    {
        "title": "Principles of Evolution, Ecology and Behavior",
        "instructor": "Stephen C. Stearns",
        "dept": "Biology",
        "source_url": "https://oyc.yale.edu/ecology-and-evolutionary-biology/eeb-122",
        "youtube_playlist_id": "PLF7CBA45AEBAD18B8",
        "level": "undergraduate",
        "year": 2009,
        "semester": "Spring",
    },
    {
        "title": "Frontiers and Controversies in Astrophysics",
        "instructor": "Charles Bailyn",
        "dept": "Astronomy",
        "source_url": "https://oyc.yale.edu/astronomy/astr-160",
        "youtube_playlist_id": "PLh9mgdi4rNewMbr3x-fAm7zcmOVOlVoT4",
        "level": "undergraduate",
        "year": 2007,
        "semester": "Spring",
    },
    {
        "title": "African American History: From Emancipation to the Present",
        "instructor": "Jonathan Holloway",
        "dept": "African American Studies",
        "source_url": "https://oyc.yale.edu/african-american-studies/afam-162",
        "youtube_playlist_id": "PLfVCJZxvQA2j-BRHpCDQIWrI5sZoJKPfk",
        "level": "undergraduate",
        "year": 2010,
        "semester": "Spring",
    },
    {
        "title": "Introduction to Ancient Greek History",
        "instructor": "Donald Kagan",
        "dept": "History",
        "source_url": "https://oyc.yale.edu/classics/clcv-205",
        "youtube_playlist_id": "PL023BCE5134243987",
        "level": "undergraduate",
        "year": 2007,
        "semester": "Fall",
    },
    {
        "title": "European Civilization, 1648-1945",
        "instructor": "John Merriman",
        "dept": "History",
        "source_url": "https://oyc.yale.edu/history/hist-202",
        "youtube_playlist_id": "PLh9mgdi4rNeSXcggwbSNEAqNIGpFe5i3S",
        "level": "undergraduate",
        "year": 2008,
        "semester": "Fall",
    },
    {
        "title": "The American Novel Since 1945",
        "instructor": "Amy Hungerford",
        "dept": "English",
        "source_url": "https://oyc.yale.edu/english/engl-291",
        "youtube_playlist_id": "PLh9mgdi4rNeTsz9pQjQDkfZ55cCGBKN7B",
        "level": "undergraduate",
        "year": 2008,
        "semester": "Spring",
    },
    {
        "title": "Milton",
        "instructor": "John Rogers",
        "dept": "English",
        "source_url": "https://oyc.yale.edu/english/engl-220",
        "youtube_playlist_id": "PLh9mgdi4rNeTsz9pQjQDkfZ55cCGBKN7B",
        "level": "undergraduate",
        "year": 2007,
        "semester": "Spring",
    },
]


class YaleOCWScraper(BaseScraper):
    source_key = "yale_ocw"
    university_name = "Yale University"
    university_slug = "yale"
    university_website = "https://oyc.yale.edu"
    university_country = "US"

    async def scrape(self) -> ScraperResult:
        """Yale's Open Yale Courses are well-known; return curated list plus live scrape."""
        result = ScraperResult()
        seen_slugs: set[str] = set()

        # Load curated courses
        for entry in YALE_COURSES:
            slug = slugify(f"{entry['title']} yale")
            i = 2
            while slug in seen_slugs:
                slug = f"{slug}-{i}"
                i += 1
            seen_slugs.add(slug)

            course = ScrapedCourse(
                title=entry["title"],
                source_key=self.source_key,
                source_url=entry["source_url"],
                slug=slug,
                instructor=entry.get("instructor"),
                level=entry.get("level", "undergraduate"),
                year=entry.get("year"),
                semester=entry.get("semester"),
                has_video_lectures=True,
                youtube_playlist_id=entry.get("youtube_playlist_id"),
                university_name=self.university_name,
                university_slug=self.university_slug,
                department_name=entry.get("dept"),
                subjects=[entry.get("dept", "")] if entry.get("dept") else [],
            )
            result.courses.append(course)

        # Try to scrape more from the live site
        try:
            live = await self._live_scrape(seen_slugs)
            result.courses.extend(live.courses)
        except Exception as exc:
            logger.warning("Yale live scrape failed (using curated only): %s", exc)

        logger.info("Yale OYC: %d courses", len(result.courses))
        return result

    async def _live_scrape(self, seen_slugs: set[str]) -> ScraperResult:
        result = ScraperResult()
        try:
            html = await self.fetch(YALE_OYC_BASE)
        except Exception:
            return result

        soup = self.parse_html(html)
        # OYC course links
        for a in soup.select("a[href*='/course']"):
            href = a.get("href", "")
            if not href or "/course" not in href:
                continue
            url = href if href.startswith("http") else f"{YALE_OYC_BASE}{href}"
            title = a.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            slug = slugify(f"{title} yale")
            i = 2
            while slug in seen_slugs:
                slug = f"{slug}-{i}"
                i += 1
            seen_slugs.add(slug)

            course = ScrapedCourse(
                title=title,
                source_key=self.source_key,
                source_url=url,
                slug=slug,
                has_video_lectures=True,
                university_name=self.university_name,
                university_slug=self.university_slug,
            )
            result.courses.append(course)
        return result
