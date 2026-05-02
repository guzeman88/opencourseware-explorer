"""NPTEL scraper — India's National Programme on Technology Enhanced Learning.

NPTEL has thousands of courses from IITs and IISc, all freely available on
YouTube. We scrape the NPTEL website for the full course catalogue.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

from slugify import slugify

from scrapers.base import BaseScraper, ScrapedCourse, ScraperResult

logger = logging.getLogger(__name__)

NPTEL_BASE = "https://nptel.ac.in"
NPTEL_API = "https://nptel.ac.in/course.html"


# Seeded high-quality NPTEL courses (all have YouTube playlists)
NPTEL_SEED_COURSES = [
    {
        "title": "Mathematics I",
        "dept": "Mathematics",
        "instructor": "Prof. S.K. Gupta",
        "source_url": "https://nptel.ac.in/courses/111/107/111107085/",
        "youtube_playlist_id": "PLbMVogVj5nJROJJlkP0UzFQZG0Q_LYOQV",
        "level": "undergraduate",
        "subjects": ["Mathematics", "Calculus"],
    },
    {
        "title": "Data Structures and Algorithms",
        "dept": "Computer Science",
        "instructor": "Prof. Naveen Garg",
        "source_url": "https://nptel.ac.in/courses/106/102/106102064/",
        "youtube_playlist_id": "PLBF3763AF2452C8C6",
        "level": "undergraduate",
        "subjects": ["Data Structures", "Algorithms", "Computer Science"],
    },
    {
        "title": "Programming in Java",
        "dept": "Computer Science",
        "instructor": "Prof. Debasis Samanta",
        "source_url": "https://nptel.ac.in/courses/106/105/106105191/",
        "youtube_playlist_id": "PLJ5C_6qdAvBFMAko7ENe2EWjH4t-rMaGd",
        "level": "undergraduate",
        "subjects": ["Java", "Programming", "Computer Science"],
    },
    {
        "title": "Introduction to Machine Learning",
        "dept": "Computer Science",
        "instructor": "Prof. Balaraman Ravindran",
        "source_url": "https://nptel.ac.in/courses/106/106/106106139/",
        "youtube_playlist_id": "PLyqSpQzTE6M9gCgajvQbc68Hk_JKGBAYT",
        "level": "graduate",
        "subjects": ["Machine Learning", "Artificial Intelligence"],
    },
    {
        "title": "Deep Learning",
        "dept": "Computer Science",
        "instructor": "Prof. Mitesh M. Khapra",
        "source_url": "https://nptel.ac.in/courses/106/106/106106184/",
        "youtube_playlist_id": "PLyqSpQzTE6M-SISTunGRBRiZk7opYBf_K",
        "level": "graduate",
        "subjects": ["Deep Learning", "Neural Networks", "Machine Learning"],
    },
    {
        "title": "Database Management System",
        "dept": "Computer Science",
        "instructor": "Prof. Partha Pratim Das",
        "source_url": "https://nptel.ac.in/courses/106/105/106105177/",
        "youtube_playlist_id": "PL3bGLnkkGnuV6MQr_WX6GTgAe8YGb6nJV",
        "level": "undergraduate",
        "subjects": ["Databases", "SQL", "Computer Science"],
    },
    {
        "title": "Theory of Computation",
        "dept": "Computer Science",
        "instructor": "Prof. Somenath Biswas",
        "source_url": "https://nptel.ac.in/courses/106/104/106104028/",
        "youtube_playlist_id": "PLbMVogVj5nJTZOFjQCMXSz-CilBVIBMtn",
        "level": "undergraduate",
        "subjects": ["Theory of Computation", "Automata", "Computer Science"],
    },
    {
        "title": "Operating System Concepts",
        "dept": "Computer Science",
        "instructor": "Prof. Chester Rebeiro",
        "source_url": "https://nptel.ac.in/courses/106/106/106106144/",
        "youtube_playlist_id": "PLXj4XH7LcRfBDcuaLMBb9CuGNOhHOGMJW",
        "level": "undergraduate",
        "subjects": ["Operating Systems", "Computer Science"],
    },
    {
        "title": "Computer Networks and Internet Protocol",
        "dept": "Computer Science",
        "instructor": "Prof. Saahil Bhatt",
        "source_url": "https://nptel.ac.in/courses/106/105/106105183/",
        "youtube_playlist_id": "PL3bGLnkkGnuWDpQnCkLiSbPfBPFoJwbL0",
        "level": "undergraduate",
        "subjects": ["Computer Networks", "Networking"],
    },
    {
        "title": "Probability and Statistics",
        "dept": "Mathematics",
        "instructor": "Prof. Somesh Kumar",
        "source_url": "https://nptel.ac.in/courses/111/105/111105041/",
        "youtube_playlist_id": "PLbMVogVj5nJQqNx0ElSk3Ip04Ofg3B6sF",
        "level": "undergraduate",
        "subjects": ["Probability", "Statistics", "Mathematics"],
    },
    {
        "title": "Discrete Mathematics",
        "dept": "Mathematics",
        "instructor": "Prof. Sudarshan Iyengar",
        "source_url": "https://nptel.ac.in/courses/111/106/111106086/",
        "youtube_playlist_id": "PLJ5C_6qdAvBGnKJOseMwIUo6ZGfY3grp_",
        "level": "undergraduate",
        "subjects": ["Discrete Mathematics", "Computer Science"],
    },
    {
        "title": "Introduction to IoT",
        "dept": "Computer Science",
        "instructor": "Prof. Sudip Misra",
        "source_url": "https://nptel.ac.in/courses/106/105/106105166/",
        "youtube_playlist_id": "PLJ5C_6qdAvBFGX9YUAXjapR-jnO-m0T5V",
        "level": "graduate",
        "subjects": ["IoT", "Embedded Systems", "Networking"],
    },
    {
        "title": "Thermodynamics: Classical to Statistical",
        "dept": "Physics",
        "instructor": "Prof. Madan Rao",
        "source_url": "https://nptel.ac.in/courses/115/106/115106102/",
        "youtube_playlist_id": "PLbMVogVj5nJQ_YJkR22GFfqjEOoNlQIRi",
        "level": "undergraduate",
        "subjects": ["Thermodynamics", "Physics"],
    },
    {
        "title": "Quantum Mechanics and Applications",
        "dept": "Physics",
        "instructor": "Prof. Ajoy Ghatak",
        "source_url": "https://nptel.ac.in/courses/115/103/115103106/",
        "youtube_playlist_id": "PLbMVogVj5nJTnLe5pHoSTpHvvVF9u9ZGO",
        "level": "graduate",
        "subjects": ["Quantum Mechanics", "Physics"],
    },
    {
        "title": "Basic Electronics",
        "dept": "Electrical Engineering",
        "instructor": "Prof. Mahesh Patil",
        "source_url": "https://nptel.ac.in/courses/117/101/117101058/",
        "youtube_playlist_id": "PLVsHp_RA5wFkbmWNpRtHpPELLbsZhb2EM",
        "level": "undergraduate",
        "subjects": ["Electronics", "Electrical Engineering"],
    },
]


class NPTELScraper(BaseScraper):
    source_key = "nptel"
    university_name = "NPTEL (IIT/IISc)"
    university_slug = "nptel"
    university_website = "https://nptel.ac.in"
    university_country = "IN"

    async def scrape(self) -> ScraperResult:
        result = ScraperResult()
        seen_slugs: set[str] = set()

        # Load seed courses
        for entry in NPTEL_SEED_COURSES:
            slug = slugify(f"{entry['title']} nptel")
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
                subjects=entry.get("subjects", []),
            )
            result.courses.append(course)

        # Try live scrape for additional courses
        try:
            additional = await self._live_scrape(seen_slugs)
            result.courses.extend(additional.courses)
        except Exception as exc:
            logger.warning("NPTEL live scrape error: %s", exc)

        logger.info("NPTEL: %d courses", len(result.courses))
        return result

    async def _live_scrape(self, seen_slugs: set[str]) -> ScraperResult:
        result = ScraperResult()
        # NPTEL course list endpoint
        url = f"{NPTEL_BASE}/course.html"
        try:
            html = await self.fetch(url)
        except Exception:
            return result

        soup = self.parse_html(html)
        for a in soup.select("a[href*='/courses/']"):
            href = a.get("href", "")
            if not href:
                continue
            full_url = href if href.startswith("http") else f"{NPTEL_BASE}{href}"
            title = a.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            slug = slugify(f"{title} nptel")
            i = 2
            while slug in seen_slugs:
                slug = f"{slug}-{i}"
                i += 1
            seen_slugs.add(slug)

            result.courses.append(
                ScrapedCourse(
                    title=title,
                    source_key=self.source_key,
                    source_url=full_url,
                    slug=slug,
                    has_video_lectures=True,
                    university_name=self.university_name,
                    university_slug=self.university_slug,
                )
            )
        return result
