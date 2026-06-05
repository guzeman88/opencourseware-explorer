"""Reconcile public catalog subject tags from direct course evidence.

This script is intentionally stricter than tag_courses_prod.py:
- only catalog-ready courses are considered
- broad parent rollups are suppressed unless directly named
- existing catalog tags are backed up before apply
- apply refuses to run if any eligible course has no proposed tag

Default mode is report-only.
"""
from __future__ import annotations

import argparse
import ast
import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import lru_cache
import json
import os
from pathlib import Path
import re
import time
import unicodedata
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import urlopen

import psycopg


SCRIPT_DIR = Path(__file__).resolve().parent
LEGACY_TAGGER = SCRIPT_DIR / "tag_courses_prod.py"
BACKUP_DIR = SCRIPT_DIR / "tag_backups"

SOURCE = "catalog_reconcile"
VERSION = "v1"

NON_CATALOG_SOURCE_KEYS = {"nptel"}
NON_COURSE_TITLE_FRAGMENTS = (
    "about ",
    "#short",
    "admissions",
    "alumni",
    "anniversary",
    "annual review",
    "apply to",
    "around campus",
    "best of",
    "campus life",
    "centenary lectures",
    "challenge",
    "ceremony",
    "colloquium",
    "commencement",
    "competition",
    "conference",
    "congregation",
    "convocation",
    "conversation with",
    "covid",
    "departmental day",
    "election",
    "episode",
    "event recordings",
    "events",
    "family weekend",
    "forum",
    "graduation",
    "groupe calcul",
    "help sessions",
    "heures avec",
    "highlights",
    "homework, exams",
    "homecoming",
    "information session",
    "interview",
    "lecture series",
    "live clips",
    "meeting",
    "minutes to change",
    "orientation",
    "playlist",
    "programme",
    "programs",
    "promo",
    "promotional",
    "recap",
    "research at",
    "stories",
    "student life",
    "reunion",
    "season ",
    "seminar",
    "special talks",
    "student spotlight",
    "student lectures",
    "symposium",
    "teaser",
    "trailer",
    "video series",
    "workshop",
    "year in review",
    "\" series",
    "colóquio",
    "comunauté",
    "conferência",
    "conférence",
    "encuentro",
)

NON_ENGLISH_SCRIPT_RE = re.compile(
    r"[\u0400-\u052f\u2de0-\u2dff\ua640-\ua69f\u0370-\u03ff"
    r"\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]"
)

GENERIC_SUBJECT_SLUGS = {
    "arts",
    "biology",
    "business",
    "chemistry",
    "computer-science",
    "economics",
    "engineering",
    "health",
    "history",
    "language",
    "law",
    "literature",
    "mathematics",
    "medicine",
    "music",
    "philosophy",
    "physics",
    "programming",
    "psychology",
    "sociology",
    "statistics",
    "technology",
}

GENERIC_TOKENS = {
    "advanced",
    "and",
    "course",
    "courses",
    "for",
    "intro",
    "introduction",
    "lecture",
    "lectures",
    "part",
    "seminar",
    "the",
    "topics",
    "with",
}


@dataclass(frozen=True)
class Subject:
    id: str
    slug: str
    name: str


@dataclass(frozen=True)
class PreparedSubject:
    subject: Subject
    phrases: tuple[str, ...]
    tokens: frozenset[str]


@dataclass(frozen=True)
class Course:
    id: str
    title: str
    description: str
    source_key: str
    source_url: str
    course_number: str
    video_titles: tuple[str, ...]
    existing_subjects: frozenset[str]


@dataclass(frozen=True)
class CourseEvidence:
    title: str
    full_title: str
    description: str
    video_text: str


@dataclass
class ProposedTag:
    course_id: str
    subject_slug: str
    subject_id: str
    score: int
    relationship: str
    reason: str


