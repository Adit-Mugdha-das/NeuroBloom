from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Annotated
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy import text
from sqlmodel import SQLModel, Session, create_engine


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _load_env_files() -> None:
    # Load the shared repo-level env first and keep backend/.env only as a fallback.
    for env_path in (REPO_ROOT / ".env.local", REPO_ROOT / ".env", BACKEND_ROOT / ".env"):
        if env_path.exists():
            load_dotenv(env_path, override=False)


def _default_cors_allowed_origins() -> list[str]:
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]


_load_env_files()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "neurobloom_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    DATABASE_URL: str | None = None
    CORS_ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=_default_cors_allowed_origins
    )
    API_BASE_URL: str = "http://localhost:8000"
    SQL_ECHO: bool = False
    DB_STARTUP_MAX_ATTEMPTS: int = 20
    DB_STARTUP_RETRY_SECONDS: float = 2.0

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_allowed_origins(cls, value: object) -> object:
        if value is None or value == "":
            return _default_cors_allowed_origins()

        if isinstance(value, str):
            raw_value = value.strip()
            if not raw_value:
                return []

            if raw_value.startswith("["):
                parsed_value = json.loads(raw_value)
                if not isinstance(parsed_value, list):
                    raise ValueError("CORS_ALLOWED_ORIGINS must be a list or comma-separated string")
                return [str(item).strip().rstrip("/") for item in parsed_value if str(item).strip()]

            return [item.strip().rstrip("/") for item in raw_value.split(",") if item.strip()]

        if isinstance(value, list):
            return [str(item).strip().rstrip("/") for item in value if str(item).strip()]

        return value

    @field_validator("API_BASE_URL", mode="before")
    @classmethod
    def normalize_api_base_url(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().rstrip("/")
        return value

    @model_validator(mode="after")
    def build_database_url(self) -> "Settings":
        if not self.DATABASE_URL:
            user = quote_plus(self.POSTGRES_USER)
            password = quote_plus(self.POSTGRES_PASSWORD)
            database = quote_plus(self.POSTGRES_DB)
            self.DATABASE_URL = (
                f"postgresql://{user}:{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{database}"
            )

        return self


settings = Settings()

engine = create_engine(settings.DATABASE_URL, echo=settings.SQL_ECHO, pool_pre_ping=True)


def build_api_url(path: str = "") -> str:
    if not path:
        return settings.API_BASE_URL

    normalized_path = path if path.startswith("/") else f"/{path}"
    return f"{settings.API_BASE_URL}{normalized_path}"


def wait_for_database() -> None:
    last_error: Exception | None = None

    for attempt in range(1, settings.DB_STARTUP_MAX_ATTEMPTS + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return
        except Exception as exc:  # pragma: no cover - exercised in container startup
            last_error = exc
            if attempt == settings.DB_STARTUP_MAX_ATTEMPTS:
                break

            print(
                "Database not ready yet "
                f"(attempt {attempt}/{settings.DB_STARTUP_MAX_ATTEMPTS}): {exc}"
            )
            time.sleep(settings.DB_STARTUP_RETRY_SECONDS)

    raise RuntimeError("Database did not become ready before startup timeout") from last_error


def _ensure_training_plan_pacing_columns() -> None:
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


def _ensure_legacy_account_columns() -> None:
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


def _ensure_reference_data() -> None:
    """Populate required reference tables for a fresh environment."""
    from seed_cognitive_tasks import seed_cognitive_tasks

    seed_cognitive_tasks(verbose=False)


def init_db() -> None:
    # Import all models here so SQLModel knows about them.
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

    SQLModel.metadata.create_all(engine, checkfirst=True)
    _ensure_legacy_account_columns()
    _ensure_training_plan_pacing_columns()
    _ensure_reference_data()
