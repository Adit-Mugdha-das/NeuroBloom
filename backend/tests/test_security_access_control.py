"""
Authentication and authorization regression tests.

  A. Route inventory: every API route except login/registration requires a valid
     session, and every route that takes a user, patient, doctor or admin
     identifier binds it to the signed-in account.
  B. Authentication: login tokens and the httpOnly cookie, /me, logout, expired,
     tampered and foreign tokens, password changes, deactivated accounts, and
     the cross-site request forgery header.
  C. Authorization: patients, clinicians and administrators cannot act as one
     another or reach records they do not own, including records addressed by
     message, prescription, report, request, session, context or plan identifiers.
  D. Consent revocation: withdrawing consent removes clinician access to the
     patient's data everywhere; restoring it brings access back.
  E. Session completion and result persistence through authenticated requests.
"""
import json
import re
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.routing import APIRoute
from sqlmodel import select

from app.core.access_control import (
    ALL_POLICIES,
    CSRF_HEADER,
    CSRF_HEADER_VALUE,
    IDENTITY_POLICIES,
    TOKEN_ISSUER,
    password_fingerprint,
)
from app.core.config import settings
from app.core.security import hash_password
from app.main import app
from app.models.admin import Admin
from app.models.assignment_request import AssignmentRequest
from app.models.baseline_assessment import BaselineAssessment
from app.models.doctor import Doctor
from app.models.doctor_intervention import DoctorIntervention
from app.models.message import Message
from app.models.patient_assignment import PatientAssignment
from app.models.progress_report import ProgressReport
from app.models.session_context import SessionContext
from app.models.training_plan import TrainingPlan
from app.models.training_session import TrainingSession
from app.models.user import User

PUBLIC_ROUTES = {
    ("POST", "/api/auth/register"),
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/doctor/register"),
    ("POST", "/api/auth/doctor/login"),
    ("POST", "/api/auth/logout"),
    ("POST", "/api/admin/login"),
}
IDENTIFIER_PARAMS = {"user_id", "patient_id", "doctor_id", "admin_id"}


# ── data helpers ──────────────────────────────────────────────────────────────

def make_patient(session, email, consent=True, active=True):
    user = User(email=email, password_hash=hash_password("patient-pass"), full_name=email.split("@")[0],
                consent_to_share=consent, is_active=active)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def make_doctor(session, email, verified=True, active=True):
    doctor = Doctor(email=email, password_hash=hash_password("doctor-pass"), full_name=email.split("@")[0],
                    is_verified=verified, is_active=active)
    session.add(doctor)
    session.commit()
    session.refresh(doctor)
    return doctor


def make_admin(session, email="admin@example.org"):
    admin = Admin(email=email, password_hash=hash_password("admin-pass"))
    session.add(admin)
    session.commit()
    session.refresh(admin)
    return admin


def assign(session, doctor, patient):
    session.add(PatientAssignment(doctor_id=doctor.id, patient_id=patient.id, is_active=True))
    session.commit()


