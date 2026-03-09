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


DEMO_DOCTOR_PASSWORD = "doctor1234"
DEMO_PATIENT_PASSWORD = "patient1234"
RANDOM_SEED = 42

LEGACY_DEMO_DOCTOR_EMAILS = [
    "dr.samira.rahman@demo.neurobloom.bd",
    "dr.arefin.kabir@demo.neurobloom.bd",
]

LEGACY_DEMO_PATIENT_EMAILS = [
    "sharmin.akter@demo.neurobloom.bd",
    "rashedul.islam@demo.neurobloom.bd",
]


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
    session_count: int
    report_commentary: str
    baseline_scores: dict[str, float]


DOCTORS = [
    DoctorSeed(
        full_name="Dr. Samira Rahman",
        email="dr.samira.rahman@gmail.com",
        license_number="BD-NEU-24031",
        specialization="Neurology",
        institution="National Institute of Neurosciences & Hospital, Dhaka",
    ),
    DoctorSeed(
        full_name="Dr. Arefin Kabir",
        email="dr.arefin.kabir@gmail.com",
        license_number="BD-NPSY-18742",
        specialization="Neuropsychology",
        institution="Bangabandhu Sheikh Mujib Medical University, Shahbagh, Dhaka",
    ),
    DoctorSeed(
        full_name="Dr. Nusrat Jahan",
        email="dr.nusrat.jahan@gmail.com",
        license_number="BD-PMR-25108",
        specialization="Physical Medicine and Rehabilitation",
        institution="Centre for the Rehabilitation of the Paralysed, Savar",
    ),
    DoctorSeed(
        full_name="Dr. Tanvir Hossain",
        email="dr.tanvir.hossain@gmail.com",
        license_number="BD-CN-22917",
        specialization="Cognitive Neurology",
        institution="Dhaka Medical College Hospital, Dhaka",
    ),
    DoctorSeed(
        full_name="Dr. Lamiya Sultana",
        email="dr.lamiya.sultana@gmail.com",
        license_number="BD-MS-26411",
        specialization="MS Clinical Care",
        institution="Square Hospital Neurology Centre, Dhaka",
    ),
    DoctorSeed(
        full_name="Dr. Sabbir Ahmed",
        email="dr.sabbir.ahmed@gmail.com",
        license_number="BD-RM-23384",
        specialization="Rehabilitation Medicine",
        institution="Evercare Hospital Dhaka, Neurology and Rehabilitation Unit",
    ),
    DoctorSeed(
        full_name="Dr. Mehzabin Karim",
        email="dr.mehzabin.karim@gmail.com",
        license_number="BD-NR-27116",
        specialization="Neurorehabilitation",
        institution="Apollo Imperial Neurorehabilitation Clinic, Dhaka",
    ),
    DoctorSeed(
        full_name="Dr. Rafid Mahmud",
        email="dr.rafid.mahmud@gmail.com",
        license_number="BD-BN-24607",
        specialization="Behavioral Neurology",
        institution="Chattogram Medical College Hospital, Neurology Unit",
    ),
]


