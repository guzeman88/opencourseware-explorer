"""Unpublish catalog rows that still cannot receive defensible subject tags.

This script runs after reconcile_catalog_subject_tags.py has had a chance to
propose tags. It only handles the remaining untagged rows, and only when they
match strong non-course, non-English, or topic-fragment signals.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import re

import psycopg

from reconcile_catalog_subject_tags import (
    Course,
    build_proposals,
    load_db_data,
    load_rules,
    normalize,
    psycopg_url,
)


SCRIPT_DIR = Path(__file__).resolve().parent
BACKUP_DIR = SCRIPT_DIR / "untagged_catalog_repair_backups"
DEFAULT_REPORT = SCRIPT_DIR / "untagged_catalog_repair_report.csv"

NON_COURSE_FRAGMENTS = (
    "access and opportunity",
    "accessibility",
    "accommodation",
    "admitted students",
    "advice",
    "annual industry day",
    "annual latke",
    "ase planetary congress",
    "ask what you can do",
    "bears ",
    "becoming caltech",
    "behind the book",
    "berkeley in the 80s",
    "beyond the chalk",
    "bicentennial",
    "birthday",
    "boat race",
    "campus",
    "cambridge and the erc",
    "cine club",
    "class photo",
    "clearing",
    "common love",
    "corporate video",
    "coronavirus resources",
    "cultural landscapes",
    "curious objects",
    "degree conferral",
    "digital time capsule",
    "disability",
    "doctorate addresses",
    "dna team",
    "erc celebrating",
    "eureka moments",
    "famelab",
    "faculty reads",
    "fall preview",
    "favorites",
    "festival",
    "first year diaries",
    "first-generation",
    "greeting cards",
    "holiday",
    "honorary degree",
    "honorary doctorate",
    "international student experience",
    "it services",
    "learning commons",
    "life in",
    "lions and little mics",
    "live sessions",
    "lowell bells",
    "master's guide",
    "meditations translations and calligraphy",
    "meet the class",
    "meet harvard",
    "meet our students",
    "my favorite things",
    "office hours",
    "office of the president",
    "open badges",
    "our tower",
    "oxford in voice",
    "pause for art",
    "president ",
    "presidential lectures",
    "recipes from my kitchen",
    "recruiting profiles",
    "religious life",
    "residences",
    "research in options",
    "season's greetings",
    "state of the field",
    "student portal",
    "student service",
    "studying with us",
    "taps ",
    "teaching and learning practices",
    "this week at",
    "time double degree",
    "top moments",
    "top 10 all time favourites",
    "transport talks",
    "undergrad",
    "undergraduate experience",
    "university church",
    "veterans day",
    "visitas",
    "wall of faces",
    "wellness week",
    "why i m taking",
    "why king",
    "world class facilities",
    "cosmo 2013",
    "feast radical hospitality",
    "felix klein lecture",
    "from my house",
    "get in cambridge",
    "getting ready",
    "go figure",
    "lgbtq math day",
    "lgbtq+math day",
    "hispanic heritage month",
    "ias and the theme",
    "imagine what you could do",
    "inspiring students",
    "purdue experts",
    "students with disabilities",
    "the edinburgh experience",
)

NON_ENGLISH_FRAGMENTS = (
    "algebren",
    "bicentenaire",
    "ciclo de palestras",
    "combinatoria",
    "combinatoria",
    "communaute",
    "comunidade",
    "curso online",
    "determinanten",
    "distributionen",
    "divulgacao",
    "doutorado",
    "ecole",
    "encontro nacional",
    "ensino",
    "escola",
    "entrevistas",
    "festival da matematica",
    "historias",
    "iniciacao cientifica",
    "janeiro",
    "jornada",
    "journee",
    "julho",
    "matematica",
    "mestrado",
    "mini curso",
    "minicurso",
    "palestras",
    "papmem",
    "prolimpico",
    "seminario",
    "seminarios",
    "simposio",
    "serie",
    "topicos",
    "drei minuten",
    "impa 70 anos",
    "mathematiques",
    "mathematik fur alle",
    "lacea lames",
    "lives e webinares",
    "pic introducao",
    "seminaire",
    "une question",
)

TOPIC_FRAGMENT_SOURCES = {
    "bill_kinney",
    "bright_side_math",
    "michelvanbiezen",
    "patrickjmt",
    "prof_dave",
}

SOURCE_UNTAGGED_NON_COURSE = {
    "cs50",
    "duke",
    "epfl",
    "gatech",
    "hku",
    "hkust",
    "jhu",
    "kcl",
    "mcgill",
    "princeton",
    "rice",
    "ubc",
    "waterloo",
    "yale",
}

GENERIC_SHORT_TITLES = {
    "2015 mdc",
    "cake",
    "favorites",
    "featured",
    "mashup",
    "mispellings",
    "sentiments",
    "snippets",
}


@dataclass(frozen=True)
class Decision:
    course: Course
    operation: str
    reason: str


def has_fragment(title: str, fragments: tuple[str, ...]) -> bool:
    normalized = normalize(title)
    return any(fragment in normalized for fragment in fragments)


def classify(course: Course) -> Decision:
    title = normalize(course.title)
    raw_title = course.title.lower()

    if title in GENERIC_SHORT_TITLES:
        return Decision(course, "unpublish", "generic short non-course title")
    if raw_title.startswith("filter ("):
        return Decision(course, "unpublish", "CS50 exercise fragment")
    if has_fragment(course.title, NON_COURSE_FRAGMENTS):
        return Decision(course, "unpublish", "non-course title signal")
    if has_fragment(course.title, NON_ENGLISH_FRAGMENTS):
        return Decision(course, "unpublish", "non-English title signal")
    if course.source_key in TOPIC_FRAGMENT_SOURCES:
        return Decision(course, "unpublish", "topic-fragment source without course-level tag evidence")
    if course.source_key in SOURCE_UNTAGGED_NON_COURSE:
        return Decision(course, "unpublish", "source-specific untagged row is non-course material")
    if re.search(r"\b\d+\s+seconds?\b", title):
        return Decision(course, "unpublish", "short-form video collection")
    if re.search(r"\b\d+\s+minute\b", title):
        return Decision(course, "unpublish", "short-form video collection")
    if "bourbaki" in title:
        return Decision(course, "unpublish", "seminar series rather than full course")
    if "bogomolov" in title:
        return Decision(course, "unpublish", "tribute/event title rather than full course")
    if "lecture collection" in title:
        return Decision(course, "unpublish", "collection title is not a course")
    if "mini course" in title or "mini curso" in title or "mini-course" in title:
        return Decision(course, "unpublish", "mini-course row without tag evidence")
    if "open lectures" in title or "lightning talks" in title or "roundtable talks" in title:
        return Decision(course, "unpublish", "talk series rather than full course")
    if "hausdorff school" in title:
        return Decision(course, "unpublish", "school/workshop row rather than full course")
    if "structures and functions" in title:
        return Decision(course, "unpublish", "generic topic row without course-level evidence")
    if "web salon" in title or "salon" in title:
        return Decision(course, "unpublish", "event/salon rather than full course")

    return Decision(course, "review", "no safe unpublish rule matched")


def load_untagged(conn) -> list[Course]:
    rules, rollups = load_rules()
    courses, subjects = load_db_data(conn)
    result = build_proposals(courses, subjects, rules, rollups)
    return result.untagged


def write_report(decisions: list[Decision], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["operation", "reason", "course_id", "title", "source_key"])
        for decision in decisions:
            writer.writerow(
                [
                    decision.operation,
                    decision.reason,
                    decision.course.id,
                    decision.course.title,
                    decision.course.source_key,
                ]
            )


def backup_courses(conn, decisions: list[Decision]) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = BACKUP_DIR / f"untagged_catalog_backup_{stamp}.csv"
    ids = [decision.course.id for decision in decisions if decision.operation == "unpublish"]
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
          COALESCE(string_agg(DISTINCT s.slug, '|' ORDER BY s.slug), '')
        FROM courses c
        LEFT JOIN course_subjects cs ON cs.course_id = c.id
        LEFT JOIN subjects s ON s.id = cs.subject_id
        WHERE c.id = ANY(%s)
        GROUP BY c.id
        ORDER BY c.source_key, c.title
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
                "subject_slugs",
            ]
        )
        writer.writerows(cur.fetchall())
    return path


def apply_decisions(conn, decisions: list[Decision]) -> tuple[Path, int]:
    review = [decision for decision in decisions if decision.operation != "unpublish"]
    if review:
        examples = "\n".join(
            f"  {decision.course.title} [{decision.course.source_key}]: {decision.reason}"
            for decision in review[:30]
        )
        raise RuntimeError(
            f"Refusing to apply: {len(review)} untagged rows need review.\n{examples}"
        )
    backup = backup_courses(conn, decisions)
    ids = [decision.course.id for decision in decisions]
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE courses
        SET is_published = FALSE,
            updated_at = now()
        WHERE id = ANY(%s)
          AND is_published = TRUE
        """,
        (ids,),
    )
    changed = cur.rowcount
    conn.commit()
    return backup, changed


def print_summary(decisions: list[Decision], report_path: Path) -> None:
    unpublish = [decision for decision in decisions if decision.operation == "unpublish"]
    review = [decision for decision in decisions if decision.operation != "unpublish"]
    print(f"Untagged catalog rows classified: {len(decisions):,}")
    print(f"Safe to unpublish: {len(unpublish):,}")
    print(f"Need review: {len(review):,}")
    print(f"Report: {report_path}")
    if review:
        print("\nReview examples:")
        for decision in review[:30]:
            print(f"  {decision.course.title} [{decision.course.source_key}]")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    with psycopg.connect(psycopg_url(database_url), connect_timeout=20) as conn:
        untagged = load_untagged(conn)
        decisions = [classify(course) for course in untagged]
        report_path = Path(args.report)
        write_report(decisions, report_path)
        print_summary(decisions, report_path)
        if args.apply:
            backup, changed = apply_decisions(conn, decisions)
            print(f"Applied untagged catalog repair. Backup: {backup}")
            print(f"Unpublished rows changed: {changed:,}")
        else:
            conn.rollback()
            print("Report-only. Re-run with --apply to mutate the database.")


if __name__ == "__main__":
    main()
