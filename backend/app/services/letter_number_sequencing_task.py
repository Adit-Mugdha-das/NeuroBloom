"""
Letter-Number Sequencing Task Service

WAIS-IV subtest measuring executive working memory and mental manipulation.
User hears/sees mixed letters and numbers, must recall numbers in ascending order
followed by letters in alphabetical order.

Example: "B-3-A-1" → "1-3-A-B"

Clinical Validation: WAIS-IV component, sensitive to MS cognitive dysfunction
Reference: Parmenter et al., 2007

Scoring model (per trial, 0–100):
  Component A – Set recall       (50 pts): did the patient pick the right items?
  Component B – Ordering         (35 pts): are they in the right order?
  Component C – Speed bonus      (15 pts): reaction time relative to a generous par time
  Penalty                        (−pts)  : each wrong item selected costs extra points

Session score is the weighted mean of trial scores, where later (harder) trials
in the warmup-peak-stretch arc count more, matching clinical practice.
"""

import random
from typing import List, Dict, Tuple


class LetterNumberSequencingTask:
    """
    Service for generating and scoring Letter-Number Sequencing trials.
    """

    # ---------------------------------------------------------------------------
    # Difficulty configuration
    # Every level is meaningfully distinct across THREE axes:
    #   1. Sequence length  (memory load)
    #   2. Number/letter ratio  (cognitive switching load — letters are harder to sort)
    #   3. Display timing  (processing speed demand)
    #
    # display_ms  : how long each item is shown  (shorter = less encoding time)
    # interval_ms : blank gap between items       (shorter = less rehearsal time)
    # par_ms      : target RT for the speed bonus — set to length × 2000 ms so
    #               the bonus is earned only by genuinely fast responders.
    #               Old values (14 000–36 000 ms) were far too generous — the bonus
    #               was essentially free at every level.
    # interval_ms floor: kept at 200 ms minimum (below ~150 ms is sub-perceptual).
    # ---------------------------------------------------------------------------
    DIFFICULTY_CONFIG = {
        1:  {"length": 4,  "numbers": 3, "letters": 1, "display_ms":  900, "interval_ms": 400, "par_ms":  8000},
        2:  {"length": 4,  "numbers": 2, "letters": 2, "display_ms":  850, "interval_ms": 375, "par_ms":  8000},
        3:  {"length": 5,  "numbers": 3, "letters": 2, "display_ms":  800, "interval_ms": 350, "par_ms": 10000},
        4:  {"length": 5,  "numbers": 2, "letters": 3, "display_ms":  750, "interval_ms": 325, "par_ms": 10000},
        5:  {"length": 6,  "numbers": 3, "letters": 3, "display_ms":  700, "interval_ms": 300, "par_ms": 12000},
        6:  {"length": 6,  "numbers": 2, "letters": 4, "display_ms":  650, "interval_ms": 275, "par_ms": 12000},
        7:  {"length": 7,  "numbers": 4, "letters": 3, "display_ms":  600, "interval_ms": 250, "par_ms": 14000},
        8:  {"length": 8,  "numbers": 4, "letters": 4, "display_ms":  550, "interval_ms": 225, "par_ms": 16000},
        9:  {"length": 9,  "numbers": 5, "letters": 4, "display_ms":  500, "interval_ms": 210, "par_ms": 18000},
        10: {"length": 10, "numbers": 5, "letters": 5, "display_ms":  450, "interval_ms": 200, "par_ms": 20000},
    }

    # Scoring weights (must sum to 100)
    W_SET       = 50   # correct items recalled regardless of order
    W_ORDER     = 35   # items in the correct sorted order
    W_SPEED     = 15   # reaction time bonus
    PENALTY_PER_WRONG = 5   # deducted per incorrectly selected item (wrong item, not wrong position)

    # Difficulty adaptation thresholds (based on weighted session score, not binary accuracy)
    # Tightened dead-zone: player must genuinely master a level to advance,
    # and falls back sooner when the level is too hard.
    ADVANCE_THRESHOLD  = 82   # score >= this → increase difficulty
    REGRESS_THRESHOLD  = 50   # score <  this → decrease difficulty

    # Available pool
    NUMBERS = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
    LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'R', 'S', 'T']
    # I, O, Q excluded to avoid visual confusion with 1, 0

    # ---------------------------------------------------------------------------
    # Generation
    # ---------------------------------------------------------------------------

    @staticmethod
    def generate_sequence(difficulty: int) -> Tuple[List[str], List[str], List[str]]:
        """Return (scrambled_sequence, correct_numbers, correct_letters)."""
        config = LetterNumberSequencingTask.DIFFICULTY_CONFIG.get(
            difficulty, {"length": 5, "numbers": 3, "letters": 2}
        )
        selected_numbers = random.sample(LetterNumberSequencingTask.NUMBERS, config["numbers"])
        selected_letters = random.sample(LetterNumberSequencingTask.LETTERS, config["letters"])

        sequence = selected_numbers + selected_letters
        random.shuffle(sequence)

        correct_numbers = sorted(selected_numbers, key=lambda x: int(x))
        correct_letters = sorted(selected_letters)

        return sequence, correct_numbers, correct_letters

    @staticmethod
    def generate_trial(difficulty: int) -> Dict:
        """Generate one trial dict with all metadata needed by the frontend."""
        sequence, correct_numbers, correct_letters = LetterNumberSequencingTask.generate_sequence(difficulty)
        config = LetterNumberSequencingTask.DIFFICULTY_CONFIG.get(
            difficulty, {"length": 5, "numbers": 3, "letters": 2, "display_ms": 1000, "interval_ms": 400, "par_ms": 18000}
        )
        return {
            "sequence":        sequence,
            "correct_numbers": correct_numbers,
            "correct_letters": correct_letters,
            "difficulty":      difficulty,
            "length":          len(sequence),
            "display_ms":      config["display_ms"],
            "interval_ms":     config["interval_ms"],
            "par_ms":          config["par_ms"],
        }

    @staticmethod
    def generate_session(difficulty: int, num_trials: int = 8) -> List[Dict]:
        """
        Generate a session with a warmup → peak → stretch arc.
          Trial 1          : difficulty − 1  (warmup,  builds confidence)
          Trials 2 – n−2   : difficulty       (target,  core assessment)
          Trial n−1        : difficulty + 1  (stretch, tests ceiling)
          Trial n          : difficulty       (cooldown, ends on familiar ground)
        """
        trials = []
        for i in range(num_trials):
            if i == 0:
                d = max(1, difficulty - 1)
            elif i == num_trials - 2:
                d = min(10, difficulty + 1)
            else:
                d = difficulty
            trials.append(LetterNumberSequencingTask.generate_trial(d))
        return trials

    # ---------------------------------------------------------------------------
    # Scoring
    # ---------------------------------------------------------------------------

    @staticmethod
    def score_response(
        correct_numbers: List[str],
        correct_letters: List[str],
        user_numbers:    List[str],
        user_letters:    List[str],
        reaction_time_ms: int = 0,
        par_ms: int = 18000,
    ) -> Dict:
        """
        Score one trial using a three-component weighted model.

        Component A – Set recall (W_SET = 50 pts)
            Fraction of correct items the patient actually selected,
            independent of order.  Captures "did they remember what was there?"

        Component B – Ordering (W_ORDER = 35 pts)
            Of the items they got right, how many are in the correct position?
            Weighted by set recall so a patient who recalled nothing can't
            accidentally score ordering points.

        Component C – Speed bonus (W_SPEED = 15 pts)
            Linear bonus for finishing within par time.
            At 0 ms → full 15 pts.  At par_ms or beyond → 0 pts.
            Reaction time is never penalised beyond 0 (no negative speed score).

        Penalty
            Each item selected that does NOT belong in the correct set costs
            PENALTY_PER_WRONG points, capped so total never goes below 0.

        Returns a score in [0, 100].
        """
        W_SET   = LetterNumberSequencingTask.W_SET
        W_ORDER = LetterNumberSequencingTask.W_ORDER
        W_SPEED = LetterNumberSequencingTask.W_SPEED
        PENALTY = LetterNumberSequencingTask.PENALTY_PER_WRONG

        def _score_group(correct: List[str], user: List[str]):
            """Return (set_score 0-1, order_score 0-1, wrong_count)."""
            if not correct:
                return 1.0, 1.0, 0

            correct_set = set(correct)
            user_set    = set(user)

            # Set recall: how many correct items did the user include?
            recalled     = correct_set & user_set
            set_score    = len(recalled) / len(correct)

            # Wrong items: items the user chose that don't belong
            wrong_count  = len(user_set - correct_set)

            # Ordering: positional matches, but only for items in the correct set
            # Compare user's answer against the gold standard position-by-position
            pos_correct = 0
            for i, item in enumerate(correct):
                if i < len(user) and user[i] == item:
                    pos_correct += 1
            order_score = pos_correct / len(correct)

            return set_score, order_score, wrong_count

        num_set, num_ord, num_wrong   = _score_group(correct_numbers, user_numbers)
        let_set, let_ord, let_wrong   = _score_group(correct_letters,  user_letters)

        # Combine numbers and letters proportionally by their share of total items
        total_items = len(correct_numbers) + len(correct_letters)
        if total_items == 0:
            return {"trial_score": 0, "correct": False, "numbers_correct": False,
                    "letters_correct": False, "set_accuracy": 0.0, "order_accuracy": 0.0,
                    "speed_bonus": 0.0, "penalty": 0, "error_type": None,
                    "numbers_set_accuracy": 0.0, "letters_set_accuracy": 0.0,
                    "numbers_order_accuracy": 0.0, "letters_order_accuracy": 0.0}

        w_n = len(correct_numbers) / total_items
        w_l = len(correct_letters) / total_items

        combined_set   = w_n * num_set   + w_l * let_set
        combined_order = w_n * num_ord   + w_l * let_ord
        total_wrong    = num_wrong + let_wrong

        # Component scores
        set_pts   = W_SET   * combined_set
        order_pts = W_ORDER * combined_order

        # Speed bonus: linear decay from W_SPEED → 0 as rt goes from 0 → par_ms
        if par_ms > 0 and reaction_time_ms > 0:
            speed_ratio = max(0.0, 1.0 - reaction_time_ms / par_ms)
        else:
            speed_ratio = 0.0
        speed_pts = W_SPEED * speed_ratio

        # Penalty
        penalty_pts = min(PENALTY * total_wrong, set_pts + order_pts)  # can't go below 0

        raw_score   = set_pts + order_pts + speed_pts - penalty_pts
        trial_score = max(0.0, min(100.0, raw_score))

        # Exact correctness flags (still useful for clinical display)
        numbers_correct = (user_numbers == correct_numbers)
        letters_correct = (user_letters == correct_letters)
        fully_correct   = numbers_correct and letters_correct

        # Error classification
        if fully_correct:
            error_type = None
        elif not numbers_correct and not letters_correct:
            error_type = "both_incorrect"
        elif not numbers_correct:
            error_type = "numbers_incorrect"
        else:
            error_type = "letters_incorrect"

        return {
            "trial_score":              round(trial_score, 1),
            "correct":                  fully_correct,
            "numbers_correct":          numbers_correct,
            "letters_correct":          letters_correct,
            # Granular breakdown
            "set_accuracy":             round(combined_set   * 100, 1),
            "order_accuracy":           round(combined_order * 100, 1),
            "speed_bonus":              round(speed_pts, 1),
            "penalty":                  round(penalty_pts, 1),
            "error_type":               error_type,
            # Per-group detail
            "numbers_set_accuracy":     round(num_set * 100, 1),
            "letters_set_accuracy":     round(let_set * 100, 1),
            "numbers_order_accuracy":   round(num_ord * 100, 1),
            "letters_order_accuracy":   round(let_ord * 100, 1),
        }

    # ---------------------------------------------------------------------------
    # Session metrics
    # ---------------------------------------------------------------------------

    @staticmethod
    def calculate_session_metrics(scored_trials: List[Dict]) -> Dict:
        """
        Aggregate trial scores into session-level metrics.

        Weighting scheme:
          - Warmup trial (index 0)    : weight 0.5  (below-par difficulty, don't over-reward)
          - Core trials               : weight 1.0
          - Stretch trial (index n-2) : weight 1.5  (above-par difficulty, reward extra)
          - Cooldown trial (index n-1): weight 1.0

        Session score = weighted mean of trial_score values (0–100).
        Difficulty adaptation uses this score against ADVANCE/REGRESS thresholds.
        """
        total_trials = len(scored_trials)
        if total_trials == 0:
            return _empty_metrics()

        # Assign weights based on position
        weights = []
        for i in range(total_trials):
            if i == 0:
                weights.append(0.5)
            elif i == total_trials - 2:
                weights.append(1.5)
            else:
                weights.append(1.0)

        total_weight = sum(weights)

        # Weighted session score
        weighted_score = sum(
            w * t.get("trial_score", 0)
            for w, t in zip(weights, scored_trials)
        ) / total_weight

        # Component breakdowns (unweighted averages for display)
        avg_set_acc   = sum(t.get("set_accuracy",   0) for t in scored_trials) / total_trials
        avg_ord_acc   = sum(t.get("order_accuracy", 0) for t in scored_trials) / total_trials
        avg_speed_bon = sum(t.get("speed_bonus",    0) for t in scored_trials) / total_trials
        avg_penalty   = sum(t.get("penalty",        0) for t in scored_trials) / total_trials

        avg_num_set   = sum(t.get("numbers_set_accuracy",   0) for t in scored_trials) / total_trials
        avg_let_set   = sum(t.get("letters_set_accuracy",   0) for t in scored_trials) / total_trials
        avg_num_ord   = sum(t.get("numbers_order_accuracy", 0) for t in scored_trials) / total_trials
        avg_let_ord   = sum(t.get("letters_order_accuracy", 0) for t in scored_trials) / total_trials

        # Binary accuracy (for clinical reference)
        correct_count    = sum(1 for t in scored_trials if t.get("correct", False))
        binary_accuracy  = (correct_count / total_trials) * 100

        # Longest correctly recalled sequence (fully correct trials only)
        longest_sequence = max(
            (t.get("length", 0) for t in scored_trials if t.get("correct", False)),
            default=0
        )

        # Consistency: std-dev of trial_score values (lower std = more consistent)
        trial_scores = [t.get("trial_score", 0) for t in scored_trials]
        mean_ts  = sum(trial_scores) / total_trials
        variance = sum((s - mean_ts) ** 2 for s in trial_scores) / total_trials
        std_dev  = variance ** 0.5
        consistency = max(0.0, 100.0 - std_dev)

        # Speed trend: are they getting faster or slower across trials?
        rts = [t.get("reaction_time", 0) for t in scored_trials if t.get("reaction_time", 0) > 0]
        if len(rts) >= 2:
            speed_trend = "improving" if rts[-1] < rts[0] else "slowing" if rts[-1] > rts[0] * 1.1 else "stable"
        else:
            speed_trend = "stable"

        return {
            # Primary score used for adaptation
            "score":               round(weighted_score, 1),
            # Supporting metrics
            "binary_accuracy":     round(binary_accuracy, 1),
            "correct_count":       correct_count,
            "total_trials":        total_trials,
            "consistency":         round(consistency, 1),
            "longest_sequence":    longest_sequence,
            "speed_trend":         speed_trend,
            # Component breakdown
            "avg_set_accuracy":    round(avg_set_acc,   1),
            "avg_order_accuracy":  round(avg_ord_acc,   1),
            "avg_speed_bonus":     round(avg_speed_bon, 1),
            "avg_penalty":         round(avg_penalty,   1),
            # Per-group breakdown
            "numbers_set_accuracy":    round(avg_num_set, 1),
            "letters_set_accuracy":    round(avg_let_set, 1),
            "numbers_order_accuracy":  round(avg_num_ord, 1),
            "letters_order_accuracy":  round(avg_let_ord, 1),
        }

    # ---------------------------------------------------------------------------
    # Reaction time
    # ---------------------------------------------------------------------------

    @staticmethod
    def calculate_average_reaction_time(scored_trials: List[Dict]) -> int:
        """Return average reaction time in ms across trials that have one."""
        rts = [t.get("reaction_time", 0) for t in scored_trials if t.get("reaction_time", 0) > 0]
        return int(sum(rts) / len(rts)) if rts else 0


def _empty_metrics() -> Dict:
    return {
        "score": 0, "binary_accuracy": 0.0, "correct_count": 0, "total_trials": 0,
        "consistency": 0.0, "longest_sequence": 0, "speed_trend": "stable",
        "avg_set_accuracy": 0.0, "avg_order_accuracy": 0.0,
        "avg_speed_bonus": 0.0, "avg_penalty": 0.0,
        "numbers_set_accuracy": 0.0, "letters_set_accuracy": 0.0,
        "numbers_order_accuracy": 0.0, "letters_order_accuracy": 0.0,
    }
