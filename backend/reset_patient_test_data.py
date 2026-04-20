from __future__ import annotations

import argparse

from sqlmodel import Session, delete, select

from app.core.config import engine
from app.models.badge import UserBadge
from app.models.baseline_assessment import BaselineAssessment
from app.models.cognitive_task import UserTaskPreference
from app.models.doctor_intervention import DoctorIntervention
from app.models.message import Message
from app.models.patient_assignment import PatientAssignment
from app.models.session_context import SessionContext
from app.models.test_result import TestResult
from app.models.training_plan import TrainingPlan
from app.models.training_session import TrainingSession
from app.models.user import User


def reset_patient_test_data(apply_changes: bool = False) -> dict[str, int]:
    with Session(engine) as session:
        patient_ids = session.exec(select(User.id)).all()
        patient_ids = [int(patient_id) for patient_id in patient_ids]

        counts = {
            "users": len(patient_ids),
            "test_results": 0,
            "baseline_assessments": 0,
            "training_plans": 0,
            "training_sessions": 0,
            "session_contexts": 0,
            "user_badges": 0,
            "user_task_preferences": 0,
            "patient_assignments": 0,
            "doctor_interventions": 0,
            "messages": 0,
        }

        if not patient_ids:
            return counts

        counts["test_results"] = len(
            session.exec(select(TestResult.id).where(TestResult.user_id.in_(patient_ids))).all()
        )
        counts["baseline_assessments"] = len(
            session.exec(
                select(BaselineAssessment.id).where(BaselineAssessment.user_id.in_(patient_ids))
            ).all()
        )
        counts["training_plans"] = len(
            session.exec(select(TrainingPlan.id).where(TrainingPlan.user_id.in_(patient_ids))).all()
        )
        counts["training_sessions"] = len(
            session.exec(
                select(TrainingSession.id).where(TrainingSession.user_id.in_(patient_ids))
            ).all()
        )
        counts["session_contexts"] = len(
            session.exec(select(SessionContext.id).where(SessionContext.user_id.in_(patient_ids))).all()
        )
        counts["user_badges"] = len(
            session.exec(select(UserBadge.id).where(UserBadge.user_id.in_(patient_ids))).all()
        )
        counts["user_task_preferences"] = len(
            session.exec(
                select(UserTaskPreference.user_id).where(UserTaskPreference.user_id.in_(patient_ids))
            ).all()
        )
        counts["patient_assignments"] = len(
            session.exec(
                select(PatientAssignment.id).where(PatientAssignment.patient_id.in_(patient_ids))
            ).all()
        )
        counts["doctor_interventions"] = len(
            session.exec(
                select(DoctorIntervention.id).where(DoctorIntervention.patient_id.in_(patient_ids))
            ).all()
        )
        counts["messages"] = len(
            session.exec(
                select(Message.id).where(
                    (Message.sender_type == "patient") | (Message.recipient_type == "patient")
                )
            ).all()
        )

        if not apply_changes:
            return counts

        session.exec(delete(SessionContext).where(SessionContext.user_id.in_(patient_ids)))
        session.exec(delete(TrainingSession).where(TrainingSession.user_id.in_(patient_ids)))
        session.exec(delete(UserBadge).where(UserBadge.user_id.in_(patient_ids)))
        session.exec(delete(UserTaskPreference).where(UserTaskPreference.user_id.in_(patient_ids)))
        session.exec(delete(TrainingPlan).where(TrainingPlan.user_id.in_(patient_ids)))
        session.exec(delete(BaselineAssessment).where(BaselineAssessment.user_id.in_(patient_ids)))
        session.exec(delete(TestResult).where(TestResult.user_id.in_(patient_ids)))
        session.exec(delete(PatientAssignment).where(PatientAssignment.patient_id.in_(patient_ids)))
        session.exec(delete(DoctorIntervention).where(DoctorIntervention.patient_id.in_(patient_ids)))
        session.exec(
            delete(Message).where(
                (Message.sender_type == "patient") | (Message.recipient_type == "patient")
            )
        )
        session.exec(delete(User).where(User.id.in_(patient_ids)))
        session.commit()

        return counts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clear disposable patient-facing test data while preserving reference/system tables."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete the patient-facing records. Without this flag, the script only reports counts.",
    )
    args = parser.parse_args()

    counts = reset_patient_test_data(apply_changes=args.apply)
    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"[{mode}] patient test-data reset summary")
    for key, value in counts.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
