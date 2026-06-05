from scraper.audit_course_title_integrity import CourseRow, inspect_course


def course(title: str, video_titles: tuple[str, ...], total_videos: int = 8) -> CourseRow:
    return CourseRow(
        course_id="course-1",
        title=title,
        source_key="test",
        university_name="Test University",
        source_url="",
        youtube_playlist_id="playlist",
        total_videos=total_videos,
        total_duration_seconds=0,
        is_published=True,
        video_titles=video_titles,
    )


def test_course_code_title_is_not_flagged_just_because_video_titles_are_weird():
    issue = inspect_course(
        course(
            "CS 168: The Modern Algorithmic Toolbox",
            ("tjf l25", "tjf l24", "tjf l23"),
            total_videos=25,
        )
    )

    assert issue is None


def test_numbered_tutorial_chapter_is_flagged_for_unpublish_review():
    issue = inspect_course(
        course(
            "10: Images and Pixels - Processing Tutorial",
            ("10.1: Intro to Images - Processing Tutorial",),
            total_videos=7,
        )
    )

    assert issue is not None
    assert issue.suggested_action == "review_unpublish"


def test_exact_video_title_match_is_flagged():
    issue = inspect_course(
        course(
            "Lecture 1 Introduction",
            ("Lecture 1 Introduction", "Lecture 2 Next Topic"),
            total_videos=12,
        )
    )

    assert issue is not None
    assert "course title exactly matches a video title" in issue.reasons
