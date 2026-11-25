"""
Pytest fixtures: test database + FastAPI TestClient.

By default every test gets a fresh in-memory SQLite database. Set
TEST_DATABASE_URL (e.g. postgresql://postgres:postgres@localhost:5432/neurobloom_test)
to run the same suite against PostgreSQL; the tables are then created once and
emptied (with identity counters reset) before every test.

startup patching: wait_for_database and init_db are patched to no-ops so that
the FastAPI app can start without an actual Postgres connection during tests.
"""
import os

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.api.auth import get_session
import app.api.admin as _admin_module
import app.api.advanced_analytics as _analytics_module
import app.api.baseline as _baseline_module
import app.api.doctor as _doctor_module
import app.api.patient_journey as _journey_module
import app.api.tasks as _tasks_module
import app.api.training as _training_module
import app.core.access_control as _access_control
from app.core.access_control import create_access_token

# Set TEST_DATABASE_URL (e.g. postgresql://...) to run the suite against PostgreSQL.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "").strip()


@pytest.fixture(scope="session")
def postgres_engine():
    """One PostgreSQL schema for the whole run (only used with TEST_DATABASE_URL)."""
    engine = create_engine(TEST_DATABASE_URL)
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(name="session", scope="function")
def session_fixture(request):
    """An empty database for every test function."""
    if TEST_DATABASE_URL:
        engine = request.getfixturevalue("postgres_engine")
        # Row deletes (children first) plus identity resets: much faster than
        # TRUNCATE for small tables, which forces file syncs on every call.
        with engine.begin() as connection:
            for table in reversed(SQLModel.metadata.sorted_tables):
                connection.execute(table.delete())
            sequences = connection.execute(text(
                "SELECT sequence_schema, sequence_name FROM information_schema.sequences"
            )).all()
            for schema, name in sequences:
                connection.execute(text(f'ALTER SEQUENCE "{schema}"."{name}" RESTART WITH 1'))
        with Session(engine) as session:
            yield session
        return

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(name="client", scope="function")
def client_fixture(session: Session):
    """TestClient with every DB dependency overridden to use the test session."""

    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    for module in (_admin_module, _analytics_module, _baseline_module, _doctor_module,
                   _journey_module, _tasks_module, _training_module):
        app.dependency_overrides[module.get_session] = get_session_override
    app.dependency_overrides[_access_control.get_db_session] = get_session_override

    # Patch startup helpers so TestClient never tries to reach real Postgres.
    with (
        patch("app.main.wait_for_database", return_value=None),
        patch("app.main.init_db", return_value=None),
    ):
        client = TestClient(app, raise_server_exceptions=False)
        yield client

    app.dependency_overrides.clear()


def bearer_for(account, role: str) -> dict:
    """Authorization header for an existing account (role: patient, doctor or admin)."""
    token, _ = create_access_token(role, account.id, account.password_hash)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(name="auth_headers")
def auth_headers_fixture():
    return bearer_for
