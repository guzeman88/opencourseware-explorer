"""Repair catalog rows whose course title is not a real course title.

Default mode is report-only. Applying the repair is intentionally conservative:
- non-course and educational non-course rows are unpublished, never deleted
- lecture/module rows are merged into a confirmed or newly created parent course
- course-like playlists are left for review unless they have a clear parent
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import uuid

import psycopg

from audit_course_title_integrity import (
    CourseRow,
    Issue,
    audit,
    base_title_candidate,
    load_courses,
    normalize,
    psycopg_url,
)


SCRIPT_DIR = Path(__file__).resolve().parent
BACKUP_DIR = SCRIPT_DIR / "catalog_title_repair_backups"
DEFAULT_REPORT = SCRIPT_DIR / "catalog_title_repair_report.csv"

SOURCE_VERSION = "catalog_title_repair_v1"

HARD_NON_COURSE_FRAGMENTS = (
    "admissions",
    "alumni",
    "annual review",
    "apply to",
    "campus",
    "commencement",
    "congregation",
    "graduation",
    "highlights",
    "interview",
    "outtakes",
    "promo",
    "recap",
    "student life",
    "trailer",
)

EDUCATIONAL_NON_COURSE_FRAGMENTS = (
    "colloquium",
    "conference",
    "conversation",
    "covid",
    "departmental day",
    "event",
    "forum",
    "lecture series",
    "seminar",
    "special talks",
    "symposium",
    "workshop",
)

LOW_VALUE_PLAYLIST_FRAGMENTS = (
    "all videos",
    "ged",
    "homework help",
    "how is",
    "how to",
    "student tutorials",
    "tutorial recording",
    "what is",
    "why",
)

COURSE_LIKE_TERMS = (
    "algebra",
    "artificial intelligence",
    "calculus",
    "chemistry",
    "computer science",
    "differential equations",
    "geometry",
    "linear algebra",
    "organic chemistry",
    "physics",
    "precalculus",
    "programming",
    "statistics",
    "trigonometry",
)

COURSE_LIKE_KEEP_SOURCES = {
    "bill_kinney",
    "drtefor",
    "kimberly_brehm",
    "prof_leonard",
    "stanford",
}


@dataclass(frozen=True)
class RepairDecision:
    issue: Issue
    category: str
    operation: str
    parent_course_id: str = ""
    parent_course_title: str = ""
    clean_title: str = ""
    reason: str = ""


def contains_any(title: str, fragments: tuple[str, ...]) -> bool:
    normalized = normalize(title)
    return any(fragment in normalized for fragment in fragments)


def is_course_like_playlist(course: CourseRow) -> bool:
    title = normalize(course.title)
    if "playlist" not in title and "tutorial" not in title:
        return False
    if contains_any(course.title, LOW_VALUE_PLAYLIST_FRAGMENTS):
        return False
    return course.total_videos >= 15 and any(term in title for term in COURSE_LIKE_TERMS)


def classify_issue(issue: Issue) -> RepairDecision:
    course = issue.course
    title = course.title
    normalized = normalize(title)

    if issue.parent_action == "merge_existing_course" and issue.parent_course_id:
        return RepairDecision(
            issue=issue,
            category="parent_course_fragment",
            operation="merge_into_existing_parent",
            parent_course_id=issue.parent_course_id,
            parent_course_title=issue.parent_course_title,
            reason=issue.parent_reason,
        )

    if issue.parent_action == "create_or_rename_parent_course" and issue.parent_course_title:
        return RepairDecision(
            issue=issue,
            category="parent_course_fragment",
            operation="create_parent_and_merge",
            parent_course_title=issue.parent_course_title,
            reason=issue.parent_reason,
        )

    if contains_any(title, HARD_NON_COURSE_FRAGMENTS):
        return RepairDecision(
            issue=issue,
            category="not_lectures_or_courses",
            operation="unpublish",
            reason="hard non-course title signal",
        )

    if contains_any(title, EDUCATIONAL_NON_COURSE_FRAGMENTS):
        return RepairDecision(
            issue=issue,
            category="workshop_conference_individual_lecture",
            operation="unpublish",
            reason="educational material but not a full course",
        )

    if "course title exactly matches a video title" in issue.reasons and course.total_videos <= 4:
        return RepairDecision(
            issue=issue,
            category="workshop_conference_individual_lecture",
            operation="unpublish",
            reason="course row is a single lecture or tiny video set",
        )

    if is_course_like_playlist(course):
        clean_title = clean_playlist_title(title)
        if course.source_key in COURSE_LIKE_KEEP_SOURCES:
            return RepairDecision(
                issue=issue,
                category="course_like_playlist",
                operation="rename_or_merge_course_like_playlist",
                clean_title=clean_title,
                parent_course_title=clean_title,
                reason="trusted course-like playlist source; clean playlist wording",
            )
        return RepairDecision(
            issue=issue,
            category="course_like_playlist",
            operation="unpublish",
            clean_title=clean_title,
            reason="course-like playlist from a source not approved for full-course catalog inclusion",
        )

    if "playlist" in normalized or "tutorial" in normalized or "all videos" in normalized:
        return RepairDecision(
            issue=issue,
            category="not_lectures_or_courses",
            operation="unpublish",
            reason="generic playlist/tutorial row without a safe parent course",
        )

    return RepairDecision(
        issue=issue,
        category="not_lectures_or_courses",
        operation="unpublish",
        reason="flagged title has no reliable parent course",
    )


def clean_playlist_title(title: str) -> str:
    value = re.sub(r"\bnew\b", "", title, flags=re.I)
    value = re.sub(r"\bold\b", "", value, flags=re.I)
    value = re.sub(r"\bvideo\s+playlist\b", "", value, flags=re.I)
    value = re.sub(r"\bplaylist\s+\d+\b", "", value, flags=re.I)
    value = re.sub(r"\bplaylist\b", "", value, flags=re.I)
    value = re.sub(r"\btutorials?\b", "", value, flags=re.I)
    value = re.sub(r"\s*\([^)]*\)\s*", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" -")
    return value or title


def build_decisions(issues: list[Issue]) -> list[RepairDecision]:
    return [classify_issue(issue) for issue in issues]


def write_report(decisions: list[RepairDecision], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "category",
                "operation",
                "course_id",
                "course_title",
                "source_key",
                "institution",
                "videos",
                "parent_course_id",
                "parent_course_title",
                "clean_title",
                "reason",
                "audit_reasons",
            ]
        )
        for decision in decisions:
            course = decision.issue.course
            writer.writerow(
                [
                    decision.category,
                    decision.operation,
                    course.course_id,
                    course.title,
                    course.source_key,
                    course.university_name,
                    course.total_videos,
                    decision.parent_course_id,
                    decision.parent_course_title,
                    decision.clean_title,
                    decision.reason,
                    " | ".join(decision.issue.reasons),
                ]
            )


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "course"


def unique_slug(cur, base: str) -> str:
    slug = base[:580].strip("-") or "course"
    candidate = slug
    suffix = 2
    while True:
        cur.execute("SELECT 1 FROM courses WHERE slug = %s LIMIT 1", (candidate,))
        if cur.fetchone() is None:
            return candidate
        tail = f"-{suffix}"
        candidate = f"{slug[:600 - len(tail)]}{tail}"
        suffix += 1


def backup_rows(conn, decisions: list[RepairDecision]) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = BACKUP_DIR / f"title_repair_backup_{stamp}.csv"
    course_ids = sorted({decision.issue.course.course_id for decision in decisions})
    parent_ids = sorted(
        {
            decision.parent_course_id
            for decision in decisions
            if decision.operation == "merge_into_existing_parent" and decision.parent_course_id
        }
    )
    ids = course_ids + parent_ids
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
          c.id::text,
          c.title,
          c.slug,
          c.source_key,
          c.is_published,
          c.has_video_lectures,
          c.total_videos,
          c.total_duration_seconds,
          COALESCE(string_agg(DISTINCT s.slug, '|' ORDER BY s.slug), ''),
          COALESCE(string_agg(DISTINCT v.id::text || ':' || v.youtube_id || ':' || v."order"::text, '|' ORDER BY v.id::text || ':' || v.youtube_id || ':' || v."order"::text), '')
        FROM courses c
        LEFT JOIN course_subjects cs ON cs.course_id = c.id
        LEFT JOIN subjects s ON s.id = cs.subject_id
        LEFT JOIN videos v ON v.course_id = c.id
        WHERE c.id = ANY(%s)
        GROUP BY c.id
        ORDER BY c.title
        """,
        (ids,),
    )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "course_id",
                "title",
                "slug",
                "source_key",
                "is_published",
                "has_video_lectures",
                "total_videos",
                "total_duration_seconds",
                "subject_slugs",
                "video_refs",
            ]
        )
        writer.writerows(cur.fetchall())
    return path


