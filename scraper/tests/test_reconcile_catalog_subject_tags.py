from scraper.reconcile_catalog_subject_tags import (
    Course,
    ProposedTag,
    ReconcileResult,
    Subject,
    build_membership_rows,
    build_proposals,
)


SUBJECTS = [
    Subject(id="1", slug="discrete-mathematics", name="Discrete Mathematics"),
    Subject(id="2", slug="logic", name="Logic"),
    Subject(id="3", slug="proof-writing", name="Proof Writing"),
    Subject(id="4", slug="combinatorics", name="Combinatorics"),
    Subject(id="5", slug="mathematics", name="Mathematics"),
]

RULES = [
    ("discrete-mathematics", ["discrete mathematics", "discrete math"]),
    ("logic", ["logic", "mathematical logic"]),
    ("proof-writing", ["proof writing", "proofs", "proof", "logic and proof"]),
    ("combinatorics", ["combinatorics", "combinatorial"]),
    ("mathematics", ["mathematics", "mathematical"]),
]

ROLLUPS = {
    "combinatorics": ["discrete-mathematics", "mathematics"],
    "logic": ["discrete-mathematics", "mathematics"],
    "proof-writing": ["mathematics"],
}


def course(title: str) -> Course:
    return Course(
        id=title.lower().replace(" ", "-"),
        title=title,
        description="",
        source_key="test",
        source_url="",
        course_number="",
        video_titles=(),
        existing_subjects=frozenset(),
    )


def proposed_slugs(title: str) -> set[str]:
    result = build_proposals([course(title)], SUBJECTS, RULES, ROLLUPS)
    return {tag.subject_slug for tag in result.proposed[course(title).id]}


def test_discrete_math_stays_discrete():
    assert proposed_slugs("Discrete Mathematics") == {"discrete-mathematics"}


def test_logic_and_proof_gets_both_direct_subjects_without_discrete_rollup():
    assert proposed_slugs("Logic and Proof") == {"logic", "proof-writing"}


def test_combinatorics_does_not_roll_up_to_discrete_math():
    assert proposed_slugs("Enumerative Combinatorics") == {"combinatorics"}


def test_membership_rows_include_required_ids():
    result = ReconcileResult(
        proposed={
            "course-1": [
                ProposedTag(
                    course_id="course-1",
                    subject_slug="logic",
                    subject_id="subject-1",
                    score=100,
                    relationship="title_match",
                    reason="exact title match",
                )
            ]
        }
    )

    rows = build_membership_rows(result)

    assert len(rows) == 1
    assert rows[0][0]
    assert rows[0][1:] == ("course-1", "subject-1")
