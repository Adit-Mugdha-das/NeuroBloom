"""
Focus rebalancing after every fourth completed session.

Task-specific submit routes complete sessions through track_session_completion();
the generic /training-session/submit route has its own completion logic. Both
must call rebalance_focus_areas() exactly once when the completed-session count
reaches 4, and the rebalancing query must see the task result just submitted.
"""
import json

import pytest
from sqlmodel import desc, select

import app.api.training as training_api
from app.core.security import hash_password
from app.main import app
from app.models.baseline_assessment import BaselineAssessment
from app.models.training_plan import TrainingPlan
from app.models.training_session import TrainingSession
from app.models.user import User

TASKS_PER_SESSION = 4
SESSIONS = 4


@pytest.fixture(name="api")
def api_fixture(client, session):
    def get_session_override():
        yield session

    app.dependency_overrides[training_api.get_session] = get_session_override
    return client


@pytest.fixture(name="plan")
def plan_fixture(session):
    user = User(email="rebalance@example.org", password_hash=hash_password("pass"), full_name="Synthetic")
    session.add(user)
    session.commit()
    session.refresh(user)

    baseline = BaselineAssessment(user_id=user.id, working_memory_score=60, attention_score=55,
                                  flexibility_score=65, planning_score=70, processing_speed_score=50,
                                  visual_scanning_score=75, overall_score=62.5)
    session.add(baseline)
    session.commit()
    session.refresh(baseline)

    plan = TrainingPlan(
        user_id=user.id,
        baseline_assessment_id=baseline.id,
        primary_focus=json.dumps(["processing_speed", "attention"]),
        secondary_focus=json.dumps(["working_memory", "flexibility"]),
        maintenance=json.dumps(["planning", "visual_scanning"]),
        initial_difficulty=json.dumps({"working_memory": 4}),
        current_difficulty=json.dumps({"working_memory": 4}),
        # Pacing limits would block 4 sessions in one test run; they are not under test here.
        max_sessions_per_day=SESSIONS + 1,
        cooldown_between_sessions_minutes=0,
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan


@pytest.fixture(name="rebalance_spy")
def rebalance_spy_fixture(monkeypatch):
    """Record each rebalancing call and what its query can see, then run the real function."""
    calls = []
    original = training_api.rebalance_focus_areas

    def spy(plan, db_session):
        visible = db_session.exec(
            select(TrainingSession)
            .where(TrainingSession.training_plan_id == plan.id)
            .order_by(desc(TrainingSession.created_at), desc(TrainingSession.id))
            .limit(12)
        ).all()
        calls.append({
            "completed_sessions": plan.total_sessions_completed,
            "visible_ids": [row.id for row in visible],
        })
        return original(plan, db_session)

    monkeypatch.setattr(training_api, "rebalance_focus_areas", spy)
    return calls


DIGIT_SPAN_TRIAL = {"sequence": [3, 7, 2, 9], "span_type": "forward", "length": 4,
                    "user_response": [3, 7, 2, 9], "reaction_time": 3500}


def test_task_specific_route_rebalances_once_after_fourth_session(api, session, plan, rebalance_spy):
    last_session_id = None
    for session_number in range(1, SESSIONS + 1):
        for slot in range(TASKS_PER_SESSION):
            resp = api.post(f"/api/training/tasks/digit-span/submit/{plan.user_id}", json={
                "difficulty": 4,
                "task_id": f"working_memory_{slot}",
                "trials": [DIGIT_SPAN_TRIAL],
            })
            assert resp.status_code == 200, resp.text
            last_session_id = resp.json()["session_id"]
            assert resp.json()["session_complete"] is (slot == TASKS_PER_SESSION - 1)

        session.refresh(plan)
        assert plan.total_sessions_completed == session_number
        # No rebalancing after sessions 1-3; exactly one call after session 4.
        assert len(rebalance_spy) == (1 if session_number == 4 else 0)

    call = rebalance_spy[0]
    assert call["completed_sessions"] == 4
    # The task that completed session 4 is visible to the rebalancing query (flushed before the call).
    assert call["visible_ids"][0] == last_session_id
    assert len(call["visible_ids"]) == 12


def test_generic_route_still_rebalances_once_after_fourth_session(api, session, plan, rebalance_spy):
    domains = ["processing_speed", "attention", "working_memory", "flexibility"]
    for session_number in range(1, SESSIONS + 1):
        for slot, domain in enumerate(domains):
            resp = api.post("/api/training/training-session/submit", params={
                "user_id": plan.user_id, "training_plan_id": plan.id, "domain": domain,
                "task_type": domain, "task_id": f"{domain}_{slot}",
                "score": 75, "accuracy": 75, "average_reaction_time": 600, "duration": 60,
            }, json={})
            assert resp.status_code == 200, resp.text

        session.refresh(plan)
        assert plan.total_sessions_completed == session_number
        assert len(rebalance_spy) == (1 if session_number == 4 else 0)

    assert rebalance_spy[0]["completed_sessions"] == 4
