"""Exact numerical scoring fixtures for the ten tasks whose earlier tests were
behavioural (range or direction checks).

Each expected value is derived by hand from the scoring formula in the task
service and shown in the comment, so the fixture checks the arithmetic rather
than echoing program output. All inputs are fixed; nothing is randomly generated.
"""

import pytest

from app.services.cancellation_test_task import CancellationTestTask
from app.services.category_fluency_task import CategoryFluencyTask
from app.services.choice_reaction_time_task import ChoiceReactionTimeTask
from app.services.dual_n_back_task import DualNBackTask
from app.services.landmark_task import LandmarkTask
from app.services.multiple_object_tracking_task import MultipleObjectTrackingTask
from app.services.rule_shift_task import RuleShiftTask
from app.services.sart_task import SARTTask
from app.services.twenty_questions_task import TwentyQuestionsTask
from app.services.visual_search_task import VisualSearchTask


def test_dual_n_back_weighted_trial_score():
    # n=2, so stimuli with index < 2 are not scored (three eligible stimuli).
    stimuli = [
        {"index": 0}, {"index": 1},
        {"index": 2, "visual_target": True, "audio_target": True,
         "user_visual_match": True, "user_audio_match": True},
        {"index": 3, "visual_target": True, "audio_target": False,
         "user_visual_match": False, "user_audio_match": False},
        {"index": 4, "visual_target": False, "audio_target": False,
         "user_visual_match": True, "user_audio_match": False},
    ]
    metrics = DualNBackTask.score_trial({"n_level": 2, "stimuli": stimuli})
    # Correct decisions 4 of 6 -> overall 66.667; hit rates 50 and 100 -> mean 75;
    # the one dual target is answered correctly -> dual accuracy 100.
    # score = 0.55*66.667 + 0.25*75 + 0.20*100 = 36.667 + 18.75 + 20 = 75.417.
    assert metrics["eligible_stimuli"] == 3
    assert metrics["overall_accuracy"] == 66.7
    assert metrics["visual_accuracy"] == 33.3
    assert metrics["audio_accuracy"] == 100.0
    assert metrics["dual_accuracy"] == 100.0
    assert metrics["score"] == 75.4


def test_choice_reaction_time_weighted_score():
    trials = [
        {"trial_index": 0, "correct_key": "f", "max_response_ms": 2000},
        {"trial_index": 1, "correct_key": "j", "max_response_ms": 2000},
    ]
    responses = [
        {"trial_index": 0, "user_key": "f", "reaction_time": 730},  # correct
        {"trial_index": 1, "user_key": "f", "reaction_time": 600},  # wrong key
    ]
    metrics = ChoiceReactionTimeTask.score_session({"difficulty": 5, "trials": trials}, responses)["metrics"]
    # accuracy=50; mean correct RT=730 -> RT score=100-(730-650)/8=90; one valid RT -> consistency 100.
    # score = 0.55*50 + 0.30*90 + 0.15*100 = 27.5 + 27 + 15 = 69.5.
    assert metrics["accuracy"] == 50.0
    assert metrics["average_reaction_time"] == 730.0
    assert metrics["score"] == 69.5


def test_sart_weighted_score_and_penalty():
    trials = [
        {"trial_index": 0, "trial_type": "nontarget", "should_respond": True},
        {"trial_index": 1, "trial_type": "nontarget", "should_respond": True},
        {"trial_index": 2, "trial_type": "target", "should_respond": False},
        {"trial_index": 3, "trial_type": "target", "should_respond": False},
    ]
    responses = [
        {"trial_index": 0, "responded": True, "reaction_time_ms": 400},
        {"trial_index": 1, "responded": True, "reaction_time_ms": 400},
        {"trial_index": 2, "responded": False},
        {"trial_index": 3, "responded": True, "reaction_time_ms": 350},  # commission error
    ]
    result = SARTTask.score_session({"difficulty": 5, "trials": trials}, responses)
    metrics = result["metrics"]
    # overall accuracy 75, no-go accuracy 50, mean go RT 400 -> RT score 100-(400-320)/8=90,
    # identical go RTs -> consistency 100, vigilance penalty=3.0 per commission.
    # score = 0.50*75 + 0.20*50 + 0.15*90 + 0.15*100 - 3 = 37.5+10+13.5+15-3 = 73.
    assert metrics["commission_errors"] == 1
    assert metrics["score"] == 73.0
    assert result["difficulty_adjustment"] == 5  # 64 <= 73 < 84: maintained


def test_rule_shift_weighted_score_and_shift_cost():
    trials = [
        {"trial_index": 0, "correct_side": "left", "previous_rule": None, "is_switch_trial": False},
        {"trial_index": 1, "correct_side": "right", "previous_rule": "color", "is_switch_trial": True},
        {"trial_index": 2, "correct_side": "left", "previous_rule": None, "is_switch_trial": False},
        {"trial_index": 3, "correct_side": "right", "previous_rule": "color", "is_switch_trial": True},
    ]
    responses = [
        {"trial_index": 0, "selected_side": "left", "reaction_time_ms": 700},
        {"trial_index": 1, "selected_side": "right", "reaction_time_ms": 900},
        {"trial_index": 2, "selected_side": None},
        {"trial_index": 3, "selected_side": None},
    ]
    result = RuleShiftTask.score_session({"difficulty": 5, "trials": trials}, responses)
    metrics = result["metrics"]
    # accuracy=switch accuracy=50; correct RTs 700 and 900 -> mean 800 -> RT score 100-100/12=91.667;
    # SD 100 -> consistency 100-100/3.5=71.429; shift cost 900-700=200 -> penalty 200/22=9.091.
    # score = 0.48*50 + 0.22*50 + 0.15*91.667 + 0.15*71.429 - 9.091 = 50.373.
    assert metrics["accuracy"] == 50.0
    assert metrics["switch_accuracy"] == 50.0
    assert metrics["shift_cost_ms"] == 200.0
    assert metrics["score"] == 50.4
    assert result["difficulty_adjustment"] == 4  # score below 63: level decreases