def find_or_create_parent(conn, parent_title: str, child_ids: list[str]) -> tuple[str, bool]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT c.id::text
        FROM courses c
        WHERE regexp_replace(trim(lower(c.title)), '\\s+', ' ', 'g') =
              regexp_replace(trim(lower(%s)), '\\s+', ' ', 'g')
          AND c.source_key = (
            SELECT source_key FROM courses WHERE id = %s
          )
          AND c.university_id = (
            SELECT university_id FROM courses WHERE id = %s
          )
        ORDER BY c.total_videos DESC, c.title
        LIMIT 1
        """,
        (parent_title, child_ids[0], child_ids[0]),
    )
    existing = cur.fetchone()
    if existing:
        return existing[0], False

    cur.execute(
        """
        SELECT
          university_id,
          department_id,
          level,
          source_key,
          source_url,
          thumbnail_url,
          instructor,
          year,
          semester,
          view_count
        FROM courses
        WHERE id = %s
        """,
        (child_ids[0],),
    )
    template = cur.fetchone()
    if template is None:
        raise RuntimeError(f"Missing child course template {child_ids[0]}")

    parent_id = str(uuid.uuid4())
    slug = unique_slug(cur, slugify(f"{template[3]}-{parent_title}"))
    cur.execute(
        """
        INSERT INTO courses (
          id,
          university_id,
          department_id,
          course_number,
          title,
          slug,
          description,
          level,
          source_url,
          source_key,
          thumbnail_url,
          instructor,
          year,
          semester,
          has_video_lectures,
          has_lecture_notes,
          has_exams,
          total_videos,
          total_duration_seconds,
          view_count,
          is_published,
          created_at,
          updated_at
        )
        VALUES (
          %s, %s, %s, NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
          TRUE, FALSE, FALSE, 0, 0, %s, TRUE, now(), now()
        )
        """,
        (
            parent_id,
            template[0],
            template[1],
            parent_title,
            slug,
            f"Merged parent course created by {SOURCE_VERSION}.",
            template[2],
            template[4],
            template[3],
            template[5],
            template[6],
            template[7],
            template[8],
            template[9],
        ),
    )
    return parent_id, True


def move_child_videos(conn, child_id: str, parent_id: str) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT COALESCE(MAX("order"), -1)
        FROM videos
        WHERE course_id = %s
        """,
        (parent_id,),
    )
    start_order = (cur.fetchone()[0] or -1) + 1
    cur.execute(
        """
        WITH moving AS (
          SELECT id, row_number() OVER (ORDER BY "order", created_at, id) - 1 AS offset
          FROM videos
          WHERE course_id = %s
            AND youtube_id NOT IN (
              SELECT youtube_id FROM videos WHERE course_id = %s
            )
        )
        UPDATE videos v
        SET course_id = %s,
            "order" = %s + moving.offset,
            updated_at = now()
        FROM moving
        WHERE v.id = moving.id
        """,
        (child_id, parent_id, parent_id, start_order),
    )
    return cur.rowcount


