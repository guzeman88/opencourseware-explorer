"""YouTube Data API v3 helpers for enriching course data with video details."""
from __future__ import annotations

import logging
import re
from typing import Optional

from scrapers.base import BaseScraper, ScrapedVideo

logger = logging.getLogger(__name__)

YT_API_BASE = "https://www.googleapis.com/youtube/v3"


def _iso8601_to_seconds(duration: str) -> int:
    """Convert ISO 8601 duration (PT1H2M3S) to total seconds."""
    match = re.match(
        r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration
    )
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


class YouTubeAPIClient:
    """Thin async wrapper around YouTube Data API v3."""

    def __init__(self, api_key: str, session_holder: BaseScraper):
        self.api_key = api_key
        self._sh = session_holder  # uses the parent scraper's session

    async def get_playlist_videos(self, playlist_id: str) -> list[ScrapedVideo]:
        """Fetch all videos in a YouTube playlist."""
        if not self.api_key:
            logger.warning("No YouTube API key; skipping playlist %s", playlist_id)
            return []

        videos: list[ScrapedVideo] = []
        page_token: Optional[str] = None
        order = 0

        while True:
            params: dict = {
                "part": "snippet,contentDetails",
                "playlistId": playlist_id,
                "maxResults": 50,
                "key": self.api_key,
            }
            if page_token:
                params["pageToken"] = page_token

            try:
                data = await self._sh.fetch_json(
                    f"{YT_API_BASE}/playlistItems", params=params
                )
            except Exception as exc:
                logger.error("YouTube API error for playlist %s: %s", playlist_id, exc)
                break

            if "error" in data:
                logger.error(
                    "YouTube API error: %s", data["error"].get("message", "Unknown")
                )
                break

            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                vid_id = snippet.get("resourceId", {}).get("videoId", "")
                if not vid_id or vid_id == "deleted":
                    continue

                videos.append(
                    ScrapedVideo(
                        youtube_id=vid_id,
                        title=snippet.get("title", ""),
                        description=snippet.get("description", ""),
                        thumbnail_url=(
                            snippet.get("thumbnails", {})
                            .get("high", {})
                            .get("url")
                        ),
                        order=order,
                        published_at=snippet.get("publishedAt"),
                    )
                )
                order += 1

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        # Enrich with video durations
        if videos:
            await self._enrich_durations(videos)

        return videos

    async def _enrich_durations(self, videos: list[ScrapedVideo]) -> None:
        """Batch-fetch durations for a list of videos (max 50 per request)."""
        if not self.api_key:
            return

        batch_size = 50
        for i in range(0, len(videos), batch_size):
            batch = videos[i : i + batch_size]
            ids = ",".join(v.youtube_id for v in batch)
            params = {
                "part": "contentDetails,statistics",
                "id": ids,
                "key": self.api_key,
            }
            try:
                data = await self._sh.fetch_json(f"{YT_API_BASE}/videos", params=params)
            except Exception as exc:
                logger.warning("Duration enrichment failed: %s", exc)
                continue

            duration_map = {}
            views_map = {}
            for item in data.get("items", []):
                vid_id = item["id"]
                duration_map[vid_id] = _iso8601_to_seconds(
                    item.get("contentDetails", {}).get("duration", "")
                )
                views_map[vid_id] = int(
                    item.get("statistics", {}).get("viewCount", 0)
                )

            for v in batch:
                if v.youtube_id in duration_map:
                    v.duration_seconds = duration_map[v.youtube_id]
                if v.youtube_id in views_map:
                    v.view_count = views_map[v.youtube_id]
