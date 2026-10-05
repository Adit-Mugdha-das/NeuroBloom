"""
Unavailable measurements must stay unavailable, and valid zeros must stay zero.

Covers reaction-time variability (CV), contextual correlations, EWMA score
filtering, and the biomarkers API response that the dashboard reads.
"""
import json

import pytest

import app.api.advanced_analytics as analytics_api
from app.core.advanced_analytics import (
    calculate_contextual_correlations,
    calculate_iiv_metrics,
    generate_longitudinal_report,
)
from app.core.security import hash_password
from app.main import app
from app.models.baseline_assessment import BaselineAssessment
from app.models.session_context import SessionContext
from app.models.training_plan import TrainingPlan
from app.models.training_session import TrainingSession
from app.models.user import User


# ── A. Reaction-time variability ───────────────────────────────────────────────

def test_cv_unavailable_without_valid_reaction_times():
    for reaction_times in ([], [None, 0, -50, float("nan")]):
        result = calculate_iiv_metrics(reaction_times)
        assert result["rt_cv"] is None
        assert result["status"] == "insufficient_data"


def test_cv_unavailable_with_one_valid_reaction_time():
    result = calculate_iiv_metrics([0, 520])
    assert result["rt_cv"] is None
    assert result["valid_rt_count"] == 1
    assert result["status"] == "insufficient_data"


def test_identical_reaction_times_give_a_measured_cv_of_zero():
    result = calculate_iiv_metrics([500, 500, 500])
    assert result["rt_cv"] == 0.0
    assert result["status"] == "available"


def test_unavailable_cv_is_excluded_from_the_longitudinal_average():
    sessions = [
        {"score": 60, "iiv_metrics": {"rt_cv": 0.2}},
        {"score": 62, "iiv_metrics": {"rt_cv": None}},
        {"score": 64, "iiv_metrics": {"rt_cv": 0.4}},
    ]
    indicators = generate_longitudinal_report(sessions, include_context_correlation=False)["descriptive_indicators"]
    assert indicators["average_cv"] == pytest.approx(0.3)
    assert indicators["cv_session_count"] == 2
    assert indicators["cv_status"] == "available"


def test_average_cv_is_none_when_no_session_has_a_valid_cv():
    sessions = [{"score": 60, "iiv_metrics": {"rt_cv": None}} for _ in range(3)]
    indicators = generate_longitudinal_report(sessions, include_context_correlation=False)["descriptive_indicators"]
    assert indicators["average_cv"] is None
    assert indicators["cv_status"] == "insufficient_data"


# ── B. Contextual correlations ─────────────────────────────────────────────────

def _fatigue(sessions):
    return calculate_contextual_correlations(sessions, ["fatigue_level"])["fatigue_level"]


def test_correlation_unavailable_with_fewer_than_three_pairs():
    result = _fatigue([{"fatigue_level": 3, "score": 70}, {"fatigue_level": 6, "score": 50}])
    assert result["correlation_with_score"] is None
    assert result["score_status"] == "insufficient_data"
    assert result["sample_size"] == 2


def test_correlation_unavailable_for_constant_context():
    result = _fatigue([{"fatigue_level": 5, "score": s} for s in (40, 55, 70)])
    assert result["correlation_with_score"] is None
    assert result["score_status"] == "insufficient_data"
    assert result["sample_size"] == 3


def test_correlation_unavailable_for_constant_outcome():
    result = _fatigue([{"fatigue_level": f, "score": 60} for f in (2, 5, 8)])
    assert result["correlation_with_score"] is None
    assert result["score_status"] == "insufficient_data"


def test_measured_zero_correlation_stays_zero():
    # x = [1, 2, 3], y = [1, 3, 1]: covariance is exactly 0 and both variances are positive.
    result = _fatigue([{"fatigue_level": x, "score": y} for x, y in ((1, 1), (2, 3), (3, 1))])
    assert result["correlation_with_score"] == 0.0
    assert result["score_status"] == "available"


# ── C. EWMA keeps valid zero scores ────────────────────────────────────────────

def test_zero_score_is_kept_in_the_ewma():
    report = generate_longitudinal_report(
        [{"score": 50}, {"score": 0}, {"score": 50}], include_context_correlation=False
    )
    # alpha = 0.2: 50 -> 0.2*0 + 0.8*50 = 40 -> 0.2*50 + 0.8*40 = 42
    assert report["trends"]["score_trend"]["ewma_values"] == [50, 40, 42]


# ── D. API keeps missing values unavailable ────────────────────────────────────

@pytest.fixture(name="api")
def api_fixture(client, session):
    def get_session_override():
        yield session

    app.dependency_overrides[analytics_api.get_session] = get_session_override
    return client


def _patient_with_sessions(session, fatigue_levels, trials):
    user = User(email="analytics@example.org", password_hash=hash_password("pass"), full_name="Synthetic")
    session.add(user)
    session.commit()
    session.refresh(user)
    baseline = BaselineAssessment(user_id=user.id)
    session.add(baseline)
    session.commit()
    session.refresh(baseline)
    plan = TrainingPlan(user_id=user.id, baseline_assessment_id=baseline.id)
    session.add(plan)
    session.commit()
    session.refresh(plan)

    for index, fatigue in enumerate(fatigue_levels):
        record = TrainingSession(
            user_id=user.id, training_plan_id=plan.id, domain="attention", task_type="stroop",
            score=50 + 5 * index, accuracy=70, average_reaction_time=0, consistency=0, errors=0,
            difficulty_before=3, difficulty_after=3, duration=60,
            raw_data=json.dumps({"trials": trials}),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        if fatigue is not None:
            session.add(SessionContext(user_id=user.id, training_session_id=record.id, fatigue_level=fatigue))
            session.commit()
    return user.id


def test_api_reports_missing_cv_and_correlation_as_insufficient_data(api, session):
    # Three sessions without reaction-time trials and without any context records.
    user_id = _patient_with_sessions(session, [None, None, None], trials=[])
    data = api.get(f"/api/training/advanced-analytics/{user_id}/biomarkers").json()

    cv = data["rt_coefficient_of_variation"]
    assert cv["mean"] is None
    assert cv["status"] == "insufficient_data"
    assert cv["interpretation"] != "Normal"

    fatigue = data["fatigue_correlation"]
    assert fatigue["correlation_with_score"] is None
    assert fatigue["score_status"] == "insufficient_data"
    assert fatigue["correlation_with_rt"] is None


def test_api_reports_constant_context_correlation_as_insufficient_data(api, session):
    trials = [{"trial_num": i, "correct": True, "reaction_time": 500 + 10 * i} for i in range(10)]
    user_id = _patient_with_sessions(session, [5, 5, 5], trials=trials)
    data = api.get(f"/api/training/advanced-analytics/{user_id}/biomarkers").json()

    fatigue = data["fatigue_correlation"]
    assert fatigue["sample_size"] == 3
    assert fatigue["correlation_with_score"] is None
    assert fatigue["score_status"] == "insufficient_data"

    # With valid trial RTs the CV is a measured value.
    assert data["rt_coefficient_of_variation"]["status"] == "available"
    assert data["rt_coefficient_of_variation"]["mean"] is not None
    assert data["rt_trend"]["response_time_change"] in {"longer", "shorter", "stable"}
