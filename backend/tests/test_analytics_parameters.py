"""Checks that documented analytics parameters match the code and committed results.

The supplementary parameter and sensitivity tables (S3-S5) are generated from
these values, so the tests fail if the code, the configuration, or the committed
sensitivity results drift apart.
"""

import importlib.util
import json
from pathlib import Path

import pytest

from app.core.advanced_analytics import calculate_ewma_trend

BACKEND = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, BACKEND / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fatigue_proxy_configuration_matches_documented_values():
    config = json.loads((BACKEND / "config" / "analytics.json").read_text(encoding="utf-8"))["fatigue_proxy"]
    assert config["weights"] == {
        "accuracy_decline": 0.5, "reaction_time_increase": 0.3, "performance_slope": 0.2,
    }
    assert config["scales"] == {
        "accuracy_percentage_points": 30.0, "reaction_time_ms": 200.0, "negative_slope_per_trial": 0.01,
    }
    assert config["minimum_trials"] == 8
    assert config["minimum_quartile_observations"] == 2


def test_ewma_defaults_and_hand_derived_values():
    # alpha=0.2: EWMA = [10, 0.2*20+0.8*10] = [10, 12]; slope 2 over two points;
    # series mean 15 -> relative slope 0.1333 > 0.01 -> improving; strength min(1, 0.1333*20)=1.
    result = calculate_ewma_trend([10, 20])
    assert result["ewma_values"] == [10, 12]
    assert result["recent_slope"] == 2.0
    assert result["trend_direction"] == "improving"
    assert result["trend_strength"] == 1.0


def test_ewma_threshold_parameter_changes_the_label():
    # Relative slope is 0.1333, so a threshold above that leaves the series stable.
    assert calculate_ewma_trend([10, 20], relative_slope_threshold=0.2)["trend_direction"] == "stable"


def test_ewma_window_parameter_limits_the_points_used():
    values = [50, 50, 50, 50, 50, 50, 80]
    # With alpha=1 the EWMA equals the series. Window 2 sees only 50 -> 80 (slope 30).
    # Window 7 regresses over all seven points, giving a smaller slope.
    narrow = calculate_ewma_trend(values, alpha=1.0, window=2)["recent_slope"]
    wide = calculate_ewma_trend(values, alpha=1.0, window=7)["recent_slope"]
    assert narrow == 30.0
    assert 0 < wide < narrow


def test_default_trend_labels_on_synthetic_series():
    module = load_script("trend_sensitivity")
    default = module.build_payload()["results"]["default"]
    assert {name: default[name]["direction"] for name in module.synthetic_series()} == {
        "stable": "stable",
        "gradual_decline": "declining",
        "gradual_improvement": "improving",
        "noisy_stable": "stable",
        "late_step_decline": "declining",
    }


def test_committed_trend_sensitivity_results_are_current():
    module = load_script("trend_sensitivity")
    committed = json.loads((BACKEND / "analysis" / "results" / "trend_sensitivity.json").read_text(encoding="utf-8"))
    assert committed == json.loads(json.dumps(module.build_payload()))


def test_committed_illustrative_case_is_current():
    module = load_script("illustrative_case")
    committed = json.loads((BACKEND / "analysis" / "results" / "illustrative_case.json").read_text(encoding="utf-8"))
    assert committed == json.loads(json.dumps(module.build_case()))


def test_committed_fatigue_sensitivity_has_no_hard_coded_flag_result():
    committed = json.loads((BACKEND / "analysis" / "results" / "fatigue_proxy_sensitivity.json").read_text(encoding="utf-8"))
    assert all("review_flag_changes" not in result for result in committed["results"].values())
    assert committed["summary"]["maximum_absolute_value_change"] == pytest.approx(0.15)
