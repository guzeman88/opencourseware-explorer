from scraper.audit_course_title_integrity import CourseRow, audit, inspect_course


def course(
    title: str,
    video_titles: tuple[str, ...],
    total_videos: int = 8,
    course_id: str | None = None,
) -> CourseRow:
    return CourseRow(
        course_id=course_id or title.lower().replace(" ", "-"),
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


def test_numbered_chapter_gets_inferred_parent_title():
    issues = audit(
        [
            course(
                "10: Images and Pixels - Processing Tutorial",
                ("10.1: Intro to Images - Processing Tutorial",),
            )
        ]
    )

    assert issues[0].parent_action == "create_or_rename_parent_course"
    assert issues[0].parent_course_title == "Processing Tutorial"


def test_matching_existing_parent_course_is_found():
    issues = audit(
        [
            course("Processing Tutorial", ("Welcome",), total_videos=60, course_id="parent"),
            course(
                "10: Images and Pixels - Processing Tutorial",
                ("10.1: Intro to Images - Processing Tutorial",),
                course_id="child",
            ),
        ]
    )

    assert issues[0].parent_action == "merge_existing_course"
    assert issues[0].parent_course_id == "parent"


def test_sibling_subplaylist_is_not_used_as_parent():
    issues = audit(
        [
            course(
                "11: Video - Processing Tutorial",
                ("11.1: Capture and Live Video - Processing Tutorial",),
                course_id="sibling",
            ),
            course(
                "10: Images and Pixels - Processing Tutorial",
                ("10.1: Intro to Images - Processing Tutorial",),
                course_id="child",
            ),
        ]
    )

    target = next(issue for issue in issues if issue.course.course_id == "child")
    assert target.parent_action == "create_or_rename_parent_course"
    assert target.parent_course_title == "Processing Tutorial"


def test_covid_title_is_not_treated_as_a_course_code_parent():
    issues = audit(
        [
            course(
                "COVID-19: Preventing transmission",
                ("Understanding transmission",),
                course_id="covid",
            )
        ]
    )

    assert issues[0].parent_action == "unpublish_no_parent_found"


def test_pipe_subtopic_uses_left_side_as_parent():
    issues = audit(
        [
            course(
                "Abstract Algebra | Cyclic Groups",
                ("Abstract Algebra | Cyclic Groups",),
                course_id="subtopic",
            )
        ]
    )

    assert issues[0].parent_action == "create_or_rename_parent_course"
    assert issues[0].parent_course_title == "Abstract Algebra"


def test_event_dash_title_does_not_infer_parent_from_date():
    issues = audit(
        [
            course(
                "OCW Consortium Global Conference - May 2011",
                ("Opening remarks",),
                course_id="event",
            )
        ]
    )

    assert issues[0].parent_action == "unpublish_no_parent_found"


def test_cs50_outtake_does_not_merge_into_one_off_cs50_video():
    issues = audit(
        [
            course("CS50 Fair 2013 in Slow Motion", ("CS50 Fair 2013 in Slow Motion",), course_id="fair"),
            course("CS50 Outtakes 2013", ("CS50 Outtakes 2013",), course_id="outtakes"),
        ]
    )

    target = next(issue for issue in issues if issue.course.course_id == "outtakes")
    assert target.parent_action == "review_course_code_parent"
    assert target.parent_course_title == "CS50"


def test_non_course_exact_parent_is_not_merge_ready():
    issues = audit(
        [
            course("UBC Library", ("Library introduction",), total_videos=40, course_id="library"),
            course("UBC Library | EDUC500 Tutorials", ("Tutorial 1",), course_id="tutorials"),
        ]
    )

    target = next(issue for issue in issues if issue.course.course_id == "tutorials")
    assert target.parent_action == "unpublish_no_parent_found"
