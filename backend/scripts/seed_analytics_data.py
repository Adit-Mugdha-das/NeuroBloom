"""
Seed recent analytics data so the admin analytics charts are populated.

Injects sessions (and session contexts) for the last 14 days so that:
  - Patient Activity chart  (last 7 days)  shows daily bars
  - Cognitive Performance Trend (last 14 days) shows an upward trend
  - Fatigue Trends (last 14 days) shows a downward fatigue curve
  - Task Completion Rate (last 14 days) shows high completion %

Run from backend/:
    venv\\Scripts\\python.exe scripts/seed_analytics_data.py
"""

import json
import random
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.core.config import engine
from app.models.session_context import SessionContext
from app.models.training_plan import TrainingPlan  # noqa: F401 – registers table for FK resolution
from app.models.training_session import TrainingSession
from app.models.user import User  # noqa: F401 – registers table for FK resolution

# --------------------------------------------------------------------------- #
# Patient → TrainingPlan mapping (from DB)                                    #
# --------------------------------------------------------------------------- #
PATIENT_PLAN_MAP = {
    2:  1,   # test@gmail.com
    30: 26,  # Sharmin Akter
    31: 27,  # Md. Rashedul Islam
    32: 28,  # Farhana Yasmin
    33: 29,  # Imran H. Chowdhury
    34: 30,  # Tania Mahmuda
    35: 31,  # Naeem Hasan
    36: 32,  # Sabina Khatun
    37: 33,  # Mahmudul Bari
    38: 34,  # Nabila Rahman
    39: 35,  # Omar Faruq
}

TASK_POOL = [
    ("working_memory", "n_back",          "n_back"),
    ("working_memory", "digit_span",      "digit_span"),
    ("attention",      "sdmt",            "sdmt"),
    ("attention",      "continuous_performance", "continuous_performance"),
    ("attention",      "trail_making",    "trail_making_a"),
    ("processing",     "pattern_comparison", "pattern_comparison"),
    ("processing",     "inspection_time", "inspection_time"),
    ("executive",      "rule_switch",     "rule_shift"),
    ("executive",      "stroop",          "stroop"),
    ("memory",         "verbal_fluency",  "category_fluency"),
]

RANDOM_SEED = 99
random.seed(RANDOM_SEED)

TODAY = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

# --------------------------------------------------------------------------- #
# How many patients are active each day over the 14-day window                #
# (index 0 = 14 days ago, index 13 = yesterday)                               #
# We gradually increase activity toward the present                           #
# --------------------------------------------------------------------------- #
#  day_offset: how many patients do at least one session that day
DAILY_ACTIVE_PATIENTS = [3, 2, 4, 3, 5, 4, 6, 5, 7, 6, 8, 7, 9, 8]  # index 0..13

# Score trajectory: slight improvement over the 14 days
BASE_SCORES = [62, 64, 66, 63, 68, 70, 67, 72, 71, 74, 76, 73, 78, 80]

# Fatigue trajectory: improving (lower = less fatigue)
BASE_FATIGUE = [7, 7, 6, 7, 6, 6, 5, 6, 5, 5, 4, 5, 4, 3]


def make_raw_data(task_code: str, score: float, accuracy: float, rt: float) -> str:
    trials = []
    for i in range(20):
        trial_rt = rt + random.randint(-80, 80)
        trial_correct = random.random() < (accuracy / 100)
        trials.append({
            "trial": i + 1,
            "reaction_time_ms": max(200, trial_rt),
            "correct": trial_correct,
            "stimulus": random.randint(1, 5),
        })
    return json.dumps({
        "task_code": task_code,
        "trials": trials,
        "summary": {"score": score, "accuracy": accuracy, "avg_rt": rt},
    })


def seed_sessions(db: Session) -> int:
    patient_ids = list(PATIENT_PLAN_MAP.keys())
    total_added = 0

    for day_idx in range(14):  # 0 = 14 days ago, 13 = yesterday
        days_ago = 13 - day_idx
        day_start = TODAY - timedelta(days=days_ago)
        n_active = DAILY_ACTIVE_PATIENTS[day_idx]
        score_base = BASE_SCORES[day_idx]
        fatigue_base = BASE_FATIGUE[day_idx]

        # Pick n_active distinct patients for this day
        active_today = random.sample(patient_ids, min(n_active, len(patient_ids)))

        for uid in active_today:
            plan_id = PATIENT_PLAN_MAP[uid]
            # Each patient does 1-3 tasks per day
            n_tasks = random.randint(1, 3)
            tasks_today = random.sample(TASK_POOL, min(n_tasks, len(TASK_POOL)))

            # Session context for the day (one per patient per day)
            fatigue = max(1, min(10, fatigue_base + random.randint(-1, 2)))
            sleep_q = max(1, min(10, 10 - fatigue + random.randint(-1, 1)))
            sleep_hrs = round(random.uniform(5.5, 8.5), 1)
            hour_offset = timedelta(
                hours=random.randint(8, 20),
                minutes=random.randint(0, 59),
            )
            context_ts = day_start + hour_offset

            context_obj = SessionContext(
                user_id=uid,
                training_session_id=None,  # will set after first session
                created_at=context_ts,
                fatigue_level=fatigue,
                sleep_quality=sleep_q,
                sleep_hours=sleep_hrs,
                medication_taken_today=random.random() > 0.2,
                hours_since_medication=round(random.uniform(1.0, 8.0), 1),
                pain_level=random.randint(1, 4),
                stress_level=random.randint(2, 6),
                time_of_day=random.choice(["morning", "afternoon", "evening"]),
                readiness_level=max(1, min(10, 10 - fatigue + random.randint(-1, 2))),
            )
            db.add(context_obj)
            db.flush()  # get context_obj.id

            first_session_id = None

            for task_idx, (domain, task_type, task_code) in enumerate(tasks_today):
                score = min(100.0, max(30.0, score_base + random.uniform(-8, 12)))
                accuracy = min(100.0, max(40.0, score + random.uniform(-5, 5)))
                rt = max(250, int(800 - score * 4 + random.randint(-60, 60)))
                difficulty = random.randint(2, 6)

                ts_offset = hour_offset + timedelta(minutes=task_idx * 12 + random.randint(2, 8))
                session_ts = day_start + ts_offset

                sess = TrainingSession(
                    user_id=uid,
                    training_plan_id=plan_id,
                    domain=domain,
                    task_type=task_type,
                    task_code=task_code,
                    score=round(score, 1),
                    accuracy=round(accuracy, 1),
                    average_reaction_time=float(rt),
                    consistency=round(random.uniform(60, 95), 1),
                    errors=random.randint(0, 5),
                    difficulty_level=difficulty,
                    difficulty_before=difficulty,
                    difficulty_after=min(10, difficulty + random.choice([-1, 0, 0, 1])),
                    duration=random.randint(240, 600),
                    completed=True,
                    created_at=session_ts,
                    raw_data=make_raw_data(task_code, score, accuracy, rt),
                    adaptation_reason=random.choice([
                        "score_above_threshold", "consistent_performance",
                        "score_below_threshold", None,
                    ]),
                )
                db.add(sess)
                db.flush()

                if first_session_id is None:
                    first_session_id = sess.id
                    context_obj.training_session_id = first_session_id

                total_added += 1

    db.commit()
    return total_added


def main():
    with Session(engine) as db:
        print("Seeding analytics demo data for last 14 days...")
        count = seed_sessions(db)
        print(f"Done. Added {count} training sessions with session contexts.")


if __name__ == "__main__":
    main()