PATIENTS = [
    PatientSeed(
        full_name="Sharmin Akter",
        email="sharmin.akter@gmail.com",
        date_of_birth="1991-04-17",
        diagnosis="Relapsing-Remitting Multiple Sclerosis",
        treatment_goal="Improve processing speed and sustain gains in working memory during daily cognitive training.",
        scenario="improving",
        session_count=8,
        report_commentary="Processing speed and working memory have improved steadily over the last month. Continue the current routine and review again in two weeks.",
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
        email="rashedul.islam@gmail.com",
        date_of_birth="1987-09-28",
        diagnosis="Relapsing-Remitting Multiple Sclerosis with fatigue-linked cognitive variability",
        treatment_goal="Reduce attention variability and improve consistency on high-fatigue days.",
        scenario="fatigue_variability",
        session_count=8,
        report_commentary="Attention remains variable on higher-fatigue days. Shorter morning sessions and close fatigue monitoring are recommended.",
        baseline_scores={
            "working_memory": 53.0,
            "attention": 44.0,
            "flexibility": 50.0,
            "planning": 55.0,
            "processing_speed": 42.0,
            "visual_scanning": 52.0,
        },
    ),
    PatientSeed(
        full_name="Farhana Yasmin",
        email="farhana.yasmin@gmail.com",
        date_of_birth="1984-02-05",
        diagnosis="Secondary Progressive Multiple Sclerosis with preserved executive planning but inconsistent home adherence",
        treatment_goal="Support adherence consistency while maintaining higher-order planning and flexibility skills.",
        scenario="inconsistent_adherence",
        session_count=6,
        report_commentary="Baseline cognitive capacity is comparatively strong, but attendance gaps are reducing the benefit of training. The focus should remain on routine adherence and shorter, more frequent sessions.",
        baseline_scores={
            "working_memory": 67.0,
            "attention": 62.0,
            "flexibility": 69.0,
            "planning": 74.0,
            "processing_speed": 58.0,
            "visual_scanning": 66.0,
        },
    ),
    PatientSeed(
        full_name="Imran H. Chowdhury",
        email="imran.chowdhury@gmail.com",
        date_of_birth="1979-11-13",
        diagnosis="Primary Progressive Multiple Sclerosis with slowed processing speed and recent improvement in structured cognitive rehab",
        treatment_goal="Recover processing speed efficiency and improve confidence with sustained multi-domain training.",
        scenario="recovery",
        session_count=7,
        report_commentary="Processing speed remains the primary vulnerability, but the last several sessions show early recovery and better session-to-session stability. Continue progression carefully without overloading fatigue-prone days.",
        baseline_scores={
            "working_memory": 50.0,
            "attention": 54.0,
            "flexibility": 52.0,
            "planning": 57.0,
            "processing_speed": 39.0,
            "visual_scanning": 48.0,
        },
    ),
    PatientSeed(
        full_name="Tania Mahmuda",
        email="tania.mahmuda@gmail.com",
        date_of_birth="1995-06-22",
        diagnosis="Clinically Isolated Syndrome under cognitive monitoring with recent enrollment",
        treatment_goal="Establish a sustainable training routine and gather enough early data for a personalised cognitive trajectory.",
        scenario="newly_enrolled",
        session_count=3,
        report_commentary="The patient is still early in onboarding, so interpretation should remain cautious. Initial engagement is good, but more sessions are needed before making stronger clinical conclusions.",
        baseline_scores={
            "working_memory": 61.0,
            "attention": 59.0,
            "flexibility": 63.0,
            "planning": 65.0,
            "processing_speed": 57.0,
            "visual_scanning": 60.0,
        },
    ),
    PatientSeed(
        full_name="Naeem Hasan",
        email="naeem.hasan@gmail.com",
        date_of_birth="1982-08-09",
        diagnosis="Relapsing-Remitting Multiple Sclerosis with sleep-related attention and processing-speed plateau",
        treatment_goal="Improve consistency by reducing the effect of poor sleep on next-day attention and processing speed.",
        scenario="sleep_variability",
        session_count=5,
        report_commentary="Performance remains broadly stable, but the strongest dips are clustering after poor sleep nights. Sleep hygiene and timing adjustments should be prioritised before pushing difficulty further.",
        baseline_scores={
            "working_memory": 57.0,
            "attention": 51.0,
            "flexibility": 55.0,
            "planning": 59.0,
            "processing_speed": 47.0,
            "visual_scanning": 54.0,
        },
    ),
    PatientSeed(
        full_name="Sabina Khatun",
        email="sabina.khatun@gmail.com",
        date_of_birth="1976-03-14",
        diagnosis="Secondary Progressive Multiple Sclerosis with long-term training adherence and gradual executive recovery",
        treatment_goal="Maintain long-term adherence while improving planning efficiency and preserving gains across multiple domains.",
        scenario="long_term_engaged",
        session_count=12,
        report_commentary="This is a longer-term engaged patient with clear cumulative benefit. Planning and flexibility are improving gradually, and the current focus should be on maintenance with moderate progression rather than aggressive difficulty jumps.",
        baseline_scores={
            "working_memory": 46.0,
            "attention": 49.0,
            "flexibility": 43.0,
            "planning": 41.0,
            "processing_speed": 45.0,
            "visual_scanning": 52.0,
        },
    ),
    PatientSeed(
        full_name="Mahmudul Bari",
        email="mahmudul.bari@gmail.com",
        date_of_birth="1989-12-02",
        diagnosis="Relapsing-Remitting Multiple Sclerosis with early gains followed by a recent processing-speed and fatigue plateau",
        treatment_goal="Break the current plateau by stabilising fatigue, reducing reaction-time variability, and restoring steady improvement in processing speed.",
        scenario="plateau_after_improvement",
        session_count=11,
        report_commentary="The patient completed a substantial training block and improved early, but the last several sessions suggest a plateau with rising variability. Recovery may require pacing adjustments and closer monitoring of fatigue-linked slowing.",
        baseline_scores={
            "working_memory": 55.0,
            "attention": 52.0,
            "flexibility": 57.0,
            "planning": 54.0,
            "processing_speed": 44.0,
            "visual_scanning": 56.0,
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


def ensure_utc(datetime_value: datetime) -> datetime:
    if datetime_value.tzinfo is None:
        return datetime_value.replace(tzinfo=timezone.utc)
    return datetime_value.astimezone(timezone.utc)


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
    if patient_seed.scenario == "improving":
        working_memory_span = 5
        commission_errors = 2
        switch_cost = 740
        optimal_moves_ratio = 0.72
        average_reaction_time = 910
        targets_found = 22
    elif patient_seed.scenario == "fatigue_variability":
        working_memory_span = 4
        commission_errors = 4
        switch_cost = 910
        optimal_moves_ratio = 0.61
        average_reaction_time = 1120
        targets_found = 18
    elif patient_seed.scenario == "inconsistent_adherence":
        working_memory_span = 6
        commission_errors = 3
        switch_cost = 690
        optimal_moves_ratio = 0.78
        average_reaction_time = 860
        targets_found = 24
    elif patient_seed.scenario == "newly_enrolled":
        working_memory_span = 5
        commission_errors = 2
        switch_cost = 760
        optimal_moves_ratio = 0.71
        average_reaction_time = 930
        targets_found = 21
    elif patient_seed.scenario == "sleep_variability":
        working_memory_span = 4
        commission_errors = 3
        switch_cost = 840
        optimal_moves_ratio = 0.67
        average_reaction_time = 1015
        targets_found = 19
    elif patient_seed.scenario == "long_term_engaged":
        working_memory_span = 5
        commission_errors = 2
        switch_cost = 720
        optimal_moves_ratio = 0.74
        average_reaction_time = 930
        targets_found = 23
    elif patient_seed.scenario == "plateau_after_improvement":
        working_memory_span = 5
        commission_errors = 3
        switch_cost = 790
        optimal_moves_ratio = 0.69
        average_reaction_time = 980
        targets_found = 20
    else:
        working_memory_span = 4
        commission_errors = 3
        switch_cost = 845
        optimal_moves_ratio = 0.66
        average_reaction_time = 1010
        targets_found = 20

    return [
        {
            "task_type": "working_memory",
            "score": scores["working_memory"],
            "details": {
                "score": scores["working_memory"],
                "accuracy": round(min(100.0, scores["working_memory"] + 18.0), 2),
                "max_span": working_memory_span,
            },
        },
        {
            "task_type": "attention",
            "score": scores["attention"],
            "details": {
                "score": scores["attention"],
                "accuracy": round(min(100.0, scores["attention"] + 16.0), 2),
                "commission_errors": commission_errors,
            },
        },
        {
            "task_type": "flexibility",
            "score": scores["flexibility"],
            "details": {
                "score": scores["flexibility"],
                "switch_cost": switch_cost,
            },
        },
        {
            "task_type": "planning",
            "score": scores["planning"],
            "details": {
                "score": scores["planning"],
                "optimal_moves_ratio": optimal_moves_ratio,
            },
        },
        {
            "task_type": "processing_speed",
            "score": scores["processing_speed"],
            "details": {
                "score": scores["processing_speed"],
                "average_reaction_time": average_reaction_time,
            },
        },
        {
            "task_type": "visual_scanning",
            "score": scores["visual_scanning"],
            "details": {
                "score": scores["visual_scanning"],
                "targets_found": targets_found,
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


def build_biomarker_snapshot(trials: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, float]:
    reaction_times = [float(trial["reaction_time"]) for trial in trials if trial.get("reaction_time")]
    correct_count = sum(1 for trial in trials if trial.get("correct"))
    accuracy_ratio = correct_count / len(trials) if trials else 0.0
    mean_rt = sum(reaction_times) / len(reaction_times) if reaction_times else 0.0
    if reaction_times and mean_rt > 0:
        variance = sum((value - mean_rt) ** 2 for value in reaction_times) / len(reaction_times)
        rt_cv = (variance ** 0.5) / mean_rt
    else:
        rt_cv = 0.0
    first_half = reaction_times[: len(reaction_times) // 2] or reaction_times
    second_half = reaction_times[len(reaction_times) // 2 :] or reaction_times
    first_avg = sum(first_half) / len(first_half) if first_half else 0.0
    second_avg = sum(second_half) / len(second_half) if second_half else 0.0
    fatigue_slope = second_avg - first_avg
    fatigue_level = float(context.get("fatigue_level") or 0)
    sleep_quality = float(context.get("sleep_quality") or 0)
    readiness_level = float(context.get("readiness_level") or 0)
    fatigue_index = min(1.0, max(0.0, (fatigue_level / 10.0) * 0.45 + min(1.0, rt_cv * 2.4) * 0.35 + max(0.0, fatigue_slope / 180.0) * 0.2))
    cognitive_efficiency = max(0.0, min(1.0, accuracy_ratio * 0.6 + max(0.0, 1 - (mean_rt / 1800.0)) * 0.25 + (readiness_level / 10.0) * 0.15))
    sleep_disruption_index = min(1.0, max(0.0, (1 - (sleep_quality / 10.0)) * 0.7 + max(0.0, (7.0 - float(context.get("sleep_hours") or 0.0)) / 7.0) * 0.3))

    return {
        "fatigue_index": round(fatigue_index, 3),
        "reaction_time_cv": round(rt_cv, 3),
        "fatigue_slope": round(fatigue_slope, 2),
        "cognitive_efficiency": round(cognitive_efficiency, 3),
        "sleep_disruption_index": round(sleep_disruption_index, 3),
    }


def scenario_session_values(patient: PatientSeed, session_index: int) -> dict[str, float]:
    if patient.scenario == "improving":
        score = 58 + (session_index * 3.4) + random.uniform(-2.0, 2.0)
        accuracy = 72 + (session_index * 2.1) + random.uniform(-2.5, 2.5)
        mean_rt = 1180 - (session_index * 38) + random.uniform(-35, 35)
        consistency = 66 + (session_index * 2.6) + random.uniform(-2.0, 2.0)
        fatigue_bias = 85 - (session_index * 4)
        difficulty_before = min(7, 3 + (session_index // 2))
    elif patient.scenario == "fatigue_variability":
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
    elif patient.scenario == "inconsistent_adherence":
        score = 66 + (session_index * 0.8) + random.uniform(-4.5, 3.5)
        if session_index in {1, 4}:
            score -= 5
        accuracy = 80 + random.uniform(-5.0, 4.0)
        if session_index in {1, 4}:
            accuracy -= 7
        mean_rt = 960 - (session_index * 10) + random.uniform(-65, 55)
        if session_index in {1, 4}:
            mean_rt += 90
        consistency = 71 + random.uniform(-6.0, 4.0)
        fatigue_bias = 72 + (10 if session_index in {1, 4} else 0)
        difficulty_before = min(7, 4 + (session_index // 2))
    elif patient.scenario == "newly_enrolled":
        score = 60 + (session_index * 1.6) + random.uniform(-2.5, 2.0)
        accuracy = 74 + (session_index * 1.5) + random.uniform(-2.0, 2.0)
        mean_rt = 1010 - (session_index * 22) + random.uniform(-40, 35)
        consistency = 68 + (session_index * 1.2) + random.uniform(-2.0, 2.0)
        fatigue_bias = 88 - (session_index * 4)
        difficulty_before = min(5, 3 + session_index)
    elif patient.scenario == "sleep_variability":
        score = 55 + (session_index * 0.7) + random.uniform(-4.0, 3.0)
        if session_index in {1, 3}:
            score -= 5
        accuracy = 73 + random.uniform(-4.0, 3.5)
        if session_index in {1, 3}:
            accuracy -= 6
        mean_rt = 1110 - (session_index * 12) + random.uniform(-70, 55)
        if session_index in {1, 3}:
            mean_rt += 95
        consistency = 64 + random.uniform(-5.0, 3.0)
        fatigue_bias = 108 + (18 if session_index in {1, 3} else 0)
        difficulty_before = min(6, 3 + (session_index // 2))
    elif patient.scenario == "long_term_engaged":
        score = 51 + (session_index * 1.9) + random.uniform(-2.5, 2.5)
        accuracy = 72 + (session_index * 1.1) + random.uniform(-2.5, 2.0)
        mean_rt = 1160 - (session_index * 24) + random.uniform(-45, 45)
        consistency = 63 + (session_index * 1.5) + random.uniform(-2.5, 2.5)
        fatigue_bias = 92 - (session_index * 2)
        difficulty_before = min(8, 3 + (session_index // 2))
    elif patient.scenario == "plateau_after_improvement":
        score = 59 + min(session_index, 5) * 1.8 + random.uniform(-3.5, 3.0)
        if session_index >= 7:
            score -= 3.5
        accuracy = 76 + random.uniform(-3.5, 2.5)
        if session_index >= 7:
            accuracy -= 4
        mean_rt = 1035 - min(session_index, 5) * 18 + random.uniform(-55, 55)
        if session_index >= 7:
            mean_rt += 85
        consistency = 68 + random.uniform(-4.0, 3.0)
        if session_index >= 7:
            consistency -= 4
        fatigue_bias = 98 + (10 if session_index >= 7 else 0)
        difficulty_before = min(7, 4 + (session_index // 2))
    else:
        score = 46 + (session_index * 3.1) + random.uniform(-3.0, 2.5)
        if session_index == 0:
            score -= 4
        accuracy = 63 + (session_index * 2.4) + random.uniform(-3.5, 2.5)
        mean_rt = 1350 - (session_index * 48) + random.uniform(-80, 60)
        consistency = 57 + (session_index * 2.0) + random.uniform(-3.0, 2.5)
        fatigue_bias = 132 - (session_index * 6)
        difficulty_before = min(6, 2 + (session_index // 2))

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

    if patient.scenario == "fatigue_variability":
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

    if patient.scenario == "inconsistent_adherence":
        return {
            "fatigue_level": 4 + (1 if session_index == 4 else 0),
            "sleep_quality": 6,
            "sleep_hours": 6.5 + (0.5 if session_index == 3 else 0.0),
            "medication_taken_today": True,
            "hours_since_medication": 3.5 + (session_index % 2) * 0.5,
            "pain_level": 2,
            "stress_level": 4 + (1 if session_index in {1, 4} else 0),
            "time_of_day": "afternoon" if session_index in {1, 4} else base_time_of_day,
            "readiness_level": 6 + (1 if session_index not in {1, 4} else -1),
            "notes": "Missed the previous scheduled session because of work and family commitments." if session_index in {1, 4} else None,
            "distractions_present": session_index in {1, 4},
            "location": "office" if session_index == 1 else "home",
        }

    if patient.scenario == "newly_enrolled":
        return {
            "fatigue_level": 3 + (1 if session_index == 2 else 0),
            "sleep_quality": 7,
            "sleep_hours": 7.0,
            "medication_taken_today": True,
            "hours_since_medication": 2.5,
            "pain_level": 1,
            "stress_level": 4,
            "time_of_day": "morning",
            "readiness_level": 7,
            "notes": "Patient is still learning the training flow and asked for reassurance about task difficulty." if session_index == 0 else None,
            "distractions_present": False,
            "location": "home",
        }

    if patient.scenario == "sleep_variability":
        return {
            "fatigue_level": 5 + (2 if session_index in {1, 3} else 0),
            "sleep_quality": 4 if session_index in {1, 3} else 6,
            "sleep_hours": 5.0 if session_index in {1, 3} else 6.5,
            "medication_taken_today": True,
            "hours_since_medication": 3.0 + (session_index % 2) * 0.5,
            "pain_level": 3,
            "stress_level": 4 + (1 if session_index in {1, 3} else 0),
            "time_of_day": base_time_of_day,
            "readiness_level": 4 if session_index in {1, 3} else 6,
            "notes": "Patient reported poor sleep due to work-related stress and noticed slower concentration." if session_index in {1, 3} else None,
            "distractions_present": session_index == 3,
            "location": "home",
        }

    if patient.scenario == "long_term_engaged":
        return {
            "fatigue_level": 4 + (1 if session_index in {5, 9} else 0),
            "sleep_quality": 7,
            "sleep_hours": 7.0 + (0.5 if session_index % 4 == 0 else 0.0),
            "medication_taken_today": True,
            "hours_since_medication": 2.5 + (session_index % 3) * 0.5,
            "pain_level": 2,
            "stress_level": 3 + (1 if session_index in {6, 10} else 0),
            "time_of_day": "morning" if session_index % 3 != 1 else "afternoon",
            "readiness_level": 7 + (1 if session_index >= 8 else 0),
            "notes": "Patient continues to keep a structured rehabilitation routine and reports improved confidence in planning tasks." if session_index in {7, 11} else None,
            "distractions_present": False,
            "location": "home",
        }

    if patient.scenario == "plateau_after_improvement":
        return {
            "fatigue_level": 5 + (1 if session_index >= 7 else 0),
            "sleep_quality": 6 - (1 if session_index in {8, 10} else 0),
            "sleep_hours": 6.5 - (0.5 if session_index in {8, 10} else 0.0),
            "medication_taken_today": True,
            "hours_since_medication": 3.0 + (session_index % 2) * 0.5,
            "pain_level": 3,
            "stress_level": 4 + (1 if session_index >= 7 else 0),
            "time_of_day": base_time_of_day,
            "readiness_level": 6 - (1 if session_index >= 7 else 0),
            "notes": "Patient feels progress has slowed recently and reports frustration with repeated slower sessions." if session_index in {8, 10} else None,
            "distractions_present": session_index == 9,
            "location": "home",
        }

    return {
        "fatigue_level": 7 + (1 if session_index in {2, 5} else 0),
        "sleep_quality": 6 + (1 if session_index >= 4 else 0),
        "sleep_hours": 6.5 + (0.5 if session_index >= 4 else 0.0),
        "medication_taken_today": True,
        "hours_since_medication": 3.0 + (session_index % 2) * 0.5,
        "pain_level": 3 + (1 if session_index in {0, 1} else 0),
        "stress_level": 4,
        "time_of_day": base_time_of_day,
        "readiness_level": 5 + (1 if session_index >= 4 else 0),
        "notes": "Reported improved confidence after two weeks of structured morning sessions." if session_index >= 4 else None,
        "distractions_present": session_index == 0,
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
    if scenario == "improving":
        bonus = 1
    elif scenario == "recovery":
        bonus = 1
    elif scenario == "inconsistent_adherence":
        bonus = 0
    elif scenario == "newly_enrolled":
        bonus = 0
    elif scenario == "sleep_variability":
        bonus = 0
    elif scenario == "long_term_engaged":
        bonus = 1
    elif scenario == "plateau_after_improvement":
        bonus = 0
    else:
        bonus = 0
    return {domain: min(10, value + bonus) for domain, value in initial.items()}


def plan_progress_metrics(patient_seed: PatientSeed) -> dict[str, int]:
    if patient_seed.scenario == "improving":
        return {"current_streak": 4, "longest_streak": 9, "total_training_days": 7, "last_session_gap_days": 2}
    if patient_seed.scenario == "fatigue_variability":
        return {"current_streak": 2, "longest_streak": 5, "total_training_days": 6, "last_session_gap_days": 3}
    if patient_seed.scenario == "inconsistent_adherence":
        return {"current_streak": 1, "longest_streak": 4, "total_training_days": 5, "last_session_gap_days": 4}
    if patient_seed.scenario == "newly_enrolled":
        return {"current_streak": 2, "longest_streak": 2, "total_training_days": 3, "last_session_gap_days": 1}
    if patient_seed.scenario == "sleep_variability":
        return {"current_streak": 1, "longest_streak": 3, "total_training_days": 4, "last_session_gap_days": 3}
    if patient_seed.scenario == "long_term_engaged":
        return {"current_streak": 5, "longest_streak": 11, "total_training_days": 10, "last_session_gap_days": 1}
    if patient_seed.scenario == "plateau_after_improvement":
        return {"current_streak": 3, "longest_streak": 8, "total_training_days": 9, "last_session_gap_days": 2}
    return {"current_streak": 3, "longest_streak": 6, "total_training_days": 6, "last_session_gap_days": 2}


def session_spacing_days(patient_seed: PatientSeed) -> int:
    if patient_seed.scenario == "improving":
        return 4
    if patient_seed.scenario == "fatigue_variability":
        return 5
    if patient_seed.scenario == "inconsistent_adherence":
        return 7
    if patient_seed.scenario == "newly_enrolled":
        return 3
    if patient_seed.scenario == "sleep_variability":
        return 6
    if patient_seed.scenario == "long_term_engaged":
        return 3
    if patient_seed.scenario == "plateau_after_improvement":
        return 3
    return 5


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
    doctor_emails = [doctor.email for doctor in DOCTORS] + LEGACY_DEMO_DOCTOR_EMAILS
    patient_emails = [patient.email for patient in PATIENTS] + LEGACY_DEMO_PATIENT_EMAILS

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
        assessment_date=utc_now() - timedelta(days=63),
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
    progress_metrics = plan_progress_metrics(patient_seed)
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
        last_updated=utc_now() - timedelta(days=progress_metrics["last_session_gap_days"]),
        is_active=True,
        total_sessions_completed=patient_seed.session_count,
        last_session_date=utc_now() - timedelta(days=progress_metrics["last_session_gap_days"]),
        current_streak=progress_metrics["current_streak"],
        longest_streak=progress_metrics["longest_streak"],
        total_training_days=progress_metrics["total_training_days"],
        streak_freeze_available=True,
        current_session_number=patient_seed.session_count + 1,
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
    total_sessions = patient_seed.session_count
    gap_days = session_spacing_days(patient_seed)
    start_date = utc_now() - timedelta(days=((max(1, total_sessions) - 1) * gap_days + 2))

    for session_index in range(total_sessions):
        task = TASK_SEQUENCE[session_index % len(TASK_SEQUENCE)]
        values = scenario_session_values(patient_seed, session_index)
        created_at = start_date + timedelta(days=session_index * gap_days, hours=(session_index % 3) * 2)
        trials = build_session_trials(values["mean_rt"], values["accuracy"], values["fatigue_bias"], session_index + patient_id)
        context_values = session_context_values(patient_seed, session_index)
        biomarker_snapshot = build_biomarker_snapshot(trials, context_values)
        raw_data = {
            "task_code": task["task_code"],
            "task_type": task["task_type"],
            "score": values["score"],
            "accuracy": values["accuracy"],
            "mean_rt": values["mean_rt"],
            "biomarker_snapshot": biomarker_snapshot,
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
            **context_values,
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


def seed_intervention_note(session: Session, doctor: Doctor, patient: User, patient_seed: PatientSeed) -> DoctorIntervention:
    doctor_id = require_id(doctor.id, "doctor.id")
    patient_id = require_id(patient.id, "patient.id")
    if patient_seed.scenario == "fatigue_variability":
        description = "Recommended shorter morning sessions and fatigue journaling on variable days."
        data = {
            "summary": "Reduce evening cognitive load when fatigue rises.",
            "recommendations": [
                "Prefer morning sessions when possible.",
                "Pause after noticeable reaction-time slowing.",
                "Record fatigue level before each session for weekly review.",
            ],
        }
    elif patient_seed.scenario == "sleep_variability":
        description = "Recommended sleep-focused pacing and avoiding cognitively heavy sessions after poor rest."
        data = {
            "summary": "Stabilise performance by improving sleep-linked consistency before raising workload.",
            "recommendations": [
                "Avoid late-night sessions after less than 6 hours of sleep.",
                "Track sleep quality beside each session for two weeks.",
                "Prioritise shorter processing-speed sessions on low-rest days.",
            ],
        }
    elif patient_seed.scenario == "plateau_after_improvement":
        description = "Recommended plateau-focused pacing review and variability monitoring."
        data = {
            "summary": "Break the recent plateau by reducing overload and tightening recovery habits.",
            "recommendations": [
                "Keep session length consistent instead of adding extra catch-up sessions.",
                "Review fatigue and sleep notes alongside reaction-time variability each week.",
                "Delay further difficulty increases until speed and accuracy stabilise again.",
            ],
        }
    else:
        description = "Recommended adherence-focused scheduling and shorter structured sessions."
        data = {
            "summary": "Support routine adherence without overloading high-demand days.",
            "recommendations": [
                "Use fixed training slots three times per week.",
                "Complete shorter sessions after work rather than skipping entirely.",
                "Notify the doctor after two missed sessions in one week.",
            ],
        }

    note = DoctorIntervention(
        doctor_id=doctor_id,
        patient_id=patient_id,
        intervention_type="training_plan_adjustment",
        description=description,
        intervention_data=json.dumps(data),
        created_at=utc_now() - timedelta(days=4),
    )
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


def seed_messages(session: Session, seeded_records: list[tuple[Doctor, User, PatientSeed, BaselineAssessment, list[TrainingSession]]]) -> None:
    doctor_a, patient_a, _, _, _ = seeded_records[0]
    doctor_b, patient_b, _, _, _ = seeded_records[1]
    doctor_c, patient_c, _, _, _ = seeded_records[2]
    doctor_d, patient_d, _, _, _ = seeded_records[3]
    doctor_e, patient_e, _, _, _ = seeded_records[4]
    doctor_f, patient_f, _, _, _ = seeded_records[5]
    doctor_g, patient_g, _, _, _ = seeded_records[6]
    doctor_h, patient_h, _, _, _ = seeded_records[7]
    doctor_a_id = require_id(doctor_a.id, "doctor_a.id")
    doctor_b_id = require_id(doctor_b.id, "doctor_b.id")
    doctor_c_id = require_id(doctor_c.id, "doctor_c.id")
    doctor_d_id = require_id(doctor_d.id, "doctor_d.id")
    doctor_e_id = require_id(doctor_e.id, "doctor_e.id")
    doctor_f_id = require_id(doctor_f.id, "doctor_f.id")
    doctor_g_id = require_id(doctor_g.id, "doctor_g.id")
    doctor_h_id = require_id(doctor_h.id, "doctor_h.id")
    patient_a_id = require_id(patient_a.id, "patient_a.id")
    patient_b_id = require_id(patient_b.id, "patient_b.id")
    patient_c_id = require_id(patient_c.id, "patient_c.id")
    patient_d_id = require_id(patient_d.id, "patient_d.id")
    patient_e_id = require_id(patient_e.id, "patient_e.id")
    patient_f_id = require_id(patient_f.id, "patient_f.id")
    patient_g_id = require_id(patient_g.id, "patient_g.id")
    patient_h_id = require_id(patient_h.id, "patient_h.id")
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
        Message(
            sender_id=patient_c_id,
            sender_type="patient",
            recipient_id=doctor_c_id,
            recipient_type="doctor",
            subject="Scheduling around work hours",
            message="I missed two sessions this week because of my office schedule. Can we shift the plan to shorter evening sessions on weekdays?",
            is_read=True,
            read_at=utc_now() - timedelta(days=1),
            created_at=utc_now() - timedelta(days=2),
            updated_at=utc_now() - timedelta(days=1),
        ),
        Message(
            sender_id=doctor_c_id,
            sender_type="doctor",
            recipient_id=patient_c_id,
            recipient_type="patient",
            subject="Re: Scheduling around work hours",
            message="Yes. I have adjusted your guidance toward shorter, more regular sessions. The goal is consistency rather than long single sittings.",
            is_read=False,
            created_at=utc_now() - timedelta(hours=20),
            updated_at=utc_now() - timedelta(hours=20),
        ),
        Message(
            sender_id=doctor_d_id,
            sender_type="doctor",
            recipient_id=patient_d_id,
            recipient_type="patient",
            subject="Encouraging early recovery trend",
            message="Your last few sessions show faster responses and better stability. Keep the current pace and avoid doubling sessions on low-energy days.",
            is_read=False,
            created_at=utc_now() - timedelta(days=1),
            updated_at=utc_now() - timedelta(days=1),
        ),
        Message(
            sender_id=doctor_e_id,
            sender_type="doctor",
            recipient_id=patient_e_id,
            recipient_type="patient",
            subject="Welcome to NeuroBloom",
            message="You have completed a strong first week. At this stage the priority is consistency, not pushing performance. We will review your early pattern after a few more sessions.",
            is_read=True,
            read_at=utc_now() - timedelta(hours=12),
            created_at=utc_now() - timedelta(days=1),
            updated_at=utc_now() - timedelta(hours=12),
        ),
        Message(
            sender_id=patient_e_id,
            sender_type="patient",
            recipient_id=doctor_e_id,
            recipient_type="doctor",
            subject="Re: Welcome to NeuroBloom",
            message="Thank you. The sessions feel manageable so far, and I am getting more comfortable with the task instructions.",
            is_read=False,
            created_at=utc_now() - timedelta(hours=10),
            updated_at=utc_now() - timedelta(hours=10),
        ),
        Message(
            sender_id=patient_f_id,
            sender_type="patient",
            recipient_id=doctor_f_id,
            recipient_type="doctor",
            subject="Sleep affecting sessions",
            message="I noticed my slower days mostly happen after poor sleep. Should I skip the harder tasks on those mornings or continue with a shorter session?",
            is_read=True,
            read_at=utc_now() - timedelta(hours=6),
            created_at=utc_now() - timedelta(hours=16),
            updated_at=utc_now() - timedelta(hours=6),
        ),
        Message(
            sender_id=doctor_f_id,
            sender_type="doctor",
            recipient_id=patient_f_id,
            recipient_type="patient",
            subject="Re: Sleep affecting sessions",
            message="Continue, but keep the session shorter and avoid doubling up later in the day. I have added sleep tracking guidance so we can confirm the pattern more clearly.",
            is_read=False,
            created_at=utc_now() - timedelta(hours=4),
            updated_at=utc_now() - timedelta(hours=4),
        ),
        Message(
            sender_id=doctor_g_id,
            sender_type="doctor",
            recipient_id=patient_g_id,
            recipient_type="patient",
            subject="Maintaining your long-term gains",
            message="Your longer training history is showing gradual executive improvement. We will keep progression measured and focus on preserving consistency across planning and flexibility tasks.",
            is_read=True,
            read_at=utc_now() - timedelta(hours=18),
            created_at=utc_now() - timedelta(days=2),
            updated_at=utc_now() - timedelta(hours=18),
        ),
        Message(
            sender_id=patient_g_id,
            sender_type="patient",
            recipient_id=doctor_g_id,
            recipient_type="doctor",
            subject="Re: Maintaining your long-term gains",
            message="That sounds good. I feel more confident with the planning tasks now, though I still slow down when sessions run too long.",
            is_read=False,
            created_at=utc_now() - timedelta(hours=14),
            updated_at=utc_now() - timedelta(hours=14),
        ),
        Message(
            sender_id=patient_h_id,
            sender_type="patient",
            recipient_id=doctor_h_id,
            recipient_type="doctor",
            subject="Feeling stuck lately",
            message="I improved at first, but the last few sessions feel flat and more tiring. Should I reduce difficulty for a week or just keep going?",
            is_read=True,
            read_at=utc_now() - timedelta(hours=9),
            created_at=utc_now() - timedelta(hours=20),
            updated_at=utc_now() - timedelta(hours=9),
        ),
        Message(
            sender_id=doctor_h_id,
            sender_type="doctor",
            recipient_id=patient_h_id,
            recipient_type="patient",
            subject="Re: Feeling stuck lately",
            message="Do not push harder for now. I want one week of steadier pacing with attention to sleep and fatigue so we can see whether the plateau reflects overload rather than lost capacity.",
            is_read=False,
            created_at=utc_now() - timedelta(hours=6),
            updated_at=utc_now() - timedelta(hours=6),
        ),
    ]
    for message in messages:
        session.add(message)
    session.commit()


def can_seed_doctor_patient_messages(session: Session, doctors: list[Doctor]) -> bool:
    return all(doctor.id is not None for doctor in doctors)


def seed_progress_report(
    session: Session,
    patient: User,
    doctor: Doctor,
    baseline: BaselineAssessment,
    sessions_for_patient: list[TrainingSession],
    commentary: str,
) -> ProgressReport:
    period_end = utc_now()
    period_start = period_end - timedelta(days=30)
    patient_id = require_id(patient.id, "patient.id")
    doctor_id = require_id(doctor.id, "doctor.id")
    sessions_in_period = [item for item in sessions_for_patient if ensure_utc(item.created_at) >= period_start]
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


def seed_risk_alert(session: Session, patient: User, doctor: Doctor, patient_seed: PatientSeed) -> RiskAlert:
    patient_id = require_id(patient.id, "patient.id")
    doctor_id = require_id(doctor.id, "doctor.id")
    if patient_seed.scenario == "fatigue_variability":
        risk_score = 74
        risk_level = "high"
        alert_summary = "Attention consistency declined on recent high-fatigue sessions."
        reasons = [
            "High fatigue reported before multiple sessions",
            "Reaction-time variability increased over the last two weeks",
            "Evening sessions show lower readiness and slower processing speed",
        ]
    elif patient_seed.scenario == "sleep_variability":
        risk_score = 58
        risk_level = "moderate"
        alert_summary = "Sleep-related inconsistency is reducing attention and processing-speed reliability."
        reasons = [
            "Lowest scores cluster after shorter sleep nights",
            "Readiness drops on mornings following poor rest",
            "Processing speed gains have plateaued despite continued participation",
        ]
    elif patient_seed.scenario == "plateau_after_improvement":
        risk_score = 63
        risk_level = "moderate"
        alert_summary = "Recent performance plateau suggests reduced recovery despite continued engagement."
        reasons = [
            "Early gains were not sustained in the most recent sessions",
            "Reaction-time variability increased after difficulty progression",
            "Patient reports frustration and reduced confidence during slower sessions",
        ]
    else:
        risk_score = 61
        risk_level = "moderate"
        alert_summary = "Training adherence dropped after repeated missed home sessions."
        reasons = [
            "Several longer gaps between scheduled sessions",
            "Attention and speed performance dipped after adherence interruptions",
            "Patient reported work and family schedule conflicts affecting routine",
        ]

    alert = RiskAlert(
        patient_id=patient_id,
        assigned_doctor_id=doctor_id,
        risk_score=risk_score,
        risk_level=risk_level,
        alert_summary=alert_summary,
        risk_reasons_json=json.dumps(reasons),
        status="open",
        doctor_notified_at=utc_now() - timedelta(days=2),
        created_at=utc_now() - timedelta(days=2),
        updated_at=utc_now() - timedelta(days=2),
    )
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return alert


def print_summary(
    doctors: dict[str, Doctor],
    patients: dict[str, User],
    total_sessions: int,
    prescription_count: int,
    intervention_note_count: int,
    risk_alert_count: int,
    message_count: int,
    message_seeded: bool,
) -> None:
    print("\nSynthetic demo clinical dataset created successfully.")
    print("\nDoctor demo accounts")
    for doctor in doctors.values():
        print(f"- {doctor.full_name} | {doctor.email} | password: {DEMO_DOCTOR_PASSWORD}")

    print("\nPatient demo accounts")
    for patient in patients.values():
        print(f"- {patient.full_name} | {patient.email} | password: {DEMO_PATIENT_PASSWORD}")

    print("\nDataset includes")
    print(f"- {len(doctors)} verified doctors")
    print(f"- {len(patients)} active patients with consent enabled")
    print(f"- {len(patients)} active assignments")
    print(f"- {len(patients)} baseline assessments")
    print(f"- {len(patients)} active training plans")
    print(f"- {total_sessions} linked training sessions with biomarker-ready raw_data and session context")
    print(f"- {len(patients)} monthly progress reports")
    print(f"- {prescription_count} digital prescriptions")
    print(f"- {intervention_note_count} additional intervention notes")
    if message_seeded:
        print(f"- {message_count} believable secure messages")
    else:
        print("- secure messages intentionally skipped because the current Message schema cannot safely represent doctor IDs")
    print(f"- {risk_alert_count} open risk alerts")


def main() -> None:
    random.seed(RANDOM_SEED)

    with Session(engine) as session:
        cleanup_existing_demo_data(session)

        doctors = seed_doctors(session)
        patients = seed_patients(session)

        seeded_records: list[tuple[Doctor, User, PatientSeed, BaselineAssessment, list[TrainingSession]]] = []

        for doctor_seed, patient_seed in zip(DOCTORS, PATIENTS):
            doctor = doctors[doctor_seed.email]
            patient = patients[patient_seed.email]

            seed_assignment(session, doctor, patient, patient_seed)
            seed_baseline_test_results(session, patient, patient_seed)
            baseline = seed_baseline(session, patient, patient_seed)
            plan = seed_training_plan(session, patient, baseline, patient_seed)
            sessions_for_patient = seed_training_sessions(session, patient, plan, patient_seed)

            seed_progress_report(
                session,
                patient,
                doctor,
                baseline,
                sessions_for_patient,
                patient_seed.report_commentary,
            )

            seeded_records.append((doctor, patient, patient_seed, baseline, sessions_for_patient))

        prescription_records = [
            seed_prescription(session, seeded_records[0][0], seeded_records[0][1]),
            seed_prescription(session, seeded_records[2][0], seeded_records[2][1]),
            seed_prescription(session, seeded_records[4][0], seeded_records[4][1]),
            seed_prescription(session, seeded_records[6][0], seeded_records[6][1]),
        ]
        intervention_notes = [
            seed_intervention_note(session, seeded_records[1][0], seeded_records[1][1], seeded_records[1][2]),
            seed_intervention_note(session, seeded_records[3][0], seeded_records[3][1], seeded_records[3][2]),
            seed_intervention_note(session, seeded_records[5][0], seeded_records[5][1], seeded_records[5][2]),
            seed_intervention_note(session, seeded_records[7][0], seeded_records[7][1], seeded_records[7][2]),
        ]
        risk_alerts = [
            seed_risk_alert(session, seeded_records[1][1], seeded_records[1][0], seeded_records[1][2]),
            seed_risk_alert(session, seeded_records[3][1], seeded_records[3][0], seeded_records[3][2]),
            seed_risk_alert(session, seeded_records[5][1], seeded_records[5][0], seeded_records[5][2]),
            seed_risk_alert(session, seeded_records[7][1], seeded_records[7][0], seeded_records[7][2]),
        ]

        message_seeded = False
        message_count = 0
        if can_seed_doctor_patient_messages(session, [item[0] for item in seeded_records]):
            seed_messages(session, seeded_records)
            message_seeded = True
            message_count = 14
        else:
            print("Skipping demo message seeding because the current Message model stores both doctor and patient IDs against the user table.")

        print_summary(
            doctors,
            patients,
            total_sessions=sum(len(item[4]) for item in seeded_records),
            prescription_count=len(prescription_records),
            intervention_note_count=len(intervention_notes),
            risk_alert_count=len(risk_alerts),
            message_count=message_count,
            message_seeded=message_seeded,
        )


if __name__ == "__main__":
    main()