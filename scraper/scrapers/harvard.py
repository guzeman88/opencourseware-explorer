"""Harvard Open Learning / Extension School courses on YouTube."""
from __future__ import annotations

import logging

from slugify import slugify

from scrapers.base import BaseScraper, ScrapedCourse, ScraperResult

logger = logging.getLogger(__name__)

HARVARD_COURSES = [
    {
        "title": "CS50: Introduction to Computer Science",
        "instructor": "David J. Malan",
        "dept": "Computer Science",
        "source_url": "https://cs50.harvard.edu/x/",
        "youtube_playlist_id": "PLhQjrBD2T380F_inVRXMIHCqLaNUd7bN4",
        "level": "undergraduate",
        "year": 2023,
        "semester": "Spring",
        "subjects": ["Computer Science", "Programming", "C", "Python"],
    },
    {
        "title": "CS50P: Introduction to Programming with Python",
        "instructor": "David J. Malan",
        "dept": "Computer Science",
        "source_url": "https://cs50.harvard.edu/python/",
        "youtube_playlist_id": "PLhQjrBD2T3817j24-GogXmWqO5Q5vYy0V",
        "level": "undergraduate",
        "year": 2022,
        "subjects": ["Python", "Programming", "Computer Science"],
    },
    {
        "title": "CS50W: Web Programming with Python and JavaScript",
        "instructor": "Brian Yu",
        "dept": "Computer Science",
        "source_url": "https://cs50.harvard.edu/web/",
        "youtube_playlist_id": "PLhQjrBD2T380xvFSUmToMMzERZ3qB5Ueu",
        "level": "undergraduate",
        "year": 2020,
        "subjects": ["Web Development", "Python", "JavaScript"],
    },
    {
        "title": "CS50AI: Introduction to Artificial Intelligence with Python",
        "instructor": "Brian Yu",
        "dept": "Computer Science",
        "source_url": "https://cs50.harvard.edu/ai/",
        "youtube_playlist_id": "PLhQjrBD2T380El0MdL9dBHniqSFJiZWMa",
        "level": "undergraduate",
        "year": 2020,
        "subjects": ["Artificial Intelligence", "Python", "Machine Learning"],
    },
    {
        "title": "CS50G: Introduction to Game Development",
        "instructor": "Colton Ogden",
        "dept": "Computer Science",
        "source_url": "https://cs50.harvard.edu/games/",
        "youtube_playlist_id": "PLhQjrBD2T381Q-lRkm40LBJGHPAy1YhKv",
        "level": "undergraduate",
        "year": 2020,
        "subjects": ["Game Development", "Lua", "Python"],
    },
    {
        "title": "Justice",
        "instructor": "Michael Sandel",
        "dept": "Political Philosophy",
        "source_url": "https://justiceharvard.org/",
        "youtube_playlist_id": "PLkXkbxA6dkVQZ7MeX5grFiR_tUvniOBhv",
        "level": "undergraduate",
        "year": 2009,
        "subjects": ["Philosophy", "Ethics", "Political Science"],
    },
    {
        "title": "Science & Cooking: From Haute Cuisine to Soft Matter Science",
        "instructor": "David Weitz, Michael Brenner",
        "dept": "Applied Physics",
        "source_url": "https://online-learning.harvard.edu/course/science-cooking",
        "youtube_playlist_id": "PLQyPl6C7EwMCuFNntnbFBYIJHIHl0M7j7",
        "level": "undergraduate",
        "year": 2015,
        "subjects": ["Physics", "Chemistry", "Food Science"],
    },
    {
        "title": "Abstract Algebra",
        "instructor": "Benedict Gross",
        "dept": "Mathematics",
        "source_url": "https://www.extension.harvard.edu/academics/courses/abstract-algebra/14684",
        "youtube_playlist_id": "PLelIK3uylPMGzHBuR3hLMHnblO3buoMyd",
        "level": "undergraduate",
        "year": 2003,
        "subjects": ["Algebra", "Mathematics"],
    },
]


class HarvardScraper(BaseScraper):
    source_key = "harvard"
    university_name = "Harvard University"
    university_slug = "harvard"
    university_website = "https://online.harvard.edu"
    university_country = "US"

    async def scrape(self) -> ScraperResult:
        result = ScraperResult()
        seen_slugs: set[str] = set()

        for entry in HARVARD_COURSES:
            slug = slugify(f"{entry['title']} harvard")
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

        logger.info("Harvard: %d courses", len(result.courses))
        return result
