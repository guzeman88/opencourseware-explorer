from scrapers.base import BaseScraper, ScrapedCourse, ScraperResult, ScrapedVideo
from scrapers.mit_ocw import MITOCWScraper
from scrapers.yale_ocw import YaleOCWScraper
from scrapers.stanford import StanfordScraper
from scrapers.nptel import NPTELScraper
from scrapers.berkeley import BerkeleyScraper
from scrapers.harvard import HarvardScraper
from scrapers.youtube_api import YouTubeAPIClient

__all__ = [
    "BaseScraper",
    "ScrapedCourse",
    "ScraperResult",
    "ScrapedVideo",
    "MITOCWScraper",
    "YaleOCWScraper",
    "StanfordScraper",
    "NPTELScraper",
    "BerkeleyScraper",
    "HarvardScraper",
    "YouTubeAPIClient",
]

SCRAPER_MAP = {
    "mit_ocw": MITOCWScraper,
    "yale_ocw": YaleOCWScraper,
    "stanford": StanfordScraper,
    "nptel": NPTELScraper,
    "berkeley": BerkeleyScraper,
    "harvard": HarvardScraper,
}
