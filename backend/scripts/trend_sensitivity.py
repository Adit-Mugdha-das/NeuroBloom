"""Reproduce the NeuroBloom EWMA trend sensitivity analysis.

Run from the backend directory:
    python scripts/trend_sensitivity.py

Each developer-selected trend parameter (smoothing alpha, slope window, and the
relative-slope label threshold) is varied one at a time on deterministic
synthetic score series. The production function is used unchanged. Results are
written to analysis/results/trend_sensitivity.json.
"""

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.core.advanced_analytics import calculate_ewma_trend

OUTPUT = BACKEND / "analysis" / "results" / "trend_sensitivity.json"
LENGTH = 20


def synthetic_series():
    """Five 20-session score series with a known underlying pattern."""
    return {
        "stable": [70 + (1 if i % 2 == 0 else -1) for i in range(LENGTH)],
        "gradual_decline": [80 - 0.8 * i for i in range(LENGTH)],
        "gradual_improvement": [60 + 0.8 * i for i in range(LENGTH)],
        "noisy_stable": [70 + (8 if i % 2 == 0 else -8) for i in range(LENGTH)],
        "late_step_decline": [75 if i < 12 else 62 for i in range(LENGTH)],
    }


# One parameter is changed per setting; the others stay at their defaults.
SETTINGS = {
    "default": {},
    "alpha_0.1": {"alpha": 0.1},
    "alpha_0.3": {"alpha": 0.3},
    "alpha_0.5": {"alpha": 0.5},
    "window_3": {"window": 3},
    "window_7": {"window": 7},
    "threshold_0.005": {"relative_slope_threshold": 0.005},
    "threshold_0.02": {"relative_slope_threshold": 0.02},
}


def build_payload():
    series = synthetic_series()
    results = {}
    for setting, kwargs in SETTINGS.items():
        results[setting] = {}
        for name, values in series.items():
            trend = calculate_ewma_trend(values, **kwargs)
            mean_value = sum(values) / len(values)
            results[setting][name] = {
                "direction": trend["trend_direction"],
                "recent_slope": trend["recent_slope"],
                "relative_slope": round(trend["recent_slope"] / mean_value, 4),
            }

    default = results["default"]
    for setting, by_series in results.items():
        changed = [
            name for name in by_series
            if by_series[name]["direction"] != default[name]["direction"]
        ]
        by_series["_summary"] = {
            "label_changes_vs_default": len(changed),
            "changed_series": changed,
        }

    return {
        "fixture_type": "deterministic synthetic score series (20 sessions each)",
        "series_length": LENGTH,
        "settings": {name: kwargs for name, kwargs in SETTINGS.items()},
        "results": results,
    }


def main():
    payload = build_payload()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
