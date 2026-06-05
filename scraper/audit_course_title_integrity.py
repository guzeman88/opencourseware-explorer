"""Audit course rows whose title looks like a lecture, episode, or sub-playlist.

The subject tag reconciler intentionally reads courses.title. When bad rows show
lecture-style titles there, the fix is not more tagging; it is a course-title
integrity pass that separates real course records from video/chapter/event rows.

Default mode is report-only.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import os

import psycopg


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = SCRIPT_DIR / "course_title_integrity_report.csv"
DEFAULT_HTML = SCRIPT_DIR / "course_title_integrity_report.html"

NON_CATALOG_SOURCE_KEYS = {"nptel"}

NON_COURSE_FRAGMENTS = (
    "admissions",
    "alumni",
    "annual review",
    "apply to",
    "campus",
    "commencement",
    "conference",
    "congregation",
    "conversation",
    "covid",
    "event",
    "forum",
    "graduation",
    "hackathon",
    "highlights",
    "interview",
    "outtakes",
    "playlist",
    "promo",
    "recap",
    "stories",
    "student life",
    "symposium",
    "trailer",
    "workshop",
)

LECTURE_TITLE_PATTERNS = (
    re.compile(r"^\s*(lecture|lec|episode|ep|chapter|part|lesson|session|class)\s+\d+\b", re.I),
    re.compile(r"^\s*week\s+\d+\b", re.I),
    re.compile(r"^\s*\d{1,2}(?:\.\d+)?\s*:\s+\S", re.I),
    re.compile(r"^\s*\d{1,2}(?:\.\d+)?\s*-\s+\S", re.I),
)

SUB_PLAYLIST_FRAGMENTS = (
    "tutorial",
    "walkthrough",
    "solved problems",
    "solved questions",
    "quick concepts",
    "laboratory videos",
    "all videos",
)

COURSE_CODE_RE = re.compile(
    r"\b([A-Z]{2,5}|CS|CSE|EE|EECS|MATH|PHYS|CHEM|BIO|ECON|STAT)\s*[-:]?\s*\d{2,4}[A-Z]?\b"
)


@dataclass(frozen=True)
class CourseRow:
    course_id: str
    title: str
    source_key: str
    university_name: str
    source_url: str
    youtube_playlist_id: str
    total_videos: int
    total_duration_seconds: int
    is_published: bool
    video_titles: tuple[str, ...]


@dataclass(frozen=True)
class Issue:
    course: CourseRow
    score: int
    reasons: tuple[str, ...]
    suggested_action: str
    suggested_title: str


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
    value = value.lower()
    value = re.sub(r"[^a-z0-9+#.]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def load_courses(conn) -> list[CourseRow]:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
          c.id::text,
          c.title,
          c.source_key,
          COALESCE(u.name, ''),
          COALESCE(c.source_url, ''),
          COALESCE(c.youtube_playlist_id, ''),
          c.total_videos,
          c.total_duration_seconds,
          c.is_published,
          COALESCE(array_agg(v.title ORDER BY v."order") FILTER (WHERE v.title IS NOT NULL), '{}')
        FROM courses c
        JOIN universities u ON u.id = c.university_id
        JOIN videos v ON v.course_id = c.id
        WHERE c.has_video_lectures = TRUE
          AND c.total_videos > 0
          AND NOT (c.source_key = ANY(%s))
        GROUP BY c.id, c.title, c.source_key, u.name, c.source_url, c.youtube_playlist_id,
                 c.total_videos, c.total_duration_seconds, c.is_published
        ORDER BY c.title
        """,
        (list(NON_CATALOG_SOURCE_KEYS),),
    )
    return [
        CourseRow(
            course_id=row[0],
            title=row[1],
            source_key=row[2],
            university_name=row[3],
            source_url=row[4],
            youtube_playlist_id=row[5],
            total_videos=row[6],
            total_duration_seconds=row[7],
            is_published=row[8],
            video_titles=tuple(row[9] or ()),
        )
        for row in cur.fetchall()
    ]


def title_matches_video_title(course: CourseRow) -> bool:
    title = normalize(course.title)
    if not title:
        return False
    return any(title == normalize(video_title) for video_title in course.video_titles[:25])


