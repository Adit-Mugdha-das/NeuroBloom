from __future__ import annotations

import json
import random
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import and_, or_
from sqlmodel import Session, col, select

from app.core.config import engine
from app.core.security import hash_password
from app.core.prescriptions import build_prescription_verification_id
from app.models.admin import Admin
from app.models.baseline_assessment import BaselineAssessment
from app.models.doctor import Doctor
from app.models.doctor_intervention import DoctorIntervention
from app.models.message import Message
from app.models.patient_assignment import PatientAssignment
from app.models.progress_report import ProgressReport
from app.models.risk_alert import RiskAlert
from app.models.session_context import SessionContext
from app.models.test_result import TestResult
from app.models.training_plan import TrainingPlan
from app.models.training_session import TrainingSession
from app.models.user import User


DEMO_DOCTOR_PASSWORD = "DoctorDemo123!"
DEMO_PATIENT_PASSWORD = "PatientDemo123!"
RANDOM_SEED = 42


@dataclass(frozen=True)
class DoctorSeed:
    full_name: str
    email: str
    license_number: str
    specialization: str
    institution: str


@dataclass(frozen=True)
class PatientSeed:
    full_name: str
    email: str
    date_of_birth: str
    diagnosis: str
    treatment_goal: str
    scenario: str
    baseline_scores: dict[str, float]


DOCTORS = [
    DoctorSeed(
        full_name="Dr. Samira Rahman",
        email="dr.samira.rahman@demo.neurobloom.bd",
        license_number="BD-NEU-24031",
        specialization="Neurology",
        institution="National Institute of Neurosciences & Hospital, Dhaka",
    ),
    DoctorSeed(
        full_name="Dr. Arefin Kabir",
        email="dr.arefin.kabir@demo.neurobloom.bd",
        license_number="BD-NPSY-18742",
        specialization="Neuropsychology",
        institution="Bangabandhu Sheikh Mujib Medical University, Shahbagh, Dhaka",
    ),
]


PATIENTS = [
    PatientSeed(
        full_name="Sharmin Akter",
        email="sharmin.akter@demo.neurobloom.bd",
        date_of_birth="1991-04-17",
        diagnosis="Relapsing-Remitting Multiple Sclerosis",
        treatment_goal="Improve processing speed and sustain gains in working memory during daily cognitive training.",
        scenario="improving",
        baseline_scores={
            "working_memory": 58.0,
            "attention": 56.0,
            "flexibility": 60.0,
            "planning": 64.0,
            "processing_speed": 49.0,
            "visual_scanning": 61.0,
        },
    ),
    PatientSeed(
        full_name="Md. Rashedul Islam",
        email="rashedul.islam@demo.neurobloom.bd",
        date_of_birth="1987-09-28",
        diagnosis="Relapsing-Remitting Multiple Sclerosis with fatigue-linked cognitive variability",
        treatment_goal="Reduce attention variability and improve consistency on high-fatigue days.",
        scenario="fatigue_variability",
        baseline_scores={
            "working_memory": 53.0,
            "attention": 44.0,
            "flexibility": 50.0,
            "planning": 55.0,
            "processing_speed": 42.0,
            "visual_scanning": 52.0,
        },
    ),
]


TASK_SEQUENCE = [
    {"domain": "working_memory", "task_type": "n_back", "task_code": "n_back"},
    {"domain": "processing_speed", "task_type": "sdmt", "task_code": "sdmt"},
    {"domain": "attention", "task_type": "pasat", "task_code": "pasat"},
    {"domain": "flexibility", "task_type": "task_switching", "task_code": "task_switching"},
    {"domain": "planning", "task_type": "tower_of_london", "task_code": "tower_of_london"},
    {"domain": "visual_scanning", "task_type": "visual_search", "task_code": "visual_search"},
    {"domain": "attention", "task_type": "stroop", "task_code": "stroop"},
    {"domain": "processing_speed", "task_type": "pattern_comparison", "task_code": "pattern_comparison"},
]


