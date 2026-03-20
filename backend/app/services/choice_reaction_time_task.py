"""
Choice Reaction Time task implementation.
"""

import random
from statistics import pstdev
from typing import Any, Dict, List


class ChoiceReactionTimeTask:
    """
    Decision-speed task extending simple reaction time with stimulus discrimination.
    """

    STIMULI = [
        {"code": "red_circle", "label": "Red Circle", "shape": "circle", "color": "#d64545", "key": "1"},
        {"code": "blue_square", "label": "Blue Square", "shape": "square", "color": "#2f6fd8", "key": "2"},
        {"code": "green_triangle", "label": "Green Triangle", "shape": "triangle", "color": "#2b9a61", "key": "3"},
        {"code": "gold_star", "label": "Gold Star", "shape": "star", "color": "#c89412", "key": "4"},
    ]

    DIFFICULTY_CONFIG = {
        1: {"stimulus_count": 2, "trials": 18, "max_response_ms": 2200, "stimulus_ms": 1800, "iti_ms": 900},
        2: {"stimulus_count": 2, "trials": 20, "max_response_ms": 2100, "stimulus_ms": 1700, "iti_ms": 850},
        3: {"stimulus_count": 3, "trials": 22, "max_response_ms": 2000, "stimulus_ms": 1650, "iti_ms": 800},
        4: {"stimulus_count": 3, "trials": 24, "max_response_ms": 1900, "stimulus_ms": 1550, "iti_ms": 750},
        5: {"stimulus_count": 4, "trials": 24, "max_response_ms": 1800, "stimulus_ms": 1500, "iti_ms": 700},
        6: {"stimulus_count": 4, "trials": 26, "max_response_ms": 1700, "stimulus_ms": 1450, "iti_ms": 650},
        7: {"stimulus_count": 4, "trials": 28, "max_response_ms": 1600, "stimulus_ms": 1400, "iti_ms": 620},
        8: {"stimulus_count": 4, "trials": 30, "max_response_ms": 1500, "stimulus_ms": 1300, "iti_ms": 580},
        9: {"stimulus_count": 4, "trials": 32, "max_response_ms": 1400, "stimulus_ms": 1200, "iti_ms": 540},
        10: {"stimulus_count": 4, "trials": 34, "max_response_ms": 1300, "stimulus_ms": 1100, "iti_ms": 500},
    }

    ADVANCE_THRESHOLD = 83
    REGRESS_THRESHOLD = 63

    @classmethod
    def generate_session(cls, difficulty: int) -> Dict[str, Any]:
        config = cls.DIFFICULTY_CONFIG.get(difficulty, cls.DIFFICULTY_CONFIG[5])
        active_stimuli = cls.STIMULI[: config["stimulus_count"]]
        trials: List[Dict[str, Any]] = []

        for trial_index in range(config["trials"]):
            stimulus = random.choice(active_stimuli)
            trials.append(
                {
                    "trial_index": trial_index,
                    "stimulus_code": stimulus["code"],
                    "stimulus_label": stimulus["label"],
                    "shape": stimulus["shape"],
                    "color": stimulus["color"],
                    "correct_key": stimulus["key"],
                    "max_response_ms": config["max_response_ms"],
                    "stimulus_ms": config["stimulus_ms"],
                    "iti_ms": config["iti_ms"],
                }
            )

        return {
            "difficulty": difficulty,
            "stimuli": active_stimuli,
            "total_trials": len(trials),
            "trials": trials,
            "config": config,
        }

    @classmethod
    def score_session(cls, session_data: Dict[str, Any], responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        trial_map = {trial["trial_index"]: trial for trial in session_data.get("trials", [])}
        scored_trials = []

        for response in responses:
            trial = trial_map.get(response.get("trial_index"))
            if not trial:
                continue

            user_key = str(response.get("user_key", "")).strip()
            reaction_time = float(response.get("reaction_time", 0) or 0)
            timed_out = reaction_time <= 0 or reaction_time > trial["max_response_ms"]
            correct = (not timed_out) and user_key == trial["correct_key"]

            scored_trials.append(
                {
                    **trial,
                    "user_key": user_key,
                    "reaction_time": reaction_time,
                    "timed_out": timed_out,
                    "correct": correct,
                }
            )

        total_trials = len(trial_map)
        correct_trials = [trial for trial in scored_trials if trial["correct"]]
        valid_rts = [trial["reaction_time"] for trial in correct_trials if trial["reaction_time"] > 0]
        correct_count = len(correct_trials)
        timeout_count = sum(1 for trial in scored_trials if trial["timed_out"])
        accuracy = (correct_count / max(total_trials, 1)) * 100
        avg_rt = sum(valid_rts) / len(valid_rts) if valid_rts else 0.0
        consistency = max(0.0, 100.0 - min(pstdev(valid_rts), 350) / 3) if len(valid_rts) > 1 else (100.0 if valid_rts else 0.0)
        total_seconds = sum(trial["reaction_time"] for trial in scored_trials) / 1000 if scored_trials else 0.0
        processing_speed = correct_count / max(total_seconds, 1)
        decision_efficiency = accuracy if avg_rt == 0 else max(0.0, accuracy - max(0.0, (avg_rt - 900) / 25))
        rt_score = 100.0 if avg_rt == 0 else max(0.0, min(100.0, 100 - ((avg_rt - 650) / 8)))
        score = (accuracy * 0.55) + (rt_score * 0.30) + (consistency * 0.15)

        metrics = {
            "score": round(score, 1),
            "accuracy": round(accuracy, 1),
            "average_reaction_time": round(avg_rt, 1),
            "processing_speed": round(processing_speed, 1),
            "consistency": round(consistency, 1),
            "correct_count": correct_count,
            "total_trials": total_trials,
            "timeout_count": timeout_count,
            "decision_efficiency": round(decision_efficiency, 1),
        }

        difficulty = int(session_data.get("difficulty", 5))
        if metrics["score"] >= cls.ADVANCE_THRESHOLD and metrics["accuracy"] >= 82:
            next_difficulty = min(difficulty + 1, 10)
            adaptation_reason = f"Increased difficulty (score {metrics['score']:.1f} with strong decision accuracy)"
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
