from scripts.build_subject_catalog_counts import build_counts


def test_build_counts_matches_multi_subject_titles():
    courses = [
        {"id": "1", "title": "Logic and Proof"},
        {"id": "2", "title": "Discrete Mathematics"},
    ]
    subjects = [
        {"id": "logic", "slug": "logic", "name": "Logic"},
        {"id": "proof", "slug": "proof-writing", "name": "Proof Writing"},
        {"id": "discrete", "slug": "discrete-mathematics", "name": "Discrete Mathematics"},
    ]

    counts = {row["slug"]: row["course_count"] for row in build_counts(courses, subjects)}

    assert counts == {"logic": 1, "proof-writing": 1, "discrete-mathematics": 1}


def test_build_counts_prefers_relevance_for_subject_result_parity():
    courses = [
        {"id": "1", "title": "Logic and Proof"},
        {"id": "2", "title": "Advanced Logic"},
    ]
    subjects = [{"id": "logic", "slug": "logic", "name": "Logic"}]

    counts = build_counts(courses, subjects, {"logic": {"2", "not-eligible"}})

    assert counts[0]["course_count"] == 1
