"""
Rule Shift task service.

Clinically grounded set-shifting task designed as a lighter, more directed
alternative to WCST. Users follow a simple classification rule for a short
block, then must adapt when the active rule changes.
"""

import random
from statistics import pstdev
from typing import Any, Dict, List


class RuleShiftTask:
    """Block-based cognitive flexibility task with explicit rule changes."""

    DIFFICULTY_CONFIG = {
        1: {"blocks": ["color", "shape", "color"], "trials_per_block": 8, "switch_cue_ms": 2600, "target_switch_trials": 2},
        2: {"blocks": ["color", "shape", "color"], "trials_per_block": 9, "switch_cue_ms": 2400, "target_switch_trials": 2},
        3: {"blocks": ["shape", "color", "shape", "color"], "trials_per_block": 9, "switch_cue_ms": 2200, "target_switch_trials": 2},
        4: {"blocks": ["shape", "color", "shape", "count"], "trials_per_block": 9, "switch_cue_ms": 2000, "target_switch_trials": 2},
        5: {"blocks": ["color", "shape", "count", "shape"], "trials_per_block": 10, "switch_cue_ms": 1800, "target_switch_trials": 3},
        6: {"blocks": ["shape", "count", "color", "shape"], "trials_per_block": 10, "switch_cue_ms": 1600, "target_switch_trials": 3},
        7: {"blocks": ["count", "shape", "color", "count", "shape"], "trials_per_block": 10, "switch_cue_ms": 1400, "target_switch_trials": 3},
        8: {"blocks": ["shape", "count", "color", "shape", "count"], "trials_per_block": 11, "switch_cue_ms": 1200, "target_switch_trials": 3},
        9: {"blocks": ["count", "color", "shape", "count", "color"], "trials_per_block": 12, "switch_cue_ms": 1000, "target_switch_trials": 4},
        10: {"blocks": ["shape", "count", "color", "shape", "count", "color"], "trials_per_block": 12, "switch_cue_ms": 900, "target_switch_trials": 4},
    }

    COLORS = ["teal", "orange"]
    SHAPES = ["circle", "triangle"]
    COUNTS = [1, 2]
    LABELS = {
        "color": {"left": "Teal", "right": "Orange"},
        "shape": {"left": "Circle", "right": "Triangle"},
        "count": {"left": "One", "right": "Two"},
    }
    ADVANCE_THRESHOLD = 83
    REGRESS_THRESHOLD = 63

    @classmethod
    def generate_session(cls, difficulty: int) -> Dict[str, Any]:
        config = cls.DIFFICULTY_CONFIG.get(difficulty, cls.DIFFICULTY_CONFIG[5])
        trials: List[Dict[str, Any]] = []

        trial_index = 0
        for block_index, rule in enumerate(config["blocks"]):
            previous_rule = config["blocks"][block_index - 1] if block_index > 0 else None
            block_trials = cls._generate_block_trials(
                block_index=block_index,
                rule=rule,
                previous_rule=previous_rule,
                trials_per_block=config["trials_per_block"],
                target_switch_trials=config["target_switch_trials"],
                start_index=trial_index,
            )
            trials.extend(block_trials)
            trial_index += len(block_trials)

        return {
            "difficulty": difficulty,
            "switch_cue_ms": config["switch_cue_ms"],
            "labels": cls.LABELS,
            "blocks": [
                {
                    "block_index": idx,
                    "rule": rule,
                    "instruction": cls._instruction_for_rule(rule),
                    "trials": config["trials_per_block"],
                }
                for idx, rule in enumerate(config["blocks"])
            ],
            "total_trials": len(trials),
            "trials": trials,
        }

    @classmethod
    def _generate_block_trials(
        cls,
        block_index: int,
        rule: str,
        previous_rule: str,
        trials_per_block: int,
        target_switch_trials: int,
        start_index: int,
    ) -> List[Dict[str, Any]]:
        trials: List[Dict[str, Any]] = []

        for within_block_index in range(trials_per_block):
            trial = cls._generate_trial(rule)
            rule_value = cls._value_for_rule(trial, rule)
            correct_side = cls._correct_side(rule, rule_value)

            is_switch_window = previous_rule is not None and within_block_index < target_switch_trials
            if is_switch_window:
                previous_value = cls._value_for_rule(trial, previous_rule)
                previous_side = cls._correct_side(previous_rule, previous_value)
                if previous_side == correct_side:
                    trial = cls._regenerate_with_different_previous_side(rule, previous_rule, correct_side)
                    rule_value = cls._value_for_rule(trial, rule)
                    correct_side = cls._correct_side(rule, rule_value)

            trial.update(
                {
                    "trial_index": start_index + within_block_index,
                    "block_index": block_index,
                    "within_block_index": within_block_index,
                    "active_rule": rule,
                    "previous_rule": previous_rule,
                    "correct_side": correct_side,
                    "is_switch_trial": is_switch_window,
                }
            )
            trials.append(trial)

        return trials

    @classmethod
    def _generate_trial(cls, rule: str) -> Dict[str, Any]:
        return {
            "color": random.choice(cls.COLORS),
            "shape": random.choice(cls.SHAPES),
            "count": random.choice(cls.COUNTS),
        }

    @classmethod
    def _regenerate_with_different_previous_side(cls, rule: str, previous_rule: str, target_side: str) -> Dict[str, Any]:
        for _ in range(30):
            candidate = cls._generate_trial(rule)
            if cls._correct_side(previous_rule, cls._value_for_rule(candidate, previous_rule)) != target_side:
                return candidate
        return cls._generate_trial(rule)

    @classmethod
    def score_session(cls, session_data: Dict[str, Any], responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        trials = session_data.get("trials", [])
        response_map = {response.get("trial_index"): response for response in responses}
        scored_trials: List[Dict[str, Any]] = []

        for trial in trials:
            response = response_map.get(trial["trial_index"], {})
            selected_side = response.get("selected_side")
            reaction_time_ms = float(response.get("reaction_time_ms", 0) or 0)
            is_correct = selected_side == trial["correct_side"]

            previous_rule = trial.get("previous_rule")
            perseverative = False
            if previous_rule and selected_side in ("left", "right") and selected_side != trial["correct_side"]:
                previous_side = cls._correct_side(previous_rule, cls._value_for_rule(trial, previous_rule))
                perseverative = selected_side == previous_side

            scored_trials.append(
                {
                    **trial,
                    "selected_side": selected_side,
                    "reaction_time_ms": reaction_time_ms,
                    "correct": is_correct,
                    "perseverative_error": perseverative,
                }
            )

        total_trials = len(scored_trials)
        correct_count = sum(1 for trial in scored_trials if trial["correct"])
        overall_accuracy = (correct_count / total_trials) * 100 if total_trials else 0.0

        switch_trials = [trial for trial in scored_trials if trial["is_switch_trial"]]
        stay_trials = [trial for trial in scored_trials if not trial["is_switch_trial"]]

        switch_accuracy = (sum(1 for trial in switch_trials if trial["correct"]) / len(switch_trials) * 100) if switch_trials else 0.0
        stay_accuracy = (sum(1 for trial in stay_trials if trial["correct"]) / len(stay_trials) * 100) if stay_trials else 0.0

        correct_rts = [trial["reaction_time_ms"] for trial in scored_trials if trial["correct"] and trial["reaction_time_ms"] > 0]
        avg_rt = sum(correct_rts) / len(correct_rts) if correct_rts else 0.0
        consistency = max(0.0, 100.0 - min(pstdev(correct_rts), 350) / 3.5) if len(correct_rts) > 1 else (100.0 if correct_rts else 0.0)

        switch_rts = [trial["reaction_time_ms"] for trial in switch_trials if trial["correct"] and trial["reaction_time_ms"] > 0]
        stay_rts = [trial["reaction_time_ms"] for trial in stay_trials if trial["correct"] and trial["reaction_time_ms"] > 0]
        shift_cost = (sum(switch_rts) / len(switch_rts) - sum(stay_rts) / len(stay_rts)) if switch_rts and stay_rts else 0.0

        perseverative_errors = sum(1 for trial in scored_trials if trial["perseverative_error"])
        rt_score = 100.0 if avg_rt == 0 else max(0.0, min(100.0, 100 - ((avg_rt - 700) / 12)))
        shift_penalty = min(max(shift_cost, 0.0) / 22.0, 18.0)
        perseveration_penalty = min(perseverative_errors * 4.5, 18.0)

        score = (
            (overall_accuracy * 0.48)
            + (switch_accuracy * 0.22)
            + (rt_score * 0.15)
            + (consistency * 0.15)
            - shift_penalty
            - perseveration_penalty
        )
        score = max(0.0, min(score, 100.0))

        metrics = {
            "score": round(score, 1),
            "accuracy": round(overall_accuracy, 1),
            "switch_accuracy": round(switch_accuracy, 1),
            "stay_accuracy": round(stay_accuracy, 1),
            "average_reaction_time": round(avg_rt, 1),
            "consistency": round(consistency, 1),
            "shift_cost_ms": round(shift_cost, 1),
            "perseverative_errors": perseverative_errors,
            "correct_count": correct_count,
            "total_trials": total_trials,
            "flexibility_index": round(max(0.0, switch_accuracy - perseverative_errors * 3.0), 1),
        }

        difficulty = int(session_data.get("difficulty", 5))
        if metrics["score"] >= cls.ADVANCE_THRESHOLD and metrics["switch_accuracy"] >= 72 and perseverative_errors <= 5:
            next_difficulty = min(difficulty + 1, 10)
            adaptation_reason = f"Increased difficulty (score {metrics['score']:.1f} with strong rule shifting)"
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

    @classmethod
    def _value_for_rule(cls, trial: Dict[str, Any], rule: str) -> Any:
        return trial[rule]

    @classmethod
    def _correct_side(cls, rule: str, value: Any) -> str:
        if rule == "color":
            return "left" if value == "teal" else "right"
        if rule == "shape":
            return "left" if value == "circle" else "right"
        return "left" if value == 1 else "right"

    @classmethod
    def _instruction_for_rule(cls, rule: str) -> str:
        if rule == "color":
            return "Sort by color: teal left, orange right."
        if rule == "shape":
            return "Sort by shape: circle left, triangle right."
        return "Sort by count: one left, two right."
