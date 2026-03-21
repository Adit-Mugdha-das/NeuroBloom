from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	DATABASE_URL: str = "postgresql://postgres:2107118@localhost:5432/neurobloom_db"

settings = Settings()

engine = create_engine(settings.DATABASE_URL, echo=True)


def _ensure_training_plan_pacing_columns():
    """Backfill training_plans pacing columns for existing databases."""
    statements = [
        "ALTER TABLE IF EXISTS training_plans ADD COLUMN IF NOT EXISTS max_sessions_per_day INTEGER DEFAULT 3",
        "ALTER TABLE IF EXISTS training_plans ADD COLUMN IF NOT EXISTS recommended_sessions_per_week INTEGER DEFAULT 7",
        "ALTER TABLE IF EXISTS training_plans ADD COLUMN IF NOT EXISTS tasks_per_session INTEGER DEFAULT 4",
        "ALTER TABLE IF EXISTS training_plans ADD COLUMN IF NOT EXISTS recommended_session_length_min_minutes INTEGER DEFAULT 5",
        "ALTER TABLE IF EXISTS training_plans ADD COLUMN IF NOT EXISTS recommended_session_length_max_minutes INTEGER DEFAULT 10",
        "ALTER TABLE IF EXISTS training_plans ADD COLUMN IF NOT EXISTS cooldown_between_sessions_minutes INTEGER DEFAULT 30",
        """
        UPDATE training_plans
        SET
            max_sessions_per_day = COALESCE(max_sessions_per_day, 3),
            recommended_sessions_per_week = COALESCE(recommended_sessions_per_week, 7),
            tasks_per_session = COALESCE(tasks_per_session, 4),
            recommended_session_length_min_minutes = COALESCE(recommended_session_length_min_minutes, 5),
            recommended_session_length_max_minutes = COALESCE(recommended_session_length_max_minutes, 10),
            cooldown_between_sessions_minutes = COALESCE(cooldown_between_sessions_minutes, 30)
        """,
    ]

    with Session(engine) as session:
        for statement in statements:
            session.execute(text(statement))
        session.commit()


def _ensure_legacy_account_columns():
    """Backfill columns added after early local database versions."""
    statements = [
        'ALTER TABLE IF EXISTS "user" ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE',
        'UPDATE "user" SET is_active = COALESCE(is_active, TRUE)',
        "ALTER TABLE IF EXISTS doctors ADD COLUMN IF NOT EXISTS department_id INTEGER",
    ]

    with Session(engine) as session:
        for statement in statements:
            session.execute(text(statement))
        session.commit()

def init_db():
    # Import all models here so SQLModel knows about them
    from app.models.admin import Admin
    from app.models.assignment_request import AssignmentRequest
    from app.models.badge import UserBadge
    from app.models.user import User
    from app.models.test_result import TestResult
    from app.models.baseline_assessment import BaselineAssessment
    from app.models.training_plan import TrainingPlan
    from app.models.training_session import TrainingSession
    from app.models.cognitive_task import CognitiveTask, UserTaskPreference
    from app.models.department import Department
    from app.models.doctor import Doctor
    from app.models.doctor_intervention import DoctorIntervention
    from app.models.message import Message
    from app.models.risk_alert import RiskAlert
    from app.models.audit_log import AuditLog
    from app.models.notification import Notification
    from app.models.patient_assignment import PatientAssignment
    from app.models.progress_report import ProgressReport
    from app.models.session_context import SessionContext

    _ = (
        Admin,
        AssignmentRequest,
        AuditLog,
        BaselineAssessment,
        CognitiveTask,
        Department,
        Doctor,
        DoctorIntervention,
        Message,
        Notification,
        PatientAssignment,
        ProgressReport,
        RiskAlert,
        SessionContext,
        TestResult,
        TrainingPlan,
        TrainingSession,
        User,
        UserBadge,
        UserTaskPreference,
    )

    # Use checkfirst=True to avoid errors on existing tables
    SQLModel.metadata.create_all(engine, checkfirst=True)

    # Ensure legacy deployments receive required new columns.
    _ensure_legacy_account_columns()
    _ensure_training_plan_pacing_columns()
