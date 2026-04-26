"""
Tests for the doctor endpoints:
- GET /api/doctor/{doctor_id}/patients
- GET /api/doctor/{doctor_id}/analytics
- GET /api/doctor/{doctor_id}/notifications
"""
from app.core.security import hash_password
from app.models.doctor import Doctor
from app.models.user import User
from app.models.patient_assignment import PatientAssignment


# ── helpers ────────────────────────────────────────────────────────────────────

def _make_doctor(session, email="doc@test.com"):
    doctor = Doctor(
        email=email,
        password_hash=hash_password("pass"),
        full_name="Dr. Test",
        is_verified=True,
        is_active=True,
    )
    session.add(doctor)
    session.commit()
    session.refresh(doctor)
    return doctor


def _make_patient(session, email="patient@test.com"):
    user = User(
        email=email,
        password_hash=hash_password("pass"),
        full_name="Test Patient",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _assign(session, doctor, patient, diagnosis="Relapsing-Remitting MS"):
    assignment = PatientAssignment(
        doctor_id=doctor.id,
        patient_id=patient.id,
        diagnosis=diagnosis,
        is_active=True,
    )
    session.add(assignment)
    session.commit()
    return assignment


# ── patients list ──────────────────────────────────────────────────────────────

def test_get_patients_empty(client, session):
    doctor = _make_doctor(session)
    resp = client.get(f"/api/doctor/{doctor.id}/patients")
    assert resp.status_code == 200
    data = resp.json()
    assert data["patients"] == []
    assert data["total"] == 0


def test_get_patients_with_assignment(client, session):
    doctor = _make_doctor(session)
    patient = _make_patient(session)
    _assign(session, doctor, patient)

    resp = client.get(f"/api/doctor/{doctor.id}/patients")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["patients"][0]["email"] == "patient@test.com"


def test_get_patients_unknown_doctor(client, session):
    resp = client.get("/api/doctor/99999/patients")
    assert resp.status_code == 404


# ── analytics ─────────────────────────────────────────────────────────────────

def test_analytics_no_patients(client, session):
    doctor = _make_doctor(session)
    resp = client.get(f"/api/doctor/{doctor.id}/analytics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["overview"]["total_patients"] == 0
    assert data["overview"]["active_patients"] == 0


def test_analytics_unknown_doctor(client, session):
    resp = client.get("/api/doctor/99999/analytics")
    assert resp.status_code == 404


# ── notifications ─────────────────────────────────────────────────────────────

def test_notifications_empty(client, session):
    doctor = _make_doctor(session)
    resp = client.get(f"/api/doctor/{doctor.id}/notifications")
    assert resp.status_code == 200
    assert resp.json()["notifications"] == []


def test_notifications_unknown_doctor(client, session):
    resp = client.get("/api/doctor/99999/notifications")
    assert resp.status_code == 404
