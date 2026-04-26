"""
Pytest fixtures: in-memory SQLite test database + FastAPI TestClient.
No real PostgreSQL needed — tests run fully isolated.

startup patching: wait_for_database and init_db are patched to no-ops so that
the FastAPI app can start without an actual Postgres connection during tests.
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.api.auth import get_session
import app.api.doctor as _doctor_module


@pytest.fixture(name="session", scope="function")
def session_fixture():
    """Create a fresh in-memory SQLite DB for every test function."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client", scope="function")
def client_fixture(session: Session):
    """TestClient with the DB dependency overridden to use the test session."""

    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[_doctor_module.get_session] = get_session_override

    # Patch startup helpers so TestClient never tries to reach real Postgres.
    with (
        patch("app.main.wait_for_database", return_value=None),
        patch("app.main.init_db", return_value=None),
    ):
        client = TestClient(app, raise_server_exceptions=False)
        yield client

    app.dependency_overrides.clear()
