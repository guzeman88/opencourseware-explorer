#!/usr/bin/env python
"""Main entry point for running all scrapers."""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

load_dotenv()

# Allow importing from backend app
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from scrapers import SCRAPER_MAP, MITOCWScraper
from scrapers.youtube_api import YouTubeAPIClient
from pipeline.ingester import DataIngester

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://ocw:ocwpass@localhost:5432/opencourseware",
)
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
MIT_CSV = os.environ.get(
    "OCW_MIT_CSV",
    str(Path(__file__).parent.parent / "MIT Course List Master - MIT Course List Master.csv"),
)


async def run_scraper(source: str, db) -> dict:
    """Run a single scraper by source key and ingest results. Returns count dict."""
    cls = SCRAPER_MAP.get(source)
    if cls is None:
        raise ValueError(f"Unknown scraper: {source!r}. Available: {list(SCRAPER_MAP)}")

    kwargs = {}
    if source == "mit_ocw" and Path(MIT_CSV).exists():
        kwargs["csv_path"] = MIT_CSV

    async with cls(**kwargs) as scraper:
        logger.info("Starting %s scraper...", source)
        result = scraper.load_from_csv(MIT_CSV) if source == "mit_ocw" and Path(MIT_CSV).exists() else await scraper.scrape()

        # Enrich YouTube playlists
        if YOUTUBE_API_KEY:
            yt = YouTubeAPIClient(api_key=YOUTUBE_API_KEY, session_holder=scraper)
            for course in result.courses:
                if course.youtube_playlist_id and course.source_url not in result.videos:
                    try:
                        videos = await yt.get_playlist_videos(course.youtube_playlist_id)
                        if videos:
                            result.videos[course.source_url] = videos
                            course.has_video_lectures = True
                    except Exception as exc:
                        logger.warning(
                            "YouTube enrichment failed for %s: %s", course.title, exc
                        )

        ingester = DataIngester(db=db, youtube_api_key=YOUTUBE_API_KEY)
        stats = await ingester.ingest(result, enrich_youtube=False)
        # Videos already ingested above

        logger.info(
            "%s done: %d new courses, %d updated, %d videos",
            source,
            stats.courses_created,
            stats.courses_updated,
            stats.videos_created,
        )
        return {
            "courses": stats.courses_created,
            "videos": stats.videos_created,
        }


async def run_all_scrapers() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    # Ensure tables exist
    sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
    from app.models import Base  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sources = list(SCRAPER_MAP.keys())

    for source in sources:
        async with session_factory() as db:
            try:
                await run_scraper(source, db)
            except Exception as exc:
                logger.error("Scraper '%s' failed: %s", source, exc)

    await engine.dispose()
    logger.info("All scrapers complete.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="OCW scraper runner")
    parser.add_argument(
        "--source",
        choices=list(SCRAPER_MAP.keys()) + ["all"],
        default="all",
        help="Which scraper to run (default: all)",
    )
    args = parser.parse_args()

    if args.source == "all":
        asyncio.run(run_all_scrapers())
    else:
        async def _single():
            engine = create_async_engine(DATABASE_URL, echo=False)
            session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
            async with session_factory() as db:
                await run_scraper(args.source, db)
            await engine.dispose()

        asyncio.run(_single())
