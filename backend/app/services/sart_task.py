"""
Sustained Attention to Response Task (SART).
"""

import random
from statistics import pstdev
from typing import Any, Dict, List


class SARTTask:
    """
    Fast, repetitive sustained-attention task.

    Users respond to frequent non-targets and withhold to rare targets.
    This makes lapses of vigilance and inhibitory failures easy to capture.
    """

    DIGIT_SETS = {
        "basic": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "perceptual": [1, 2, 3, 4, 6, 7, 8, 9],
    }

    DIFFICULTY_CONFIG = {
        1: {"digits": "basic", "target_digit": 3, "total_trials": 54, "stimulus_ms": 900, "isi_ms": 900, "target_ratio": 0.12},
        2: {"digits": "basic", "target_digit": 3, "total_trials": 60, "stimulus_ms": 850, "isi_ms": 850, "target_ratio": 0.12},
        3: {"digits": "basic", "target_digit": 3, "total_trials": 66, "stimulus_ms": 800, "isi_ms": 800, "target_ratio": 0.12},
        4: {"digits": "basic", "target_digit": 3, "total_trials": 72, "stimulus_ms": 750, "isi_ms": 760, "target_ratio": 0.13},
        5: {"digits": "basic", "target_digit": 3, "total_trials": 78, "stimulus_ms": 700, "isi_ms": 720, "target_ratio": 0.13},
        6: {"digits": "basic", "target_digit": 3, "total_trials": 84, "stimulus_ms": 650, "isi_ms": 680, "target_ratio": 0.14},
        7: {"digits": "perceptual", "target_digit": 8, "total_trials": 90, "stimulus_ms": 600, "isi_ms": 640, "target_ratio": 0.14},
        8: {"digits": "perceptual", "target_digit": 8, "total_trials": 96, "stimulus_ms": 560, "isi_ms": 600, "target_ratio": 0.15},
        9: {"digits": "perceptual", "target_digit": 8, "total_trials": 102, "stimulus_ms": 520, "isi_ms": 560, "target_ratio": 0.15},
        10: {"digits": "perceptual", "target_digit": 8, "total_trials": 108, "stimulus_ms": 480, "isi_ms": 520, "target_ratio": 0.16},
    }

    ADVANCE_THRESHOLD = 84
    REGRESS_THRESHOLD = 64

    @classmethod
    def generate_session(cls, difficulty: int) -> Dict[str, Any]:
        config = cls.DIFFICULTY_CONFIG.get(difficulty, cls.DIFFICULTY_CONFIG[5])
        digit_pool = cls.DIGIT_SETS[config["digits"]]
        target_digit = config["target_digit"]
        total_trials = config["total_trials"]

        target_count = max(6, int(total_trials * config["target_ratio"]))
        non_target_count = total_trials - target_count

        trial_types = (["target"] * target_count) + (["nontarget"] * non_target_count)
        random.shuffle(trial_types)

        trials = []
        for index, trial_type in enumerate(trial_types):
            digit = target_digit if trial_type == "target" else random.choice([d for d in digit_pool if d != target_digit])
            trials.append(
                {
                    "trial_index": index,
                    "digit": digit,
                    "trial_type": trial_type,
                    "should_respond": trial_type == "nontarget",
                }
            )

        return {
            "difficulty": difficulty,
            "target_digit": target_digit,
            "total_trials": total_trials,
            "stimulus_ms": config["stimulus_ms"],
            "inter_stimulus_interval_ms": config["isi_ms"],
            "trials": trials,
        }

    @classmethod
    def score_session(cls, session_data: Dict[str, Any], responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        responses_by_index = {response.get("trial_index"): response for response in responses}
        scored_trials = []

        for trial in session_data.get("trials", []):
            response = responses_by_index.get(trial["trial_index"], {})
            responded = bool(response.get("responded", False))
            reaction_time_ms = float(response.get("reaction_time_ms", 0) or 0)
            correct = responded if trial["should_respond"] else not responded

            scored_trials.append(
                {
                    **trial,
                    "responded": responded,
                    "reaction_time_ms": reaction_time_ms,
                    "correct": correct,
                }
            )

        go_trials = [trial for trial in scored_trials if trial["should_respond"]]
        nogo_trials = [trial for trial in scored_trials if not trial["should_respond"]]

        hits = sum(1 for trial in go_trials if trial["responded"])
        omissions = sum(1 for trial in go_trials if not trial["responded"])
        commissions = sum(1 for trial in nogo_trials if trial["responded"])
        correct_withholds = sum(1 for trial in nogo_trials if not trial["responded"])

        go_accuracy = (hits / max(len(go_trials), 1)) * 100
        nogo_accuracy = (correct_withholds / max(len(nogo_trials), 1)) * 100
        overall_accuracy = ((hits + correct_withholds) / max(len(scored_trials), 1)) * 100

        hit_rts = [trial["reaction_time_ms"] for trial in go_trials if trial["responded"] and trial["reaction_time_ms"] > 0]
        avg_rt = sum(hit_rts) / len(hit_rts) if hit_rts else 0.0
        consistency = max(0.0, 100.0 - min(pstdev(hit_rts), 320) / 3) if len(hit_rts) > 1 else (100.0 if hit_rts else 0.0)

        vigilance_penalty = min(commissions * 3.0 + omissions * 1.8, 35.0)
        rt_score = 100.0 if avg_rt == 0 else max(0.0, min(100.0, 100 - ((avg_rt - 320) / 8)))
        score = (overall_accuracy * 0.50) + (nogo_accuracy * 0.20) + (rt_score * 0.15) + (consistency * 0.15) - vigilance_penalty
        score = max(0.0, min(score, 100.0))

        metrics = {
            "score": round(score, 1),
            "accuracy": round(overall_accuracy, 1),
            "go_accuracy": round(go_accuracy, 1),
            "nogo_accuracy": round(nogo_accuracy, 1),
            "average_reaction_time": round(avg_rt, 1),
            "consistency": round(consistency, 1),
            "commission_errors": commissions,
            "omission_errors": omissions,
            "correct_count": hits + correct_withholds,
            "total_trials": len(scored_trials),
            "vigilance_index": round(max(0.0, overall_accuracy - commissions * 2.5), 1),
        }

        difficulty = int(session_data.get("difficulty", 5))
        if metrics["score"] >= cls.ADVANCE_THRESHOLD and metrics["commission_errors"] <= 4:
            next_difficulty = min(difficulty + 1, 10)
            adaptation_reason = f"Increased difficulty (score {metrics['score']:.1f} with controlled commission errors)"
        elif metrics["score"] < cls.REGRESS_THRESHOLD:
            next_difficulty = max(difficulty - 1, 1)
            adaptation_reason = f"Decreased difficulty (score {metrics['score']:.1f} below target)"
        else:
            next_difficulty = difficulty
            adaptation_reason = f"Maintained difficulty (score {metrics['score']:.1f} in target range)"

        return {
            "metrics": metrics,
            "difficulty_adjustment": next_difficulty,
            "adaptation_reason": adaptation_reason,
            "scored_trials": scored_trials,
        }
