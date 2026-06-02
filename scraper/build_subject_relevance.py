"""
Build scored subject relevance without modifying existing course_subjects.

Default mode is a dry run. Use --apply to replace this script's auto-generated
sidecar rows in course_subject_relevance. Manual rows with a different source
are left alone.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import os
import json
import re
import uuid
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import urlopen

import psycopg


DATABASE_URL = os.environ.get("DATABASE_URL")
SOURCE = "auto"
VERSION = "v1"
MIN_DISPLAY_SCORE = 40
TITLE_SUFFIX_SEPARATORS = (" | ",)

GENERIC_TOKENS = {
    "and",
    "for",
    "the",
    "with",
    "introduction",
    "intro",
    "advanced",
    "course",
    "courses",
    "topics",
    "seminar",
    "lecture",
    "lectures",
    "part",
}

SYNONYMS: dict[str, list[str]] = {
    "artificial-intelligence": ["ai", "artificial intelligence"],
    "computer-science": ["computer science", "computing", "cs"],
    "computer-networks": ["computer networks", "networking"],
    "cybersecurity": ["cyber security", "computer security", "information security"],
    "data-structures": ["data structures", "data structure"],
    "differential-equations": ["differential equations", "ordinary differential equations", "partial differential equations"],
    "discrete-mathematics": ["discrete mathematics", "discrete math", "discrete structures"],
    "large-language-models": ["large language models", "large language model", "llm", "language models"],
    "machine-learning": ["machine learning", "statistical learning"],
    "natural-language-processing": ["natural language processing", "nlp"],
    "operating-systems": ["operating systems", "operating system"],
    "probability": ["probability theory"],
    "proof-writing": ["proof writing", "proofs", "mathematical proofs", "logic and proof"],
    "real-analysis": ["real analysis"],
    "software-engineering": ["software engineering"],
}

ROLLUPS: dict[str, list[str]] = {
    "abstract-algebra": ["algebra", "mathematics"],
    "algorithms": ["computer-science"],
    "algebra": ["mathematics"],
    "calculus": ["mathematics"],
    "combinatorics": ["discrete-mathematics", "mathematics"],
    "computer-architecture": ["computer-science"],
    "computer-graphics": ["computer-science"],
    "computer-networks": ["computer-science", "networking"],
    "computer-security": ["cybersecurity", "computer-science"],
    "computer-systems": ["computer-science"],
    "convex-optimization": ["optimization", "mathematics"],
    "data-analysis": ["data-science", "statistics"],
    "data-science": ["computer-science", "statistics"],
    "data-structures": ["algorithms", "computer-science"],
    "databases": ["computer-science"],
    "deep-learning": ["machine-learning", "artificial-intelligence", "computer-science"],
    "differential-equations": ["mathematics"],
    "graph-theory": ["discrete-mathematics", "combinatorics", "mathematics"],
    "large-language-models": ["natural-language-processing", "artificial-intelligence", "computer-science"],
    "linear-algebra": ["mathematics"],
    "logic": ["discrete-mathematics", "mathematics", "philosophy"],
    "machine-learning": ["artificial-intelligence", "computer-science", "data-science"],
    "natural-language-processing": ["artificial-intelligence", "computer-science"],
    "number-theory": ["mathematics"],
    "operating-systems": ["computer-science", "computer-systems"],
    "proof-writing": ["mathematics"],
    "programming": ["computer-science"],
    "real-analysis": ["analysis", "mathematics"],
    "set-theory": ["discrete-mathematics", "mathematics"],
    "statistics": ["mathematics"],
    "theory-of-computing": ["computer-science"],
}


@dataclass(frozen=True)
class Subject:
    id: str
    slug: str
    name: str


@dataclass(frozen=True)
class Course:
    id: str
    title: str
    description: str
    existing_subjects: frozenset[str]


@dataclass
class Relevance:
    course_id: str
    subject_id: str
    subject_slug: str
    score: int
    relationship: str
    reason: str


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9+#.]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def strict_title_scope(title: str) -> str:
    scoped = title
    for separator in TITLE_SUFFIX_SEPARATORS:
        if separator in scoped:
            scoped = scoped.split(separator, 1)[0]
    return scoped


def psycopg_url(url: str) -> str:
    normalized = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    parts = urlsplit(normalized)
    params = dict(parse_qsl(parts.query, keep_blank_values=True))
    if "sslmode" not in params and (
        "railway" in normalized.lower() or "rlwy.net" in normalized.lower()
    ):
        params["sslmode"] = "require"
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(params), parts.fragment)
    )


def phrase_match(haystack: str, phrase: str) -> bool:
    phrase = normalize(phrase)
    if not phrase:
        return False
    pattern = rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])"
    return re.search(pattern, haystack) is not None


def subject_phrases(subject: Subject) -> list[str]:
    phrases = [subject.name, subject.slug.replace("-", " ")]
    phrases.extend(SYNONYMS.get(subject.slug, []))
    seen: set[str] = set()
    result: list[str] = []
    for phrase in phrases:
        norm = normalize(phrase)
        if norm and norm not in seen:
            seen.add(norm)
            result.append(norm)
    return result


def distinctive_tokens(subject: Subject) -> list[str]:
    tokens: list[str] = []
    for phrase in subject_phrases(subject):
        tokens.extend(phrase.split())
    return sorted({t for t in tokens if len(t) > 2 and t not in GENERIC_TOKENS})


def all_tokens_match(haystack: str, tokens: list[str]) -> bool:
    return bool(tokens) and all(phrase_match(haystack, token) for token in tokens)


def score_direct(
    course: Course, subject: Subject, *, strategy: str = "rollup"
) -> tuple[int, str, str]:
    title = normalize(
        strict_title_scope(course.title) if strategy == "strict" else course.title
    )
    description = normalize(course.description)
    phrases = subject_phrases(subject)
    tokens = distinctive_tokens(subject)

    for phrase in phrases:
        if phrase_match(title, phrase):
            relation = "exact_title" if phrase == normalize(subject.name) else "title_match"
            return 100 if relation == "exact_title" else 92, relation, f"title contains '{phrase}'"

    if all_tokens_match(title, tokens):
        return 86, "title_match", f"title contains subject tokens: {', '.join(tokens)}"

    for phrase in phrases:
        if phrase_match(description, phrase):
            return 74, "description_match", f"description contains '{phrase}'"

    if all_tokens_match(description, tokens):
        return 64, "description_match", f"description contains subject tokens: {', '.join(tokens)}"

    if strategy != "strict" and subject.slug in course.existing_subjects:
        return 35, "weak_existing_tag", "existing tag only; no direct text evidence"

    return 0, "none", ""


def add_or_raise(scores: dict[tuple[str, str], Relevance], item: Relevance) -> None:
    key = (item.course_id, item.subject_id)
    existing = scores.get(key)
    if existing is None or item.score > existing.score:
        scores[key] = item


def build_scores(
    courses: list[Course], subjects: list[Subject], *, strategy: str = "rollup"
) -> list[Relevance]:
    by_slug = {s.slug: s for s in subjects}
    scores: dict[tuple[str, str], Relevance] = {}
    direct_by_course: dict[str, list[Relevance]] = {}

    for course in courses:
        direct_matches: list[Relevance] = []
        for subject in subjects:
            score, relationship, reason = score_direct(
                course, subject, strategy=strategy
            )
            if score <= 0:
                continue
            item = Relevance(
                course_id=course.id,
                subject_id=subject.id,
                subject_slug=subject.slug,
                score=score,
                relationship=relationship,
                reason=reason,
            )
            add_or_raise(scores, item)
            if score >= 70:
                direct_matches.append(item)
        direct_by_course[course.id] = direct_matches

    if strategy != "strict":
        for course in courses:
            for child_match in direct_by_course.get(course.id, []):
                for parent_slug in ROLLUPS.get(child_match.subject_slug, []):
                    parent = by_slug.get(parent_slug)
                    if parent is None:
                        continue
                    score = max(MIN_DISPLAY_SCORE + 1, child_match.score - 28)
                    add_or_raise(
                        scores,
                        Relevance(
                            course_id=course.id,
                            subject_id=parent.id,
                            subject_slug=parent.slug,
                            score=score,
                            relationship="parent_rollup",
                            reason=f"related via {child_match.subject_slug}: {child_match.reason}",
                        ),
                    )

    return list(scores.values())


def load_data(conn) -> tuple[list[Course], list[Subject]]:
    cur = conn.cursor()
    cur.execute("SELECT id::text, slug, name FROM subjects ORDER BY slug")
    subjects = [Subject(id=row[0], slug=row[1], name=row[2]) for row in cur.fetchall()]

    cur.execute(
        """
        SELECT
          c.id::text,
          c.title,
          COALESCE(c.description, ''),
          COALESCE(array_agg(s.slug) FILTER (WHERE s.slug IS NOT NULL), '{}')
        FROM courses c
        LEFT JOIN course_subjects cs ON cs.course_id = c.id
        LEFT JOIN subjects s ON s.id = cs.subject_id
        WHERE c.is_published = TRUE
        GROUP BY c.id, c.title, c.description
        """
    )
    courses = [
        Course(
            id=row[0],
            title=row[1],
            description=row[2] or "",
            existing_subjects=frozenset(row[3] or []),
        )
        for row in cur.fetchall()
    ]
    return courses, subjects


def fetch_api_page(
    api_base: str, path: str, page: int, page_size: int, extra_params: dict | None = None
) -> dict:
    url = urljoin(api_base.rstrip("/") + "/", path.lstrip("/"))
    params = {"page": page, "page_size": page_size}
    if extra_params:
        params.update(extra_params)
    url = f"{url}?{urlencode(params)}"
    with urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_all_api_items(
    api_base: str, path: str, extra_params: dict | None = None
) -> list[dict]:
    page_size = 100
    first = fetch_api_page(api_base, path, 1, page_size, extra_params)
    payloads = [first]
    pages = first["pages"]
    if pages > 1:
        with ThreadPoolExecutor(max_workers=8) as executor:
            payloads.extend(
                executor.map(
                    lambda page: fetch_api_page(
                        api_base, path, page, page_size, extra_params
                    ),
                    range(2, pages + 1),
                )
            )
    items: list[dict] = []
    for payload in payloads:
        items.extend(payload["items"])
    return items


def load_api_data(
    api_base: str, *, course_subject: str | None = None
) -> tuple[list[Course], list[Subject]]:
    subject_items = fetch_all_api_items(api_base, "/api/v1/subjects")
    subjects = [
        Subject(id=item["id"], slug=item["slug"], name=item["name"])
        for item in subject_items
    ]

    course_params = {"subject_slug": course_subject} if course_subject else None
    course_items = fetch_all_api_items(api_base, "/api/v1/courses", course_params)
    courses = [
        Course(
            id=item["id"],
            title=item["title"],
            description=item.get("description") or "",
            existing_subjects=frozenset(
                subject["slug"] for subject in item.get("subjects", [])
            ),
        )
        for item in course_items
    ]

    return courses, subjects


def apply_scores(conn, scores: list[Relevance]) -> None:
    rows = [
        (
            str(uuid.uuid4()),
            item.course_id,
            item.subject_id,
            item.score,
            item.relationship,
            item.reason,
            SOURCE,
            VERSION,
        )
        for item in scores
    ]

    cur = conn.cursor()
    cur.execute(
        "DELETE FROM course_subject_relevance WHERE source = %s AND version = %s",
        (SOURCE, VERSION),
    )
    cur.executemany(
        """
        INSERT INTO course_subject_relevance
          (id, course_id, subject_id, score, relationship, reason, source, version)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (course_id, subject_id) DO UPDATE SET
          score = EXCLUDED.score,
          relationship = EXCLUDED.relationship,
          reason = EXCLUDED.reason,
          source = EXCLUDED.source,
          version = EXCLUDED.version,
          updated_at = now()
        WHERE course_subject_relevance.source = EXCLUDED.source
        """,
        rows,
    )
    conn.commit()


def print_summary(
    scores: list[Relevance], courses: list[Course], subject: str | None, limit: int
) -> None:
    course_titles = {course.id: course.title for course in courses}
    visible = [s for s in scores if s.score >= MIN_DISPLAY_SCORE]
    print(f"Scored rows: {len(scores):,}")
    print(f"Rows at display threshold >= {MIN_DISPLAY_SCORE}: {len(visible):,}")

    if subject:
        selected = sorted(
            [s for s in scores if s.subject_slug == subject],
            key=lambda s: (-s.score, s.relationship, s.reason),
        )
        print(f"\nTop {min(limit, len(selected))} for {subject}:")
        for item in selected[:limit]:
            title = course_titles.get(item.course_id, item.course_id)
            print(f"  {item.score:3d} {item.relationship:18s} {title} [{item.reason}]")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write sidecar relevance rows")
    parser.add_argument(
        "--api-base",
        help="read visible course/subject data from an API base URL instead of DATABASE_URL",
    )
    parser.add_argument(
        "--api-course-subject",
        help="when using --api-base, only fetch courses currently visible for this subject slug",
    )
    parser.add_argument("--subject", help="print sample rows for one subject slug")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument(
        "--strategy",
        choices=("rollup", "strict"),
        default="rollup",
        help="rollup keeps broad parent matches; strict only keeps direct subject evidence",
    )
    args = parser.parse_args()

    if args.apply and args.api_base:
        raise SystemExit("--apply is only available with DATABASE_URL, not --api-base")

    if not args.api_base and not DATABASE_URL:
        raise SystemExit("DATABASE_URL is required")

    conn = None
    try:
        if args.api_base:
            courses, subjects = load_api_data(
                args.api_base, course_subject=args.api_course_subject
            )
        else:
            conn = psycopg.connect(psycopg_url(DATABASE_URL))
            courses, subjects = load_data(conn)
        print(f"Courses: {len(courses):,}")
        print(f"Subjects: {len(subjects):,}")
        print(f"Strategy: {args.strategy}")
        scores = build_scores(courses, subjects, strategy=args.strategy)
        print_summary(scores, courses, args.subject, args.limit)
        if args.apply:
            if conn is None:
                raise SystemExit("--apply requires DATABASE_URL")
            apply_scores(conn, scores)
            print("Applied relevance sidecar rows.")
        else:
            print("Dry run only. Re-run with --apply to write sidecar rows.")
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    main()
