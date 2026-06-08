"""Capture a read-only preservation baseline without exposing record contents."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_API = "https://opencourseware-api.onrender.com/api/v1"
TABLES = (
    "universities",
    "departments",
    "courses",
    "videos",
    "subjects",
    "course_subjects",
    "course_subject_relevance",
    "roadmaps",
    "roadmap_entries",
    "users",
    "user_library_courses",
    "user_watch_history",
    "scraper_jobs",
)


def git_value(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
    ).strip()


def fetch_json(url: str) -> tuple[dict[str, Any], int]:
    started = time.perf_counter()
    request = urllib.request.Request(url, headers={"User-Agent": "commons-preservation/1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    return payload, round((time.perf_counter() - started) * 1000)


def public_baseline(api_url: str) -> dict[str, Any]:
    routes = {
        "courses": "/courses?page_size=1",
        "featured": "/courses/featured?page_size=1",
        "subjects": "/subjects?page_size=500&strict_counts=true",
        "universities": "/universities?page_size=1",
        "roadmaps": "/roadmaps?page_size=1",
        "discrete_mathematics": (
            "/courses?subject_slug=discrete-mathematics&sort_by=relevance"
            "&has_video_lectures=true&page_size=100"
        ),
    }
    result: dict[str, Any] = {}
    for name, path in routes.items():
        try:
            payload, elapsed_ms = fetch_json(f"{api_url.rstrip('/')}{path}")
            entry: dict[str, Any] = {"elapsed_ms": elapsed_ms}
            for field in ("total", "page", "page_size", "pages"):
                if field in payload:
                    entry[field] = payload[field]
            items = payload.get("items", [])
            entry["returned_items"] = len(items)
            if name == "subjects":
                entry["nonzero_subjects"] = sum(
                    1 for item in items if item.get("course_count", 0) > 0
                )
                entry["sample_counts"] = {
                    item["slug"]: item.get("course_count", 0)
                    for item in items
                    if item.get("slug")
                    in {"discrete-mathematics", "logic", "proof-writing", "combinatorics"}
                }
            if name == "discrete_mathematics":
                entry["zero_video_items"] = sum(
                    1 for item in items if item.get("total_videos", 0) == 0
                )
            result[name] = entry
        except Exception as exc:
            result[name] = {"error": type(exc).__name__, "message": str(exc)}
    return result


def database_baseline(database_url: str) -> dict[str, Any]:
    try:
        import psycopg
    except ImportError as exc:
        return {"error": "psycopg is unavailable", "message": str(exc)}

    url = database_url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgresql+psycopg://", "postgresql://"
    )
    result: dict[str, Any] = {"counts": {}, "integrity": {}}
    try:
        connection_context = psycopg.connect(url, connect_timeout=15)
    except Exception as exc:
        return {"error": type(exc).__name__, "message": str(exc)}

    with connection_context as connection:
        connection.execute("SET TRANSACTION READ ONLY")
        with connection.cursor() as cursor:
            for table in TABLES:
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                    result["counts"][table] = cursor.fetchone()[0]
                except psycopg.errors.UndefinedTable:
                    connection.rollback()
                    connection.execute("SET TRANSACTION READ ONLY")
                    result["counts"][table] = None

            checks = {
                "published_courses": "SELECT COUNT(*) FROM courses WHERE is_published",
                "courses_flagged_video": (
                    "SELECT COUNT(*) FROM courses WHERE has_video_lectures"
                ),
                "courses_with_zero_total_videos": (
                    "SELECT COUNT(*) FROM courses WHERE total_videos = 0"
                ),
                "flagged_video_with_zero_total": (
                    "SELECT COUNT(*) FROM courses "
                    "WHERE has_video_lectures AND total_videos = 0"
                ),
                "courses_without_video_rows": (
                    "SELECT COUNT(*) FROM courses c WHERE NOT EXISTS "
                    "(SELECT 1 FROM videos v WHERE v.course_id = c.id)"
                ),
                "total_videos_counter_sum": (
                    "SELECT COALESCE(SUM(total_videos), 0) FROM courses"
                ),
                "orphan_course_subjects": (
                    "SELECT COUNT(*) FROM course_subjects cs "
                    "LEFT JOIN courses c ON c.id = cs.course_id "
                    "LEFT JOIN subjects s ON s.id = cs.subject_id "
                    "WHERE c.id IS NULL OR s.id IS NULL"
                ),
                "orphan_library_rows": (
                    "SELECT COUNT(*) FROM user_library_courses l "
                    "LEFT JOIN users u ON u.id = l.user_id "
                    "LEFT JOIN courses c ON c.id = l.course_id "
                    "WHERE u.id IS NULL OR c.id IS NULL"
                ),
                "orphan_watch_history_rows": (
                    "SELECT COUNT(*) FROM user_watch_history h "
                    "LEFT JOIN users u ON u.id = h.user_id "
                    "LEFT JOIN courses c ON c.id = h.course_id "
                    "WHERE u.id IS NULL OR c.id IS NULL"
                ),
                "unlinked_roadmap_entries": (
                    "SELECT COUNT(*) FROM roadmap_entries WHERE course_id IS NULL"
                ),
            }
            for name, query in checks.items():
                try:
                    cursor.execute(query)
                    result["integrity"][name] = cursor.fetchone()[0]
                except psycopg.errors.UndefinedTable:
                    connection.rollback()
                    connection.execute("SET TRANSACTION READ ONLY")
                    result["integrity"][name] = None
        connection.rollback()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", default=DEFAULT_API)
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL", ""))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    captured_at = datetime.now(timezone.utc)
    output = args.output or (
        ROOT
        / "preservation"
        / "baselines"
        / f"{captured_at.strftime('%Y-%m-%dT%H-%M-%SZ')}.json"
    )
    payload = {
        "captured_at": captured_at.isoformat(),
        "git": {
            "branch": git_value("branch", "--show-current"),
            "head": git_value("rev-parse", "HEAD"),
            "status": git_value("status", "--short", "--branch"),
        },
        "public_api": public_baseline(args.api_url),
        "database": (
            database_baseline(args.database_url)
            if args.database_url
            else {"status": "not captured", "reason": "DATABASE_URL was not provided"}
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
