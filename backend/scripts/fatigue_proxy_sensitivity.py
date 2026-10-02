"""Reproduce the NeuroBloom fatigue-proxy sensitivity analysis.

Run from the backend directory:
    python scripts/fatigue_proxy_sensitivity.py
"""

import copy
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.core.advanced_analytics import FATIGUE_PROXY_CONFIG, calculate_fatigue_signature

OUTPUT = BACKEND / "analysis" / "results" / "fatigue_proxy_sensitivity.json"


def make_session(name):
    trials = []
    for index in range(40):
        correct = 1
        reaction_time = 500
        if name == "accuracy_decline" and index >= 30:
            correct = 0
        elif name == "rt_increase" and index >= 30:
            reaction_time = 700
        elif name == "combined" and index >= 30:
            correct = 0
            reaction_time = 700
        elif name == "moderate" and index >= 30:
            correct = 1 if index % 2 == 0 else 0
            reaction_time = 600
        trials.append({"trial_num": index, "correct": correct, "reaction_time": reaction_time})
    return trials


def parameter_sets():
    sets = {"default": copy.deepcopy(FATIGUE_PROXY_CONFIG)}
    for name, weights in {
        "equal_weights": (0.33, 0.33, 0.34),
        "accuracy_emphasis": (0.60, 0.20, 0.20),
        "rt_emphasis": (0.35, 0.45, 0.20),
    }.items():
        config = copy.deepcopy(FATIGUE_PROXY_CONFIG)
        config["weights"] = dict(zip(config["weights"], weights))
        sets[name] = config
    for name, factor in {"scales_minus_20_percent": 0.8, "scales_plus_20_percent": 1.2}.items():
        config = copy.deepcopy(FATIGUE_PROXY_CONFIG)
        config["scales"] = {key: value * factor for key, value in config["scales"].items()}
        sets[name] = config
    return sets


def ranks(values):
    ordered = sorted(values, key=lambda name: (-values[name], name))
    return {name: index + 1 for index, name in enumerate(ordered)}


def spearman_without_ties(first, second):
    names = list(first)
    squared_difference = sum((first[name] - second[name]) ** 2 for name in names)
    count = len(names)
    return 1 - (6 * squared_difference) / (count * (count ** 2 - 1))


def main():
    sessions = {name: make_session(name) for name in ("stable", "moderate", "rt_increase", "accuracy_decline", "combined")}
    results = {}
    for config_name, config in parameter_sets().items():
        values = {
            name: calculate_fatigue_signature(trials, config)["fatigue_proxy"]
            for name, trials in sessions.items()
        }
        results[config_name] = {"values": values, "ranks": ranks(values)}

    default_values = results["default"]["values"]
    default_ranks = results["default"]["ranks"]
    for name, result in results.items():
        result["maximum_absolute_value_change"] = round(
            max(abs(result["values"][key] - default_values[key]) for key in default_values), 3
        )
        result["rank_correlation_with_default"] = round(
            spearman_without_ties(default_ranks, result["ranks"]), 3
        )

    payload = {
        "fixture_type": "synthetic sessions (40 trials each)",
        "summary": {
            "parameter_sets": len(results),
            "maximum_absolute_value_change": max(
                r["maximum_absolute_value_change"] for r in results.values()
            ),
            "minimum_rank_correlation_with_default": min(
                r["rank_correlation_with_default"] for r in results.values()
            ),
        },
        "results": results,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
