"""
Tests for the authentication endpoints:
- POST /api/auth/login  (patient login)
- POST /api/auth/doctor/login
- POST /api/auth/register
"""
from app.core.security import hash_password
from app.models.user import User
from app.models.doctor import Doctor


# ── helpers ────────────────────────────────────────────────────────────────────

def _make_patient(session, email="patient@test.com", password="pass123"):
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name="Test Patient",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _make_doctor(session, email="doc@test.com", password="pass123", verified=True):
    doctor = Doctor(
        email=email,
        password_hash=hash_password(password),
        full_name="Dr. Test",
        is_verified=verified,
        is_active=True,
    )
    session.add(doctor)
    session.commit()
    session.refresh(doctor)
    return doctor


# ── patient login ──────────────────────────────────────────────────────────────

def test_patient_login_success(client, session):
    _make_patient(session)
    resp = client.post("/api/auth/login", json={"email": "patient@test.com", "password": "pass123"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "patient@test.com"
    assert "id" in data


def test_patient_login_wrong_password(client, session):
    _make_patient(session)
    resp = client.post("/api/auth/login", json={"email": "patient@test.com", "password": "wrong"})
    assert resp.status_code == 401


def test_patient_login_unknown_email(client, session):
    resp = client.post("/api/auth/login", json={"email": "nobody@test.com", "password": "pass123"})
    assert resp.status_code == 401


# ── patient register ───────────────────────────────────────────────────────────

def test_patient_register_success(client, session):
    resp = client.post("/api/auth/register", json={
        "email": "new@test.com",
        "password": "secret99",
        "full_name": "New User",
    })
    assert resp.status_code == 200
    assert resp.json()["email"] == "new@test.com"


def test_patient_register_duplicate_email(client, session):
    _make_patient(session)
    resp = client.post("/api/auth/register", json={
        "email": "patient@test.com",
        "password": "other",
        "full_name": "Dup User",
    })
    assert resp.status_code == 400


# ── doctor login ───────────────────────────────────────────────────────────────

def test_doctor_login_success(client, session):
    _make_doctor(session)
    resp = client.post("/api/auth/doctor/login", json={"email": "doc@test.com", "password": "pass123"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "doctor"
    assert data["is_verified"] is True


def test_doctor_login_unverified(client, session):
    _make_doctor(session, email="unverified@test.com", verified=False)
    resp = client.post("/api/auth/doctor/login", json={"email": "unverified@test.com", "password": "pass123"})
    assert resp.status_code == 403


def test_doctor_login_wrong_password(client, session):
    _make_doctor(session)
    resp = client.post("/api/auth/doctor/login", json={"email": "doc@test.com", "password": "wrong"})
    assert resp.status_code == 401