def copy_subjects(conn, child_id: str, parent_id: str) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO course_subjects (course_id, subject_id)
        SELECT %s, subject_id
        FROM course_subjects
        WHERE course_id = %s
        ON CONFLICT DO NOTHING
        """,
        (parent_id, child_id),
    )


def recalc_course(conn, course_id: str) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE courses c
        SET total_videos = stats.video_count,
            total_duration_seconds = stats.duration,
            has_video_lectures = stats.video_count > 0,
            thumbnail_url = COALESCE(c.thumbnail_url, stats.thumbnail_url),
            updated_at = now()
        FROM (
          SELECT
            COUNT(*)::int AS video_count,
            COALESCE(SUM(COALESCE(duration_seconds, 0)), 0)::int AS duration,
            (array_agg(thumbnail_url ORDER BY "order") FILTER (WHERE thumbnail_url IS NOT NULL))[1] AS thumbnail_url
          FROM videos
          WHERE course_id = %s
        ) stats
        WHERE c.id = %s
        """,
        (course_id, course_id),
    )


def unpublish_course(conn, course_id: str) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE courses
        SET is_published = FALSE,
            updated_at = now()
        WHERE id = %s
          AND is_published = TRUE
        """,
        (course_id,),
    )
    return cur.rowcount


def rename_course(conn, course_id: str, clean_title: str) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE courses
        SET title = %s,
            updated_at = now()
        WHERE id = %s
          AND title <> %s
        """,
        (clean_title, course_id, clean_title),
    )
    return cur.rowcount


