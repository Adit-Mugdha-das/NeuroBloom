"""
Landmark task service.

Clinically grounded visual-attention task in which users judge whether a line
is bisected evenly or whether the left or right segment is longer.
"""

import random
from statistics import pstdev
from typing import Any, Dict, List


class LandmarkTask:
    """Digitized landmark task for visual scanning and spatial bias."""

    DIFFICULTY_CONFIG = {
        1: {"trials": 18, "line_length": 360, "offset_range": [0, 18, 24, 30], "center_ratio": 0.28},
        2: {"trials": 20, "line_length": 380, "offset_range": [0, 14, 20, 26], "center_ratio": 0.28},
        3: {"trials": 22, "line_length": 400, "offset_range": [0, 12, 18, 24], "center_ratio": 0.26},
        4: {"trials": 24, "line_length": 420, "offset_range": [0, 10, 16, 22], "center_ratio": 0.24},
        5: {"trials": 26, "line_length": 440, "offset_range": [0, 8, 14, 20], "center_ratio": 0.24},
        6: {"trials": 28, "line_length": 460, "offset_range": [0, 6, 12, 18], "center_ratio": 0.22},
        7: {"trials": 30, "line_length": 480, "offset_range": [0, 5, 10, 16], "center_ratio": 0.22},
        8: {"trials": 32, "line_length": 500, "offset_range": [0, 4, 8, 14], "center_ratio": 0.2},
        9: {"trials": 34, "line_length": 520, "offset_range": [0, 3, 7, 12], "center_ratio": 0.2},
        10: {"trials": 36, "line_length": 540, "offset_range": [0, 2, 6, 10], "center_ratio": 0.18},
    }
    OPTIONS = ("left", "equal", "right")
    ADVANCE_THRESHOLD = 84
    REGRESS_THRESHOLD = 64

    @classmethod
    def generate_session(cls, difficulty: int) -> Dict[str, Any]:
        config = cls.DIFFICULTY_CONFIG.get(difficulty, cls.DIFFICULTY_CONFIG[5])
        trials: List[Dict[str, Any]] = []

        for trial_index in range(config["trials"]):
            is_center = random.random() < config["center_ratio"]
            if is_center:
                offset = 0
            else:
                magnitude = random.choice([value for value in config["offset_range"] if value != 0])
                direction = random.choice([-1, 1])
                offset = magnitude * direction

            if offset == 0:
                correct_response = "equal"
            elif offset > 0:
                correct_response = "left"
            else:
                correct_response = "right"

            trials.append(
                {
                    "trial_index": trial_index,
                    "line_length": config["line_length"],
                    "offset_px": offset,
                    "correct_response": correct_response,
                    "left_segment_px": int((config["line_length"] / 2) + offset),
                    "right_segment_px": int((config["line_length"] / 2) - offset),
                    "is_centered": offset == 0,
                }
            )

        return {
            "difficulty": difficulty,
            "total_trials": len(trials),
            "line_length": config["line_length"],
            "trials": trials,
            "response_options": list(cls.OPTIONS),
        }

    @classmethod
    def score_session(cls, session_data: Dict[str, Any], responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        response_map = {response.get("trial_index"): response for response in responses}
        scored_trials: List[Dict[str, Any]] = []

        for trial in session_data.get("trials", []):
            response = response_map.get(trial["trial_index"], {})
            user_response = response.get("response")
            reaction_time_ms = float(response.get("reaction_time_ms", 0) or 0)
            correct = user_response == trial["correct_response"]

            scored_trials.append(
                {
                    **trial,
                    "response": user_response,
                    "reaction_time_ms": reaction_time_ms,
                    "correct": correct,
                }
            )

        total_trials = len(scored_trials)
        correct_count = sum(1 for trial in scored_trials if trial["correct"])
        accuracy = (correct_count / total_trials) * 100 if total_trials else 0.0

        centered_trials = [trial for trial in scored_trials if trial["is_centered"]]
        offset_trials = [trial for trial in scored_trials if not trial["is_centered"]]
        centered_accuracy = (
            sum(1 for trial in centered_trials if trial["correct"]) / len(centered_trials) * 100
            if centered_trials else 0.0
        )
        offset_accuracy = (
            sum(1 for trial in offset_trials if trial["correct"]) / len(offset_trials) * 100
            if offset_trials else 0.0
        )

        correct_rts = [trial["reaction_time_ms"] for trial in scored_trials if trial["correct"] and trial["reaction_time_ms"] > 0]
        average_rt = sum(correct_rts) / len(correct_rts) if correct_rts else 0.0
        consistency = max(0.0, 100.0 - min(pstdev(correct_rts), 280) / 2.8) if len(correct_rts) > 1 else (100.0 if correct_rts else 0.0)

        left_bias_errors = sum(1 for trial in scored_trials if not trial["correct"] and trial["response"] == "left")
        right_bias_errors = sum(1 for trial in scored_trials if not trial["correct"] and trial["response"] == "right")
        center_misses = sum(1 for trial in centered_trials if trial["response"] in ("left", "right"))
        omission_count = sum(1 for trial in scored_trials if trial["response"] not in cls.OPTIONS)

        spatial_bias_index = round((left_bias_errors - right_bias_errors) / max(total_trials, 1) * 100, 1)
        rt_score = 100.0 if average_rt == 0 else max(0.0, min(100.0, 100 - ((average_rt - 850) / 14)))
        bias_penalty = min(abs(spatial_bias_index) * 0.35, 14.0)
        omission_penalty = min(omission_count * 5.0, 15.0)

        score = (
            (accuracy * 0.5)
            + (offset_accuracy * 0.18)
            + (centered_accuracy * 0.14)
            + (rt_score * 0.08)
            + (consistency * 0.1)
            - bias_penalty
            - omission_penalty
        )
        score = max(0.0, min(score, 100.0))

        metrics = {
            "score": round(score, 1),
            "accuracy": round(accuracy, 1),
            "offset_accuracy": round(offset_accuracy, 1),
            "centered_accuracy": round(centered_accuracy, 1),
            "average_reaction_time": round(average_rt, 1),
            "consistency": round(consistency, 1),
            "left_bias_errors": left_bias_errors,
            "right_bias_errors": right_bias_errors,
            "center_misses": center_misses,
            "spatial_bias_index": spatial_bias_index,
            "omissions": omission_count,
            "correct_count": correct_count,
            "total_trials": total_trials,
        }

        difficulty = int(session_data.get("difficulty", 5))
        if metrics["score"] >= cls.ADVANCE_THRESHOLD and abs(metrics["spatial_bias_index"]) <= 8 and omission_count <= 1:
            next_difficulty = min(difficulty + 1, 10)
            adaptation_reason = f"Increased difficulty (score {metrics['score']:.1f} with stable midpoint judgment)"
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
