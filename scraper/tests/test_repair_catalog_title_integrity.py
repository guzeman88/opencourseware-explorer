from scraper.audit_course_title_integrity import CourseRow, Issue
from scraper.repair_catalog_title_integrity import classify_issue


def course(title: str, total_videos: int = 8, source_key: str = "test") -> CourseRow:
    return CourseRow(
        course_id=title.lower().replace(" ", "-"),
        title=title,
        source_key=source_key,
        university_name="Test University",
        source_url="",
        youtube_playlist_id="playlist",
        total_videos=total_videos,
        total_duration_seconds=0,
        is_published=True,
        video_titles=(title,),
    )


def issue_for(
    title: str,
    reasons: tuple[str, ...] = (),
    total_videos: int = 8,
    source_key: str = "test",
    parent_action: str = "",
    parent_course_title: str = "",
    parent_course_id: str = "",
) -> Issue:
    return Issue(
        course=course(title, total_videos=total_videos, source_key=source_key),
        score=50,
        reasons=reasons,
        suggested_action="review_unpublish",
        suggested_title="",
        parent_action=parent_action,
        parent_course_id=parent_course_id,
        parent_course_title=parent_course_title,
    )


def test_hard_non_course_is_unpublished():
    decision = classify_issue(issue_for("Campus Life Highlights"))

    assert decision.category == "not_lectures_or_courses"
    assert decision.operation == "unpublish"


def test_workshop_is_unpublished_as_educational_non_course():
    decision = classify_issue(issue_for("Workshop: Harmonic Analysis and Rough Paths"))

    assert decision.category == "workshop_conference_individual_lecture"
    assert decision.operation == "unpublish"


def test_trusted_course_like_playlist_is_renamed_or_merged():
    decision = classify_issue(
        issue_for(
            "Artificial Intelligence 2023 Playlist",
            total_videos=22,
            source_key="stanford",
        )
    )

    assert decision.category == "course_like_playlist"
    assert decision.operation == "rename_or_merge_course_like_playlist"
    assert decision.clean_title == "Artificial Intelligence 2023"


def test_playlist_cleanup_removes_trailing_tutorial_packaging():
    decision = classify_issue(
        issue_for(
            "Calculus Tutorial Playlist",
            total_videos=41,
            source_key="bill_kinney",
        )
    )

    assert decision.operation == "rename_or_merge_course_like_playlist"
    assert decision.clean_title == "Calculus"


def test_untrusted_course_like_playlist_is_unpublished():
    decision = classify_issue(
        issue_for("Game Programming Tutorials", total_videos=26, source_key="freecodecamp")
    )

    assert decision.category == "course_like_playlist"
    assert decision.operation == "unpublish"


def test_parent_fragment_creates_parent_and_merges():
    decision = classify_issue(
        issue_for(
            "10: Images and Pixels - Processing Tutorial",
            parent_action="create_or_rename_parent_course",
            parent_course_title="Processing Tutorial",
        )
    )

    assert decision.category == "parent_course_fragment"
    assert decision.operation == "create_parent_and_merge"
