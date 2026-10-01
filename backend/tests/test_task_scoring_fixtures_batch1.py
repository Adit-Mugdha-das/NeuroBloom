"""Manually calculable scoring fixtures for the N-C4 task inventory."""

from app.services.digit_span_task import DigitSpanTask
from app.services.inspection_time_task import InspectionTimeTask
from app.services.pasat_task import PASATTask
from app.services.pattern_comparison_task import PatternComparisonTask
from app.services.sdmt_task import SDMTTask


def test_digit_span_score_is_weighted_full_and_positional_accuracy():
    trials = [
        {"correct": True, "accuracy": 100, "length": 3, "span_type": "forward"},
        {"correct": False, "accuracy": 50, "length": 4, "span_type": "backward"},
    ]
    # Full-trial accuracy=50 and mean positional accuracy=75:
    # 0.60*50 + 0.40*75 = 60.
    assert DigitSpanTask.calculate_session_metrics(trials)["score"] == 60.0


def test_sdmt_score_equals_number_of_correct_matches():
    trial = {
        "symbol_digit_mapping": {"A": 1, "B": 2, "C": 3},
        "test_sequence": ["A", "B", "C"],
        "duration_seconds": 60,
    }
    result = SDMTTask.score_response(trial, [1, 9, 3], [500, 600, 700], 3)
    assert result["score"] == 2
    assert result["accuracy"] == 66.7


def test_pattern_comparison_fast_slow_and_incorrect_scores():
    task = PatternComparisonTask()
    task.session_data["manual"] = {
        "trials": [{"correct_answer": "SAME", "time_limit": 2.0}]
    }
    assert task.score_response("manual", 0, "SAME", 1.0, 1)["trial_score"] == 100
    assert task.score_response("manual", 0, "SAME", 3.0, 1)["trial_score"] == 60
    assert task.score_response("manual", 0, "DIFFERENT", 1.0, 1)["trial_score"] == 0


def test_inspection_time_correct_and_incorrect_scores():
    task = InspectionTimeTask()
    task.session_data["manual"] = {
        "trials": [{"longer_side": "left", "difference_pixels": 8}]
    }
    assert task.score_response("manual", 0, "left", 500, 1)["trial_score"] == 100
    assert task.score_response("manual", 0, "right", 500, 1)["trial_score"] == 0


def test_pasat_score_is_accuracy_percentage_after_first_digit():
    task = PASATTask()
    task.session_data["manual"] = {
        "correct_answers": [5, 7, 9],
        "interval_seconds": 3.0,
    }
    responses = [
        {"trial_index": 0, "user_answer": None, "reaction_time": 0},
        {"trial_index": 1, "user_answer": 5, "reaction_time": 1000},
        {"trial_index": 2, "user_answer": 0, "reaction_time": 1000},
        {"trial_index": 3, "user_answer": 9, "reaction_time": 1000},
    ]
    # Two correct responses among three scoreable responses.
    result = task.score_session("manual", responses, difficulty=1)
    assert result["metrics"]["score"] == 66.7