def likely_real_course(course: CourseRow) -> bool:
    title = course.title
    normalized = normalize(title)
    return (
        bool(COURSE_CODE_RE.search(title))
        or "course" in normalized
        or "open yale courses" in normalized
        or "academy shared graduate course" in normalized
    )


def inspect_course(course: CourseRow) -> Issue | None:
    title = course.title
    normalized = normalize(title)
    reasons: list[str] = []
    score = 0

    if title_matches_video_title(course):
        reasons.append("course title exactly matches a video title")
        score += 45

    if any(pattern.search(title) for pattern in LECTURE_TITLE_PATTERNS):
        reasons.append("course title starts like a numbered lecture/chapter")
        score += 35

    if any(fragment in normalized for fragment in SUB_PLAYLIST_FRAGMENTS):
        reasons.append("course title looks like a tutorial/sub-playlist")
        score += 30

    if any(fragment in normalized for fragment in NON_COURSE_FRAGMENTS):
        reasons.append("course title looks like event/promo/non-course material")
        score += 35

    if course.total_videos <= 4 and not likely_real_course(course):
        reasons.append("very few videos and no strong course-level signal")
        score += 20

    if course.total_duration_seconds == 0:
        reasons.append("duration metadata missing; cannot verify full-course length")
        score += 5

    if likely_real_course(course):
        score -= 25
        reasons.append("has a course-level signal; review before changing")

    if score < 30:
        return None

    if "course title exactly matches a video title" in reasons and likely_real_course(course):
        action = "review_rename"
    elif any("event/promo" in reason or "tutorial/sub-playlist" in reason for reason in reasons):
        action = "review_unpublish"
    elif course.total_videos <= 4:
        action = "review_unpublish"
    else:
        action = "review_title"

    return Issue(
        course=course,
        score=max(score, 0),
        reasons=tuple(reasons),
        suggested_action=action,
        suggested_title="",
    )


def audit(courses: list[CourseRow]) -> list[Issue]:
    issues = [issue for course in courses if (issue := inspect_course(course))]
    return sorted(
        issues,
        key=lambda issue: (-issue.score, issue.suggested_action, issue.course.source_key, issue.course.title),
    )


def write_csv(issues: list[Issue], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "suggested_action",
                "score",
                "course_id",
                "course_title",
                "source_key",
                "institution",
                "published",
                "videos",
                "duration_seconds",
                "playlist_id",
                "source_url",
                "reasons",
                "first_video_titles",
            ]
        )
        for issue in issues:
            course = issue.course
            writer.writerow(
                [
                    issue.suggested_action,
                    issue.score,
                    course.course_id,
                    course.title,
                    course.source_key,
                    course.university_name,
                    course.is_published,
                    course.total_videos,
                    course.total_duration_seconds,
                    course.youtube_playlist_id,
                    course.source_url,
                    " | ".join(issue.reasons),
                    " || ".join(course.video_titles[:8]),
                ]
            )


def write_html(issues: list[Issue], path: Path, csv_path: Path) -> None:
    from html import escape

    action_counts: dict[str, int] = {}
    for issue in issues:
        action_counts[issue.suggested_action] = action_counts.get(issue.suggested_action, 0) + 1

    rows = []
    for issue in issues:
        course = issue.course
        rows.append(
            "<tr>"
            f"<td>{escape(issue.suggested_action)}</td>"
            f"<td>{issue.score}</td>"
            f"<td>{escape(course.title)}</td>"
            f"<td>{escape(course.source_key)}</td>"
            f"<td>{escape(course.university_name)}</td>"
            f"<td>{course.total_videos}</td>"
            f"<td>{escape(' | '.join(issue.reasons))}</td>"
            f"<td>{escape(' || '.join(course.video_titles[:8]))}</td>"
            f"<td>{escape(course.youtube_playlist_id)}</td>"
            f"<td>{escape(course.source_url)}</td>"
            "</tr>"
        )

    path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Course Title Integrity Audit</title>
