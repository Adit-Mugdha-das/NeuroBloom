import json
from typing import Any, Optional

from sqlmodel import Session, func, select

from app.models.baseline_assessment import BaselineAssessment
from app.models.cognitive_task import CognitiveTask
from app.models.test_result import TestResult
from app.models.training_plan import TrainingPlan
from app.models.training_session import TrainingSession
from app.models.user import User


BASELINE_DOMAINS = [
    "working_memory",
    "attention",
    "flexibility",
    "planning",
    "processing_speed",
    "visual_scanning",
]

BASELINE_DOMAIN_ROUTES = {
    "working_memory": "/baseline/tasks/working-memory",
    "attention": "/baseline/tasks/attention",
    "flexibility": "/baseline/tasks/flexibility",
    "planning": "/baseline/tasks/planning",
    "processing_speed": "/baseline/tasks/processing-speed",
    "visual_scanning": "/baseline/tasks/visual-scanning",
}


def _parse_raw_metrics(raw_metrics: Optional[str]) -> dict[str, Any]:
    if not raw_metrics:
        return {}
    try:
        parsed = json.loads(raw_metrics)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def is_dev_generated_baseline(baseline: Optional[BaselineAssessment]) -> bool:
    if not baseline:
        return False
    raw_metrics = _parse_raw_metrics(baseline.raw_metrics)
    return raw_metrics.get("source") == "dev_tools"


def get_active_training_plan(session: Session, user_id: int) -> Optional[TrainingPlan]:
    return session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()


def get_real_baseline(session: Session, user_id: int) -> Optional[BaselineAssessment]:
    baselines = session.exec(
        select(BaselineAssessment)
        .where(BaselineAssessment.user_id == user_id)
        .where(BaselineAssessment.is_baseline == True)
        .order_by(BaselineAssessment.created_at.desc())
    ).all()
    return next((baseline for baseline in baselines if not is_dev_generated_baseline(baseline)), None)


def get_baseline_status(session: Session, user_id: int) -> dict[str, Any]:
    results = session.exec(select(TestResult).where(TestResult.user_id == user_id)).all()
    completed_task_types = {result.task_type for result in results}
    task_status = {domain: domain in completed_task_types for domain in BASELINE_DOMAINS}
    completed_count = sum(1 for domain in BASELINE_DOMAINS if task_status[domain])
    next_domain = next((domain for domain in BASELINE_DOMAINS if not task_status[domain]), None)

    return {
        "tasks": task_status,
        "completed_count": completed_count,
        "total_tasks": len(BASELINE_DOMAINS),
        "all_completed": completed_count == len(BASELINE_DOMAINS),
        "next_domain": next_domain,
        "next_route": BASELINE_DOMAIN_ROUTES.get(next_domain),
    }


def get_reference_data_status(session: Session) -> dict[str, Any]:
    task_count = session.exec(select(func.count()).select_from(CognitiveTask)).one()
    total_tasks = int(task_count or 0)
    return {
        "cognitive_tasks_seeded": total_tasks > 0,
        "cognitive_task_count": total_tasks,
    }


def build_patient_journey(session: Session, user_id: int) -> dict[str, Any]:
    user = session.exec(
        select(User)
        .where(User.id == user_id)
        .where(User.is_active == True)
    ).first()
    if not user:
        return {
            "user_exists": False,
            "state": "missing_user",
            "blocking_reason": "User not found",
        }

    reference_data = get_reference_data_status(session)
    baseline_status = get_baseline_status(session, user_id)
    baseline = get_real_baseline(session, user_id)
    training_plan = get_active_training_plan(session, user_id)
    training_sessions_count = len(
        session.exec(select(TrainingSession).where(TrainingSession.user_id == user_id)).all()
    )

    current_session_tasks = training_plan.get_current_session_tasks_completed() if training_plan else []
    has_in_progress_session = bool(current_session_tasks)
    progress_unlocked = training_sessions_count > 0

    state = "new_user"
    next_route = "/baseline"
    next_label = "Start baseline"
    blocking_reason = None

    if not baseline_status["all_completed"]:
        state = "baseline_in_progress" if baseline_status["completed_count"] > 0 else "new_user"
        next_route = baseline_status["next_route"] or "/baseline"
        next_label = "Continue baseline" if baseline_status["completed_count"] > 0 else "Start baseline"
        if baseline and training_plan:
            blocking_reason = "Legacy patient state detected. Complete the baseline or reset the patient test data."
    elif not baseline:
        state = "baseline_ready_to_calculate"
        next_route = "/baseline"
        next_label = "Calculate baseline"
    elif not training_plan:
        state = "training_plan_missing"
        next_route = "/baseline/results"
        next_label = "Generate training plan"
    elif not reference_data["cognitive_tasks_seeded"]:
        state = "system_not_ready"
        next_route = "/training"
        next_label = "Open training"
        blocking_reason = "Training task catalog is missing. Seed the cognitive task reference data."
    elif has_in_progress_session:
        state = "training_in_session"
        next_route = "/training"
        next_label = "Continue session"
    elif progress_unlocked:
        state = "progress_available"
        next_route = "/training"
        next_label = "Continue training"
    else:
        state = "training_ready"
        next_route = "/training"
        next_label = "Start training"

    return {
        "user_exists": True,
        "user_id": user_id,
        "state": state,
        "system_ready": reference_data["cognitive_tasks_seeded"],
        "next_route": next_route,
        "next_label": next_label,
        "blocking_reason": blocking_reason,
        "baseline": {
            "has_assessment": baseline is not None,
            **baseline_status,
        },
        "training": {
            "has_plan": training_plan is not None,
            "plan_id": training_plan.id if training_plan else None,
            "session_number": training_plan.current_session_number if training_plan else None,
            "current_session_tasks_completed": current_session_tasks,
            "current_session_in_progress": has_in_progress_session,
            "training_sessions_count": training_sessions_count,
        },
        "progress": {
            "unlocked": progress_unlocked,
            "training_sessions_count": training_sessions_count,
        },
        "reference_data": reference_data,
    }
