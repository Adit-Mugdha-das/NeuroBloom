from app.services.rule_shift_task import RuleShiftTask


def test_generate_session_structure():
    session = RuleShiftTask.generate_session(5)

    assert session["difficulty"] == 5
    assert session["total_trials"] == len(session["trials"])
    assert len(session["blocks"]) == 4
    assert session["trials"][0]["active_rule"] in {"color", "shape", "count"}


def test_score_session_perfect_performance():
    session = RuleShiftTask.generate_session(4)
    responses = []

    for trial in session["trials"]:
        responses.append(
            {
                "trial_index": trial["trial_index"],
                "selected_side": trial["correct_side"],
                "reaction_time_ms": 760,
            }
        )

    results = RuleShiftTask.score_session(session, responses)

    assert results["metrics"]["accuracy"] == 100.0
    assert results["metrics"]["perseverative_errors"] == 0
    assert results["difficulty_adjustment"] >= 4


def test_perseverative_errors_reduce_score():
    session = RuleShiftTask.generate_session(6)
    responses = []

    for trial in session["trials"]:
        selected_side = trial["correct_side"]
        if trial["is_switch_trial"] and trial["previous_rule"]:
            previous_value = trial[trial["previous_rule"]]
            if trial["previous_rule"] == "color":
                selected_side = "left" if previous_value == "teal" else "right"
            elif trial["previous_rule"] == "shape":
                selected_side = "left" if previous_value == "circle" else "right"
            else:
                selected_side = "left" if previous_value == 1 else "right"

        responses.append(
            {
                "trial_index": trial["trial_index"],
                "selected_side": selected_side,
                "reaction_time_ms": 980,
            }
        )

    results = RuleShiftTask.score_session(session, responses)

    assert results["metrics"]["perseverative_errors"] > 0
    assert results["metrics"]["score"] < 83
