from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import psycopg


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
for path in (ROOT, BACKEND):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.catalog_eligibility import EligibilityInput, evaluate_catalog_eligibility  # noqa: E402
from app.subject_counts import (  # noqa: E402
    MIN_SUBJECT_RELEVANCE_SCORE,
    STRICT_COUNT_POLICY_VERSION,
)
from app.subject_matching import strict_subject_matches_title  # noqa: E402
from scripts.audit_catalog_integrity import decode_copy_text_line, psycopg_url  # noqa: E402


def load_backup(path: Path) -> tuple[list[dict], list[dict], dict[str, set[str]]]:
    with zipfile.ZipFile(path) as archive:
        subjects = [
            json.loads(decode_copy_text_line(line))
            for line in archive.open("tables/subjects.jsonl")
        ]
        video_counts: dict[str, int] = {}
        for line in archive.open("tables/videos.jsonl"):
            course_id = json.loads(decode_copy_text_line(line))["course_id"]
            video_counts[course_id] = video_counts.get(course_id, 0) + 1
        courses = []
        for line in archive.open("tables/courses.jsonl"):
            course = json.loads(decode_copy_text_line(line))
            actual_video_count = video_counts.get(course["id"], 0)
            decision = evaluate_catalog_eligibility(
                EligibilityInput(
                    source_key=course["source_key"],
                    title=course["title"],
                    is_published=course["is_published"],
                    has_video_lectures=course["has_video_lectures"],
                    youtube_playlist_id=course["youtube_playlist_id"],
                    total_videos=course["total_videos"],
                    actual_video_count=actual_video_count,
                )
            )
            if decision.current_catalog_ready:
                courses.append({"id": course["id"], "title": course["title"]})
    return courses, subjects, {}


def load_database(conn) -> tuple[list[dict], list[dict], dict[str, set[str]]]:
    with conn.cursor() as cur:
        cur.execute("SELECT id::text, slug, name FROM subjects ORDER BY slug")
        subjects = [
            {"id": row[0], "slug": row[1], "name": row[2]} for row in cur.fetchall()
        ]
        cur.execute(
            """
            SELECT c.id::text, c.title, c.source_key, c.is_published,
                   c.has_video_lectures, c.youtube_playlist_id, c.total_videos,
                   COUNT(v.id)::int
            FROM courses c
            LEFT JOIN videos v ON v.course_id = c.id
            GROUP BY c.id
            """
        )
        courses = []
        for row in cur.fetchall():
            decision = evaluate_catalog_eligibility(
                EligibilityInput(
                    source_key=row[2],
                    title=row[1],
                    is_published=row[3],
                    has_video_lectures=row[4],
                    youtube_playlist_id=row[5],
                    total_videos=row[6],
                    actual_video_count=row[7],
                )
            )
            if decision.current_catalog_ready:
                courses.append({"id": row[0], "title": row[1]})
        cur.execute("SELECT to_regclass('public.course_subject_relevance')")
        relevance_by_subject: dict[str, set[str]] = {}
        if cur.fetchone()[0] is not None:
            cur.execute(
                """
                SELECT subject_id::text, course_id::text
                FROM course_subject_relevance
                WHERE score >= %s
                """,
                (MIN_SUBJECT_RELEVANCE_SCORE,),
            )
            for subject_id, course_id in cur.fetchall():
                relevance_by_subject.setdefault(subject_id, set()).add(course_id)
    return courses, subjects, relevance_by_subject


def build_counts(
    courses: list[dict],
    subjects: list[dict],
    relevance_by_subject: dict[str, set[str]] | None = None,
) -> list[dict]:
    relevance_by_subject = relevance_by_subject or {}
    eligible_ids = {course["id"] for course in courses}
    return [
        {
            "subject_id": subject["id"],
            "slug": subject["slug"],
            "name": subject["name"],
            "course_count": (
                len(relevance_by_subject[subject["id"]] & eligible_ids)
                if subject["id"] in relevance_by_subject
                else sum(
                    1
                    for course in courses
                    if strict_subject_matches_title(course["title"], subject["slug"])
                )
            ),
            "policy_version": STRICT_COUNT_POLICY_VERSION,
        }
        for subject in subjects
    ]


def write_report(counts: list[dict], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    path = output_dir / f"subject-catalog-counts-{stamp}.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(counts[0]))
        writer.writeheader()
        writer.writerows(counts)
    return path


def apply_counts(conn, counts: list[dict]) -> None:
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO subject_catalog_counts
              (id, subject_id, course_count, policy_version)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (subject_id) DO UPDATE SET
              course_count = EXCLUDED.course_count,
              policy_version = EXCLUDED.policy_version,
              updated_at = now()
            """,
            [
                (
                    str(uuid.uuid4()),
                    row["subject_id"],
                    row["course_count"],
                    row["policy_version"],
                )
                for row in counts
            ],
        )
    conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL", ""))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "preservation" / "reports",
    )
    args = parser.parse_args()
    if args.apply and args.backup:
        raise SystemExit("--apply requires a live database")

    conn = None
    try:
        if args.backup:
            courses, subjects, relevance_by_subject = load_backup(args.backup)
        elif args.database_url:
            conn = psycopg.connect(psycopg_url(args.database_url))
            courses, subjects, relevance_by_subject = load_database(conn)
        else:
            raise SystemExit("DATABASE_URL, --database-url, or --backup is required")

        counts = build_counts(courses, subjects, relevance_by_subject)
        report = write_report(counts, args.output_dir)
        print(f"Catalog-ready courses: {len(courses):,}")
        print(f"Subjects counted: {len(counts):,}")
        print(f"Nonzero subjects: {sum(row['course_count'] > 0 for row in counts):,}")
        print(f"Report: {report}")
        if args.apply:
            if conn is None:
                raise SystemExit("--apply requires a live database")
            apply_counts(conn, counts)
            print("Applied persisted subject counts.")
        else:
            if conn is not None:
                conn.rollback()
            print("Dry run only. No subject records or memberships were changed.")
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    main()
