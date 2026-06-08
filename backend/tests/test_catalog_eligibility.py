from app.catalog_eligibility import EligibilityInput, evaluate_catalog_eligibility


def decide(**overrides):
    values = {
        "source_key": "mit_ocw",
        "title": "Linear Algebra",
        "is_published": True,
        "has_video_lectures": True,
        "youtube_playlist_id": "PL123",
        "total_videos": 10,
        "actual_video_count": 10,
    }
    values.update(overrides)
    return evaluate_catalog_eligibility(EligibilityInput(**values))


def test_verified_video_course_is_eligible():
    decision = decide()
    assert decision.status == "eligible"
    assert decision.current_catalog_ready is True


def test_counter_mismatch_does_not_hide_valid_video_course():
    decision = decide(total_videos=8)
    assert decision.status == "eligible"
    assert decision.reasons == ("video_counter_mismatch",)


def test_credible_missing_video_rows_are_preserved_for_review():
    decision = decide(total_videos=0, actual_video_count=0)
    assert decision.status == "review"
    assert decision.reasons == ("credible_video_evidence_without_rows",)


def test_non_catalog_source_is_definitively_excluded():
    decision = decide(source_key="nptel")
    assert decision.status == "excluded"
    assert decision.reasons == ("excluded_source",)


def test_language_and_title_concerns_are_reviewed_not_deleted():
    decision = decide(title="Conference по физике")
    assert decision.status == "review"
    assert "language_review" in decision.reasons
    assert "title_quality_review" in decision.reasons