def apply_repairs(conn, decisions: list[RepairDecision]) -> tuple[Path, dict[str, int]]:
    applicable = [
        decision
        for decision in decisions
        if decision.operation
        in {
            "unpublish",
            "merge_into_existing_parent",
            "create_parent_and_merge",
            "rename_or_merge_course_like_playlist",
        }
    ]
    backup_path = backup_rows(conn, applicable)
    counts = {
        "unpublished": 0,
        "created_parents": 0,
        "merged_children": 0,
        "moved_videos": 0,
        "renamed_courses": 0,
    }

    create_groups: dict[tuple[str, str], list[RepairDecision]] = {}
    for decision in applicable:
        if decision.operation == "create_parent_and_merge":
            key = (decision.issue.course.source_key, decision.parent_course_title)
            create_groups.setdefault(key, []).append(decision)

    course_like_groups: dict[tuple[str, str], list[RepairDecision]] = {}
    for decision in applicable:
        if decision.operation == "rename_or_merge_course_like_playlist":
            key = (decision.issue.course.source_key, decision.clean_title)
            course_like_groups.setdefault(key, []).append(decision)

    for decision in applicable:
        if decision.operation == "unpublish":
            counts["unpublished"] += unpublish_course(conn, decision.issue.course.course_id)

    for decision in applicable:
        if decision.operation != "merge_into_existing_parent":
            continue
        child_id = decision.issue.course.course_id
        parent_id = decision.parent_course_id
        moved = move_child_videos(conn, child_id, parent_id)
        copy_subjects(conn, child_id, parent_id)
        counts["unpublished"] += unpublish_course(conn, child_id)
        recalc_course(conn, child_id)
        recalc_course(conn, parent_id)
        counts["merged_children"] += 1
        counts["moved_videos"] += moved

    for _key, group in create_groups.items():
        parent_title = group[0].parent_course_title
        child_ids = [decision.issue.course.course_id for decision in group]
        parent_id, created = find_or_create_parent(conn, parent_title, child_ids)
        if created:
            counts["created_parents"] += 1
        for decision in group:
            child_id = decision.issue.course.course_id
            moved = move_child_videos(conn, child_id, parent_id)
            copy_subjects(conn, child_id, parent_id)
            counts["unpublished"] += unpublish_course(conn, child_id)
            recalc_course(conn, child_id)
            counts["merged_children"] += 1
            counts["moved_videos"] += moved
        recalc_course(conn, parent_id)

    for _key, group in course_like_groups.items():
        if len(group) == 1:
            decision = group[0]
            counts["renamed_courses"] += rename_course(
                conn, decision.issue.course.course_id, decision.clean_title
            )
            recalc_course(conn, decision.issue.course.course_id)
            continue

        parent_title = group[0].clean_title
        child_ids = [decision.issue.course.course_id for decision in group]
        parent_id, created = find_or_create_parent(conn, parent_title, child_ids)
        if created:
            counts["created_parents"] += 1
        for decision in group:
            child_id = decision.issue.course.course_id
            moved = move_child_videos(conn, child_id, parent_id)
            copy_subjects(conn, child_id, parent_id)
            counts["unpublished"] += unpublish_course(conn, child_id)
            recalc_course(conn, child_id)
            counts["merged_children"] += 1
            counts["moved_videos"] += moved
        recalc_course(conn, parent_id)

    conn.commit()
    return backup_path, counts


def print_summary(decisions: list[RepairDecision], report_path: Path) -> None:
    category_counts: dict[str, int] = {}
    operation_counts: dict[str, int] = {}
    for decision in decisions:
        category_counts[decision.category] = category_counts.get(decision.category, 0) + 1
        operation_counts[decision.operation] = operation_counts.get(decision.operation, 0) + 1
    print(f"Flagged rows classified: {len(decisions):,}")
    print("Categories:")
    for category, count in sorted(category_counts.items()):
        print(f"  {category}: {count:,}")
    print("Operations:")
    for operation, count in sorted(operation_counts.items()):
        print(f"  {operation}: {count:,}")
    print(f"Report: {report_path}")
    course_like = [
        decision
        for decision in decisions
        if decision.category == "course_like_playlist"
    ]
    if course_like:
        print("\nCourse-like playlist rows:")
        for decision in course_like[:25]:
            print(
                f"  {decision.operation}: {decision.issue.course.title}"
                f" -> {decision.clean_title} [{decision.issue.course.source_key}]"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="apply backed-up repairs")
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    with psycopg.connect(psycopg_url(database_url), connect_timeout=20) as conn:
        courses = load_courses(conn)
        issues = audit(courses)
        decisions = build_decisions(issues)
        report_path = Path(args.report)
        write_report(decisions, report_path)
        print_summary(decisions, report_path)

        if args.apply:
            backup_path, counts = apply_repairs(conn, decisions)
            print(f"Applied catalog title repair. Backup: {backup_path}")
            for key, count in counts.items():
                print(f"  {key}: {count:,}")
        else:
            conn.rollback()
            print("Report-only. Re-run with --apply to mutate the database.")


if __name__ == "__main__":
    main()
