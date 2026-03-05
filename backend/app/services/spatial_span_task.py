"""
Spatial Span Task (Corsi Block Test)
Visual-spatial working memory assessment

Clinical Validation: WMS-IV Spatial Span subtest; sensitive to MS-related
visuospatial working-memory deficits.
Reference: Rao et al. (1991), Wechsler (2009)

Scoring model (per trial, 0–100):
  Component A – Positional accuracy  (70 pts): fraction of positions recalled correctly
  Component B – Length bonus         (15 pts): reward for longer correct spans
  Component C – Speed bonus          (15 pts): reaction time relative to par
  Penalty                            (−pts)  : each extra/wrong click beyond sequence length

Session score = weighted mean (warmup 0.5×, core 1.0×, stretch 1.5×, cooldown 1.0×).
"""

import random
from typing import List, Dict

class SpatialSpanTask:
    """
    Corsi Block Test — Spatial Working Memory
    Shows a sequence of blocks lighting up; user reproduces in same or reverse order.
    """

    # -------------------------------------------------------------------------
    # Difficulty configuration
    #
    # Axes of challenge:
    #   grid_size   — more blocks = larger search space
    #   length      — more items to remember
    #   span_type   — backward is harder than forward (requires mental reversal)
    #   display_ms  — how long each block stays lit (shorter = harder encoding)
    #   interval_ms — blank gap between blocks (shorter = less rehearsal time)
    #   par_ms      — target RT for speed bonus = length × 1800 ms
    #
    # Each level is distinct on at least one axis.
    # Levels 1–4: forward only (establish baseline span)
    # Levels 5–7: backward only (adds reversal demand)
    # Levels 8–10: mixed (unpredictable direction = extra cognitive load)
    # -------------------------------------------------------------------------
    DIFFICULTY_CONFIG = {
        1:  {"grid_size": 3, "length": 3, "span_type": "forward",  "display_ms": 1000, "interval_ms": 500, "par_ms":  5400},
        2:  {"grid_size": 3, "length": 4, "span_type": "forward",  "display_ms":  900, "interval_ms": 450, "par_ms":  7200},
        3:  {"grid_size": 4, "length": 4, "span_type": "forward",  "display_ms":  850, "interval_ms": 400, "par_ms":  7200},
        4:  {"grid_size": 4, "length": 5, "span_type": "forward",  "display_ms":  800, "interval_ms": 375, "par_ms":  9000},
        5:  {"grid_size": 4, "length": 5, "span_type": "backward", "display_ms":  750, "interval_ms": 350, "par_ms":  9000},
        6:  {"grid_size": 4, "length": 6, "span_type": "backward", "display_ms":  700, "interval_ms": 325, "par_ms": 10800},
        7:  {"grid_size": 5, "length": 6, "span_type": "backward", "display_ms":  650, "interval_ms": 300, "par_ms": 10800},
        8:  {"grid_size": 5, "length": 7, "span_type": "mixed",    "display_ms":  600, "interval_ms": 275, "par_ms": 12600},
        9:  {"grid_size": 5, "length": 8, "span_type": "mixed",    "display_ms":  550, "interval_ms": 250, "par_ms": 14400},
        10: {"grid_size": 5, "length": 9, "span_type": "mixed",    "display_ms":  500, "interval_ms": 225, "par_ms": 16200},
    }

    # Scoring weights
    W_POSITION = 70   # positional accuracy
    W_SPAN     = 15   # span-length bonus
    W_SPEED    = 15   # reaction-time bonus
    PENALTY_PER_EXTRA = 5   # per click beyond sequence length

    # Adaptation thresholds (session score, 0–100)
    ADVANCE_THRESHOLD = 82   # score >= this → increase difficulty
    REGRESS_THRESHOLD = 50   # score <  this → decrease difficulty

    # -------------------------------------------------------------------------
    # Generation
    # -------------------------------------------------------------------------

    @staticmethod
    def generate_sequence(grid_size: int, length: int) -> List[int]:
        """
        Generate random block sequence (0 … grid_size²−1).
        No immediate repeats so consecutive blocks are always distinct.
        """
        total_blocks = grid_size * grid_size
        sequence: List[int] = []
        last: int = -1
        for _ in range(length):
            choices = [p for p in range(total_blocks) if p != last]
            pos = random.choice(choices)
            sequence.append(pos)
            last = pos
        return sequence

    @staticmethod
    def generate_trial(difficulty: int) -> Dict:
        """Generate one Spatial Span trial with all metadata the frontend needs."""
        config = SpatialSpanTask.DIFFICULTY_CONFIG.get(
            difficulty, SpatialSpanTask.DIFFICULTY_CONFIG[5]
        )
        grid_size   = config["grid_size"]
        length      = config["length"]
        span_type   = config["span_type"]

        if span_type == "mixed":
            span_type = random.choice(["forward", "backward"])

        sequence = SpatialSpanTask.generate_sequence(grid_size, length)

        return {
            "sequence":    sequence,
            "grid_size":   grid_size,
            "length":      length,
            "span_type":   span_type,
            "display_ms":  config["display_ms"],
            "interval_ms": config["interval_ms"],
            "par_ms":      config["par_ms"],
        }

    @staticmethod
    def generate_session(difficulty: int = 5, num_trials: int = 8) -> List[Dict]:
        """
        Generate a session with a warmup → peak → stretch arc.
          Trial 0       : difficulty − 1  (warmup  — builds spatial confidence)
          Trials 1…n−3  : difficulty       (core    — primary assessment)
          Trial n−2     : difficulty + 1  (stretch — tests ceiling)
          Trial n−1     : difficulty       (cooldown)
        """
        trials = []
        for i in range(num_trials):
            if i == 0:
                d = max(1, difficulty - 1)
            elif i == num_trials - 2:
                d = min(10, difficulty + 1)
            else:
                d = difficulty
            trials.append(SpatialSpanTask.generate_trial(d))
        return trials

    # -------------------------------------------------------------------------
    # Scoring
    # -------------------------------------------------------------------------

    @staticmethod
    def score_response(
        sequence: List[int],
        user_response: List[int],
        span_type: str,
        reaction_time_ms: int = 0,
        par_ms: int = 9000,
    ) -> Dict:
        """
        Score one trial on three components (total 0–100).

        Component A – Positional accuracy (W_POSITION = 70 pts)
            Fraction of positions the user got right, regardless of
            whether the response length matches.  This gives partial
            credit rather than zeroing the trial on a length mismatch.

        Component B – Span-length bonus (W_SPAN = 15 pts)
            Awarded only on a fully correct trial, scaled by how long
            the sequence was (max span = 9 at difficulty 10).
            span_bonus = W_SPAN × (length / MAX_SPAN)

        Component C – Speed bonus (W_SPEED = 15 pts)
            Linear: full bonus at 0 ms, zero bonus at par_ms or beyond.

        Penalty
            Each click beyond the correct sequence length costs
            PENALTY_PER_EXTRA points (capped so score ≥ 0).

        Error classification (clinically meaningful):
            None            — fully correct
            partial_recall  — > 50 % positions correct but not perfect
            order_error     — ≤ 50 % positions correct
            length_error    — response length differs from expected (and wrong)
        """
        expected = sequence if span_type == "forward" else list(reversed(sequence))
        exp_len  = len(expected)
        MAX_SPAN = 9  # maximum span at difficulty 10

        # Positional accuracy: compare element-by-element up to the shorter length
        min_len       = min(len(user_response), exp_len)
        pos_correct   = sum(1 for i in range(min_len) if user_response[i] == expected[i])
        position_frac = pos_correct / exp_len if exp_len > 0 else 0.0

        is_correct    = (user_response == expected)

        # Span bonus — only on a fully correct trial
        span_bonus_pts = (SpatialSpanTask.W_SPAN * (exp_len / MAX_SPAN)) if is_correct else 0.0

        # Speed bonus
        if par_ms > 0 and reaction_time_ms > 0:
            speed_ratio = max(0.0, 1.0 - reaction_time_ms / par_ms)
        else:
            speed_ratio = 0.0
        speed_pts = SpatialSpanTask.W_SPEED * speed_ratio

        # Penalty for extra clicks
        extra_clicks  = max(0, len(user_response) - exp_len)
        penalty_pts   = extra_clicks * SpatialSpanTask.PENALTY_PER_EXTRA

        # Combine
        position_pts  = SpatialSpanTask.W_POSITION * position_frac
        raw           = position_pts + span_bonus_pts + speed_pts - penalty_pts
        trial_score   = round(max(0.0, min(100.0, raw)), 1)

        # Partial accuracy (0–100) for display
        accuracy = round(position_frac * 100, 1)

        # Error classification
        if is_correct:
            error_type = None
        elif len(user_response) != exp_len:
            error_type = "length_error"
        elif position_frac > 0.5:
            error_type = "partial_recall"
        else:
            error_type = "order_error"

        return {
            "trial_score":       trial_score,
            "correct":           is_correct,
            "accuracy":          accuracy,
            "correct_positions": pos_correct,
            "error_type":        error_type,
            "expected":          expected,
            "speed_bonus":       round(speed_pts, 1),
            "span_bonus":        round(span_bonus_pts, 1),
            "penalty":           round(penalty_pts, 1),
        }

    # -------------------------------------------------------------------------
    # Session metrics
    # -------------------------------------------------------------------------

    @staticmethod
    def calculate_session_metrics(trials: List[Dict]) -> Dict:
        """
        Aggregate scored trials into session-level metrics.

        Session score = weighted mean of trial_score values:
          Warmup trial (index 0)    : weight 0.5
          Core trials               : weight 1.0
          Stretch trial (index n−2) : weight 1.5
          Cooldown trial (index n−1): weight 1.0

        This replaces the old formula which let longest_span×5 dominate
        (a span-9 trial alone contributed 45/100 regardless of accuracy).
        """
        total_trials = len(trials)
        if total_trials == 0:
            return _empty_metrics()

        # Assign weights by position
        weights = []
        for i in range(total_trials):
            if i == 0:
                weights.append(0.5)
            elif i == total_trials - 2:
                weights.append(1.5)
            else:
                weights.append(1.0)
        total_weight = sum(weights)

        # Weighted session score (uses trial_score if present, else falls back
        # to binary-accuracy-derived score for backward compatibility)
        def _trial_score(t: Dict) -> float:
            if "trial_score" in t:
                return t["trial_score"]
            return 100.0 if t.get("correct", False) else t.get("accuracy", 0.0)

        weighted_score = sum(
            w * _trial_score(t) for w, t in zip(weights, trials)
        ) / total_weight

        # Simple accuracy (binary correct %)
        correct_count = sum(1 for t in trials if t.get("correct", False))
        accuracy      = (correct_count / total_trials) * 100

        # Longest correct span
        longest_span = max(
            (t.get("length", 0) for t in trials if t.get("correct", False)),
            default=0
        )

        # Forward / backward split
        fwd = [t for t in trials if t.get("span_type") == "forward"]
        bwd = [t for t in trials if t.get("span_type") == "backward"]

        forward_accuracy = (
            sum(1 for t in fwd if t.get("correct", False)) / len(fwd) * 100
            if fwd else 0.0
        )
        backward_accuracy = (
            sum(1 for t in bwd if t.get("correct", False)) / len(bwd) * 100
            if bwd else 0.0
        )

        # Consistency: 100 − std-dev of per-trial scores
        scores   = [_trial_score(t) for t in trials]
        mean_s   = sum(scores) / total_trials
        variance = sum((s - mean_s) ** 2 for s in scores) / total_trials
        consistency = max(0.0, 100.0 - variance ** 0.5)

        return {
            "score":              round(weighted_score, 1),
            "accuracy":           round(accuracy, 1),
            "correct_count":      correct_count,
            "total_trials":       total_trials,
            "longest_span":       longest_span,
            "forward_accuracy":   round(forward_accuracy, 1),
            "backward_accuracy":  round(backward_accuracy, 1),
            "consistency":        round(consistency, 1),
        }

    # -------------------------------------------------------------------------
    # Reaction time
    # -------------------------------------------------------------------------

    @staticmethod
    def calculate_average_reaction_time(trials: List[Dict]) -> float:
        """Average reaction time (ms) across trials that recorded one."""
        rts = [t.get("reaction_time", 0) for t in trials if t.get("reaction_time", 0) > 0]
        return sum(rts) / len(rts) if rts else 0.0


def _empty_metrics() -> Dict:
    return {
        "score": 0.0, "accuracy": 0.0, "correct_count": 0, "total_trials": 0,
        "longest_span": 0, "forward_accuracy": 0.0, "backward_accuracy": 0.0,
        "consistency": 0.0,
    }
