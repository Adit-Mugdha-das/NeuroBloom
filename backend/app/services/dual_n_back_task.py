"""
Dual N-Back task implementation.

Clinically grounded extension of the standard N-Back task combining:
- visual-spatial position matching
- auditory/verbal cue matching
"""

import random
from statistics import pstdev
from typing import Any, Dict, List


class DualNBackTask:
    """
    Dual N-Back working-memory task.

    Each stimulus presents:
    - one highlighted position in a 3x3 grid
    - one spoken letter cue

    The user responds whether the current visual position and/or auditory cue
    match the item shown N steps back.
    """

    LETTER_POOL = list("BCDFGHJKLMNPQRSTVWXYZ")
    GRID_POSITIONS = list(range(9))

    DIFFICULTY_CONFIG = {
        1: {"n_level": 1, "stream_length": 10, "stimulus_ms": 1600, "response_window_ms": 1500, "target_rate": 0.22},
        2: {"n_level": 1, "stream_length": 11, "stimulus_ms": 1500, "response_window_ms": 1400, "target_rate": 0.24},
        3: {"n_level": 1, "stream_length": 12, "stimulus_ms": 1450, "response_window_ms": 1350, "target_rate": 0.26},
        4: {"n_level": 2, "stream_length": 12, "stimulus_ms": 1400, "response_window_ms": 1300, "target_rate": 0.24},
        5: {"n_level": 2, "stream_length": 13, "stimulus_ms": 1300, "response_window_ms": 1200, "target_rate": 0.26},
        6: {"n_level": 2, "stream_length": 14, "stimulus_ms": 1200, "response_window_ms": 1150, "target_rate": 0.28},
        7: {"n_level": 2, "stream_length": 15, "stimulus_ms": 1150, "response_window_ms": 1100, "target_rate": 0.30},
        8: {"n_level": 3, "stream_length": 15, "stimulus_ms": 1100, "response_window_ms": 1050, "target_rate": 0.28},
        9: {"n_level": 3, "stream_length": 16, "stimulus_ms": 1000, "response_window_ms": 1000, "target_rate": 0.30},
        10: {"n_level": 3, "stream_length": 18, "stimulus_ms": 950, "response_window_ms": 950, "target_rate": 0.32},
    }

    ADVANCE_THRESHOLD = 84
    REGRESS_THRESHOLD = 64

    @classmethod
    def _pick_non_matching(cls, pool: List[Any], forbidden: Any) -> Any:
        choices = [item for item in pool if item != forbidden]
        return random.choice(choices)

    @classmethod
    def generate_trial(cls, difficulty: int) -> Dict[str, Any]:
        config = cls.DIFFICULTY_CONFIG.get(difficulty, cls.DIFFICULTY_CONFIG[5])
        n_level = config["n_level"]
        stream_length = config["stream_length"]
        target_rate = config["target_rate"]

        stimuli: List[Dict[str, Any]] = []

        for index in range(stream_length):
            if index < n_level:
                position = random.choice(cls.GRID_POSITIONS)
                letter = random.choice(cls.LETTER_POOL)
                visual_target = False
                audio_target = False
            else:
                n_back_stimulus = stimuli[index - n_level]
                visual_target = random.random() < target_rate
                audio_target = random.random() < target_rate

                position = (
                    n_back_stimulus["position"]
                    if visual_target
                    else cls._pick_non_matching(cls.GRID_POSITIONS, n_back_stimulus["position"])
                )
                letter = (
                    n_back_stimulus["letter"]
                    if audio_target
                    else cls._pick_non_matching(cls.LETTER_POOL, n_back_stimulus["letter"])
                )

            stimuli.append(
                {
                    "index": index,
                    "position": position,
                    "letter": letter,
                    "visual_target": visual_target,
                    "audio_target": audio_target,
                    "dual_target": visual_target and audio_target,
                    "user_visual_match": False,
                    "user_audio_match": False,
                    "response_time_ms": 0,
                }
            )

        return {
            "difficulty": difficulty,
            "n_level": n_level,
            "stream_length": stream_length,
            "stimulus_ms": config["stimulus_ms"],
            "response_window_ms": config["response_window_ms"],
            "stimuli": stimuli,
        }

    @classmethod
    def generate_session(cls, difficulty: int, num_trials: int = 4) -> List[Dict[str, Any]]:
        trials: List[Dict[str, Any]] = []

        for index in range(num_trials):
            trial_difficulty = difficulty
            if index >= 2 and difficulty < 10:
                trial_difficulty += 1
            trial = cls.generate_trial(min(trial_difficulty, 10))
            trial["trial_number"] = index + 1
            trials.append(trial)

        return trials

    @classmethod
    def score_trial(cls, trial: Dict[str, Any]) -> Dict[str, Any]:
        stimuli = trial.get("stimuli", [])
        n_level = trial.get("n_level", 2)
        eligible = [stimulus for stimulus in stimuli if stimulus.get("index", 0) >= n_level]

        visual_hits = visual_targets = visual_false_alarms = visual_non_targets = 0
        audio_hits = audio_targets = audio_false_alarms = audio_non_targets = 0
        correct_decisions = total_decisions = dual_targets = dual_correct = 0

        for stimulus in eligible:
            user_visual = bool(stimulus.get("user_visual_match", False))
            user_audio = bool(stimulus.get("user_audio_match", False))
            visual_target = bool(stimulus.get("visual_target", False))
            audio_target = bool(stimulus.get("audio_target", False))

            total_decisions += 2
            correct_decisions += int(user_visual == visual_target) + int(user_audio == audio_target)

            if visual_target:
                visual_targets += 1
                visual_hits += int(user_visual)
            else:
                visual_non_targets += 1
                visual_false_alarms += int(user_visual)

            if audio_target:
                audio_targets += 1
                audio_hits += int(user_audio)
            else:
                audio_non_targets += 1
                audio_false_alarms += int(user_audio)

            if visual_target and audio_target:
                dual_targets += 1
                dual_correct += int(user_visual and user_audio)

        visual_accuracy = ((visual_hits + (visual_non_targets - visual_false_alarms)) / max(visual_targets + visual_non_targets, 1)) * 100
        audio_accuracy = ((audio_hits + (audio_non_targets - audio_false_alarms)) / max(audio_targets + audio_non_targets, 1)) * 100
        overall_accuracy = (correct_decisions / max(total_decisions, 1)) * 100
        visual_hit_rate = (visual_hits / max(visual_targets, 1)) * 100 if visual_targets else 100.0
        audio_hit_rate = (audio_hits / max(audio_targets, 1)) * 100 if audio_targets else 100.0
        visual_false_alarm_rate = (visual_false_alarms / max(visual_non_targets, 1)) * 100 if visual_non_targets else 0.0
        audio_false_alarm_rate = (audio_false_alarms / max(audio_non_targets, 1)) * 100 if audio_non_targets else 0.0
        dual_accuracy = (dual_correct / dual_targets) * 100 if dual_targets else overall_accuracy

        score = (
            (overall_accuracy * 0.55)
            + (((visual_hit_rate + audio_hit_rate) / 2) * 0.25)
            + (dual_accuracy * 0.20)
        )

        return {
            "eligible_stimuli": len(eligible),
            "score": round(score, 1),
            "overall_accuracy": round(overall_accuracy, 1),
            "visual_accuracy": round(visual_accuracy, 1),
            "audio_accuracy": round(audio_accuracy, 1),
            "visual_hit_rate": round(visual_hit_rate, 1),
            "audio_hit_rate": round(audio_hit_rate, 1),
            "visual_false_alarm_rate": round(visual_false_alarm_rate, 1),
            "audio_false_alarm_rate": round(audio_false_alarm_rate, 1),
            "dual_accuracy": round(dual_accuracy, 1),
            "visual_targets": visual_targets,
            "audio_targets": audio_targets,
            "dual_targets": dual_targets,
            "correct_decisions": correct_decisions,
            "total_decisions": total_decisions,
        }

    @classmethod
    def calculate_session_metrics(cls, trials: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not trials:
            return {
                "score": 0.0,
                "accuracy": 0.0,
                "visual_accuracy": 0.0,
                "audio_accuracy": 0.0,
                "dual_accuracy": 0.0,
                "consistency": 0.0,
                "eligible_stimuli": 0,
                "correct_decisions": 0,
                "total_decisions": 0,
                "visual_false_alarm_rate": 0.0,
                "audio_false_alarm_rate": 0.0,
                "n_level": 0,
            }

        trial_scores = [trial["metrics"]["score"] for trial in trials]
        visual_acc = [trial["metrics"]["visual_accuracy"] for trial in trials]
        audio_acc = [trial["metrics"]["audio_accuracy"] for trial in trials]
        dual_acc = [trial["metrics"]["dual_accuracy"] for trial in trials]

        correct_decisions = sum(trial["metrics"]["correct_decisions"] for trial in trials)
        total_decisions = sum(trial["metrics"]["total_decisions"] for trial in trials)
        eligible_stimuli = sum(trial["metrics"]["eligible_stimuli"] for trial in trials)

        consistency_penalty = min(pstdev(trial_scores), 35) * 2 if len(trial_scores) > 1 else 0
        consistency = max(0.0, 100.0 - consistency_penalty)

        return {
            "score": round(sum(trial_scores) / len(trial_scores), 1),
            "accuracy": round((correct_decisions / max(total_decisions, 1)) * 100, 1),
            "visual_accuracy": round(sum(visual_acc) / len(visual_acc), 1),
            "audio_accuracy": round(sum(audio_acc) / len(audio_acc), 1),
            "dual_accuracy": round(sum(dual_acc) / len(dual_acc), 1),
            "consistency": round(consistency, 1),
            "eligible_stimuli": eligible_stimuli,
            "correct_decisions": correct_decisions,
            "total_decisions": total_decisions,
            "visual_false_alarm_rate": round(
                sum(trial["metrics"]["visual_false_alarm_rate"] for trial in trials) / len(trials),
                1,
            ),
            "audio_false_alarm_rate": round(
                sum(trial["metrics"]["audio_false_alarm_rate"] for trial in trials) / len(trials),
                1,
            ),
            "n_level": max(trial.get("n_level", 1) for trial in trials),
        }

    @staticmethod
    def calculate_average_reaction_time(trials: List[Dict[str, Any]]) -> float:
        reaction_times = []

        for trial in trials:
            for stimulus in trial.get("stimuli", []):
                response_time = stimulus.get("response_time_ms", 0)
                if response_time and response_time > 0:
                    reaction_times.append(response_time)

        if not reaction_times:
            return 0.0

        return round(sum(reaction_times) / len(reaction_times), 1)
