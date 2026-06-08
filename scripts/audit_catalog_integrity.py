from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import uuid
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import psycopg


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.catalog_eligibility import (  # noqa: E402
    POLICY_VERSION,
    EligibilityInput,
    evaluate_catalog_eligibility,
)


def psycopg_url(url: str) -> str:
    normalized = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    parts = urlsplit(normalized)
    params = dict(parse_qsl(parts.query, keep_blank_values=True))
    if "sslmode" not in params and (
        "neon.tech" in normalized.lower()
        or "railway" in normalized.lower()
        or "rlwy.net" in normalized.lower()
    ):
        params["sslmode"] = "require"
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(params), parts.fragment)
    )


def load_rows(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              c.id::text,
              c.title,
              c.source_key,
              c.is_published,
              c.has_video_lectures,
              c.youtube_playlist_id,
              c.total_videos,
              COUNT(v.id)::int AS actual_video_count
            FROM courses c
            LEFT JOIN videos v ON v.course_id = c.id
            GROUP BY c.id
            ORDER BY c.title, c.id
            """
        )
        columns = [description.name for description in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]


def decode_copy_text_line(line: bytes) -> str:
    """Decode PostgreSQL COPY text escaping back to the original JSON text."""
    value = line.decode("utf-8").removesuffix("\n")
    escapes = {
        "b": "\b",
        "f": "\f",
        "n": "\n",
        "r": "\r",
        "t": "\t",
        "v": "\v",
        "\\": "\\",
    }
    decoded: list[str] = []
    index = 0
    while index < len(value):
        char = value[index]
        if char != "\\" or index + 1 >= len(value):
            decoded.append(char)
            index += 1
            continue
        next_char = value[index + 1]
        decoded.append(escapes.get(next_char, f"\\{next_char}"))
        index += 2
    return "".join(decoded)


def load_backup_rows(path: Path) -> list[dict]:
    video_counts: Counter[str] = Counter()
    with zipfile.ZipFile(path) as archive:
        with archive.open("tables/videos.jsonl") as handle:
            for line in handle:
                video_counts[json.loads(decode_copy_text_line(line))["course_id"]] += 1

        rows = []
        with archive.open("tables/courses.jsonl") as handle:
            for line in handle:
                course = json.loads(decode_copy_text_line(line))
                rows.append(
                    {
                        "id": course["id"],
                        "title": course["title"],
                        "source_key": course["source_key"],
                        "is_published": course["is_published"],
                        "has_video_lectures": course["has_video_lectures"],
                        "youtube_playlist_id": course["youtube_playlist_id"],
                        "total_videos": course["total_videos"],
                        "actual_video_count": video_counts[course["id"]],
                    }
                )
    return sorted(rows, key=lambda row: (row["title"], row["id"]))


def evaluate_rows(rows: list[dict]) -> list[dict]:
    evaluated: list[dict] = []
    for row in rows:
        decision = evaluate_catalog_eligibility(
            EligibilityInput(
                source_key=row["source_key"],
                title=row["title"],
                is_published=row["is_published"],
                has_video_lectures=row["has_video_lectures"],
                youtube_playlist_id=row["youtube_playlist_id"],
                total_videos=row["total_videos"],
                actual_video_count=row["actual_video_count"],
            )
        )
        evaluated.append(
            {
                **row,
                "status": decision.status,
                "reasons": list(decision.reasons),
                "current_catalog_ready": decision.current_catalog_ready,
                "policy_version": POLICY_VERSION,
            }
        )
    return evaluated


def write_reports(rows: list[dict], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    json_path = output_dir / f"catalog-integrity-{stamp}.json"
    csv_path = output_dir / f"catalog-integrity-{stamp}.csv"
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "course_id",
                "title",
                "source_key",
                "status",
                "reasons",
                "current_catalog_ready",
                "is_published",
                "has_video_lectures",
                "youtube_playlist_id",
                "total_videos",
                "actual_video_count",
                "policy_version",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row["id"],
                    row["title"],
                    row["source_key"],
                    row["status"],
                    "|".join(row["reasons"]),
                    row["current_catalog_ready"],
                    row["is_published"],
                    row["has_video_lectures"],
                    row["youtube_playlist_id"] or "",
                    row["total_videos"],
                    row["actual_video_count"],
                    row["policy_version"],
                ]
            )
    return json_path, csv_path


def apply_sidecar(conn, rows: list[dict]) -> None:
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO course_catalog_eligibility
              (id, course_id, status, reasons, actual_video_count,
               current_catalog_ready, policy_version)
            VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s)
            ON CONFLICT (course_id) DO UPDATE SET
              status = EXCLUDED.status,
              reasons = EXCLUDED.reasons,
              actual_video_count = EXCLUDED.actual_video_count,
              current_catalog_ready = EXCLUDED.current_catalog_ready,
              policy_version = EXCLUDED.policy_version,
              updated_at = now()
            """,
            [
                (
                    str(uuid.uuid4()),
                    row["id"],
                    row["status"],
                    json.dumps(row["reasons"]),
                    row["actual_video_count"],
                    row["current_catalog_ready"],
                    row["policy_version"],
                )
                for row in rows
            ],
        )
    conn.commit()


def print_summary(rows: list[dict], json_path: Path, csv_path: Path) -> None:
    statuses = Counter(row["status"] for row in rows)
    reasons = Counter(reason for row in rows for reason in row["reasons"])
    print(f"Courses evaluated: {len(rows):,}")
    for status in ("eligible", "review", "excluded"):
        print(f"{status.title()}: {statuses[status]:,}")
    print(f"Current catalog-ready: {sum(row['current_catalog_ready'] for row in rows):,}")
    print("Top reasons:")
    for reason, count in reasons.most_common(12):
        print(f"  {reason}: {count:,}")
    print(f"JSON report: {json_path}")
    print(f"CSV report: {csv_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="upsert decisions into the additive sidecar; never changes course rows",
    )
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL", ""))
    parser.add_argument(
        "--backup",
        type=Path,
        help="audit a verified logical-backup ZIP instead of connecting to the database",
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "preservation" / "reports"),
    )
    args = parser.parse_args()

    if args.apply and args.backup:
        raise SystemExit("--apply requires a live database, not --backup")

    if args.backup:
        rows = evaluate_rows(load_backup_rows(args.backup))
        json_path, csv_path = write_reports(rows, Path(args.output_dir))
        print_summary(rows, json_path, csv_path)
        print("Backup shadow audit only. No database or public behavior was changed.")
        return

    if not args.database_url:
        raise SystemExit("DATABASE_URL, --database-url, or --backup is required")
    with psycopg.connect(psycopg_url(args.database_url)) as conn:
        rows = evaluate_rows(load_rows(conn))
        json_path, csv_path = write_reports(rows, Path(args.output_dir))
        print_summary(rows, json_path, csv_path)
        if args.apply:
            apply_sidecar(conn, rows)
            print("Applied sidecar decisions. Course rows and public behavior were unchanged.")
        else:
            conn.rollback()
            print("Dry run only. Re-run with --apply after reviewing the report.")


if __name__ == "__main__":
    main()
