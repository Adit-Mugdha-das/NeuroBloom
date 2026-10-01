"""Final backend-scored N-C4 numerical fixtures."""

from app.services.dccs_task import DCCSTask
from app.services.flanker_task import FlankerTask
from app.services.go_nogo_task import GoNoGoTask
from app.services.plus_minus_task import PlusMinusTask
from app.services.soc_task import StockingsOfCambridgeTask
from app.services.stroop_task import StroopTask
from app.services.tol_task import TowerOfLondonTask
from app.services.trail_making_b_task import TrailMakingBTask
from app.services.verbal_fluency_task import VerbalFluencyTask
from app.services.wcst_task import WCSTTask
from app.services.visual_search_task import VisualSearchTask


def test_stroop_weighted_score():
    responses = [
        {"condition": "baseline", "correct": True, "reaction_time_ms": 500},
        {"condition": "congruent", "correct": True, "reaction_time_ms": 400},
        {"condition": "incongruent", "correct": True, "reaction_time_ms": 600},
    ]
    result = StroopTask().score_session({}, responses)
    # Cost=(600-500)/500=20%; normalized interference=90.
    assert result["performance_score"] == 96.0


def test_go_nogo_weighted_score():
    responses = [
        {"trial_type": "go", "responded": True, "reaction_time_ms": 500},
        {"trial_type": "nogo", "responded": False, "reaction_time_ms": 0},
    ]
    # 0.5*100 inhibition + 0.3*50 speed + 0.2*100 consistency = 85.
    assert GoNoGoTask().score_session({}, responses)["performance_score"] == 85.0


def test_flanker_weighted_score():
    session = {"trials": [
        {"trial_type": "congruent", "target_direction": "left"},
        {"trial_type": "incongruent", "target_direction": "right"},
    ]}
    responses = [
        {"trial_number": 1, "direction": "left", "reaction_time_ms": 400},
        {"trial_number": 2, "direction": "right", "reaction_time_ms": 500},
    ]
    # Accuracy=100, mean RT=450, conflict effect=100 -> 40+23.25+27.
    assert FlankerTask().score_session(session, responses)["performance_score"] == 90.25


def test_alternating_trail_adjusted_time_and_difference():
    session = {
        "correct_sequence": ["1", "A", "2", "B"],
        "time_limit_seconds": 120,
        "user_baseline_time": 30,
        "difficulty": 1,
    }
    errors = [{"type": "sequence_error"}]
    result = TrailMakingBTask().score_session(session, ["1", "A", "2", "B"], 50, errors)
    assert result["metrics"]["adjusted_time_seconds"] == 55
    assert result["metrics"]["accuracy"] == 75.0
    assert result["metrics"]["b_a_score"] == 20


def test_card_sorting_zero_category_percentile():
    card = {"color": "red", "shape": "circle", "number": 1}
    session = {
        "difficulty": 1,
        "config": {"correct_needed": 10},
        "target_cards": [card],
        "trial_cards": [card],
        "initial_rule": "color",
    }
    result = WCSTTask().score_session(session, [{"trial_index": 0, "selected_pile": 0}])
    assert result["accuracy"] == 100.0
    assert result["score"] == 10


def test_dimensional_sort_component_sum():
    session = {"difficulty": 1, "phases": {
        "phase1": {"rule": "color", "trials": [{"correct_target": 0}]}
    }}
    result = DCCSTask.score_session(session, [{"selected_target": 0, "reaction_time_ms": 1500}])
    # Accuracy=60, speed=20, and zero switch cost=20.
    assert result["score"] == 100


def test_plus_minus_component_sum():
    trial = lambda answer: {"correct_answer": answer}
    session = {"difficulty": 1, "blocks": {
        "block_a": {"trials": [trial(3)]},
        "block_b": {"trials": [trial(2)]},
        "block_c": {"trials": [trial(4)]},
    }}
    responses = [
        {"user_answer": 3, "reaction_time_ms": 2000},
        {"user_answer": 2, "reaction_time_ms": 2000},
        {"user_answer": 4, "reaction_time_ms": 2000},
    ]
    # Accuracy=50, speed=30, switching=20.
    assert PlusMinusTask.score_session(session, responses)["score"] == 100


def test_tower_planning_score():
    session = {"difficulty": 1, "config": {"planning_time_seconds": 30},
               "problems": [{"problem_number": 1, "minimum_moves": 3}]}
    solution = [{"moves_used": 6, "time_seconds": 15, "solved": True}]
    # Completion=40, efficiency=20, speed=20, perfect bonus=0.
    assert TowerOfLondonTask.score_session(session, solution)["score"] == 80


def test_stockings_score_is_capped_at_100():
    session = {"difficulty": 1, "config": {"planning_time_seconds": 30},
               "problems": [{"problem_number": 1, "minimum_moves": 3}]}
    solution = [{"moves_used": 3, "time_seconds": 15, "solved": True}]
    # Components total 110 before the documented 0-100 cap.
    assert StockingsOfCambridgeTask.score_session(session, solution)["score"] == 100


def test_verbal_fluency_five_valid_words_score_40():
    session = {"difficulty": 1, "locale": "en", "time_per_letter_seconds": 60}
    responses = [{"letter": "S", "words": ["sand", "ship", "sock", "soup", "star"]}]
    result = VerbalFluencyTask.score_session(session, responses)
    assert result["total_valid_words"] == 5
    assert result["score"] == 40


def test_feature_conjunction_correct_response_score():
    trial = {
        "target_present": True,
        "set_size": 20,
        "search_type": "conjunction",
        "time_limit": 10,
        "similarity": "medium",
        "difficulty": 5,
    }
    result = VisualSearchTask.score_response(
        trial, {"target_found": True, "reaction_time": 5}
    )
    # Correct response gives 1.0 accuracy; the speed bonus is capped at 1.0.
    assert result["correct"] is True
    assert result["score"] == 1.0
    assert result["search_efficiency"] == 0.25
