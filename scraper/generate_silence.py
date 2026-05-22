#!/usr/bin/env python
"""
Generate silence timestamps for YouTube videos and store them in the DB.

Uses the YouTube Transcript API to find gaps between caption segments.
This is instant (no audio download required), works with any YouTube video
that has auto-generated or manual captions, and does not hit YouTube bot
detection issues.

Requirements:
    pip install youtube-transcript-api psycopg2-binary python-dotenv

Usage:
    cd opencourseware/scraper
    python generate_silence.py                          # all videos with no data
    python generate_silence.py --limit 100              # first 100 unprocessed
    python generate_silence.py --source mit_ocw         # one source only
    python generate_silence.py --video-id YiqIkSHSmyc  # single video by yt id
    python generate_silence.py --force                  # re-process everything
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from urllib.parse import urlparse

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

# ── Config ─────────────────────────────────────────────────────────────────────

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_GbATRcy2v8Fo@ep-gentle-cherry-an1c9y9a-pooler.c-6.us-east-1.aws.neon.tech/opencourseware?sslmode=require",
)

# Minimum gap between caption segments to count as "silence" (seconds)
SILENCE_MIN_S = 1.5

# ── DB ─────────────────────────────────────────────────────────────────────────

def get_conn():
    url = DATABASE_URL
    for prefix in ("postgresql+asyncpg://", "postgres+asyncpg://", "postgresql+psycopg://"):
        if url.startswith(prefix):
            url = "postgresql://" + url[len(prefix):]
            break
    parsed = urlparse(url)
    return psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        dbname=parsed.path.lstrip("/"),
        user=parsed.username,
        password=parsed.password,
        sslmode="require" if "neon.tech" in (parsed.hostname or "") else "prefer",
        connect_timeout=30,
    )


# ── Silence detection via transcript gaps ──────────────────────────────────────

def detect_silence(youtube_id: str) -> list[list[float]] | None:
    """
    Fetch YouTube transcript and find gaps >= SILENCE_MIN_S seconds.
    Returns [[start, end], ...] or None on error.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
    except ImportError:
        print("    [error] youtube-transcript-api not installed. Run: pip install youtube-transcript-api")
        return None

    try:
        snippets = list(YouTubeTranscriptApi().fetch(youtube_id))
    except TranscriptsDisabled:
        print(f"    [skip] transcripts disabled for {youtube_id}")
        return []
    except NoTranscriptFound:
        print(f"    [skip] no transcript found for {youtube_id}")
        return []
    except Exception as e:
        err = str(e)
        if "Could not retrieve" in err or "No transcripts" in err:
            print(f"    [skip] {err[:100]}")
            return []
        print(f"    [error] transcript fetch: {err[:120]}")
        return None

    if not snippets:
        return []

    segments: list[list[float]] = []
    for i in range(1, len(snippets)):
        prev = snippets[i - 1]
        curr = snippets[i]
        prev_end = prev.start + prev.duration
        gap = curr.start - prev_end
        if gap >= SILENCE_MIN_S:
            segments.append([round(prev_end, 3), round(curr.start, 3)])

    return segments


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate silence segments for videos")
    parser.add_argument("--limit", type=int, default=0, help="Max videos to process (0=all)")
    parser.add_argument("--source", default="", help="Filter by source_key (e.g. mit_ocw)")
    parser.add_argument("--video-id", default="", help="Process a single YouTube video ID")
    parser.add_argument("--force", action="store_true", help="Re-process videos that already have data")
    args = parser.parse_args()

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if args.video_id:
        cur.execute("SELECT id, youtube_id, title FROM videos WHERE youtube_id = %s", (args.video_id,))
        videos = cur.fetchall()
        if not videos:
            print(f"No video found with youtube_id={args.video_id}")
            sys.exit(1)
    else:
        conditions = []
        params: list = []

        if not args.force:
            conditions.append("v.silence_segments IS NULL")
        if args.source:
            conditions.append("c.source_key = %s")
            params.append(args.source)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        limit_clause = f"LIMIT {args.limit}" if args.limit > 0 else ""

        cur.execute(f"""
            SELECT v.id, v.youtube_id, v.title, c.source_key
            FROM videos v
            JOIN courses c ON c.id = v.course_id
            {where}
            ORDER BY c.source_key, v.id
            {limit_clause}
        """, params)
        videos = cur.fetchall()

    total = len(videos)
    print(f"Processing {total} video{'s' if total != 1 else ''}")
    if total == 0:
        return

    done = 0
    errors = 0

    for video in videos:
        yt_id = video["youtube_id"]
        title = video["title"][:60]
        done += 1
        print(f"[{done}/{total}] {yt_id} -- {title}")

        t0 = time.time()
        segments = detect_silence(yt_id)
        elapsed = time.time() - t0

        if segments is None:
            errors += 1
            segments = []

        with conn.cursor() as wc:
            wc.execute(
                "UPDATE videos SET silence_segments = %s WHERE id = %s",
                (json.dumps(segments), video["id"]),
            )
        conn.commit()

        total_silence = sum(e - s for s, e in segments)
        print(
            f"    -> {len(segments)} segments, "
            f"{total_silence:.1f}s silence, "
            f"took {elapsed:.1f}s"
        )

    cur.close()
    conn.close()
    print(f"\nDone. {done} processed, {errors} errors.")


if __name__ == "__main__":
    main()
