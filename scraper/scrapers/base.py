from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Polite scraping: respect robots.txt and rate limits
DEFAULT_DELAY = 0.5  # seconds between requests
DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=30)
DEFAULT_HEADERS = {
    "User-Agent": (
        "OpenCourseWare-Explorer/1.0 "
        "(Educational course aggregator; "
        "https://github.com/opencourseware-explorer)"
    )
}


@dataclass
class ScrapedCourse:
    title: str
    source_key: str
    source_url: str
    slug: str = ""
    course_number: Optional[str] = None
    description: Optional[str] = None
    level: str = "other"  # undergraduate | graduate | professional | other
    instructor: Optional[str] = None
    year: Optional[int] = None
    semester: Optional[str] = None
    thumbnail_url: Optional[str] = None
    has_video_lectures: bool = False
    has_lecture_notes: bool = False
    has_exams: bool = False
    lecture_notes_url: Optional[str] = None
    exams_url: Optional[str] = None
    video_lectures_url: Optional[str] = None
    youtube_playlist_id: Optional[str] = None
    subjects: list[str] = field(default_factory=list)
    university_name: str = ""
    university_slug: str = ""
    department_name: Optional[str] = None


@dataclass
class ScrapedVideo:
    youtube_id: str
    title: str
    order: int = 0
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    view_count: Optional[int] = None


@dataclass
class ScraperResult:
    courses: list[ScrapedCourse] = field(default_factory=list)
    videos: dict[str, list[ScrapedVideo]] = field(default_factory=dict)
    # key = course source_url, value = list of videos


class BaseScraper(ABC):
    source_key: str
    university_name: str
    university_slug: str
    university_website: str
    university_country: str = "US"

    def __init__(self, delay: float = DEFAULT_DELAY):
        self.delay = delay
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> BaseScraper:
        self._session = aiohttp.ClientSession(
            headers=DEFAULT_HEADERS,
            timeout=DEFAULT_TIMEOUT,
        )
        return self

    async def __aexit__(self, *args) -> None:
        if self._session:
            await self._session.close()

    async def fetch(self, url: str, retries: int = 3) -> str:
        """Fetch URL with retry logic and polite delay."""
        assert self._session is not None, "Use as async context manager"
        for attempt in range(retries):
            try:
                async with self._session.get(url) as resp:
                    resp.raise_for_status()
                    text = await resp.text()
                    await asyncio.sleep(self.delay)
                    return text
            except aiohttp.ClientError as exc:
                if attempt == retries - 1:
                    logger.warning("Failed to fetch %s after %d attempts: %s", url, retries, exc)
                    raise
                await asyncio.sleep(self.delay * (attempt + 1))
        return ""

    async def fetch_json(self, url: str, params: dict | None = None, retries: int = 3) -> dict:
        assert self._session is not None
        for attempt in range(retries):
            try:
                async with self._session.get(url, params=params) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    await asyncio.sleep(self.delay)
                    return data
            except (aiohttp.ClientError, Exception) as exc:
                if attempt == retries - 1:
                    logger.warning("JSON fetch failed %s: %s", url, exc)
                    raise
                await asyncio.sleep(self.delay * (attempt + 1))
        return {}

    def parse_html(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    @abstractmethod
    async def scrape(self) -> ScraperResult:
        """Run the full scrape and return structured data."""
        ...
