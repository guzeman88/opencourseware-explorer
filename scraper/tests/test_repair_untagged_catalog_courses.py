from scraper.reconcile_catalog_subject_tags import Course
from scraper.repair_untagged_catalog_courses import classify


def course(title: str, source_key: str = "test") -> Course:
    return Course(
        id=title.lower().replace(" ", "-"),
        title=title,
        description="",
        source_key=source_key,
        source_url="",
        course_number="",
        video_titles=(),
        existing_subjects=frozenset(),
    )


def test_non_course_title_is_unpublished():
    decision = classify(course("Access and Opportunity at Princeton", "princeton"))

    assert decision.operation == "unpublish"


def test_topic_fragment_source_is_unpublished():
    decision = classify(course("Absolute Value", "patrickjmt"))

    assert decision.operation == "unpublish"


def test_unknown_untagged_row_needs_review():
    decision = classify(course("Some Unmapped Full Course", "trusted_source"))

    assert decision.operation == "review"
