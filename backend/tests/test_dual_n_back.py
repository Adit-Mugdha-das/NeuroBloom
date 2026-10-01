from app.services.dual_n_back_task import DualNBackTask


def test_generate_trial_structure():
    trial = DualNBackTask.generate_trial(5)

    assert trial["n_level"] == 2
    assert trial["stream_length"] == 13
    assert len(trial["stimuli"]) == 13
    assert all("position" in stimulus for stimulus in trial["stimuli"])
    assert all("letter" in stimulus for stimulus in trial["stimuli"])


def test_non_targets_do_not_accidentally_match():
    trial = DualNBackTask.generate_trial(7)
    n_level = trial["n_level"]

    for index in range(n_level, len(trial["stimuli"])):
        current = trial["stimuli"][index]
        prior = trial["stimuli"][index - n_level]

        if not current["visual_target"]:
            assert current["position"] != prior["position"]
        if not current["audio_target"]:
            assert current["letter"] != prior["letter"]


def test_score_trial_rewards_correct_matches():
    trial = DualNBackTask.generate_trial(4)

    for stimulus in trial["stimuli"]:
        stimulus["user_visual_match"] = stimulus["visual_target"]
        stimulus["user_audio_match"] = stimulus["audio_target"]
        stimulus["response_time_ms"] = 620

    metrics = DualNBackTask.score_trial(trial)

    assert metrics["overall_accuracy"] == 100.0
    assert metrics["visual_accuracy"] == 100.0
    assert metrics["audio_accuracy"] == 100.0
    assert metrics["score"] == 100.0


def test_session_metrics_aggregate_trials():
    trials = []

    for difficulty in (3, 5):
        trial = DualNBackTask.generate_trial(difficulty)
        for stimulus in trial["stimuli"]:
            stimulus["user_visual_match"] = stimulus["visual_target"]
            stimulus["user_audio_match"] = False
            stimulus["response_time_ms"] = 700
        trials.append({**trial, "metrics": DualNBackTask.score_trial(trial)})

    metrics = DualNBackTask.calculate_session_metrics(trials)

    assert metrics["score"] > 0
    assert metrics["accuracy"] > 0
    assert metrics["n_level"] >= 1
    assert DualNBackTask.calculate_average_reaction_time(trials) == 700.0
