"""Reproduce the synthetic longitudinal case shown in the manuscript.

Run from the backend directory:
    python scripts/illustrative_case.py

One synthetic patient completes six 40-trial sessions of one task. Trial-level
data are generated deterministically (fixed seed); a higher pre-session fatigue
rating lowers accuracy, slows responses and adds a late-session decline. Every
indicator is computed with the production functions in
app.core.advanced_analytics, and difficulty follows the session-completion rule
(accuracy >= 85%: +1 level; < 65%: -1 level). Results are written to
analysis/results/illustrative_case.json.
"""

import json
import random
import statistics
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.core.advanced_analytics import (
    calculate_contextual_correlations,
    calculate_ewma_trend,
    calculate_fatigue_signature,
    calculate_iiv_metrics,
    calculate_within_person_variability,
)

OUTPUT = BACKEND / "analysis" / "results" / "illustrative_case.json"
SEED = 42
TRIALS = 40
BASELINE_SCORE = 62  # baseline 50-69 -> starting level 4
FATIGUE = [3, 4, 7, 3, 8, 4]  # pre-session self-report, 1-10
SLEEP = [8, 7, 4, 8, 3, 7]  # pre-session self-report, 1-10


def starting_level(score):
    return 2 if score < 50 else 4 if score < 70 else 7 if score < 85 else 9


def next_level(level, accuracy):
    if accuracy >= 85:
        return min(level + 1, 10)
    if accuracy < 65:
        return max(level - 1, 1)
    return level


def generate_trials(rng, fatigue, level):
    """Synthetic trials: accuracy and speed fall with fatigue and difficulty; late decline when fatigue >= 7."""
    trials = []
    for i in range(TRIALS):
        late = i >= TRIALS * 3 // 4 and fatigue >= 7
        p_correct = 0.97 - 0.025 * (fatigue - 3) - 0.02 * (level - 4) - (0.30 if late else 0.0)
        rt = 520 + 12 * fatigue + 10 * level + rng.gauss(0, 35 + 10 * fatigue) + (160 if late else 0)
        trials.append({"trial_num": i, "correct": rng.random() < p_correct, "reaction_time": round(max(rt, 200), 1)})
    return trials


def build_case():
    rng = random.Random(SEED)
    level = starting_level(BASELINE_SCORE)
    sessions, history = [], []
    for index, (fatigue, sleep) in enumerate(zip(FATIGUE, SLEEP), start=1):
        trials = generate_trials(rng, fatigue, level)
        accuracy = round(100 * sum(t["correct"] for t in trials) / len(trials), 1)
        rts = [t["reaction_time"] for t in trials]
        mean_rt = round(statistics.mean(rts), 1)
        score = accuracy  # session score taken as accuracy for this case
        history.append({"score": score, "mean_rt": mean_rt, "date": f"session-{index:02d}",
                        "fatigue_level": fatigue, "sleep_quality": sleep})

        trend = calculate_ewma_trend([h["score"] for h in history])
        change = calculate_within_person_variability(history)
        new_level = next_level(level, accuracy)
        sessions.append({
            "session": index,
            "fatigue_rating": fatigue,
            "sleep_rating": sleep,
            "difficulty_level": level,
            "next_difficulty_level": new_level,
            "accuracy": accuracy,
            "mean_rt_ms": mean_rt,
            "fatigue_proxy": calculate_fatigue_signature(trials)["fatigue_proxy"],
            "rt_cv": calculate_iiv_metrics(rts)["rt_cv"],
            "ewma": trend["current_ewma"],
            "trend": trend["trend_direction"],
            "wpsc": change["within_person_standardized_change"],
        })
        level = new_level

    correlations = calculate_contextual_correlations(history, ["fatigue_level", "sleep_quality"])
    return {
        "description": "Synthetic single-patient case; six 40-trial sessions; fixed seed.",
        "seed": SEED,
        "baseline_score": BASELINE_SCORE,
        "sessions": sessions,
        "contextual_correlations": correlations,
    }


def main():
    payload = build_case()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
