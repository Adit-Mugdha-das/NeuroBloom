"""
End-to-end API integration test of the patient--clinician workflow.

Exercises auth, admin, doctor, tasks, baseline and training routers against one
shared in-memory database, in the order a real deployment uses them:

  patient registers and logs in
  -> clinician registers, is blocked until an administrator approves, then logs in
  -> patient requests the clinician; access is refused until the clinician approves
  -> patient completes the six baseline tasks; baseline and training plan are created
  -> patient completes one four-task training session; difficulty is adapted
  -> clinician reviews overview, session history and trends
  -> an unassigned clinician is still refused access
"""
import json

import pytest

import app.api.admin as admin_api
import app.api.baseline as baseline_api
import app.api.tasks as tasks_api
import app.api.training as training_api
from app.core.security import hash_password
from app.main import app
from app.models.admin import Admin


@pytest.fixture(name="api")
def api_fixture(client, session):
    """Route the remaining routers to the same test database as the base client."""
    def get_session_override():
        yield session

    for module in (admin_api, baseline_api, tasks_api, training_api):
        app.dependency_overrides[module.get_session] = get_session_override
    return client


# Baseline task results: the details are the metrics read by app.core.scoring.
BASELINE_RESULTS = {
    "working_memory": {"accuracy": 55, "mean_rt": 900, "rt_std": 250},
    "attention": {"targets_shown": 20, "targets_hit": 18, "false_alarms": 1, "mean_rt": 450},
    "flexibility": {"accuracy": 70, "switch_cost_rt": 400, "perseveration_errors": 2},
    "planning": {"moves_taken": 12, "optimal_moves": 7, "planning_time_ms": 20000, "completed": True},
    "processing_speed": {"simple_rt_mean": 300, "choice_rt_mean": 450, "simple_rt_std": 40, "choice_accuracy": 0.95},
    "visual_scanning": {"targets_total": 5, "targets_found": 5, "search_time_ms": 8000},
}


def test_patient_clinician_workflow(api, session):
    # ── 1. Patient account ────────────────────────────────────────────────────
    resp = api.post("/api/auth/register", json={
        "email": "patient@example.org", "password": "patient-pass", "full_name": "Synthetic Patient",
    })
    assert resp.status_code == 200
    patient_id = resp.json()["id"]
    resp = api.post("/api/auth/login", json={"email": "patient@example.org", "password": "patient-pass"})
    assert resp.status_code == 200 and resp.json()["role"] == "patient"

    # ── 2. Clinician account requires administrator approval ─────────────────
    resp = api.post("/api/auth/doctor/register", json={
        "email": "clinician@example.org", "password": "clinician-pass", "full_name": "Dr. Synthetic",
        "license_number": "TEST-001", "specialization": "Neurology", "institution": "Test Clinic",
    })
    assert resp.status_code == 200
    doctor_id = resp.json()["id"]
    login = {"email": "clinician@example.org", "password": "clinician-pass"}
    assert api.post("/api/auth/doctor/login", json=login).status_code == 403

    admin = Admin(email="admin@example.org", password_hash=hash_password("admin-pass"))
    session.add(admin)
    session.commit()
    session.refresh(admin)
    resp = api.patch(f"/api/admin/doctors/{doctor_id}/approve", params={"admin_id": admin.id})
    assert resp.status_code == 200
    resp = api.post("/api/auth/doctor/login", json=login)
    assert resp.status_code == 200 and resp.json()["role"] == "doctor"

    # ── 3. Patient--clinician association ─────────────────────────────────────
    available = api.get("/api/doctor/available-doctors").json()["doctors"]
    assert doctor_id in [d["id"] for d in available]
    resp = api.post("/api/doctor/request-assignment", params={
        "patient_id": patient_id, "doctor_id": doctor_id, "diagnosis": "Relapsing-remitting MS",
    })
    assert resp.status_code == 200
    request_id = resp.json()["request_id"]

    # Access is refused while the request is pending.
    assert api.get(f"/api/doctor/{doctor_id}/patient/{patient_id}/overview").status_code == 403

    pending = api.get(f"/api/doctor/{doctor_id}/pending-requests").json()["requests"]
    assert [r["patient_id"] for r in pending] == [patient_id]
    resp = api.post(f"/api/doctor/request/{request_id}/approve", params={"doctor_id": doctor_id})
    assert resp.status_code == 200
    patients = api.get(f"/api/doctor/{doctor_id}/patients").json()
    assert patients["total"] == 1

    # ── 4. Baseline assessment and training plan ─────────────────────────────
    for domain, metrics in BASELINE_RESULTS.items():
        resp = api.post("/api/tasks/results", params={"user_id": patient_id}, json={
            "task_type": domain, "score": 0, "details": json.dumps(metrics),
        })
        assert resp.status_code == 200
    resp = api.post("/api/baseline/calculate", params={"user_id": patient_id})
    assert resp.status_code == 200
    resp = api.post(f"/api/training/training-plan/generate/{patient_id}")
    assert resp.status_code == 200
    plan = resp.json()
    session_domains = plan["primary_focus"] + plan["secondary_focus"]
    assert len(session_domains) == 4

    # ── 5. One complete four-task training session ──────────────────────────
    # Accuracies chosen to exercise all three adaptation branches (>=85, 65-84, <65).
    accuracies = [90.0, 75.0, 60.0, 88.0]
    for index, (domain, accuracy) in enumerate(zip(session_domains, accuracies)):
        resp = api.post("/api/training/training-session/submit", params={
            "user_id": patient_id, "training_plan_id": plan["id"], "domain": domain,
            "task_type": domain, "task_id": f"{domain}_{index}",
            "score": accuracy, "accuracy": accuracy, "average_reaction_time": 600, "duration": 120,
        }, json={})
        assert resp.status_code == 200, resp.text

    # ── 6. Clinician review of the stored data ───────────────────────────────
    overview = api.get(f"/api/doctor/{doctor_id}/patient/{patient_id}/overview")
    assert overview.status_code == 200
    overview = overview.json()
    assert overview["baseline"]["completed"] is True
    assert overview["training_summary"]["total_sessions"] == 4
    assert set(overview["domain_performance"]) == set(session_domains)

    expected = {}
    for domain, accuracy in zip(session_domains, accuracies):
        start = plan["initial_difficulty"][domain]
        expected[domain] = min(start + 1, 10) if accuracy >= 85 else max(start - 1, 1) if accuracy < 65 else start
    assert {d: overview["current_difficulty"][d] for d in session_domains} == expected

    history = api.get(f"/api/doctor/{doctor_id}/patient/{patient_id}/sessions").json()
    assert history["total"] == 4
    assert sorted(s["accuracy"] for s in history["sessions"]) == sorted(accuracies)

    trends = api.get(f"/api/doctor/{doctor_id}/patient/{patient_id}/trends")
    assert trends.status_code == 200 and trends.json()["total_sessions"] == 4

    # ── 7. An unassigned clinician cannot read the record ────────────────────
    resp = api.post("/api/auth/doctor/register", json={
        "email": "other@example.org", "password": "other-pass", "full_name": "Dr. Other",
        "license_number": "TEST-002", "specialization": "Neurology", "institution": "Other Clinic",
    })
    other_id = resp.json()["id"]
    api.patch(f"/api/admin/doctors/{other_id}/approve", params={"admin_id": admin.id})
    assert api.get(f"/api/doctor/{other_id}/patient/{patient_id}/overview").status_code == 403
    assert api.get(f"/api/doctor/{other_id}/patient/{patient_id}/sessions").status_code == 403
