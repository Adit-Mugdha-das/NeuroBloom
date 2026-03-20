from app.services.choice_reaction_time_task import ChoiceReactionTimeTask


def test_generate_session_structure():
    session = ChoiceReactionTimeTask.generate_session(5)

    assert session["difficulty"] == 5
    assert session["total_trials"] == 24
    assert len(session["stimuli"]) == 4
    assert len(session["trials"]) == 24
    assert all("correct_key" in trial for trial in session["trials"])


def test_score_session_correct_responses():
    session = ChoiceReactionTimeTask.generate_session(3)
    responses = [
        {
            "trial_index": trial["trial_index"],
            "user_key": trial["correct_key"],
            "reaction_time": 850,
        }
        for trial in session["trials"]
    ]

    results = ChoiceReactionTimeTask.score_session(session, responses)

    assert results["metrics"]["accuracy"] == 100.0
    assert results["metrics"]["score"] > 90
    assert results["difficulty_adjustment"] >= 3


def test_score_session_handles_timeouts():
    session = ChoiceReactionTimeTask.generate_session(1)
    responses = [
        {
            "trial_index": trial["trial_index"],
            "user_key": "",
            "reaction_time": trial["max_response_ms"] + 200,
        }
        for trial in session["trials"]
    ]

    results = ChoiceReactionTimeTask.score_session(session, responses)

    assert results["metrics"]["accuracy"] == 0.0
    assert results["metrics"]["timeout_count"] == session["total_trials"]
    assert results["difficulty_adjustment"] <= 1