def test_category_fluency_unique_word_score():
    words = ["Dog", " dog", "cat", "", "fish", "123"]
    result = CategoryFluencyTask.score_response(words, 60, 5)
    # Normalised duplicates collapse (dog, dog); blank and numeric entries are invalid.
    # 3 unique words; expected maximum=20+2*5=30 -> 3/30*100=10.
    assert result["unique_count"] == 3
    assert result["duplicate_count"] == 1
    assert result["invalid_count"] == 2
    assert result["normalized_score"] == 10.0
    assert result["should_advance"] is False


def test_twenty_questions_efficiency_band_and_multiplier():
    history = [
        {"question": "Is it living?"},
        {"question": "Does it fly?"},
        {"question": "A dog?"},
    ]
    result = TwentyQuestionsTask.score_game(9, True, 3, history)
    # 9 questions falls in the 8-12 band -> raw 85; level 3 multiplier=1+2*0.05=1.10 -> 93.5.
    assert result["raw_score"] == 85
    assert result["normalized_score"] == 93.5
    assert result["question_efficiency"] == 55.0
    assert result["strategy_score"] == 66.67
    assert result["should_advance"] is True


def test_visual_search_target_absent_and_error_scores():
    trial = {
        "target_present": False, "set_size": 10, "search_type": "feature",
        "time_limit": 10, "similarity": "low", "difficulty": 2,
    }
    correct = VisualSearchTask.score_response(trial, {"target_found": False, "reaction_time": 5})
    wrong = VisualSearchTask.score_response(trial, {"target_found": True, "reaction_time": 5})
    # Correct rejection: accuracy 1 + speed bonus 0.1 is capped at 1; 5 s over 10 items -> 0.5 s/item.
    assert correct["correct"] is True
    assert correct["score"] == 1.0
    assert correct["search_efficiency"] == 0.5
    assert correct["search_slope_ms"] == 500.0
    # A false alarm scores zero regardless of speed.
    assert wrong["correct"] is False
    assert wrong["score"] == 0.0


def test_cancellation_accuracy_band_and_adjustment():
    targets = [{"row": 0, "col": 0}, {"row": 1, "col": 3}, {"row": 2, "col": 5}, {"row": 3, "col": 7}]
    marked = [{"row": 0, "col": 0}, {"row": 1, "col": 3}, {"row": 2, "col": 5}, {"row": 9, "col": 9}]
    result = CancellationTestTask.score_response(marked, targets, 40.0, 120, 1)
    # 3 of 4 targets found -> accuracy 75 -> 'average' band (70-84) -> score 70; one false alarm.
    # Accuracy 75 is neither >=90 nor <75, so the difficulty adjustment is 0.
    assert result["targets_found"] == 3
    assert result["targets_missed"] == 1
    assert result["false_alarms"] == 1
    assert result["accuracy"] == 75.0
    assert result["score"] == 70.0
    assert result["difficulty_adjustment"] == 0


def test_landmark_weighted_score_and_bias_penalty():
    def trial(i, offset, correct):
        return {"trial_index": i, "offset_px": offset, "correct_response": correct,
                "is_centered": offset == 0}

    trials = [trial(0, 0, "equal"), trial(1, 10, "left"), trial(2, -10, "right"),
              trial(3, 10, "left"), trial(4, 10, "left")]
    responses = [
        {"trial_index": 0, "response": "equal", "reaction_time_ms": 850},
        {"trial_index": 1, "response": "left", "reaction_time_ms": 850},
        {"trial_index": 2, "response": "left", "reaction_time_ms": 900},   # left-bias error
        {"trial_index": 3, "response": "equal", "reaction_time_ms": 900},  # missed offset
        {"trial_index": 4, "response": "left", "reaction_time_ms": 850},
    ]
    result = LandmarkTask.score_session({"difficulty": 5, "trials": trials}, responses)
    metrics = result["metrics"]
    # accuracy 3/5=60; offset accuracy 2/4=50; centred accuracy 100; correct RTs all 850 -> RT score 100,
    # consistency 100; bias index=(1-0)/5*100=20 -> penalty 0.35*20=7; no omissions.
    # score = 0.5*60 + 0.18*50 + 0.14*100 + 0.08*100 + 0.10*100 - 7 = 64.
    assert metrics["accuracy"] == 60.0
    assert metrics["offset_accuracy"] == 50.0
    assert metrics["centered_accuracy"] == 100.0
    assert metrics["spatial_bias_index"] == 20.0
    assert metrics["score"] == 64.0
    assert result["difficulty_adjustment"] == 5  # exactly at the 64 regression threshold: maintained


def test_multiple_object_tracking_weighted_score():
    trial = {"target_indices": [0, 1, 2], "num_targets": 3, "total_objects": 10, "tracking_duration": 12}
    result = MultipleObjectTrackingTask.score_response(
        trial, {"selected_objects": [0, 1, 2, 7], "response_time": 2.0}
    )
    # Recall 3/3=1; precision 3/4=0.75; score=0.7*1+0.3*0.75=0.925.
    # Tracking efficiency = 1-(1 false positive + 0 misses)/(2*3) = 0.8333.
    assert result["accuracy"] == 1.0
    assert result["precision"] == 0.75
    assert result["score"] == pytest.approx(0.925)
    assert result["tracking_efficiency"] == pytest.approx(5 / 6)
    assert result["performance"] == "good"
