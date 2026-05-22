#!/usr/bin/env python
"""
Generate silence timestamps for YouTube videos and store them in the DB.

Uses yt-dlp to stream audio and ffmpeg to run silencedetect analysis.
No full download needed — audio is piped directly to ffmpeg.

Requirements:
    pip install yt-dlp psycopg2-binary python-dotenv
    ffmpeg must be on PATH

Usage:
    cd opencourseware/scraper
    $env:DATABASE_URL = "postgresql://..."
    python generate_silence.py                          # all videos with no data
    python generate_silence.py --limit 100              # first 100 unprocessed
    python generate_silence.py --source mit_ocw         # one source only
    python generate_silence.py --video-id YiqIkSHSmyc  # single video by yt id
    python generate_silence.py --force                  # re-process everything

Silence detection settings:
    -40 dB  noise floor  — safe threshold that captures lecturer pauses
    0.5 s   min duration — ignore sub-500ms gaps (natural speech rhythm)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
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

# Silence detection parameters
SILENCE_DB = -40       # noise floor in dB
SILENCE_MIN_S = 0.5    # minimum silence duration (seconds)

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


# ── Silence detection ──────────────────────────────────────────────────────────

def detect_silence(youtube_id: str) -> list[list[float]] | None:
    """
    Stream audio from YouTube via yt-dlp, pipe through ffmpeg silencedetect,
    and return a list of [start, end] pairs in seconds.
    Returns None on any error.
    """
    yt_url = f"https://www.youtube.com/watch?v={youtube_id}"

    # yt-dlp: download best audio format, output to stdout
    yt_cmd = [
        "yt-dlp",
        "--quiet",
        "--no-warnings",
        "-x",                       # extract audio
        "--audio-format", "wav",    # ffmpeg-compatible
        "--audio-quality", "0",
        "-o", "-",                  # pipe to stdout
        yt_url,
    ]

    # ffmpeg: read from stdin, run silencedetect, output nothing (null sink)
    ff_cmd = [
        "ffmpeg",
        "-i", "pipe:0",             # read from yt-dlp's stdout
        "-af", f"silencedetect=n={SILENCE_DB}dB:d={SILENCE_MIN_S}",
        "-f", "null",
        "-",                        # discard output
    ]

    try:
        yt_proc = subprocess.Popen(
            yt_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        ff_proc = subprocess.Popen(
            ff_cmd,
            stdin=yt_proc.stdout,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,  # silencedetect logs to stderr
        )
        yt_proc.stdout.close()      # allow yt_proc to receive SIGPIPE if ff exits
        _, ff_stderr = ff_proc.communicate(timeout=600)
        yt_proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        print(f"    [timeout] {youtube_id}")
        try:
            ff_proc.kill()
            yt_proc.kill()
        except Exception:
            pass
        return None
    except Exception as e:
        print(f"    [error] {youtube_id}: {e}")
        return None

    if ff_proc.returncode not in (0, 1):  # 1 = no silence found, still OK
        stderr_text = ff_stderr.decode("utf-8", errors="replace")
        if "No such file" in stderr_text or "not found" in stderr_text.lower():
            print("    [error] ffmpeg not found on PATH")
            sys.exit(1)
        print(f"    [ffmpeg error] {youtube_id}: {stderr_text[-200:]}")
        return None

    return _parse_silencedetect(ff_stderr.decode("utf-8", errors="replace"))


def _parse_silencedetect(stderr: str) -> list[list[float]]:
    """
    Parse ffmpeg silencedetect output into [[start, end], ...] pairs.
    Example lines:
        [silencedetect @ 0x...] silence_start: 0.523
        [silencedetect @ 0x...] silence_end: 1.847 | silence_duration: 1.324
    """
    segments: list[list[float]] = []
    current_start: float | None = None

    for line in stderr.splitlines():
        m_start = re.search(r"silence_start:\s*([\d.]+)", line)
        m_end = re.search(r"silence_end:\s*([\d.]+)", line)
        if m_start:
            current_start = float(m_start.group(1))
        elif m_end and current_start is not None:
            end = float(m_end.group(1))
            segments.append([round(current_start, 6), round(end, 6)])
            current_start = None

    return segments


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate silence segments for videos")
    parser.add_argument("--limit", type=int, default=0, help="Max videos to process (0=all)")
    parser.add_argument("--source", default="", help="Filter by source_key (e.g. mit_ocw)")
    parser.add_argument("--video-id", default="", help="Process a single YouTube video ID")
    parser.add_argument("--force", action="store_true", help="Re-process videos that already have data")
    args = parser.parse_args()

    # Check ffmpeg available
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("ERROR: ffmpeg is not installed or not on PATH.")
        print("  Windows: winget install FFmpeg  or  choco install ffmpeg")
        print("  Mac:     brew install ffmpeg")
        sys.exit(1)

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if args.video_id:
        # Single video mode
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
        source = video.get("source_key", "")
        done += 1
        print(f"[{done}/{total}] {yt_id} — {title}")

        t0 = time.time()
        segments = detect_silence(yt_id)
        elapsed = time.time() - t0

        if segments is None:
            errors += 1
            # Store empty list so we don't retry failed videos repeatedly
            # (use --force to retry)
            segments = []

        # Store result
        with conn.cursor() as wc:
            wc.execute(
                "UPDATE videos SET silence_segments = %s WHERE id = %s",
                (json.dumps(segments), video["id"]),
            )
        conn.commit()

        total_silence = sum(e - s for s, e in segments)
        print(
            f"    → {len(segments)} segments, "
            f"{total_silence:.1f}s silence, "
            f"took {elapsed:.1f}s"
        )

    cur.close()
    conn.close()
    print(f"\nDone. {done} processed, {errors} errors.")


if __name__ == "__main__":
    main()
