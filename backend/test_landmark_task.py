from app.services.landmark_task import LandmarkTask


def test_generate_session_structure():
    session = LandmarkTask.generate_session(5)

    assert session["difficulty"] == 5
    assert session["total_trials"] == 26
    assert len(session["trials"]) == 26
    assert session["response_options"] == ["left", "equal", "right"]


def test_score_session_perfect_performance():
    session = LandmarkTask.generate_session(4)
    responses = []

    for trial in session["trials"]:
        responses.append(
            {
                "trial_index": trial["trial_index"],
                "response": trial["correct_response"],
                "reaction_time_ms": 920,
            }
        )

    results = LandmarkTask.score_session(session, responses)

    assert results["metrics"]["accuracy"] == 100.0
    assert results["metrics"]["spatial_bias_index"] == 0.0
    assert results["difficulty_adjustment"] >= 4


def test_biased_errors_reduce_score():
    session = LandmarkTask.generate_session(6)
    responses = []

    for trial in session["trials"]:
        responses.append(
            {
                "trial_index": trial["trial_index"],
                "response": "left",
                "reaction_time_ms": 1100,
            }
        )

    results = LandmarkTask.score_session(session, responses)

    assert abs(results["metrics"]["spatial_bias_index"]) > 0
    assert results["metrics"]["score"] < 84