def make_plan(session, patient):
    baseline = BaselineAssessment(user_id=patient.id, working_memory_score=60, attention_score=55,
                                  flexibility_score=65, planning_score=70, processing_speed_score=50,
                                  visual_scanning_score=75, overall_score=62.5)
    session.add(baseline)
    session.commit()
    session.refresh(baseline)
    plan = TrainingPlan(
        user_id=patient.id, baseline_assessment_id=baseline.id,
        primary_focus=json.dumps(["processing_speed", "attention"]),
        secondary_focus=json.dumps(["working_memory", "flexibility"]),
        maintenance=json.dumps(["planning", "visual_scanning"]),
        initial_difficulty=json.dumps({"working_memory": 4}),
        current_difficulty=json.dumps({"working_memory": 4}),
        max_sessions_per_day=10, cooldown_between_sessions_minutes=0,
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


def make_training_session(session, patient, plan, score=70.0):
    record = TrainingSession(user_id=patient.id, training_plan_id=plan.id, domain="attention",
                             task_type="stroop", score=score, accuracy=score, average_reaction_time=600,
                             consistency=0, errors=0, difficulty_before=3, difficulty_after=3, duration=60,
                             completed=True)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


@pytest.fixture(name="world")
def world_fixture(session):
    """Two patients, an assigned clinician, an unassigned clinician and an administrator."""
    alice = make_patient(session, "alice@example.org")
    bob = make_patient(session, "bob@example.org")
    doc = make_doctor(session, "doc@example.org")
    other_doc = make_doctor(session, "other@example.org")
    admin = make_admin(session)
    assign(session, doc, alice)
    plan = make_plan(session, alice)
    make_training_session(session, alice, plan)
    return {"alice": alice, "bob": bob, "doc": doc, "other_doc": other_doc, "admin": admin, "plan": plan}


def _concrete_path(path):
    return re.sub(r"\{[^}]+\}", "1", path)


def _api_routes():
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path.startswith("/api"):
            for method in sorted(route.methods):
                yield method, route


def _top_level_calls(route):
    return {dep.call for dep in route.dependant.dependencies}


def _route_params(route):
    names = {param.name for param in route.dependant.path_params + route.dependant.query_params}
    for dep in route.dependant.dependencies:
        names |= {param.name for param in dep.path_params + dep.query_params}
    return names


# ── A. route inventory ────────────────────────────────────────────────────────

def test_public_routes_are_only_login_registration_and_logout():
    unprotected = set()
    for method, route in _api_routes():
        if route.path == "/api/auth/me":
            continue  # takes the principal as a parameter (checked below)
        if not _top_level_calls(route) & set(ALL_POLICIES):
            unprotected.add((method, route.path))
    assert unprotected == PUBLIC_ROUTES


@pytest.mark.parametrize("method,route", list(_api_routes()), ids=lambda v: getattr(v, "path", v))
def test_every_protected_route_rejects_requests_without_a_session(client, method, route):
    if (method, route.path) in PUBLIC_ROUTES:
        pytest.skip("public route")
    client.cookies.clear()
    resp = client.request(method, _concrete_path(route.path), params={name: 1 for name in IDENTIFIER_PARAMS})
    assert resp.status_code == 401, f"{method} {route.path} -> {resp.status_code}"


def test_every_identifier_route_binds_the_identifier_to_the_session():
    unbound = []
    for method, route in _api_routes():
        if (method, route.path) in PUBLIC_ROUTES:
            continue
        if _route_params(route) & IDENTIFIER_PARAMS and not _top_level_calls(route) & set(IDENTITY_POLICIES):
            unbound.append(f"{method} {route.path}")
    assert unbound == []


# ── B. authentication ─────────────────────────────────────────────────────────

def test_login_sets_httponly_cookie_and_returns_bearer_token(client, world):
    resp = client.post("/api/auth/login", json={"email": "alice@example.org", "password": "patient-pass"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer" and body["access_token"]
    cookie = resp.headers["set-cookie"].lower()
    assert f"{settings.AUTH_COOKIE_NAME}=" in cookie
    assert "httponly" in cookie and "samesite=lax" in cookie and "path=/" in cookie


@pytest.mark.parametrize("endpoint,email,password,role", [
    ("/api/auth/login", "alice@example.org", "patient-pass", "patient"),
    ("/api/auth/doctor/login", "doc@example.org", "doctor-pass", "doctor"),
    ("/api/admin/login", "admin@example.org", "admin-pass", "admin"),
])
def test_me_returns_the_account_bound_to_the_cookie_and_the_bearer_token(client, world, endpoint, email, password, role):
    login = client.post(endpoint, json={"email": email, "password": password})
    assert login.status_code == 200
    via_cookie = client.get("/api/auth/me")
    assert via_cookie.status_code == 200 and via_cookie.json()["role"] == role
    client.cookies.clear()
    via_header = client.get("/api/auth/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"})
    assert via_header.json() == via_cookie.json()
    assert via_header.json()["email"] == email


def test_login_failures_do_not_issue_tokens(client, world):
    for endpoint, email in [("/api/auth/login", "alice@example.org"),
                            ("/api/auth/doctor/login", "doc@example.org"),
                            ("/api/admin/login", "admin@example.org")]:
        resp = client.post(endpoint, json={"email": email, "password": "wrong-password"})
        assert resp.status_code == 401
        assert "access_token" not in resp.json()
        assert "set-cookie" not in resp.headers


def test_logout_clears_the_session_cookie(client, world):
    client.post("/api/auth/login", json={"email": "alice@example.org", "password": "patient-pass"})
    assert client.get("/api/auth/me").status_code == 200
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
    assert f"{settings.AUTH_COOKIE_NAME}=" in resp.headers["set-cookie"]
    assert client.get("/api/auth/me").status_code == 401


def _signed(claims, key=None):
    return jwt.encode(claims, key or settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _claims_for(account, role, **overrides):
    now = datetime.now(timezone.utc)
    claims = {"sub": str(account.id), "role": role, "pwf": password_fingerprint(account.password_hash),
              "iss": TOKEN_ISSUER, "iat": now, "exp": now + timedelta(minutes=5)}
    claims.update(overrides)
    return claims


def test_expired_token_is_rejected(client, world):
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    token = _signed(_claims_for(world["alice"], "patient", iat=past - timedelta(hours=8), exp=past))
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Session expired"


@pytest.mark.parametrize("variant", ["bad-signature", "wrong-issuer", "missing-fingerprint", "unknown-role",
                                     "unknown-account", "not-a-jwt"])
def test_forged_or_malformed_tokens_are_rejected(client, world, variant):
    alice = world["alice"]
    if variant == "bad-signature":
        token = _signed(_claims_for(alice, "patient"), key="x" * 64)
    elif variant == "wrong-issuer":
        token = _signed(_claims_for(alice, "patient", iss="someone-else"))
    elif variant == "missing-fingerprint":
        claims = _claims_for(alice, "patient")
        claims.pop("pwf")
        token = _signed(claims)
    elif variant == "unknown-role":
        token = _signed(_claims_for(alice, "superuser"))
    elif variant == "unknown-account":
        token = _signed(_claims_for(alice, "patient", sub="99999"))
    else:
        token = "not-a-jwt"
    resp = client.get(f"/api/training/training-plan/{alice.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_password_reset_invalidates_existing_tokens(client, world, auth_headers):
    alice, admin = world["alice"], world["admin"]
    old = auth_headers(alice, "patient")
    assert client.get("/api/auth/me", headers=old).status_code == 200
    resp = client.post(f"/api/admin/patients/{alice.id}/reset-password", params={"admin_id": admin.id},
                       json={"new_password": "brand-new-pass"}, headers=auth_headers(admin, "admin"))
    assert resp.status_code == 200
    assert client.get("/api/auth/me", headers=old).status_code == 401
    relogin = client.post("/api/auth/login", json={"email": "alice@example.org", "password": "brand-new-pass"})
    assert relogin.status_code == 200


def test_deactivated_patient_cannot_sign_in_and_loses_existing_session(client, world, auth_headers):
    alice, admin = world["alice"], world["admin"]
    token = auth_headers(alice, "patient")
    resp = client.patch(f"/api/admin/patients/{alice.id}/deactivate", params={"admin_id": admin.id},
                        headers=auth_headers(admin, "admin"))
    assert resp.status_code == 200
    assert client.get(f"/api/training/training-plan/{alice.id}", headers=token).status_code == 401
    login = client.post("/api/auth/login", json={"email": "alice@example.org", "password": "patient-pass"})
    assert login.status_code == 403


def test_suspended_or_unverified_clinician_sessions_are_rejected(client, world, session, auth_headers):
    doc, admin = world["doc"], world["admin"]
    token = auth_headers(doc, "doctor")
    resp = client.patch(f"/api/admin/doctors/{doc.id}/suspend", params={"admin_id": admin.id},
                        headers=auth_headers(admin, "admin"))
    assert resp.status_code == 200
    assert client.get(f"/api/doctor/{doc.id}/patients", headers=token).status_code == 401

    pending = make_doctor(session, "pending@example.org", verified=False)
    assert client.get(f"/api/doctor/{pending.id}/patients", headers=auth_headers(pending, "doctor")).status_code == 401


def test_cookie_session_requires_csrf_header_for_writes(client, world):
    alice = world["alice"]
    client.post("/api/auth/login", json={"email": "alice@example.org", "password": "patient-pass"})
    # Reads with the cookie need no extra header.
    assert client.get(f"/api/auth/patient/{alice.id}/profile").status_code == 200
    # A write with the cookie but without the header is refused (forged cross-site form).
    blocked = client.patch(f"/api/auth/patient/{alice.id}/profile", params={"full_name": "Changed"})
    assert blocked.status_code == 403
    allowed = client.patch(f"/api/auth/patient/{alice.id}/profile", params={"full_name": "Changed"},
                           headers={CSRF_HEADER: CSRF_HEADER_VALUE})
    assert allowed.status_code == 200 and allowed.json()["full_name"] == "Changed"


def test_bearer_writes_do_not_need_csrf_header(client, world, auth_headers):
    alice = world["alice"]
    client.cookies.clear()
    resp = client.patch(f"/api/auth/patient/{alice.id}/profile", params={"full_name": "Via Bearer"},
                        headers=auth_headers(alice, "patient"))
    assert resp.status_code == 200


# ── C. authorization ──────────────────────────────────────────────────────────

def test_patient_cannot_read_another_patients_records(client, world, auth_headers):
    alice, bob = world["alice"], world["bob"]
    as_bob = auth_headers(bob, "patient")
    for path in (
        f"/api/training/training-plan/{alice.id}",
        f"/api/training/training-session/history/{alice.id}",
        f"/api/training/training-session/performance-comparison/{alice.id}",
        f"/api/training/advanced-analytics/{alice.id}/biomarkers",
        f"/api/training/trends/{alice.id}",
        f"/api/baseline/{alice.id}",
        f"/api/tasks/results/{alice.id}",
        f"/api/patient-journey/{alice.id}",
        f"/api/auth/patient/{alice.id}/profile",
        f"/api/auth/patient/{alice.id}/messages",
        f"/api/auth/patient/{alice.id}/prescriptions",
        f"/api/doctor/patient/{alice.id}/assigned-doctor",
    ):
        assert client.get(path, headers=as_bob).status_code == 403, path
    # Bob can read his own record.
    assert client.get(f"/api/auth/patient/{bob.id}/profile", headers=as_bob).status_code == 200


def test_patient_cannot_write_to_another_patients_record(client, world, session, auth_headers):
    alice, bob, plan = world["alice"], world["bob"], world["plan"]
    as_bob = auth_headers(bob, "patient")
    before = len(session.exec(select(TrainingSession).where(TrainingSession.user_id == alice.id)).all())
    attempts = [
        client.post(f"/api/training/tasks/digit-span/submit/{alice.id}",
                    json={"difficulty": 4, "task_id": "working_memory_0", "trials": []}, headers=as_bob),
        client.post("/api/training/training-session/submit", params={
            "user_id": alice.id, "training_plan_id": plan.id, "domain": "attention", "task_type": "stroop",
            "score": 90, "accuracy": 90}, json={}, headers=as_bob),
        client.post(f"/api/training/training-plan/generate/{alice.id}", headers=as_bob),
        client.patch(f"/api/auth/patient/{alice.id}/consent", params={"consent": False}, headers=as_bob),
        client.post("/api/tasks/results", params={"user_id": alice.id},
                    json={"task_type": "attention", "score": 1, "details": "{}"}, headers=as_bob),
        client.delete(f"/api/training/dev/clear-sessions/{alice.id}", headers=as_bob),
    ]
    assert [r.status_code for r in attempts] == [403] * len(attempts)
    session.expire_all()
    assert len(session.exec(select(TrainingSession).where(TrainingSession.user_id == alice.id)).all()) == before
    assert session.get(User, alice.id).consent_to_share is True


def test_patient_cannot_submit_results_into_another_patients_plan(client, world, session, auth_headers):
    bob, plan = world["bob"], world["plan"]   # plan belongs to Alice
    resp = client.post("/api/training/training-session/submit", params={
        "user_id": bob.id, "training_plan_id": plan.id, "domain": "attention", "task_type": "stroop",
        "score": 90, "accuracy": 90}, json={}, headers=auth_headers(bob, "patient"))
    assert resp.status_code == 403


def test_roles_cannot_be_confused_when_ids_coincide(client, session, auth_headers):
    # Patients, clinicians and administrators live in separate tables, so ids collide.
    patient = make_patient(session, "same-id-patient@example.org")
    doctor = make_doctor(session, "same-id-doctor@example.org")
    admin = make_admin(session, "same-id-admin@example.org")
    assert patient.id == doctor.id == admin.id
    as_patient = auth_headers(patient, "patient")
    as_doctor = auth_headers(doctor, "doctor")
    assert client.get(f"/api/doctor/{doctor.id}/patients", headers=as_patient).status_code == 403
    assert client.get("/api/admin/stats", params={"admin_id": admin.id}, headers=as_patient).status_code == 403
    assert client.get("/api/admin/stats", params={"admin_id": admin.id}, headers=as_doctor).status_code == 403
    assert client.get(f"/api/training/training-plan/{patient.id}", headers=as_doctor).status_code == 403
    assert client.get("/api/admin/stats", params={"admin_id": admin.id},
                      headers=auth_headers(admin, "admin")).status_code == 200


def test_admin_identifier_cannot_be_borrowed(client, world, session, auth_headers):
    admin_a = world["admin"]
    admin_b = make_admin(session, "second-admin@example.org")
    resp = client.get("/api/admin/patients", params={"admin_id": admin_a.id}, headers=auth_headers(admin_b, "admin"))
    assert resp.status_code == 403


def test_unassigned_clinician_cannot_read_or_act_on_a_patient(client, world, auth_headers):
    alice, doc, other = world["alice"], world["doc"], world["other_doc"]
    as_other = auth_headers(other, "doctor")
    for path in (f"/api/doctor/{other.id}/patient/{alice.id}/overview",
                 f"/api/doctor/{other.id}/patient/{alice.id}/sessions",
                 f"/api/doctor/{other.id}/messages/conversation/{alice.id}",
                 f"/api/doctor/{doc.id}/patient/{alice.id}/overview",     # borrowing the assigned clinician's id
                 f"/api/training/advanced-analytics/{alice.id}/biomarkers"):
        assert client.get(path, headers=as_other).status_code == 403, path
    resp = client.patch(f"/api/doctor/{other.id}/patient/{alice.id}/training-plan",
                        params={"max_sessions_per_day": 1}, headers=as_other)
    assert resp.status_code == 403
    # The assigned clinician reads the same data.
    assert client.get(f"/api/doctor/{doc.id}/patient/{alice.id}/overview",
                      headers=auth_headers(doc, "doctor")).status_code == 200
    assert client.get(f"/api/training/advanced-analytics/{alice.id}/biomarkers",
                      headers=auth_headers(doc, "doctor")).status_code == 200


def test_clinicians_cannot_use_patient_write_routes(client, world, auth_headers):
    alice, doc = world["alice"], world["doc"]
    resp = client.post(f"/api/training/tasks/digit-span/submit/{alice.id}",
                       json={"difficulty": 4, "task_id": "working_memory_0", "trials": []},
                       headers=auth_headers(doc, "doctor"))
    assert resp.status_code == 403


def test_message_identifiers_are_checked_against_the_owner(client, world, session, auth_headers):
    alice, bob, doc = world["alice"], world["bob"], world["doc"]
    to_alice = Message(sender_id=doc.id, sender_type="doctor", recipient_id=alice.id,
                       recipient_type="patient", message="for alice")
    session.add(to_alice)
    session.commit()
    session.refresh(to_alice)
    as_bob = auth_headers(bob, "patient")
    # Bob cannot mark Alice's message read through his own record or Alice's.
    assert client.post(f"/api/auth/patient/{bob.id}/messages/{to_alice.id}/mark-read", headers=as_bob).status_code == 403
    assert client.post(f"/api/auth/patient/{alice.id}/messages/{to_alice.id}/mark-read", headers=as_bob).status_code == 403
    assert client.post(f"/api/auth/patient/{alice.id}/messages/{to_alice.id}/mark-read",
                       headers=auth_headers(alice, "patient")).status_code == 200


def test_messages_only_flow_between_assigned_patients_and_clinicians(client, world, auth_headers):
    alice, bob, doc, other = world["alice"], world["bob"], world["doc"], world["other_doc"]
    as_alice = auth_headers(alice, "patient")
    to_patient = client.post(f"/api/auth/patient/{alice.id}/messages/send", headers=as_alice,
                             json={"recipient_id": bob.id, "recipient_type": "patient", "message": "hi"})
    assert to_patient.status_code == 403
    to_unassigned = client.post(f"/api/auth/patient/{alice.id}/messages/send", headers=as_alice,
                                json={"recipient_id": other.id, "recipient_type": "doctor", "message": "hi"})
    assert to_unassigned.status_code == 403
    ok = client.post(f"/api/auth/patient/{alice.id}/messages/send", headers=as_alice,
                     json={"recipient_id": doc.id, "recipient_type": "doctor", "message": "hello"})
    assert ok.status_code == 200
    as_doc = auth_headers(doc, "doctor")
    doctor_to_doctor = client.post(f"/api/doctor/{doc.id}/messages/send", headers=as_doc,
                                   json={"recipient_id": other.id, "recipient_type": "doctor", "message": "hi"})
    assert doctor_to_doctor.status_code == 403
    doctor_to_unassigned = client.post(f"/api/doctor/{doc.id}/messages/send", headers=as_doc,
                                       json={"recipient_id": bob.id, "recipient_type": "patient", "message": "hi"})
    assert doctor_to_unassigned.status_code == 403


def test_prescription_identifiers_are_checked_against_the_owner(client, world, session, auth_headers):
    alice, bob, doc, other = world["alice"], world["bob"], world["doc"], world["other_doc"]
    prescription = DoctorIntervention(doctor_id=doc.id, patient_id=alice.id,
                                      intervention_type="digital_prescription", description="Rx",
                                      intervention_data=json.dumps({"title": "Rx", "status": "active"}))
    session.add(prescription)
    session.commit()
    session.refresh(prescription)
    as_bob = auth_headers(bob, "patient")
    assert client.get(f"/api/auth/patient/{bob.id}/prescriptions/{prescription.id}/pdf", headers=as_bob).status_code in {403, 404}
    assert client.get(f"/api/auth/patient/{alice.id}/prescriptions/{prescription.id}/pdf", headers=as_bob).status_code == 403
    as_other = auth_headers(other, "doctor")
    assert client.get(f"/api/doctor/{other.id}/patient/{alice.id}/prescriptions/{prescription.id}/pdf",
                      headers=as_other).status_code == 403
    pdf = client.get(f"/api/auth/patient/{alice.id}/prescriptions/{prescription.id}/pdf",
                     headers=auth_headers(alice, "patient"))
    assert pdf.status_code == 200 and pdf.headers["content-type"] == "application/pdf"


def test_report_identifiers_are_checked_against_the_owner(client, world, session, auth_headers):
    alice, doc, other = world["alice"], world["doc"], world["other_doc"]
    now = datetime.now(timezone.utc)
    report = ProgressReport(patient_id=alice.id, doctor_id=doc.id, period_type="weekly",
                            period_start=now - timedelta(days=7), period_end=now)
    session.add(report)
    session.commit()
    session.refresh(report)
    resp = client.patch(f"/api/doctor/{other.id}/reports/{report.id}/commentary", json={"commentary": "x"},
                        headers=auth_headers(other, "doctor"))
    assert resp.status_code == 403
    resp = client.patch(f"/api/doctor/{doc.id}/reports/{report.id}/commentary", json={"commentary": "Reviewed"},
                        headers=auth_headers(doc, "doctor"))
    assert resp.status_code == 200 and resp.json()["doctor_commentary"] == "Reviewed"


def test_assignment_request_identifiers_are_checked_against_the_owner(client, world, session, auth_headers):
    bob, doc, other = world["bob"], world["doc"], world["other_doc"]
    request = AssignmentRequest(patient_id=bob.id, doctor_id=doc.id)
    session.add(request)
    session.commit()
    session.refresh(request)
    # Another clinician cannot approve it, with its own id or the addressed clinician's id.
    as_other = auth_headers(other, "doctor")
    assert client.post(f"/api/doctor/request/{request.id}/approve", params={"doctor_id": other.id},
                       headers=as_other).status_code == 403
    assert client.post(f"/api/doctor/request/{request.id}/approve", params={"doctor_id": doc.id},
                       headers=as_other).status_code == 403
    # A patient cannot file a request on another patient's behalf.
    assert client.post("/api/doctor/request-assignment", params={"patient_id": bob.id, "doctor_id": other.id},
                       headers=auth_headers(world["alice"], "patient")).status_code == 403
    assert client.post(f"/api/doctor/request/{request.id}/approve", params={"doctor_id": doc.id},
                       headers=auth_headers(doc, "doctor")).status_code == 200


def test_direct_assignment_requires_a_request_from_the_patient(client, world, session, auth_headers):
    bob, other = world["bob"], world["other_doc"]   # Bob consents but never asked for this clinician
    as_other = auth_headers(other, "doctor")
    body = {"patient_email": bob.email, "diagnosis": "RRMS"}
    assert client.post(f"/api/doctor/{other.id}/assign-patient", json=body, headers=as_other).status_code == 403
    session.add(AssignmentRequest(patient_id=bob.id, doctor_id=other.id))
    session.commit()
    resp = client.post(f"/api/doctor/{other.id}/assign-patient", json=body, headers=as_other)
    assert resp.status_code == 200
    assert client.get(f"/api/doctor/{other.id}/patient/{bob.id}/overview", headers=as_other).status_code == 200


def test_session_and_context_identifiers_are_checked_against_the_owner(client, world, session, auth_headers):
    alice, bob = world["alice"], world["bob"]
    alice_session = session.exec(select(TrainingSession).where(TrainingSession.user_id == alice.id)).first()
    as_bob = auth_headers(bob, "patient")
    # Context for someone else is refused.
    resp = client.post("/api/training/session-context", json={"user_id": alice.id, "fatigue_level": 5}, headers=as_bob)
    assert resp.status_code == 403
    # Bob's own context cannot be attached to Alice's session.
    bob_context = client.post("/api/training/session-context", json={"user_id": bob.id, "fatigue_level": 5},
                              headers=as_bob)
    assert bob_context.status_code == 200
    context_id = bob_context.json()["context_id"]
    resp = client.patch(f"/api/training/training-session/{alice_session.id}/link-context",
                        params={"context_id": context_id}, headers=as_bob)
    assert resp.status_code == 403
    assert session.get(SessionContext, context_id).training_session_id is None
    # Alice's session analytics are not reachable through Bob's own user id.
    resp = client.get(f"/api/training/advanced-analytics/{bob.id}/session/{alice_session.id}", headers=as_bob)
    assert resp.status_code == 404


# ── D. consent revocation ─────────────────────────────────────────────────────

def test_withdrawn_consent_removes_clinician_access_everywhere(client, world, session, auth_headers):
    alice, doc = world["alice"], world["doc"]
    as_doc = auth_headers(doc, "doctor")
    as_alice = auth_headers(alice, "patient")
    session.add(DoctorIntervention(doctor_id=doc.id, patient_id=alice.id, intervention_type="digital_prescription",
                                   description="Rx", intervention_data=json.dumps({"title": "Rx", "status": "active"})))
    now = datetime.now(timezone.utc)
    report = ProgressReport(patient_id=alice.id, doctor_id=doc.id, period_type="weekly",
                            period_start=now - timedelta(days=7), period_end=now)
    session.add(report)
    session.commit()
    session.refresh(report)

    reads = [
        f"/api/doctor/{doc.id}/patient/{alice.id}/overview",
        f"/api/doctor/{doc.id}/patient/{alice.id}/sessions",
        f"/api/doctor/{doc.id}/patient/{alice.id}/trends",
        f"/api/doctor/{doc.id}/patient/{alice.id}/progress-monitoring",
        f"/api/doctor/{doc.id}/patient/{alice.id}/interventions",
        f"/api/doctor/{doc.id}/patient/{alice.id}/prescriptions",
        f"/api/doctor/{doc.id}/patients/{alice.id}/reports",
        f"/api/training/advanced-analytics/{alice.id}/biomarkers",
        f"/api/training/training-session/history/{alice.id}",
    ]
    for path in reads:
        assert client.get(path, headers=as_doc).status_code == 200, path
    assert client.get(f"/api/doctor/{doc.id}/analytics", headers=as_doc).json()["overview"]["total_patients"] == 1

    # The patient withdraws consent.
    resp = client.patch(f"/api/auth/patient/{alice.id}/consent", params={"consent": False}, headers=as_alice)
    assert resp.status_code == 200 and resp.json()["consent_to_share"] is False

    for path in reads:
        assert client.get(path, headers=as_doc).status_code == 403, path
    writes = [
        client.patch(f"/api/doctor/{doc.id}/patient/{alice.id}/training-plan", params={"max_sessions_per_day": 1}, headers=as_doc),
        client.patch(f"/api/doctor/{doc.id}/patient/{alice.id}/focus-areas",
                     params={"primary_focus": json.dumps(["attention", "planning"])}, headers=as_doc),
        client.post(f"/api/doctor/{doc.id}/patients/{alice.id}/generate-report", params={"period_type": "weekly"}, headers=as_doc),
        client.patch(f"/api/doctor/{doc.id}/reports/{report.id}/commentary", json={"commentary": "x"}, headers=as_doc),
    ]
    assert [r.status_code for r in writes] == [403] * len(writes)

    # The assignment stays visible, without performance data; aggregates exclude the patient.
    listing = client.get(f"/api/doctor/{doc.id}/patients", headers=as_doc).json()["patients"]
    assert listing[0]["consent_to_share"] is False
    assert listing[0]["last_activity"] is None and listing[0]["baseline_completed"] is False
    assert client.get(f"/api/doctor/{doc.id}/analytics", headers=as_doc).json()["overview"]["total_patients"] == 0
    assert client.get(f"/api/doctor/{doc.id}/prescriptions", headers=as_doc).json()["patients"] == []
    assert client.get(f"/api/doctor/{doc.id}/analytics/domains", headers=as_doc).json()["domains"] == {}

    # Messaging with the assigned clinician remains available to the patient.
    msg = client.post(f"/api/auth/patient/{alice.id}/messages/send", headers=as_alice,
                      json={"recipient_id": doc.id, "recipient_type": "doctor", "message": "still here"})
    assert msg.status_code == 200

    # Restoring consent restores access.
    client.patch(f"/api/auth/patient/{alice.id}/consent", params={"consent": True}, headers=as_alice)
    for path in reads:
        assert client.get(path, headers=as_doc).status_code == 200, path


# ── E. session completion and result persistence ──────────────────────────────

DIGIT_SPAN_TRIAL = {"sequence": [3, 7, 2, 9], "span_type": "forward", "length": 4,
                    "user_response": [3, 7, 2, 9], "reaction_time": 3500}


def test_authenticated_session_completion_persists_results(client, world, session, auth_headers):
    alice, doc, plan = world["alice"], world["doc"], world["plan"]
    as_alice = auth_headers(alice, "patient")
    before = len(session.exec(select(TrainingSession).where(TrainingSession.user_id == alice.id)).all())

    session_ids = []
    for slot in range(4):
        resp = client.post(f"/api/training/tasks/digit-span/submit/{alice.id}", headers=as_alice, json={
            "difficulty": 4, "task_id": f"working_memory_{slot}", "trials": [DIGIT_SPAN_TRIAL]})
        assert resp.status_code == 200, resp.text
        session_ids.append(resp.json()["session_id"])
        assert resp.json()["session_complete"] is (slot == 3)

    session.expire_all()
    stored = session.exec(select(TrainingSession).where(TrainingSession.user_id == alice.id)).all()
    assert len(stored) == before + 4
    assert {row.id for row in stored} >= set(session_ids)
    assert all(row.user_id == alice.id and row.training_plan_id == plan.id for row in stored if row.id in session_ids)
    assert session.get(TrainingPlan, plan.id).total_sessions_completed == 1

    # The stored results are returned to the patient and to the consented clinician.
    history = client.get(f"/api/training/training-session/history/{alice.id}", headers=as_alice)
    assert history.status_code == 200
    returned = {item["id"] for item in history.json()["sessions"]} if isinstance(history.json(), dict) \
        else {item["id"] for item in history.json()}
    assert set(session_ids) <= returned
    overview = client.get(f"/api/doctor/{doc.id}/patient/{alice.id}/overview", headers=auth_headers(doc, "doctor"))
    assert overview.status_code == 200
    assert overview.json()["training_summary"]["total_sessions"] == before + 4


def test_approval_does_not_override_withdrawn_consent(client, session, auth_headers):
    patient = make_patient(session, "new-patient@example.org", consent=False)
    doctor = make_doctor(session, "requested@example.org")
    as_patient, as_doctor = auth_headers(patient, "patient"), auth_headers(doctor, "doctor")

    # Requesting a clinician is the patient's consent to share data.
    resp = client.post("/api/doctor/request-assignment", params={"patient_id": patient.id, "doctor_id": doctor.id},
                       headers=as_patient)
    assert resp.status_code == 200
    request_id = resp.json()["request_id"]
    session.expire_all()
    assert session.get(User, patient.id).consent_to_share is True

    # The patient withdraws consent while the request is still pending.
    client.patch(f"/api/auth/patient/{patient.id}/consent", params={"consent": False}, headers=as_patient)
    assert client.post(f"/api/doctor/request/{request_id}/approve", params={"doctor_id": doctor.id},
                       headers=as_doctor).status_code == 200
    session.expire_all()
    assert session.get(User, patient.id).consent_to_share is False
    overview = f"/api/doctor/{doctor.id}/patient/{patient.id}/overview"
    assert client.get(overview, headers=as_doctor).status_code == 403

    # Only the patient can turn sharing back on.
    client.patch(f"/api/auth/patient/{patient.id}/consent", params={"consent": True}, headers=as_patient)
    assert client.get(overview, headers=as_doctor).status_code == 200


def test_unassignment_removes_clinician_access_immediately(client, world, auth_headers):
    alice, doc = world["alice"], world["doc"]
    as_doc = auth_headers(doc, "doctor")
    overview = f"/api/doctor/{doc.id}/patient/{alice.id}/overview"
    assert client.get(overview, headers=as_doc).status_code == 200
    assert client.post(f"/api/doctor/{doc.id}/unassign/{alice.id}", headers=as_doc).status_code == 200
    # The same, still valid, session is refused on the next request.
    assert client.get(overview, headers=as_doc).status_code == 403
    assert client.get(f"/api/training/advanced-analytics/{alice.id}/biomarkers", headers=as_doc).status_code == 403
    assert client.get(f"/api/doctor/{doc.id}/messages/conversation/{alice.id}", headers=as_doc).status_code == 403


def test_admin_session_cannot_use_patient_or_clinician_routes(client, world, auth_headers):
    alice, doc, admin = world["alice"], world["doc"], world["admin"]
    as_admin = auth_headers(admin, "admin")
    for path in (f"/api/training/training-plan/{alice.id}",
                 f"/api/training/advanced-analytics/{alice.id}/biomarkers",
                 f"/api/auth/patient/{alice.id}/messages",
                 f"/api/doctor/{doc.id}/patients",
                 f"/api/doctor/{doc.id}/patient/{alice.id}/overview"):
        assert client.get(path, headers=as_admin).status_code == 403, path
    # Patient records are reachable for administrators only through the admin routes.
    resp = client.get(f"/api/admin/patients/{alice.id}/overview", params={"admin_id": admin.id}, headers=as_admin)
    assert resp.status_code == 200
