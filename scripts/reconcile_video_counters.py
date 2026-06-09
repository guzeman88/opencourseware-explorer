"""Reconcile course video counters only where preserved video rows exist."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import psycopg

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_catalog_integrity import psycopg_url  # noqa: E402


LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def ensure_safe_target(database_url: str, allow_remote: bool) -> None:
    host = urlsplit(psycopg_url(database_url)).hostname
    if not allow_remote and host not in LOCAL_HOSTS:
        raise SystemExit(
            f"Refusing remote target {host!r}. "
            "Use --allow-remote only after a verified backup and review."
        )


def load_mismatches(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              c.id::text,
              c.title,
              c.total_videos,
              COUNT(v.id)::int AS actual_video_count
            FROM courses c
            JOIN videos v ON v.course_id = c.id
            GROUP BY c.id, c.title, c.total_videos
            HAVING c.total_videos <> COUNT(v.id)
            ORDER BY c.title, c.id
            """
        )
        return [
            {
                "course_id": row[0],
                "title": row[1],
                "stored_total_videos": row[2],
                "actual_video_count": row[3],
            }
            for row in cur.fetchall()
        ]


def write_report(rows: list[dict], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    path = output_dir / f"video-counter-mismatches-{stamp}.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "course_id",
                "title",
                "stored_total_videos",
                "actual_video_count",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    return path


def apply_mismatches(conn, rows: list[dict]) -> int:
    with conn.cursor() as cur:
        cur.executemany(
            """
            UPDATE courses
            SET total_videos = %s, updated_at = now()
            WHERE id = %s
              AND total_videos = %s
            """,
            [
                (
                    row["actual_video_count"],
                    row["course_id"],
                    row["stored_total_videos"],
                )
                for row in rows
            ],
        )
        changed = cur.rowcount
    conn.commit()
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--allow-remote", action="store_true")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL", ""))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "preservation" / "reports",
    )
    args = parser.parse_args()

    if not args.database_url:
        raise SystemExit("DATABASE_URL or --database-url is required.")
    if args.apply:
        ensure_safe_target(args.database_url, args.allow_remote)

    with psycopg.connect(psycopg_url(args.database_url)) as conn:
        rows = load_mismatches(conn)
        report = write_report(rows, args.output_dir)
        print(f"Verified-row counter mismatches: {len(rows):,}")
        print(f"Report: {report}")
        if args.apply:
            changed = apply_mismatches(conn, rows)
            print(f"Applied counter updates: {changed:,}")
        else:
            conn.rollback()
            print("Dry run only. Courses without video rows were intentionally preserved.")


if __name__ == "__main__":
    main()
