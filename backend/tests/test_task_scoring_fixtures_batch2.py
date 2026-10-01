"""Second set of manually calculable N-C4 scoring fixtures."""

from app.services.letter_number_sequencing_task import LetterNumberSequencingTask
from app.services.operation_span_task import OperationSpanTask
from app.services.spatial_span_task import SpatialSpanTask
from app.services.trail_making_a_task import TrailMakingATask
from app.services.useful_field_of_view_task import score_response as score_peripheral_detection


def test_spatial_span_component_sum():
    result = SpatialSpanTask.score_response(
        [1, 2, 3], [1, 2, 3], "forward", reaction_time_ms=4500, par_ms=9000
    )
    # Position=70, span=15*(3/9)=5, speed=15*(1-4500/9000)=7.5.
    assert result["trial_score"] == 82.5


def test_letter_number_component_sum():
    result = LetterNumberSequencingTask.score_response(
        ["1", "2"], ["A", "B"], ["1", "2"], ["A", "B"],
        reaction_time_ms=9000, par_ms=18000,
    )
    # Set=50, order=35, speed=15*(1-9000/18000)=7.5.
    assert result["trial_score"] == 92.5


def test_operation_span_dual_task_average():
    result = OperationSpanTask.score_response(
        ["A", "B"], ["A", "X"], [True, False], [True, True]
    )
    # Letter accuracy=50 and mathematics accuracy=50; their mean is 50.
    assert result["letter_accuracy"] == 50
    assert result["math_accuracy"] == 50
    assert result["dual_task_score"] == 50


def test_numeric_trail_time_band_and_error_penalty():
    circles = [{"x": i * 10, "y": 0} for i in range(25)]
    clicks = [{"x": i * 10, "y": 0} for i in range(25)]
    errors = [{"timestamp": 1}, {"timestamp": 2}]
    result = TrailMakingATask.score_response(
        {"circles": circles}, completion_time=30000, errors=errors, clicks=clicks
    )
    # Thirty seconds gives the 85-point band; two errors cost 5 points each.
    assert result["normalized_time"] == 30.0
    assert result["score"] == 75


def test_peripheral_detection_full_and_partial_credit():
    trial = {
        "subtest": "central_peripheral",
        "central_target": "car",
        "peripheral_position": "3 o'clock",
        "presentation_time_ms": 800,
    }
    full = score_peripheral_detection(trial, "car", "3 o'clock")
    partial = score_peripheral_detection(trial, "car", "9 o'clock")
    assert full["score"] == 100
    assert partial["score"] == 50