<style>
body {{ margin:0; font-family:Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; background:#f7f8fb; color:#172033; }}
header {{ position:sticky; top:0; z-index:3; background:white; border-bottom:1px solid #dde3ee; padding:20px 24px 14px; }}
h1 {{ margin:0 0 6px; font-size:24px; }}
p {{ margin:0 0 14px; color:#667085; }}
.stats {{ display:flex; flex-wrap:wrap; gap:10px; margin-bottom:12px; }}
.stat {{ min-width:150px; border:1px solid #dde3ee; background:#fafbfe; border-radius:8px; padding:10px 12px; }}
.stat span {{ display:block; color:#667085; font-size:12px; }}
.stat strong {{ display:block; margin-top:4px; font-size:22px; }}
.toolbar {{ display:flex; gap:10px; flex-wrap:wrap; }}
input, select, a {{ height:36px; border:1px solid #dde3ee; border-radius:6px; background:white; padding:0 10px; color:#172033; }}
input {{ min-width:360px; flex:1; }}
a {{ display:inline-flex; align-items:center; text-decoration:none; }}
main {{ padding:18px 24px 30px; }}
table {{ width:100%; table-layout:fixed; border-collapse:separate; border-spacing:0; background:white; border:1px solid #dde3ee; border-radius:8px; overflow:hidden; }}
th, td {{ border-bottom:1px solid #dde3ee; padding:9px 10px; text-align:left; vertical-align:top; font-size:13px; overflow-wrap:anywhere; }}
th {{ position:sticky; top:154px; background:#eef2f8; z-index:2; font-size:12px; color:#344054; }}
th:nth-child(1), td:nth-child(1) {{ width:150px; }}
th:nth-child(2), td:nth-child(2) {{ width:70px; }}
th:nth-child(4), td:nth-child(4) {{ width:130px; }}
th:nth-child(6), td:nth-child(6) {{ width:80px; }}
.hidden {{ display:none; }}
</style>
</head>
<body>
<header>
<h1>Course Title Integrity Audit</h1>
<p>Rows where courses.title may be a lecture, episode, tutorial chapter, event, or other non-course title. No admin login required.</p>
<div class="stats">
  <div class="stat"><span>Flagged rows</span><strong id="visible">{len(issues):,}</strong></div>
  <div class="stat"><span>Review unpublish</span><strong>{action_counts.get('review_unpublish', 0):,}</strong></div>
  <div class="stat"><span>Review title</span><strong>{action_counts.get('review_title', 0):,}</strong></div>
  <div class="stat"><span>Review rename</span><strong>{action_counts.get('review_rename', 0):,}</strong></div>
</div>
<div class="toolbar">
  <input id="q" type="search" placeholder="Search course title, source, institution, reason, or video titles">
  <select id="action"><option value="">All actions</option><option>review_unpublish</option><option>review_title</option><option>review_rename</option></select>
  <a href="{escape(csv_path.name)}" download>Download CSV</a>
</div>
</header>
<main>
<table>
<thead><tr><th>Action</th><th>Score</th><th>Course Title</th><th>Source</th><th>Institution</th><th>Videos</th><th>Reasons</th><th>First Video Titles</th><th>Playlist ID</th><th>Source URL</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
</main>
<script>
const q = document.getElementById('q');
const action = document.getElementById('action');
const visible = document.getElementById('visible');
const rows = Array.from(document.querySelectorAll('tbody tr'));
function applyFilter() {{
  const term = q.value.trim().toLowerCase();
  const selected = action.value;
  let count = 0;
  for (const row of rows) {{
    const okAction = !selected || row.cells[0].textContent === selected;
    const okTerm = !term || row.textContent.toLowerCase().includes(term);
    const show = okAction && okTerm;
    row.classList.toggle('hidden', !show);
    if (show) count++;
  }}
  visible.textContent = count.toLocaleString();
}}
q.addEventListener('input', applyFilter);
action.addEventListener('change', applyFilter);
</script>
</body>
</html>""",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=str(DEFAULT_CSV))
    parser.add_argument("--html", default=str(DEFAULT_HTML))
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required")

    with psycopg.connect(psycopg_url(database_url), connect_timeout=20) as conn:
        courses = load_courses(conn)

    issues = audit(courses)
    csv_path = Path(args.csv)
    html_path = Path(args.html)
    write_csv(issues, csv_path)
    write_html(issues, html_path, csv_path)

    print(f"Video courses inspected: {len(courses):,}")
    print(f"Flagged title-integrity rows: {len(issues):,}")
    print(f"CSV: {csv_path}")
    print(f"HTML: {html_path}")


if __name__ == "__main__":
    main()
