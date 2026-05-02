"""Stanford Engineering Everywhere + Stanford YouTube channel scraper."""
from __future__ import annotations

import logging
import re
from typing import Optional

from slugify import slugify

from scrapers.base import BaseScraper, ScrapedCourse, ScraperResult

logger = logging.getLogger(__name__)

# Stanford publishes course videos primarily on YouTube
STANFORD_COURSES = [
    {
        "title": "Machine Learning",
        "instructor": "Andrew Ng",
        "dept": "Computer Science",
        "source_url": "https://see.stanford.edu/Course/CS229",
        "youtube_playlist_id": "PLoROMvodv4rMiGQp3WXShtMGgzqpfVfbU",
        "level": "graduate",
        "year": 2018,
        "semester": "Fall",
        "subjects": ["Machine Learning", "Artificial Intelligence"],
    },
    {
        "title": "CS231n: Deep Learning for Computer Vision",
        "instructor": "Fei-Fei Li, Andrej Karpathy",
        "dept": "Computer Science",
        "source_url": "http://cs231n.stanford.edu/",
        "youtube_playlist_id": "PL3FW7Lu3i5JvHM8ljYj-zLfQRF3EO8sYv",
        "level": "graduate",
        "year": 2017,
        "semester": "Spring",
        "subjects": ["Computer Vision", "Deep Learning"],
    },
    {
        "title": "Natural Language Processing with Deep Learning",
        "instructor": "Christopher Manning",
        "dept": "Computer Science",
        "source_url": "http://web.stanford.edu/class/cs224n/",
        "youtube_playlist_id": "PLoROMvodv4rOSH4v6133s9LFPRHjEmbmJ",
        "level": "graduate",
        "year": 2021,
        "semester": "Winter",
        "subjects": ["Natural Language Processing", "Deep Learning"],
    },
    {
        "title": "Probabilistic Graphical Models",
        "instructor": "Daphne Koller",
        "dept": "Computer Science",
        "source_url": "https://see.stanford.edu/Course/CS228",
        "youtube_playlist_id": "PLzERW_Obpmv-_TkPEmCyzaJUGHtl7S01i",
        "level": "graduate",
        "year": 2012,
        "semester": "Fall",
        "subjects": ["Machine Learning", "Probability"],
    },
    {
        "title": "Algorithms: Design and Analysis Part 1",
        "instructor": "Tim Roughgarden",
        "dept": "Computer Science",
        "source_url": "https://see.stanford.edu/Course/CS161",
        "youtube_playlist_id": "PLXFMmlk03Dt7Q0xr1PIAriY5623cKiH7V",
        "level": "undergraduate",
        "year": 2018,
        "subjects": ["Algorithms", "Computer Science"],
    },
    {
        "title": "Linear Algebra and its Applications",
        "instructor": "Gilbert Strang",
        "dept": "Mathematics",
        "source_url": "https://see.stanford.edu/Course/EE263",
        "youtube_playlist_id": "PL49CF3715CB9EF31D",
        "level": "undergraduate",
        "year": 2005,
        "subjects": ["Linear Algebra", "Mathematics"],
    },
    {
        "title": "Introduction to Robotics",
        "instructor": "Oussama Khatib",
        "dept": "Computer Science",
        "source_url": "https://see.stanford.edu/Course/CS223A",
        "youtube_playlist_id": "PL65CC0384A1798ADF",
        "level": "graduate",
        "year": 2008,
        "subjects": ["Robotics", "Engineering"],
    },
    {
        "title": "iOS App Development with Swift",
        "instructor": "Various",
        "dept": "Computer Science",
        "source_url": "https://cs193p.sites.stanford.edu/",
        "youtube_playlist_id": "PLpGHT1n4-mAsxuRxVPv7kj4-dQYoC3VVu",
        "level": "undergraduate",
        "year": 2023,
        "semester": "Spring",
        "subjects": ["iOS Development", "Swift", "Mobile Development"],
    },
    {
        "title": "CS224W: Machine Learning with Graphs",
        "instructor": "Jure Leskovec",
        "dept": "Computer Science",
        "source_url": "http://web.stanford.edu/class/cs224w/",
        "youtube_playlist_id": "PLoROMvodv4rPLKxIpqhjhPgdQy7imNkDn",
        "level": "graduate",
        "year": 2021,
        "semester": "Fall",
        "subjects": ["Graph Neural Networks", "Machine Learning"],
    },
    {
        "title": "Human-Computer Interaction",
        "instructor": "Various",
        "dept": "Computer Science",
        "source_url": "https://hci.stanford.edu/courses/cs147/",
        "youtube_playlist_id": "PLLssT5z_DsK-TLR_VUEy4LjM1mfBGfWqb",
        "level": "undergraduate",
        "year": 2020,
        "subjects": ["Human-Computer Interaction", "Design"],
    },
    {
        "title": "Statistical Learning",
        "instructor": "Trevor Hastie, Rob Tibshirani",
        "dept": "Statistics",
        "source_url": "https://web.stanford.edu/~hastie/ElemStatLearn/",
        "youtube_playlist_id": "PLoROMvodv4rOzrYsAxzQyHB8lOS4teMoT",
        "level": "graduate",
        "year": 2021,
        "subjects": ["Statistics", "Machine Learning"],
    },
    {
        "title": "Databases: Relational Databases and SQL",
        "instructor": "Jennifer Widom",
        "dept": "Computer Science",
        "source_url": "https://online.stanford.edu/courses/soe-ydatabases0005-databases-relational-databases-and-sql",
        "youtube_playlist_id": "PLroEs25KGvwzmvIxYHRhoGTz9w8LeXek0",
        "level": "undergraduate",
        "year": 2019,
        "subjects": ["Databases", "SQL"],
    },
    {
        "title": "Convolutional Neural Networks for Visual Recognition",
        "instructor": "Andrej Karpathy",
        "dept": "Computer Science",
        "source_url": "http://cs231n.stanford.edu/2016/",
        "youtube_playlist_id": "PLkt2uSq6rBVctENoVBg1TpCC7OQi31AlC",
        "level": "graduate",
        "year": 2016,
        "subjects": ["Deep Learning", "Computer Vision"],
    },
]


class StanfordScraper(BaseScraper):
    source_key = "stanford"
    university_name = "Stanford University"
    university_slug = "stanford"
    university_website = "https://see.stanford.edu"
    university_country = "US"

    async def scrape(self) -> ScraperResult:
        result = ScraperResult()
        seen_slugs: set[str] = set()

        for entry in STANFORD_COURSES:
            slug = slugify(f"{entry['title']} stanford")
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
                level=entry.get("level", "other"),
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

        logger.info("Stanford: %d courses", len(result.courses))
        return result
