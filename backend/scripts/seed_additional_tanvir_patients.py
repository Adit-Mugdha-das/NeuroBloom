from __future__ import annotations

import random
import sys
from pathlib import Path

from sqlmodel import Session, col, select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import engine
from app.core.security import hash_password
from app.models.baseline_assessment import BaselineAssessment
from app.models.doctor import Doctor
from app.models.patient_assignment import PatientAssignment
from app.models.progress_report import ProgressReport
from app.models.test_result import TestResult
from app.models.training_plan import TrainingPlan
from app.models.training_session import TrainingSession
from app.models.user import User
from scripts.seed_demo_clinical_data import (
    DEMO_PATIENT_PASSWORD,
    RANDOM_SEED,
    PatientSeed,
    seed_assignment,
    seed_baseline,
    seed_baseline_test_results,
    seed_progress_report,
    seed_training_plan,
    seed_training_sessions,
)


DOCTOR_EMAIL = "dr.tanvir.hossain@gmail.com"

ADDITIONAL_PATIENTS = [
    PatientSeed(
        full_name="Nabila Rahman",
        email="nabila.rahman+tanvir@gmail.com",
        date_of_birth="1993-08-11",
        diagnosis="Relapsing-Remitting Multiple Sclerosis with fatigue-sensitive processing speed and attention variability",
        treatment_goal="Improve processing speed consistency while tracking fatigue-linked slowing across repeated home sessions.",
        scenario="fatigue_variability",
        session_count=7,
        report_commentary="Fatigue-sensitive variability remains visible, especially in attention-heavy sessions. Dr. Tanvir should continue shorter blocks with closer monitoring of context-linked slowing.",
        baseline_scores={
            "working_memory": 56.0,
            "attention": 47.0,
            "flexibility": 53.0,
            "planning": 58.0,
            "processing_speed": 45.0,
            "visual_scanning": 54.0,
        },
    ),
    PatientSeed(
        full_name="Omar Faruq",
        email="omar.faruq+tanvir@gmail.com",
        date_of_birth="1985-01-24",
        diagnosis="Secondary Progressive Multiple Sclerosis with reduced processing speed and gradual executive recovery during structured rehabilitation",
        treatment_goal="Support gradual recovery in processing speed and planning while maintaining steady adherence to clinician-guided training.",
        scenario="recovery",
        session_count=8,
        report_commentary="Recent sessions suggest early recovery with better consistency than baseline. Dr. Tanvir can continue progressive training while avoiding overload on fatigue-prone days.",
        baseline_scores={
            "working_memory": 52.0,
            "attention": 50.0,
            "flexibility": 55.0,
            "planning": 57.0,
            "processing_speed": 41.0,
            "visual_scanning": 49.0,
        },
    ),
]


def get_or_create_patient(session: Session, seed: PatientSeed) -> tuple[User, bool]:
    patient = session.exec(select(User).where(User.email == seed.email)).first()
    if patient:
        patient.full_name = seed.full_name
        patient.date_of_birth = seed.date_of_birth
        patient.diagnosis = seed.diagnosis
        patient.consent_to_share = True
        patient.is_active = True
        session.add(patient)
        session.commit()
        session.refresh(patient)
        return patient, False

    patient = User(
        email=seed.email,
        password_hash=hash_password(DEMO_PATIENT_PASSWORD),
        full_name=seed.full_name,
        date_of_birth=seed.date_of_birth,
        diagnosis=seed.diagnosis,
        consent_to_share=True,
        is_active=True,
    )
    session.add(patient)
    session.commit()
    session.refresh(patient)
    return patient, True


def ensure_assignment(session: Session, doctor: Doctor, patient: User, seed: PatientSeed) -> bool:
    existing = session.exec(
        select(PatientAssignment)
        .where(PatientAssignment.doctor_id == doctor.id)
        .where(PatientAssignment.patient_id == patient.id)
        .where(PatientAssignment.is_active == True)
    ).first()
    if existing:
        return False

    seed_assignment(session, doctor, patient, seed)
    return True


def ensure_baseline(session: Session, patient: User, seed: PatientSeed) -> BaselineAssessment:
    existing = session.exec(
        select(BaselineAssessment)
        .where(BaselineAssessment.user_id == patient.id)
        .order_by(col(BaselineAssessment.assessment_date).desc())
    ).first()
    if existing:
        return existing

    seed_baseline_test_results(session, patient, seed)
    return seed_baseline(session, patient, seed)


def ensure_training_plan(session: Session, patient: User, baseline: BaselineAssessment, seed: PatientSeed) -> TrainingPlan:
    existing = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == patient.id)
        .where(TrainingPlan.is_active == True)
        .order_by(col(TrainingPlan.created_at).desc())
    ).first()
    if existing:
        return existing

    return seed_training_plan(session, patient, baseline, seed)


def ensure_training_sessions(session: Session, patient: User, plan: TrainingPlan, seed: PatientSeed) -> list[TrainingSession]:
    existing = session.exec(
        select(TrainingSession)
        .where(TrainingSession.user_id == patient.id)
        .order_by(col(TrainingSession.created_at).asc())
    ).all()
    if existing:
        return list(existing)

    return seed_training_sessions(session, patient, plan, seed)


def ensure_progress_report(
    session: Session,
    patient: User,
    doctor: Doctor,
    baseline: BaselineAssessment,
    sessions_for_patient: list[TrainingSession],
    seed: PatientSeed,
) -> bool:
    existing = session.exec(
        select(ProgressReport)
        .where(ProgressReport.patient_id == patient.id)
        .where(ProgressReport.doctor_id == doctor.id)
    ).first()
    if existing:
        return False

    seed_progress_report(session, patient, doctor, baseline, sessions_for_patient, seed.report_commentary)
    return True


def main() -> None:
    with Session(engine) as session:
        doctor = session.exec(select(Doctor).where(Doctor.email == DOCTOR_EMAIL)).first()
        if not doctor:
            raise SystemExit(f"Doctor not found: {DOCTOR_EMAIL}")

        print(f"Seeding patients for Dr. {doctor.full_name} ({doctor.email})")
        print(f"Default patient password: {DEMO_PATIENT_PASSWORD}")

        for index, seed in enumerate(ADDITIONAL_PATIENTS):
            random.seed(RANDOM_SEED + 100 + index)
            patient, created = get_or_create_patient(session, seed)
            assignment_created = ensure_assignment(session, doctor, patient, seed)
            baseline = ensure_baseline(session, patient, seed)
            plan = ensure_training_plan(session, patient, baseline, seed)
            sessions_for_patient = ensure_training_sessions(session, patient, plan, seed)
            report_created = ensure_progress_report(session, patient, doctor, baseline, sessions_for_patient, seed)

            has_test_results = session.exec(select(TestResult).where(TestResult.user_id == patient.id)).first() is not None

            print("-")
            print(f"Patient: {patient.full_name} <{patient.email}>")
            print(f"  Created account: {'yes' if created else 'no'}")
            print(f"  Active assignment to Dr. Tanvir: {'created' if assignment_created else 'already existed'}")
            print(f"  Baseline present: yes")
            print(f"  Training plan present: yes")
            print(f"  Training sessions present: {len(sessions_for_patient)}")
            print(f"  Baseline test results present: {'yes' if has_test_results else 'no'}")
            print(f"  Progress report: {'created' if report_created else 'already existed'}")


if __name__ == "__main__":
    main()