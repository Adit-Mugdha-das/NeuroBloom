from app.services.sart_task import SARTTask


def test_generate_session_structure():
    session = SARTTask.generate_session(5)

    assert session["difficulty"] == 5
    assert session["total_trials"] == 78
    assert len(session["trials"]) == 78
    assert "target_digit" in session


def test_score_session_perfect_performance():
    session = SARTTask.generate_session(3)
    responses = []

    for trial in session["trials"]:
        responses.append(
            {
                "trial_index": trial["trial_index"],
                "responded": trial["should_respond"],
                "reaction_time_ms": 410 if trial["should_respond"] else 0,
            }
        )

    results = SARTTask.score_session(session, responses)

    assert results["metrics"]["accuracy"] == 100.0
    assert results["metrics"]["commission_errors"] == 0
    assert results["difficulty_adjustment"] >= 3


def test_score_session_commission_errors_reduce_score():
    session = SARTTask.generate_session(4)
    responses = []

    for trial in session["trials"]:
        responses.append(
            {
                "trial_index": trial["trial_index"],
                "responded": True,
                "reaction_time_ms": 420,
            }
        )

    results = SARTTask.score_session(session, responses)

    assert results["metrics"]["commission_errors"] > 0
    assert results["metrics"]["score"] < 84