@dataclass
class ReconcileResult:
    proposed: dict[str, list[ProposedTag]] = field(default_factory=dict)
    untagged: list[Course] = field(default_factory=list)
    added: list[ProposedTag] = field(default_factory=list)
    removed: list[tuple[str, str]] = field(default_factory=list)


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


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.lower()
    value = re.sub(r"[^a-z0-9+#]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def phrase_match(haystack: str, phrase: str) -> bool:
    normalized = normalize(phrase)
    if not normalized:
        return False
    return f" {normalized} " in f" {haystack} "


def strict_title_scope(title: str) -> str:
    return title.split(" | ", 1)[0]


def literal_assignment(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name:
                return ast.literal_eval(node.value)
    raise ValueError(f"{name} not found in {path}")


def load_rules() -> tuple[list[tuple[str, list[str]]], dict[str, list[str]]]:
    rules = literal_assignment(LEGACY_TAGGER, "RULES")
    rollups = literal_assignment(LEGACY_TAGGER, "ROLLUPS")
    return rules, rollups


def subject_phrases(subject: Subject, rules_by_slug: dict[str, list[str]]) -> list[str]:
    raw = [subject.name, subject.slug.replace("-", " "), *rules_by_slug.get(subject.slug, [])]
    seen: set[str] = set()
    phrases: list[str] = []
    for phrase in raw:
        variants = [normalize(phrase)]
        if variants[0].endswith("s") and len(variants[0]) > 5:
            variants.append(variants[0][:-1])
        if " " in variants[0]:
            parts = variants[0].split()
            if parts[-1].endswith("s") and len(parts[-1]) > 4:
                variants.append(" ".join([*parts[:-1], parts[-1][:-1]]))
        for normalized in variants:
            if normalized and normalized not in seen:
                seen.add(normalized)
                phrases.append(normalized)
    return phrases


def distinctive_tokens(phrases: list[str]) -> set[str]:
    tokens: set[str] = set()
    for phrase in phrases:
        tokens.update(phrase.split())
    return {token for token in tokens if len(token) > 2 and token not in GENERIC_TOKENS}


@lru_cache(maxsize=None)
def course_evidence(course: Course) -> CourseEvidence:
    return CourseEvidence(
        title=normalize(strict_title_scope(course.title)),
        full_title=normalize(course.title),
        description=normalize(course.description),
        video_text=normalize(" ".join(course.video_titles[:40])),
    )


def score_subject(
    course: Course,
    prepared: PreparedSubject,
) -> ProposedTag | None:
    subject = prepared.subject
    evidence = course_evidence(course)
    title = evidence.title
    full_title = evidence.full_title
    description = evidence.description
    video_text = evidence.video_text
    phrases = prepared.phrases
    tokens = prepared.tokens

    for phrase in phrases:
        if phrase_match(title, phrase):
            return ProposedTag(
                course_id=course.id,
                subject_slug=subject.slug,
                subject_id=subject.id,
                score=100 if phrase == normalize(subject.name) else 94,
                relationship="title_match",
                reason=f"title contains '{phrase}'",
            )

    for phrase in phrases:
        if phrase_match(full_title, phrase):
            return ProposedTag(
                course_id=course.id,
                subject_slug=subject.slug,
                subject_id=subject.id,
                score=82,
                relationship="title_context_match",
                reason=f"title context contains '{phrase}'",
            )

    if tokens and all(phrase_match(title, token) for token in tokens):
        return ProposedTag(
            course_id=course.id,
            subject_slug=subject.slug,
            subject_id=subject.id,
            score=88,
            relationship="title_token_match",
            reason=f"title contains subject tokens: {', '.join(sorted(tokens))}",
        )

    for phrase in phrases:
        if phrase_match(video_text, phrase):
            return ProposedTag(
                course_id=course.id,
                subject_slug=subject.slug,
                subject_id=subject.id,
                score=76,
                relationship="video_title_match",
                reason=f"video titles contain '{phrase}'",
            )

    for phrase in phrases:
        if phrase_match(description, phrase):
            return ProposedTag(
                course_id=course.id,
                subject_slug=subject.slug,
                subject_id=subject.id,
                score=72,
                relationship="description_match",
                reason=f"description contains '{phrase}'",
            )

    return None


def suppress_rollups(tags: list[ProposedTag], rollups: dict[str, list[str]]) -> list[ProposedTag]:
    direct_slugs = {tag.subject_slug for tag in tags}
    has_specific_subject = any(slug not in GENERIC_SUBJECT_SLUGS for slug in direct_slugs)
    suppress: set[str] = set()
    for slug in direct_slugs:
        suppress.update(rollups.get(slug, []))
    result: list[ProposedTag] = []
    for tag in tags:
        if has_specific_subject and tag.subject_slug in GENERIC_SUBJECT_SLUGS:
            continue
        if tag.subject_slug not in suppress:
            result.append(tag)
            continue
        if tag.subject_slug in GENERIC_SUBJECT_SLUGS:
            continue
        if tag.relationship == "title_match" and tag.score >= 100:
            result.append(tag)
            continue
        result.append(tag)
    return result


def heuristic_subject_slugs(course: Course) -> list[tuple[str, int, str]]:
    title = normalize(course.title)
    raw_title = course.title
    source = course.source_key
    matches: list[tuple[str, int, str]] = []

    def add(slug: str, score: int, reason: str) -> None:
        matches.append((slug, score, reason))

    if re.search(r"\b(cs|cse|comp\s*sci)\s*[-:]?\s*\d", title) or "cs50" in title:
        add("computer-science", 74, "course code indicates computer science")
    if "eecs" in title:
        add("computer-science", 74, "course code indicates computer science")
        add("electrical-engineering", 74, "course code indicates electrical engineering")
    if any(phrase in title for phrase in ("algorithm", "toolbox", "big o", "asymptotic notation")):
        add("algorithms", 78, "title indicates algorithms")
    if re.search(r"\b(chm|chem)\s*[-:]?\s*\d", title):
        add("chemistry", 74, "course code indicates chemistry")
    if re.search(r"\bbme\s*[-:]?\s*\d", title):
        add("bioengineering", 74, "course code indicates biomedical engineering")
    if re.search(r"\b(econ|ec|bem)\s*[-:]?\s*\d", title):
        add("economics", 72, "course code indicates economics")
    if any(phrase in title for phrase in ("mixed signal", "rf ", "integrated circuit", " ics")):
        add("electronics", 76, "title indicates electronics")
        add("circuits", 76, "title indicates circuits")
    if "control system" in title:
        add("control-systems", 78, "title indicates control systems")
    if "javascript" in title or "p5 js" in title or "p5.js" in title:
        add("javascript", 76, "title indicates JavaScript")
    if "python" in title:
        add("python", 76, "title indicates Python")
    if "c#" in raw_title.lower():
        add("programming", 72, "title indicates programming language")
    if source == "ictp_diploma":
        if "cmp eps" in title or "electrons and phonons" in title:
            add("condensed-matter", 90, "ICTP diploma code/title indicates condensed matter")
            add("solid-state-physics", 88, "ICTP title indicates solid-state physics")
        if "cmp pt" in title or "phase transitions" in title:
            add("condensed-matter", 90, "ICTP diploma code/title indicates condensed matter")
            add("statistical-mechanics", 88, "ICTP title indicates phase transitions")
        if "hep ll" in title or "lie groups and lie algebras" in title:
            add("group-theory", 90, "ICTP code/title indicates Lie groups and Lie algebras")
            add("representation-theory", 86, "ICTP title indicates Lie algebra representations")
        if "esp sg" in title or "space geodesy" in title or "insar" in title:
            add("earth-science", 88, "ICTP diploma code/title indicates geoscience")
            add("geology", 78, "ICTP title indicates geodesy")
        if "qls bio" in title or "biophysics" in title:
            add("biology", 82, "ICTP diploma code/title indicates biophysics")
            add("physics", 78, "ICTP diploma code/title indicates biophysics")

    if re.search(r"\bmit\s+11\s+", title):
        add("urban-planning", 82, "MIT 11 course number indicates urban studies/planning")
    if re.search(r"\bmit\s+21f\s+", title):
        add("language", 82, "MIT 21F course number indicates language")
    if re.search(r"\bmit\s+21m\s+", title):
        add("music", 82, "MIT 21M course number indicates music")
    if re.search(r"\bmit\s+3\s+", title):
        add("materials-science", 82, "MIT 3 course number indicates materials science")
    if re.search(r"\bmit\s+6\s+013\b", title) or "electromagnetics" in title:
        add("electromagnetism", 86, "title indicates electromagnetics")
        add("electrical-engineering", 78, "MIT 6.013 is electrical engineering")
    if "nanomaker" in title:
        add("nanotechnology", 82, "title indicates nanotechnology")
    if "digital lab techniques" in title:
        add("chemistry", 78, "title indicates laboratory chemistry techniques")

    if "data 102" in title and "data inference and decisions" in title:
        add("data-science", 90, "Berkeley Data 102 title indicates data science")
        add("statistics", 84, "Berkeley Data 102 title indicates statistical inference")
        add("decision-theory", 76, "Berkeley Data 102 title indicates decisions")
    if "cme296" in title or "large vision models" in title:
        add("computer-vision", 90, "title indicates computer vision")
        add("generative-models", 84, "title indicates diffusion models")
        add("deep-learning", 80, "title indicates large vision models")
    if "darwin" in title and "legacy" in title:
        add("evolution", 84, "title indicates Darwin and evolution")
        add("biology", 74, "title indicates Darwin and biology")
    if "fourier transforms" in title or "fourier transform" in title:
        add("harmonic-analysis", 84, "title indicates Fourier transforms")
        add("signal-processing", 76, "Fourier transforms are signal-processing evidence")
    if "human emotion" in title:
        add("psychology", 82, "title indicates human emotion")
    if "bible study" in title:
        add("religious-studies", 82, "title indicates Bible study")
        add("religion", 78, "title indicates Bible study")
    if "masterpieces of western art" in title:
        add("art-history", 86, "title indicates western art history")
    if "einstein vacuum equations" in title:
        add("general-relativity", 88, "title indicates Einstein vacuum equations")
        add("relativity", 80, "title indicates relativity")
    if "physical problem solving" in title:
        add("physics", 80, "title indicates physics problem solving")
    if "lyapunov" in title:
        add("differential-equations", 80, "title indicates Lyapunov exponents")
        add("control-systems", 76, "title indicates stability analysis")
    if "lead lag compensator" in title or "lead lag compensators" in title:
        add("control-systems", 84, "title indicates control compensators")
    if "bode plot" in title or "bode plots" in title:
        add("control-systems", 82, "title indicates Bode plots")
    if "matrix groups" in title:
        add("group-theory", 84, "title indicates matrix groups")
        add("linear-algebra", 78, "title indicates matrix groups")
    if "elliptic functions" in title:
        add("complex-analysis", 84, "title indicates elliptic functions")
    if "semigroups and their representations" in title:
        add("representation-theory", 84, "title indicates semigroup representations")
        add("group-theory", 76, "title indicates semigroups")
    if title == "prealgebra" or "pre algebra" in title:
        add("algebra", 82, "title indicates prealgebra")
    if "covariance and variance" in title or "bayes theorem" in title:
        add("statistics", 84, "title indicates statistics")
        add("probability", 78, "title indicates probability")
    if "kalman filter" in title:
        add("control-systems", 84, "title indicates Kalman filtering")
        add("signal-processing", 76, "title indicates filtering")
    if "fundamental investing" in title:
        add("finance", 82, "title indicates investing")
    if "application of stacks" in title:
        add("data-structures", 82, "title indicates stack data structures")
        add("computer-science", 74, "title indicates data structures")
    if "context free grammar" in title or "cfgs" in title:
        add("theory-of-computing", 86, "title indicates formal languages")
        add("computer-science", 74, "title indicates formal grammars")
    if "cisco packet tracer" in title:
        add("networking", 84, "title indicates packet networking")
        add("computer-networks", 82, "title indicates networking")
    if "code smells" in title:
        add("software-engineering", 82, "title indicates code quality")
    if "discrete markov chains" in title:
        add("stochastic-processes", 88, "title indicates Markov chains")
        add("probability", 78, "title indicates stochastic processes")
    if "homological stability" in title:
        add("homological-algebra", 86, "title indicates homological methods")
        add("algebraic-topology", 78, "title indicates homological stability")
    if "quiver moduli" in title or "moduli spaces" in title:
        add("algebraic-geometry", 82, "title indicates moduli spaces")
        add("representation-theory", 76, "title indicates quivers")
    if "p adic numbers" in title or "p-adic numbers" in raw_title.lower():
        add("number-theory", 86, "title indicates p-adic numbers")
    if "gromov hyperbolic groups" in title:
        add("group-theory", 86, "title indicates hyperbolic groups")
        add("geometry", 76, "title indicates geometric group theory")
    if "grothendieck duality" in title or "toric varieties" in title or "k3 surfaces" in title:
        add("algebraic-geometry", 86, "title indicates algebraic geometry")
    if "fluid flows" in title or "concentrated vorticity" in title:
        add("fluid-dynamics", 84, "title indicates fluid flows")
    if "isoperimetric inequalities" in title:
        add("geometry", 82, "title indicates geometric inequalities")
        add("analysis", 74, "title indicates inequalities")
    if "lie algebras" in title:
        add("group-theory", 86, "title indicates Lie algebras")
        add("representation-theory", 82, "title indicates Lie algebra representations")
    if "motives and l functions" in title or "zagier salam" in title:
        add("number-theory", 84, "title indicates L-functions/number theory")
        add("algebraic-geometry", 76, "title indicates motives")
    if "nonlinear pdes" in title or "nonlinear pde" in title:
        add("differential-equations", 86, "title indicates PDEs")
    if "pseudorandomness" in title:
        add("theory-of-computing", 84, "title indicates pseudorandomness")
        add("algorithms", 74, "title indicates theoretical computer science")
    if "rational points" in title:
        add("number-theory", 84, "title indicates rational points")
        add("algebraic-geometry", 78, "title indicates arithmetic geometry")
    if "asymptotic methods" in title:
        add("analysis", 80, "title indicates asymptotic methods")
        add("applied-mathematics", 74, "title indicates mathematical methods")
    if "complex networks" in title:
        add("graph-theory", 82, "title indicates networks")
        add("networking", 72, "title indicates networks")
    if "supersymmetry" in title:
        add("theoretical-physics", 82, "title indicates supersymmetry")
        add("mathematics", 72, "title indicates mathematical physics")
    if "symmetric functions" in title or "young diagrams" in title:
        add("combinatorics", 84, "title indicates symmetric functions")
        add("representation-theory", 78, "title indicates Young diagrams")
    if "graphs and randomness" in title:
        add("graph-theory", 86, "title indicates graphs")
        add("probability", 78, "title indicates randomness")
    if "hasse diagram" in title or "partially ordered sets" in title:
        add("discrete-mathematics", 84, "title indicates partially ordered sets")
        add("set-theory", 76, "title indicates ordered sets")
    if "hyperbolic manifolds" in title:
        add("geometry", 84, "title indicates hyperbolic manifolds")
        add("topology", 76, "title indicates manifolds")
    if "laplace transform" in title:
        add("differential-equations", 82, "title indicates Laplace transforms")
        add("signal-processing", 74, "title indicates transforms")

    return matches


def is_catalog_ready_title(title: str) -> bool:
    lowered = title.lower()
    stripped = title.strip()
    return (
        not stripped.startswith(("#", "@"))
        and not NON_ENGLISH_SCRIPT_RE.search(title)
        and not any(fragment in lowered for fragment in NON_COURSE_TITLE_FRAGMENTS)
    )


def build_proposals(
    courses: list[Course],
    subjects: list[Subject],
    rules: list[tuple[str, list[str]]],
    rollups: dict[str, list[str]],
) -> ReconcileResult:
    subjects_by_slug = {subject.slug: subject for subject in subjects}
    rules_by_slug = {slug: keywords for slug, keywords in rules}
    ordered_subjects = [
        subjects_by_slug[slug]
        for slug, _keywords in rules
        if slug in subjects_by_slug
    ]
    existing_slugs = {subject.slug for subject in subjects}
    ordered_subjects.extend(
        subject for subject in subjects if subject.slug not in {s.slug for s in ordered_subjects}
    )
    prepared_subjects = [
        PreparedSubject(
            subject=subject,
            phrases=tuple(subject_phrases(subject, rules_by_slug)),
            tokens=frozenset(distinctive_tokens(subject_phrases(subject, rules_by_slug))),
        )
        for subject in ordered_subjects
    ]

    result = ReconcileResult()
    for course in courses:
        if not is_catalog_ready_title(course.title):
            continue
        scored: dict[str, ProposedTag] = {}
        for prepared in prepared_subjects:
            subject = prepared.subject
            if subject.slug not in existing_slugs:
                continue
            tag = score_subject(course, prepared)
            if tag is None:
                continue
            existing = scored.get(tag.subject_slug)
            if existing is None or tag.score > existing.score:
                scored[tag.subject_slug] = tag
        for slug, score, reason in heuristic_subject_slugs(course):
            subject = subjects_by_slug.get(slug)
            if subject is None:
                continue
            existing = scored.get(slug)
            tag = ProposedTag(
                course_id=course.id,
                subject_slug=slug,
                subject_id=subject.id,
                score=score,
                relationship="course_code_match",
                reason=reason,
            )
            if existing is None or tag.score > existing.score:
                scored[slug] = tag

        proposed = sorted(
            suppress_rollups(list(scored.values()), rollups),
            key=lambda tag: (-tag.score, tag.subject_slug),
        )
        result.proposed[course.id] = proposed
        proposed_slugs = {tag.subject_slug for tag in proposed}
        if not proposed:
            result.untagged.append(course)
        for tag in proposed:
            if tag.subject_slug not in course.existing_subjects:
                result.added.append(tag)
        for slug in course.existing_subjects - proposed_slugs:
            result.removed.append((course.id, slug))
    return result


def load_db_data(conn) -> tuple[list[Course], list[Subject]]:
    cur = conn.cursor()
    cur.execute("SELECT id::text, slug, name FROM subjects ORDER BY slug")
    subjects = [Subject(id=row[0], slug=row[1], name=row[2]) for row in cur.fetchall()]
    blockers_sql = " AND ".join(["c.title NOT ILIKE %s" for _ in NON_COURSE_TITLE_FRAGMENTS])
    cur.execute(
        f"""
        WITH subject_agg AS (
          SELECT
            cs.course_id,
            array_agg(DISTINCT s.slug) FILTER (WHERE s.slug IS NOT NULL) AS subject_slugs
          FROM course_subjects cs
          JOIN subjects s ON s.id = cs.subject_id
          GROUP BY cs.course_id
        ),
        video_agg AS (
          SELECT
            course_id,
            array_agg(title ORDER BY "order") FILTER (WHERE title IS NOT NULL) AS video_titles
          FROM videos
          GROUP BY course_id
        )
        SELECT
          c.id::text,
          c.title,
          COALESCE(c.description, ''),
          c.source_key,
          COALESCE(c.source_url, ''),
          COALESCE(c.course_number, ''),
          COALESCE(sa.subject_slugs, '{{}}'),
          COALESCE(va.video_titles, '{{}}')
        FROM courses c
        LEFT JOIN subject_agg sa ON sa.course_id = c.id
        JOIN video_agg va ON va.course_id = c.id
        WHERE c.is_published = TRUE
          AND c.has_video_lectures = TRUE
          AND c.total_videos > 0
          AND NOT (c.source_key = ANY(%s))
          AND {blockers_sql}
        ORDER BY c.title
        """,
        [list(NON_CATALOG_SOURCE_KEYS), *[f"%{fragment}%" for fragment in NON_COURSE_TITLE_FRAGMENTS]],
    )
    courses = [
        Course(
            id=row[0],
            title=row[1],
            description=row[2] or "",
            source_key=row[3],
            source_url=row[4] or "",
            course_number=row[5] or "",
            video_titles=tuple(row[7] or ()),
            existing_subjects=frozenset(row[6] or []),
        )
        for row in cur.fetchall()
        if is_catalog_ready_title(row[1])
    ]
    return courses, subjects


def fetch_api_page(api_base: str, path: str, page: int, page_size: int) -> dict:
    url = urljoin(api_base.rstrip("/") + "/", path.lstrip("/"))
    url = f"{url}?{urlencode({'page': page, 'page_size': page_size})}"
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            with urlopen(url, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504}:
                raise
        except URLError as exc:
            last_error = exc
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}") from last_error


def fetch_api_items(api_base: str, path: str, page_size: int) -> list[dict]:
    first = fetch_api_page(api_base, path, 1, page_size)
    items = list(first["items"])
    for page in range(2, first["pages"] + 1):
        items.extend(fetch_api_page(api_base, path, page, page_size)["items"])
    return items


def load_api_data(api_base: str, page_size: int) -> tuple[list[Course], list[Subject]]:
    subject_items = fetch_api_items(api_base, "/api/v1/subjects", page_size)
    subjects = [
        Subject(id=item["id"], slug=item["slug"], name=item["name"])
        for item in subject_items
    ]
    course_items = fetch_api_items(api_base, "/api/v1/courses", page_size)
    courses = [
        Course(
            id=item["id"],
            title=item["title"],
            description=item.get("description") or "",
            source_key=item["source_key"],
            source_url=item.get("source_url") or "",
            course_number=item.get("course_number") or "",
            video_titles=(),
            existing_subjects=frozenset(subject["slug"] for subject in item.get("subjects", [])),
        )
        for item in course_items
        if is_catalog_ready_title(item["title"])
    ]
    return courses, subjects


def backup_existing_tags(conn, courses: list[Course]) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = BACKUP_DIR / f"course_subjects_backup_{stamp}.csv"
    ids = [course.id for course in courses]
    cur = conn.cursor()
    cur.execute(
        """
        SELECT cs.course_id::text, cs.subject_id::text, s.slug
        FROM course_subjects cs
        JOIN subjects s ON s.id = cs.subject_id
        WHERE cs.course_id = ANY(%s)
        ORDER BY cs.course_id, s.slug
        """,
        (ids,),
    )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["course_id", "subject_id", "subject_slug"])
        writer.writerows(cur.fetchall())
    return path