RECOMMENDED_TASKS = {
    "working_memory": ["n_back", "digit_span"],
    "attention": ["pasat", "stroop"],
    "flexibility": ["task_switching", "trail_making_b"],
    "planning": ["tower_of_london", "category_fluency"],
    "processing_speed": ["sdmt", "pattern_comparison"],
    "visual_scanning": ["visual_search", "cancellation"],
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def average(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def compute_overall_score(domain_scores: dict[str, float]) -> float:
    return round(sum(domain_scores.values()) / len(domain_scores), 2)


def password_hash(password: str) -> str:
    return hash_password(password)


def require_id(value: int | None, label: str) -> int:
    if value is None:
        raise ValueError(f"{label} must be persisted before use")
    return value


def delete_records(records: list[Any], session: Session) -> None:
    for record in records:
        session.delete(record)


def baseline_test_result_payloads(patient_seed: PatientSeed) -> list[dict[str, Any]]:
    scores = patient_seed.baseline_scores
    return [
        {
            "task_type": "working_memory",
            "score": scores["working_memory"],
            "details": {
                "score": scores["working_memory"],
                "accuracy": round(min(100.0, scores["working_memory"] + 18.0), 2),
                "max_span": 5 if patient_seed.scenario == "improving" else 4,
            },
        },
        {
            "task_type": "attention",
            "score": scores["attention"],
            "details": {
                "score": scores["attention"],
                "accuracy": round(min(100.0, scores["attention"] + 16.0), 2),
                "commission_errors": 2 if patient_seed.scenario == "improving" else 4,
            },
        },
        {
            "task_type": "flexibility",
            "score": scores["flexibility"],
            "details": {
                "score": scores["flexibility"],
                "switch_cost": 740 if patient_seed.scenario == "improving" else 910,
            },
        },
        {
            "task_type": "planning",
            "score": scores["planning"],
            "details": {
                "score": scores["planning"],
                "optimal_moves_ratio": 0.72 if patient_seed.scenario == "improving" else 0.61,
            },
        },
        {
            "task_type": "processing_speed",
            "score": scores["processing_speed"],
            "details": {
                "score": scores["processing_speed"],
                "average_reaction_time": 910 if patient_seed.scenario == "improving" else 1120,
            },
        },
        {
            "task_type": "visual_scanning",
            "score": scores["visual_scanning"],
            "details": {
                "score": scores["visual_scanning"],
                "targets_found": 22 if patient_seed.scenario == "improving" else 18,
            },
        },
    ]


def build_session_trials(mean_rt: float, accuracy: float, fatigue_bias: float, seed_index: int) -> list[dict[str, Any]]:
    randomizer = random.Random(RANDOM_SEED + seed_index)
    trials: list[dict[str, Any]] = []
    correct_trials = max(1, round(12 * (accuracy / 100.0)))

    for index in range(12):
        progression = index / 11 if 11 else 0
        reaction_time = mean_rt + (progression * fatigue_bias) + randomizer.randint(-55, 55)
        is_correct = index < correct_trials
        trials.append(
            {
                "trial_number": index + 1,
                "stimulus": f"stimulus_{index + 1}",
                "response": "correct" if is_correct else "incorrect",
                "correct": is_correct,
                "reaction_time": max(250, round(reaction_time, 2)),
            }
        )

    randomizer.shuffle(trials)
    trials.sort(key=lambda item: item["trial_number"])
    return trials


def scenario_session_values(patient: PatientSeed, session_index: int) -> dict[str, float]:
    if patient.scenario == "improving":
        score = 58 + (session_index * 3.4) + random.uniform(-2.0, 2.0)
        accuracy = 72 + (session_index * 2.1) + random.uniform(-2.5, 2.5)
        mean_rt = 1180 - (session_index * 38) + random.uniform(-35, 35)
        consistency = 66 + (session_index * 2.6) + random.uniform(-2.0, 2.0)
        fatigue_bias = 85 - (session_index * 4)
        difficulty_before = min(7, 3 + (session_index // 2))
    else:
        score = 49 + (session_index * 1.3) + random.uniform(-5.0, 4.0)
        if session_index in {2, 5}:
            score -= 6
        accuracy = 67 + (session_index * 1.0) + random.uniform(-4.0, 3.0)
        mean_rt = 1285 - (session_index * 18) + random.uniform(-70, 70)
        if session_index in {2, 5}:
            mean_rt += 120
        consistency = 59 + (session_index * 1.1) + random.uniform(-4.0, 3.0)
        fatigue_bias = 145 - (session_index * 3)
        difficulty_before = min(6, 3 + (session_index // 3))

    difficulty_after = difficulty_before + (1 if accuracy >= 78 else 0)
    errors = max(0, round((100 - accuracy) / 7))

    return {
        "score": round(max(35, min(score, 92)), 2),
        "accuracy": round(max(50, min(accuracy, 97)), 2),
        "mean_rt": round(max(420, mean_rt), 2),
        "consistency": round(max(45, min(consistency, 96)), 2),
        "fatigue_bias": round(max(35, fatigue_bias), 2),
        "difficulty_before": difficulty_before,
        "difficulty_after": min(10, difficulty_after),
        "errors": errors,
    }


def session_context_values(patient: PatientSeed, session_index: int) -> dict[str, Any]:
    base_time_of_day = "morning" if session_index % 2 == 0 else "evening"

    if patient.scenario == "improving":
        return {
            "fatigue_level": 4 + (1 if session_index in {3, 6} else 0),
            "sleep_quality": 7 + (1 if session_index >= 4 else 0),
            "sleep_hours": 7.0 + (0.5 if session_index % 3 == 0 else 0.0),
            "medication_taken_today": True,
            "hours_since_medication": 2.0 + (session_index % 3) * 0.5,
            "pain_level": 2,
            "stress_level": 3 + (1 if session_index == 2 else 0),
            "time_of_day": base_time_of_day,
            "readiness_level": 7 + (1 if session_index >= 5 else 0),
            "notes": "Reported a productive training session with manageable fatigue." if session_index == 4 else None,
            "distractions_present": session_index == 1,
            "location": "home",
        }

    return {
        "fatigue_level": 7 + (1 if session_index in {2, 5} else 0),
        "sleep_quality": 5 - (1 if session_index in {2, 5} else 0),
        "sleep_hours": 6.0 - (0.5 if session_index in {2, 5} else 0.0),
        "medication_taken_today": True,
        "hours_since_medication": 4.0 + (session_index % 2),
        "pain_level": 4 + (1 if session_index in {2, 5} else 0),
        "stress_level": 5 + (1 if session_index >= 4 else 0),
        "time_of_day": base_time_of_day,
        "readiness_level": 5 - (1 if session_index in {2, 5} else 0),
        "notes": "Patient noted fatigue and slower focus in the evening." if session_index in {2, 5} else None,
        "distractions_present": session_index in {1, 6},
        "location": "home",
    }


def derive_focus_areas(baseline_scores: dict[str, float]) -> tuple[list[str], list[str], list[str]]:
    ordered = sorted(baseline_scores.items(), key=lambda item: item[1])
    primary = [domain for domain, _ in ordered[:2]]
    secondary = [domain for domain, _ in ordered[2:4]]
    maintenance = [domain for domain, _ in ordered[4:6]]
    return primary, secondary, maintenance


def build_initial_difficulty(baseline_scores: dict[str, float]) -> dict[str, int]:
    difficulty = {}
    for domain, score in baseline_scores.items():
        if score < 45:
            difficulty[domain] = 2
        elif score < 55:
            difficulty[domain] = 3
        elif score < 65:
            difficulty[domain] = 4
        else:
            difficulty[domain] = 5
    return difficulty


def build_current_difficulty(initial: dict[str, int], scenario: str) -> dict[str, int]:
    bonus = 1 if scenario == "improving" else 0
    return {domain: min(10, value + bonus) for domain, value in initial.items()}


def build_report_data(
    sessions: list[TrainingSession],
    baseline: BaselineAssessment,
    period_start: datetime,
    period_end: datetime,
) -> dict[str, Any]:
    domain_stats: dict[str, dict[str, Any]] = {}
    task_performance: dict[str, dict[str, Any]] = {}
    daily_activity: dict[str, dict[str, Any]] = {}

    for session in sessions:
        domain_entry = domain_stats.setdefault(
            session.domain,
            {
                "session_count": 0,
                "avg_score": 0.0,
                "avg_accuracy": 0.0,
                "avg_reaction_time": 0.0,
                "avg_difficulty": 0.0,
                "baseline_score": getattr(baseline, f"{session.domain}_score", None),
                "scores": [],
                "difficulties": [],
                "total_score": 0.0,
                "total_accuracy": 0.0,
                "total_reaction_time": 0.0,
            },
        )
        domain_entry["session_count"] += 1
        domain_entry["total_score"] += session.score
        domain_entry["total_accuracy"] += session.accuracy
        domain_entry["total_reaction_time"] += session.average_reaction_time
        domain_entry["scores"].append(session.score)
        domain_entry["difficulties"].append(session.difficulty_level)

        task_entry = task_performance.setdefault(
            session.task_code or session.task_type,
            {"task_type": session.task_type, "task_code": session.task_code, "session_count": 0, "scores": []},
        )
        task_entry["session_count"] += 1
        task_entry["scores"].append(session.score)

        day_key = session.created_at.date().isoformat()
        day_entry = daily_activity.setdefault(day_key, {"sessions": 0, "total_duration": 0, "scores": []})
        day_entry["sessions"] += 1
        day_entry["total_duration"] += session.duration
        day_entry["scores"].append(session.score)

    for stats in domain_stats.values():
        count = stats["session_count"]
        stats["avg_score"] = round(stats["total_score"] / count, 2)
        stats["avg_accuracy"] = round(stats["total_accuracy"] / count, 2)
        stats["avg_reaction_time"] = round(stats["total_reaction_time"] / count, 2)
        stats["avg_difficulty"] = round(sum(stats["difficulties"]) / len(stats["difficulties"]), 2)

        baseline_score = stats["baseline_score"]
        if baseline_score is not None:
            improvement = stats["avg_score"] - baseline_score
            stats["improvement"] = round(improvement, 2)
            stats["improvement_percent"] = round((improvement / baseline_score) * 100, 1) if baseline_score > 0 else 0.0
        else:
            stats["improvement"] = None
            stats["improvement_percent"] = None

        if len(stats["scores"]) >= 2:
            midpoint = len(stats["scores"]) // 2
            first_avg = sum(stats["scores"][:midpoint]) / len(stats["scores"][:midpoint])
            second_avg = sum(stats["scores"][midpoint:]) / len(stats["scores"][midpoint:])
            stats["trend"] = "improving" if second_avg > first_avg else "declining"
            stats["trend_change"] = round(second_avg - first_avg, 2)
        else:
            stats["trend"] = "stable"
            stats["trend_change"] = 0.0

        del stats["scores"]
        del stats["difficulties"]
        del stats["total_score"]
        del stats["total_accuracy"]
        del stats["total_reaction_time"]

    for task_entry in task_performance.values():
        task_entry["avg_score"] = average(task_entry["scores"])
        del task_entry["scores"]

    for day_entry in daily_activity.values():
        day_entry["avg_score"] = average(day_entry["scores"])
        del day_entry["scores"]

    return {
        "summary": {
            "total_sessions": len(sessions),
            "total_duration_minutes": round(sum(session.duration for session in sessions) / 60, 2),
            "avg_overall_score": average([session.score for session in sessions]),
            "active_days": len(daily_activity),
            "period_days": max(1, (period_end - period_start).days),
        },
        "baseline": {
            "completed": True,
            "date": baseline.assessment_date.isoformat(),
            "overall_score": baseline.overall_score,
            "domain_scores": {
                "working_memory": baseline.working_memory_score,
                "attention": baseline.attention_score,
                "flexibility": baseline.flexibility_score,
                "planning": baseline.planning_score,
                "processing_speed": baseline.processing_speed_score,
                "visual_scanning": baseline.visual_scanning_score,
            },
        },
        "domain_stats": domain_stats,
        "task_performance": task_performance,
        "daily_activity": daily_activity,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
    }


def cleanup_existing_demo_data(session: Session) -> None:
    doctor_emails = [doctor.email for doctor in DOCTORS]
    patient_emails = [patient.email for patient in PATIENTS]

    existing_doctors = list(session.exec(select(Doctor).where(col(Doctor.email).in_(doctor_emails))).all())
    existing_patients = list(session.exec(select(User).where(col(User.email).in_(patient_emails))).all())

    doctor_ids = {doctor.id for doctor in existing_doctors if doctor.id is not None}
    patient_ids = {patient.id for patient in existing_patients if patient.id is not None}

    if patient_ids:
        delete_records(
            list(
                session.exec(
                    select(Message).where(
                        or_(
                            and_(col(Message.sender_type) == "patient", col(Message.sender_id).in_(patient_ids)),
                            and_(col(Message.recipient_type) == "patient", col(Message.recipient_id).in_(patient_ids)),
                        )
                    )
                ).all()
            ),
            session,
        )
        delete_records(list(session.exec(select(RiskAlert).where(col(RiskAlert.patient_id).in_(patient_ids))).all()), session)
        delete_records(list(session.exec(select(ProgressReport).where(col(ProgressReport.patient_id).in_(patient_ids))).all()), session)
        delete_records(list(session.exec(select(SessionContext).where(col(SessionContext.user_id).in_(patient_ids))).all()), session)
        delete_records(list(session.exec(select(TrainingSession).where(col(TrainingSession.user_id).in_(patient_ids))).all()), session)
        delete_records(list(session.exec(select(TrainingPlan).where(col(TrainingPlan.user_id).in_(patient_ids))).all()), session)
        delete_records(list(session.exec(select(BaselineAssessment).where(col(BaselineAssessment.user_id).in_(patient_ids))).all()), session)
        delete_records(list(session.exec(select(TestResult).where(col(TestResult.user_id).in_(patient_ids))).all()), session)
        delete_records(list(session.exec(select(PatientAssignment).where(col(PatientAssignment.patient_id).in_(patient_ids))).all()), session)

    if doctor_ids:
        delete_records(
            list(
                session.exec(
                    select(Message).where(
                        or_(
                            and_(col(Message.sender_type) == "doctor", col(Message.sender_id).in_(doctor_ids)),
                            and_(col(Message.recipient_type) == "doctor", col(Message.recipient_id).in_(doctor_ids)),
                        )
                    )
                ).all()
            ),
            session,
        )
        delete_records(list(session.exec(select(ProgressReport).where(col(ProgressReport.doctor_id).in_(doctor_ids))).all()), session)
        delete_records(list(session.exec(select(DoctorIntervention).where(col(DoctorIntervention.doctor_id).in_(doctor_ids))).all()), session)
        delete_records(list(session.exec(select(PatientAssignment).where(col(PatientAssignment.doctor_id).in_(doctor_ids))).all()), session)

    session.flush()
    delete_records(existing_patients, session)
    delete_records(existing_doctors, session)
    session.commit()


def seed_doctors(session: Session) -> dict[str, Doctor]:
    created: dict[str, Doctor] = {}
    for seed in DOCTORS:
        doctor = Doctor(
            email=seed.email,
            password_hash=password_hash(DEMO_DOCTOR_PASSWORD),
            full_name=seed.full_name,
            license_number=seed.license_number,
            specialization=seed.specialization,
            institution=seed.institution,
            is_active=True,
            is_verified=True,
            created_at=datetime.now(timezone.utc) - timedelta(days=120),
        )
        session.add(doctor)
        session.commit()
        session.refresh(doctor)
        created[seed.email] = doctor
    return created


def seed_patients(session: Session) -> dict[str, User]:
    created: dict[str, User] = {}
    for seed in PATIENTS:
        patient = User(
            email=seed.email,
            password_hash=password_hash(DEMO_PATIENT_PASSWORD),
            full_name=seed.full_name,
            date_of_birth=seed.date_of_birth,
            diagnosis=seed.diagnosis,
            consent_to_share=True,
            is_active=True,
        )
        session.add(patient)
        session.commit()
        session.refresh(patient)
        created[seed.email] = patient
    return created


def seed_assignment(session: Session, doctor: Doctor, patient: User, patient_seed: PatientSeed) -> PatientAssignment:
    doctor_id = require_id(doctor.id, "doctor.id")
    patient_id = require_id(patient.id, "patient.id")
    assignment = PatientAssignment(
        doctor_id=doctor_id,
        patient_id=patient_id,
        assigned_at=datetime.now(timezone.utc) - timedelta(days=70),
        is_active=True,
        diagnosis=patient_seed.diagnosis,
        notes="Synthetic demo assignment for teacher presentation.",
        treatment_goal=patient_seed.treatment_goal,
    )
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    return assignment


def seed_baseline(session: Session, patient: User, patient_seed: PatientSeed) -> BaselineAssessment:
    patient_id = require_id(patient.id, "patient.id")
    baseline = BaselineAssessment(
        user_id=patient_id,
        assessment_date=datetime.now() - timedelta(days=63),
        working_memory_score=patient_seed.baseline_scores["working_memory"],
        attention_score=patient_seed.baseline_scores["attention"],
        flexibility_score=patient_seed.baseline_scores["flexibility"],
        planning_score=patient_seed.baseline_scores["planning"],
        processing_speed_score=patient_seed.baseline_scores["processing_speed"],
        visual_scanning_score=patient_seed.baseline_scores["visual_scanning"],
        overall_score=compute_overall_score(patient_seed.baseline_scores),
        raw_metrics=json.dumps({"source": "synthetic_demo_dataset", "scenario": patient_seed.scenario}),
        is_baseline=True,
        assessment_duration_minutes=34,
    )
    session.add(baseline)
    session.commit()
    session.refresh(baseline)
    return baseline


def seed_baseline_test_results(session: Session, patient: User, patient_seed: PatientSeed) -> list[TestResult]:
    patient_id = require_id(patient.id, "patient.id")
    created_at = utc_now() - timedelta(days=63, minutes=20)
    rows: list[TestResult] = []
    for offset, payload in enumerate(baseline_test_result_payloads(patient_seed)):
        row = TestResult(
            user_id=patient_id,
            task_type=str(payload["task_type"]),
            score=float(payload["score"]),
            details=json.dumps(payload["details"]),
            created_at=created_at + timedelta(minutes=offset * 7),
        )
        session.add(row)
        rows.append(row)
    session.commit()
    return rows


def seed_training_plan(session: Session, patient: User, baseline: BaselineAssessment, patient_seed: PatientSeed) -> TrainingPlan:
    patient_id = require_id(patient.id, "patient.id")
    baseline_id = require_id(baseline.id, "baseline.id")
    primary, secondary, maintenance = derive_focus_areas(patient_seed.baseline_scores)
    initial_difficulty = build_initial_difficulty(patient_seed.baseline_scores)
    current_difficulty = build_current_difficulty(initial_difficulty, patient_seed.scenario)
    training_plan = TrainingPlan(
        user_id=patient_id,
        baseline_assessment_id=baseline_id,
        primary_focus=json.dumps(primary),
        secondary_focus=json.dumps(secondary),
        maintenance=json.dumps(maintenance),
        recommended_tasks=json.dumps(RECOMMENDED_TASKS),
        initial_difficulty=json.dumps(initial_difficulty),
        current_difficulty=json.dumps(current_difficulty),
        created_at=utc_now() - timedelta(days=62),
        last_updated=utc_now() - timedelta(days=2),
        is_active=True,
        total_sessions_completed=len(TASK_SEQUENCE),
        last_session_date=utc_now() - timedelta(days=2),
        current_streak=4 if patient_seed.scenario == "improving" else 2,
        longest_streak=9 if patient_seed.scenario == "improving" else 5,
        total_training_days=7 if patient_seed.scenario == "improving" else 6,
        streak_freeze_available=True,
        current_session_number=9,
        current_session_tasks_completed=json.dumps([]),
    )
    session.add(training_plan)
    session.commit()
    session.refresh(training_plan)
    return training_plan


def seed_training_sessions(
    session: Session,
    patient: User,
    training_plan: TrainingPlan,
    patient_seed: PatientSeed,
) -> list[TrainingSession]:
    created_sessions: list[TrainingSession] = []
    patient_id = require_id(patient.id, "patient.id")
    training_plan_id = require_id(training_plan.id, "training_plan.id")
    start_date = utc_now() - timedelta(days=56)

    for session_index, task in enumerate(TASK_SEQUENCE):
        values = scenario_session_values(patient_seed, session_index)
        created_at = start_date + timedelta(days=session_index * 6, hours=(session_index % 3) * 2)
        trials = build_session_trials(values["mean_rt"], values["accuracy"], values["fatigue_bias"], session_index + patient_id)
        raw_data = {
            "task_code": task["task_code"],
            "task_type": task["task_type"],
            "score": values["score"],
            "accuracy": values["accuracy"],
            "mean_rt": values["mean_rt"],
            "trials": trials,
        }
        training_session = TrainingSession(
            user_id=patient_id,
            training_plan_id=training_plan_id,
            domain=task["domain"],
            task_type=task["task_type"],
            task_code=task["task_code"],
            score=values["score"],
            accuracy=values["accuracy"],
            average_reaction_time=values["mean_rt"],
            consistency=values["consistency"],
            errors=int(values["errors"]),
            difficulty_level=int(values["difficulty_after"]),
            difficulty_before=int(values["difficulty_before"]),
            difficulty_after=int(values["difficulty_after"]),
            duration=300 + (session_index * 18),
            completed=True,
            created_at=created_at,
            raw_data=json.dumps(raw_data),
            adaptation_reason="Synthetic demo progression based on patient-specific performance pattern.",
        )
        session.add(training_session)
        session.commit()
        session.refresh(training_session)

        context = SessionContext(
            user_id=patient_id,
            training_session_id=require_id(training_session.id, "training_session.id"),
            created_at=created_at - timedelta(minutes=5),
            **session_context_values(patient_seed, session_index),
        )
        session.add(context)
        session.commit()

        created_sessions.append(training_session)

    return created_sessions


def seed_prescription(session: Session, doctor: Doctor, patient: User) -> DoctorIntervention:
    doctor_id = require_id(doctor.id, "doctor.id")
    patient_id = require_id(patient.id, "patient.id")
    payload = {
        "title": "Cognitive support and fatigue management plan",
        "summary": "Short-term intervention plan to support processing speed and daily cognitive endurance.",
        "patient_instructions": "Take medication as directed and continue structured training five days per week.",
        "clinician_notes": "Synthetic demo prescription created for system walkthrough.",
        "status": "active",
        "valid_from": (utc_now() - timedelta(days=7)).isoformat(),
        "valid_until": (utc_now() + timedelta(days=23)).isoformat(),
        "review_date": (utc_now() + timedelta(days=14)).isoformat(),
        "follow_up_plan": "Review adherence, fatigue trend, and processing speed in two weeks.",
        "diagnosis": patient.diagnosis,
        "medications": [
            {
                "name": "Modafinil",
                "dosage": "100 mg",
                "frequency": "Once daily in the morning",
                "duration": "30 days",
                "instructions": "Take after breakfast unless otherwise advised by the treating physician.",
            }
        ],
        "lifestyle_plan": [
            "Maintain a fixed sleep schedule on training days.",
            "Prefer training within 2 to 3 hours after morning medication.",
            "Pause sessions on severe-fatigue days and notify the clinician if this repeats.",
        ],
        "version_number": 1,
    }
    intervention = DoctorIntervention(
        doctor_id=doctor_id,
        patient_id=patient_id,
        intervention_type="digital_prescription",
        description="Digital prescription for cognitive support.",
        intervention_data=json.dumps(payload),
        created_at=utc_now() - timedelta(days=6),
    )
    session.add(intervention)
    session.commit()
    session.refresh(intervention)

    data = json.loads(intervention.intervention_data or "{}")
    data["verification_id"] = build_prescription_verification_id(intervention.id)
    data["prescription_group_id"] = intervention.id
    intervention.intervention_data = json.dumps(data)
    session.add(intervention)
    session.commit()
    session.refresh(intervention)
    return intervention


def seed_intervention_note(session: Session, doctor: Doctor, patient: User) -> DoctorIntervention:
    doctor_id = require_id(doctor.id, "doctor.id")
    patient_id = require_id(patient.id, "patient.id")
    note = DoctorIntervention(
        doctor_id=doctor_id,
        patient_id=patient_id,
        intervention_type="training_plan_adjustment",
        description="Recommended shorter evening sessions on high-fatigue days.",
        intervention_data=json.dumps(
            {
                "summary": "Reduce evening cognitive load when fatigue rises.",
                "recommendations": [
                    "Prefer morning sessions when possible.",
                    "Pause after noticeable reaction-time slowing.",
                ],
            }
        ),
        created_at=utc_now() - timedelta(days=4),
    )
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


def seed_messages(session: Session, doctor_a: Doctor, doctor_b: Doctor, patient_a: User, patient_b: User) -> None:
    doctor_a_id = require_id(doctor_a.id, "doctor_a.id")
    doctor_b_id = require_id(doctor_b.id, "doctor_b.id")
    patient_a_id = require_id(patient_a.id, "patient_a.id")
    patient_b_id = require_id(patient_b.id, "patient_b.id")
    messages = [
        Message(
            sender_id=doctor_a_id,
            sender_type="doctor",
            recipient_id=patient_a_id,
            recipient_type="patient",
            subject="Progress update",
            message="Your recent processing-speed sessions show steady improvement. Continue the current training schedule.",
            is_read=True,
            read_at=utc_now() - timedelta(days=3),
            created_at=utc_now() - timedelta(days=4),
            updated_at=utc_now() - timedelta(days=3),
        ),
        Message(
            sender_id=patient_a_id,
            sender_type="patient",
            recipient_id=doctor_a_id,
            recipient_type="doctor",
            subject="Re: Progress update",
            message="Thank you, doctor. Morning sessions have been easier to complete consistently this week.",
            is_read=True,
            read_at=utc_now() - timedelta(days=2),
            created_at=utc_now() - timedelta(days=3),
            updated_at=utc_now() - timedelta(days=2),
        ),
        Message(
            sender_id=doctor_b_id,
            sender_type="doctor",
            recipient_id=patient_b_id,
            recipient_type="patient",
            subject="Fatigue check-in",
            message="I noticed slower attention performance on recent evening sessions. Please prioritize shorter morning sessions when possible.",
            is_read=False,
            created_at=utc_now() - timedelta(days=2),
            updated_at=utc_now() - timedelta(days=2),
        ),
    ]
    for message in messages:
        session.add(message)
    session.commit()


def can_seed_doctor_patient_messages(session: Session, doctors: list[Doctor]) -> bool:
    user_ids = {item for item in session.exec(select(User.id)).all() if item is not None}
    doctor_ids = {doctor.id for doctor in doctors if doctor.id is not None}
    return doctor_ids.issubset(user_ids)


def seed_progress_report(
    session: Session,
    patient: User,
    doctor: Doctor,
    baseline: BaselineAssessment,
    sessions_for_patient: list[TrainingSession],
    commentary: str,
) -> ProgressReport:
    period_end = datetime.now(timezone.utc)
    period_start = period_end - timedelta(days=30)
    patient_id = require_id(patient.id, "patient.id")
    doctor_id = require_id(doctor.id, "doctor.id")
    sessions_in_period = [item for item in sessions_for_patient if item.created_at >= period_start]
    report = ProgressReport(
        patient_id=patient_id,
        doctor_id=doctor_id,
        period_type="monthly",
        period_start=period_start,
        period_end=period_end,
        report_data=json.dumps(build_report_data(sessions_in_period, baseline, period_start, period_end)),
        doctor_commentary=commentary,
        generated_at=period_end,
        updated_at=period_end,
    )
    session.add(report)
    session.commit()
    session.refresh(report)
    return report


def seed_risk_alert(session: Session, patient: User, doctor: Doctor) -> RiskAlert:
    patient_id = require_id(patient.id, "patient.id")
    doctor_id = require_id(doctor.id, "doctor.id")
    alert = RiskAlert(
        patient_id=patient_id,
        assigned_doctor_id=doctor_id,
        risk_score=74,
        risk_level="high",
        alert_summary="Attention consistency declined on recent high-fatigue sessions.",
        risk_reasons_json=json.dumps(
            [
                "High fatigue reported before multiple sessions",
                "Reaction-time variability increased over the last two weeks",
                "Evening sessions show lower readiness and slower processing speed",
            ]
        ),
        status="open",
        doctor_notified_at=utc_now() - timedelta(days=2),
        created_at=utc_now() - timedelta(days=2),
        updated_at=utc_now() - timedelta(days=2),
    )
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return alert


def print_summary(doctors: dict[str, Doctor], patients: dict[str, User], message_seeded: bool) -> None:
    print("\nSynthetic demo clinical dataset created successfully.")
    print("\nDoctor demo accounts")
    for doctor in doctors.values():
        print(f"- {doctor.full_name} | {doctor.email} | password: {DEMO_DOCTOR_PASSWORD}")

    print("\nPatient demo accounts")
    for patient in patients.values():
        print(f"- {patient.full_name} | {patient.email} | password: {DEMO_PATIENT_PASSWORD}")

    print("\nDataset includes")
    print("- 2 verified doctors")
    print("- 2 active patients with consent enabled")
    print("- 2 active assignments")
    print("- 2 baseline assessments")
    print("- 2 active training plans")
    print("- 16 linked training sessions with biomarker-ready raw_data and session context")
    print("- 2 monthly progress reports")
    print("- 1 digital prescription")
    print("- 1 additional intervention note")
    if message_seeded:
        print("- 3 believable secure messages")
    else:
        print("- secure messages intentionally skipped because the current Message schema cannot safely represent doctor IDs")
    print("- 1 open risk alert")


def main() -> None:
    random.seed(RANDOM_SEED)

    with Session(engine) as session:
        cleanup_existing_demo_data(session)

        doctors = seed_doctors(session)
        patients = seed_patients(session)

        doctor_a = doctors[DOCTORS[0].email]
        doctor_b = doctors[DOCTORS[1].email]
        patient_a = patients[PATIENTS[0].email]
        patient_b = patients[PATIENTS[1].email]

        seed_assignment(session, doctor_a, patient_a, PATIENTS[0])
        seed_assignment(session, doctor_b, patient_b, PATIENTS[1])

        seed_baseline_test_results(session, patient_a, PATIENTS[0])
        seed_baseline_test_results(session, patient_b, PATIENTS[1])

        baseline_a = seed_baseline(session, patient_a, PATIENTS[0])
        baseline_b = seed_baseline(session, patient_b, PATIENTS[1])

        plan_a = seed_training_plan(session, patient_a, baseline_a, PATIENTS[0])
        plan_b = seed_training_plan(session, patient_b, baseline_b, PATIENTS[1])

        sessions_a = seed_training_sessions(session, patient_a, plan_a, PATIENTS[0])
        sessions_b = seed_training_sessions(session, patient_b, plan_b, PATIENTS[1])

        seed_prescription(session, doctor_a, patient_a)
        seed_intervention_note(session, doctor_b, patient_b)

        seed_progress_report(
            session,
            patient_a,
            doctor_a,
            baseline_a,
            sessions_a,
            "Processing speed and working memory have improved steadily over the last month. Continue the current routine and review again in two weeks.",
        )
        seed_progress_report(
            session,
            patient_b,
            doctor_b,
            baseline_b,
            sessions_b,
            "Attention remains variable on higher-fatigue days. Shorter morning sessions and close fatigue monitoring are recommended.",
        )

        seed_risk_alert(session, patient_b, doctor_b)

        message_seeded = False
        if can_seed_doctor_patient_messages(session, [doctor_a, doctor_b]):
            seed_messages(session, doctor_a, doctor_b, patient_a, patient_b)
            message_seeded = True
        else:
            print("Skipping demo message seeding because the current Message model stores both doctor and patient IDs against the user table.")

        print_summary(doctors, patients, message_seeded)


if __name__ == "__main__":
    main()