def apply_tags(conn, courses: list[Course], result: ReconcileResult) -> Path:
    if result.untagged:
        raise RuntimeError(
            f"Refusing to apply: {len(result.untagged)} catalog-ready courses have no proposed tags."
        )
    backup_path = backup_existing_tags(conn, courses)
    course_ids = [course.id for course in courses]
    rows = [
        (tag.course_id, tag.subject_id)
        for tags in result.proposed.values()
        for tag in tags
    ]
    relevance_rows = [
        (
            str(uuid.uuid4()),
            tag.course_id,
            tag.subject_id,
            tag.score,
            tag.relationship,
            tag.reason,
            SOURCE,
            VERSION,
        )
        for tags in result.proposed.values()
        for tag in tags
    ]
    cur = conn.cursor()
    cur.execute("DELETE FROM course_subjects WHERE course_id = ANY(%s)", (course_ids,))
    cur.executemany(
        "INSERT INTO course_subjects (course_id, subject_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        rows,
    )
    cur.execute("SELECT to_regclass('public.course_subject_relevance')")
    has_relevance_table = cur.fetchone()[0] is not None
    if has_relevance_table:
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
            """,
            relevance_rows,
        )
    conn.commit()
    return backup_path


def write_report(courses: list[Course], result: ReconcileResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "status",
                "course_id",
                "title",
                "source_key",
                "existing_subjects",
                "proposed_subjects",
                "evidence",
            ]
        )
        by_id = {course.id: course for course in courses}
        for course in courses:
            tags = result.proposed.get(course.id, [])
            status = "untagged" if not tags else "tagged"
            writer.writerow(
                [
                    status,
                    course.id,
                    course.title,
                    course.source_key,
                    "|".join(sorted(course.existing_subjects)),
                    "|".join(tag.subject_slug for tag in tags),
                    " || ".join(f"{tag.subject_slug}:{tag.relationship}:{tag.reason}" for tag in tags),
                ]
            )
        for course_id, slug in result.removed:
            course = by_id.get(course_id)
            writer.writerow(
                [
                    "would_remove",
                    course_id,
                    course.title if course else "",
                    course.source_key if course else "",
                    slug,
                    "",
                    "existing tag has no direct catalog evidence",
                ]
            )


def print_summary(courses: list[Course], result: ReconcileResult, report_path: Path) -> None:
    tagged = len(courses) - len(result.untagged)
    print(f"Catalog-ready courses: {len(courses):,}")
    print(f"Courses with proposed tags: {tagged:,}")
    print(f"Courses with no proposed tags: {len(result.untagged):,}")
    print(f"Tags that would be added: {len(result.added):,}")
    print(f"Existing tags that would be removed: {len(result.removed):,}")
    print(f"Report: {report_path}")
    if result.untagged:
        print("\nFirst untagged courses:")
        for course in result.untagged[:20]:
            print(f"  {course.title} [{course.source_key}]")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="replace catalog-ready course_subjects")
    parser.add_argument("--api-base", help="audit visible API data instead of DATABASE_URL")
    parser.add_argument("--page-size", type=int, default=50, help="API page size for report-only audits")
    parser.add_argument(
        "--report",
        default=str(SCRIPT_DIR / "tag_audit_report.csv"),
        help="CSV report path",
    )
    args = parser.parse_args()

    if args.apply and args.api_base:
        raise SystemExit("--apply requires DATABASE_URL; API mode is report-only")

    rules, rollups = load_rules()
    conn = None
    try:
        if args.api_base:
            courses, subjects = load_api_data(args.api_base, args.page_size)
        else:
            database_url = os.environ.get("DATABASE_URL")
            if not database_url:
                raise SystemExit("DATABASE_URL is required unless --api-base is used")
            conn = psycopg.connect(psycopg_url(database_url))
            courses, subjects = load_db_data(conn)

        result = build_proposals(courses, subjects, rules, rollups)
        report_path = Path(args.report)
        write_report(courses, result, report_path)
        print_summary(courses, result, report_path)

        if args.apply:
            if conn is None:
                raise SystemExit("--apply requires DATABASE_URL")
            backup_path = apply_tags(conn, courses, result)
            print(f"Applied tags. Backup: {backup_path}")
        else:
            print("Report-only. Re-run with --apply after the untagged count is 0.")
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    main()
