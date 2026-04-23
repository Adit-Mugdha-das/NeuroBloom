from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session, select, desc, col
from pydantic import BaseModel
import json
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from app.models.training_plan import TrainingPlan
from app.models.training_session import TrainingSession
from app.models.baseline_assessment import BaselineAssessment
from app.models.badge import UserBadge, BadgeDefinition
from app.models.user import User
from app.services.badge_service import BadgeService
from app.services.patient_journey import get_real_baseline, get_reference_data_status
from app.services.task_keys import normalize_task_key
from app.services.task_rotation import TaskRotationService
from app.core.config import engine

router = APIRouter()

DEFAULT_SESSION_DURATION_RANGE_MINUTES = (5, 10)
DEV_BASELINE_SCORE = 50.0
DEV_MAX_SESSIONS_PER_DAY = 999
DEV_COOLDOWN_MINUTES = 0

def get_session():
    with Session(engine) as session:
        yield session


def _empty_training_plan_response(message: str):
    return {
        "has_plan": False,
        "message": message,
        "primary_focus": [],
        "secondary_focus": [],
        "maintenance": [],
        "recommended_tasks": {},
        "initial_difficulty": {},
        "current_difficulty": {},
        "total_sessions": 0,
        "last_session": None,
        "session_constraints": None,
        "session_pacing": None,
    }


def _empty_training_metrics(message: str):
    return {
        "has_data": False,
        "message": message,
        "total_sessions": 0,
        "total_tasks": 0,
        "metrics_by_domain": {},
        "current_difficulty": {},
        "recent_sessions": [],
        "last_training_date": None,
    }


def _empty_next_tasks_response(message: str, has_plan: bool = False, system_ready: bool = True):
    return {
        "has_plan": has_plan,
        "system_ready": system_ready,
        "message": message,
        "training_plan_id": None,
        "session_number": 1,
        "tasks": [],
        "total_tasks": 0,
        "completed_tasks": 0,
        "session_complete": False,
        "rotation_info": None,
    }

# Task type mapping for each cognitive domain
DOMAIN_TASK_MAPPING = {
    "working_memory": "n_back",
    "attention": "continuous_performance",
    "flexibility": "task_switching",
    "planning": "tower_of_hanoi",
    "processing_speed": "reaction_time",
    "visual_scanning": "target_search"
}


def _score_to_difficulty(score: float) -> int:
    """Map a domain score onto the default 1-10 training difficulty bands."""
    if score < 50:
        return 2
    if score < 70:
        return 4
    if score < 85:
        return 7
    return 9


def _apply_dev_access_overrides(plan: TrainingPlan) -> None:
    """
    Relax pacing-only constraints for development access.

    This keeps the normal patient-facing backend checks intact while letting the
    dev tool launch tasks repeatedly for QA without cooldowns or daily caps.
    """
    plan.max_sessions_per_day = max(plan.max_sessions_per_day or 0, DEV_MAX_SESSIONS_PER_DAY)
    plan.cooldown_between_sessions_minutes = DEV_COOLDOWN_MINUTES
    plan.last_updated = datetime.utcnow()


def _ensure_dev_training_plan(user_id: int, session: Session) -> TrainingPlan:
    """
    Guarantee that dev-only tooling has an active training plan to work with.

    The public training flow should still require a real baseline. This helper is
    intentionally used only by `/dev/...` endpoints so direct QA access does not
    weaken normal backend rules.
    """
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()

    if plan:
        _apply_dev_access_overrides(plan)
        session.add(plan)
        session.flush()
        return plan

    user = session.exec(
        select(User)
        .where(User.id == user_id)
        .where(User.is_active == True)
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="Active user not found")

    baseline = session.exec(
        select(BaselineAssessment)
        .where(BaselineAssessment.user_id == user_id)
        .order_by(desc(BaselineAssessment.created_at))
    ).first()

    if not baseline:
        baseline = BaselineAssessment(
            user_id=user_id,
            working_memory_score=DEV_BASELINE_SCORE,
            attention_score=DEV_BASELINE_SCORE,
            flexibility_score=DEV_BASELINE_SCORE,
            planning_score=DEV_BASELINE_SCORE,
            processing_speed_score=DEV_BASELINE_SCORE,
            visual_scanning_score=DEV_BASELINE_SCORE,
            overall_score=DEV_BASELINE_SCORE,
            raw_metrics=json.dumps({
                "source": "dev_tools",
                "generated_for": "direct_task_access",
                "note": "Synthetic baseline created automatically so the dev tool can launch training games."
            }),
            is_baseline=False,
            assessment_duration_minutes=0,
        )
        session.add(baseline)
        session.flush()

    domain_scores = {
        "working_memory": baseline.working_memory_score,
        "attention": baseline.attention_score,
        "flexibility": baseline.flexibility_score,
        "planning": baseline.planning_score,
        "processing_speed": baseline.processing_speed_score,
        "visual_scanning": baseline.visual_scanning_score,
    }
    sorted_domains = sorted(domain_scores.items(), key=lambda item: item[1])
    recommended_tasks = {
        domain: DOMAIN_TASK_MAPPING[domain] for domain in domain_scores.keys()
    }
    initial_difficulty = {
        domain: _score_to_difficulty(score) for domain, score in domain_scores.items()
    }

    assert baseline.id is not None

    plan = TrainingPlan(
        user_id=user_id,
        baseline_assessment_id=baseline.id,
        primary_focus=json.dumps([sorted_domains[0][0], sorted_domains[1][0]]),
        secondary_focus=json.dumps([sorted_domains[2][0], sorted_domains[3][0]]),
        maintenance=json.dumps([sorted_domains[4][0], sorted_domains[5][0]]),
        recommended_tasks=json.dumps(recommended_tasks),
        initial_difficulty=json.dumps(initial_difficulty),
        current_difficulty=json.dumps(initial_difficulty),
        is_active=True,
        max_sessions_per_day=DEV_MAX_SESSIONS_PER_DAY,
        cooldown_between_sessions_minutes=DEV_COOLDOWN_MINUTES,
    )
    session.add(plan)
    session.flush()

    return plan


def _session_window_start(day: datetime) -> datetime:
    return day.replace(hour=0, minute=0, second=0, microsecond=0)


def _count_completed_sessions(
    session: Session,
    user_id: int,
    start_at: datetime,
    end_at: datetime,
    tasks_per_session: int
) -> int:
    task_count = len(session.exec(
        select(TrainingSession)
        .where(TrainingSession.user_id == user_id)
        .where(TrainingSession.created_at >= start_at)
        .where(TrainingSession.created_at < end_at)
    ).all())
    return task_count // max(tasks_per_session, 1)


def _build_session_constraints(training_plan: TrainingPlan) -> dict:
    return {
        "max_sessions_per_day": training_plan.max_sessions_per_day,
        "recommended_sessions_per_week": training_plan.recommended_sessions_per_week,
        "tasks_per_session": training_plan.tasks_per_session,
        "recommended_session_length_minutes": {
            "min": training_plan.recommended_session_length_min_minutes,
            "max": training_plan.recommended_session_length_max_minutes,
        },
        "cooldown_between_sessions_minutes": training_plan.cooldown_between_sessions_minutes,
    }


def _build_session_pacing_status(training_plan: TrainingPlan, session: Session, user_id: int) -> dict:
    now = datetime.utcnow()
    tasks_per_session = max(training_plan.tasks_per_session, 1)
    today_start = _session_window_start(now)
    tomorrow_start = today_start + timedelta(days=1)
    week_start = today_start - timedelta(days=today_start.weekday())
    next_week_start = week_start + timedelta(days=7)

    completed_sessions_today = _count_completed_sessions(
        session,
        user_id,
        today_start,
        tomorrow_start,
        tasks_per_session,
    )
    completed_sessions_this_week = _count_completed_sessions(
        session,
        user_id,
        week_start,
        next_week_start,
        tasks_per_session,
    )

    current_session_in_progress = len(training_plan.get_current_session_tasks_completed()) > 0
    latest_task = session.exec(
        select(TrainingSession)
        .where(TrainingSession.user_id == user_id)
        .order_by(desc(TrainingSession.created_at))
    ).first()

    cooldown_remaining_seconds = 0
    next_session_available_at = None
    if latest_task and not current_session_in_progress:
        cooldown_delta = timedelta(minutes=max(training_plan.cooldown_between_sessions_minutes, 0))
        cooldown_remaining = cooldown_delta - (now - latest_task.created_at)
        if cooldown_remaining.total_seconds() > 0:
            cooldown_remaining_seconds = int(cooldown_remaining.total_seconds())
            next_session_available_at = (latest_task.created_at + cooldown_delta).isoformat()

    return {
        "completed_sessions_today": completed_sessions_today,
        "remaining_sessions_today": max(training_plan.max_sessions_per_day - completed_sessions_today, 0),
        "completed_sessions_this_week": completed_sessions_this_week,
        "recommended_sessions_per_week": training_plan.recommended_sessions_per_week,
        "weekly_recommendation_met": completed_sessions_this_week >= training_plan.recommended_sessions_per_week,
        "current_session_in_progress": current_session_in_progress,
        "cooldown_active": cooldown_remaining_seconds > 0,
        "cooldown_remaining_seconds": cooldown_remaining_seconds,
        "next_session_available_at": next_session_available_at,
    }


def enforce_session_limits(training_plan: TrainingPlan, session: Session, user_id: int):
    current_session_tasks = training_plan.get_current_session_tasks_completed()
    if current_session_tasks:
        return

    now = datetime.utcnow()
    tasks_per_session = max(training_plan.tasks_per_session, 1)
    today_start = _session_window_start(now)
    tomorrow_start = today_start + timedelta(days=1)
    completed_sessions_today = _count_completed_sessions(
        session,
        user_id,
        today_start,
        tomorrow_start,
        tasks_per_session,
    )

    if completed_sessions_today >= training_plan.max_sessions_per_day:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Daily training limit reached. You have already completed "
                f"{training_plan.max_sessions_per_day} sessions today."
            ),
        )

    latest_task = session.exec(
        select(TrainingSession)
        .where(TrainingSession.user_id == user_id)
        .order_by(desc(TrainingSession.created_at))
    ).first()

    if not latest_task:
        return

    cooldown_delta = timedelta(minutes=max(training_plan.cooldown_between_sessions_minutes, 0))
    elapsed = now - latest_task.created_at
    if elapsed < cooldown_delta:
        remaining_seconds = int((cooldown_delta - elapsed).total_seconds())
        remaining_minutes = max(1, (remaining_seconds + 59) // 60)
        raise HTTPException(
            status_code=429,
            detail=(
                f"Cooldown active. Please wait about {remaining_minutes} more minute(s) "
                f"before starting another session."
            ),
        )

@router.post("/training-plan/generate/{user_id}")
def generate_training_plan(user_id: int, session: Session = Depends(get_session)):
    """
    Generate personalized training plan from user's baseline assessment.
    
    Algorithm:
    1. Get latest baseline assessment
    2. Rank domains by score (low to high)
    3. Assign 2 weakest → primary focus
    4. Assign 2 middle → secondary focus
    5. Assign 2 strongest → maintenance
    6. Calculate initial difficulty based on baseline scores
    """
    
    # Get latest real baseline assessment
    baseline = get_real_baseline(session, user_id)

    if not baseline or baseline.id is None:
        raise HTTPException(status_code=400, detail="Calculate a real baseline assessment before generating a training plan.")
    
    # Type guard: baseline is confirmed non-null after this point
    
    # Deactivate any existing active plans
    existing_plans = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).all()
    
    for plan in existing_plans:
        plan.is_active = False
        session.add(plan)
    
    # Collect domain scores
    domains = {
        "working_memory": baseline.working_memory_score,
        "attention": baseline.attention_score,
        "flexibility": baseline.flexibility_score,
        "planning": baseline.planning_score,
        "processing_speed": baseline.processing_speed_score,
        "visual_scanning": baseline.visual_scanning_score
    }
    
    # Sort domains by score (weakest first)
    sorted_domains = sorted(domains.items(), key=lambda x: x[1])
    
    # Categorize domains
    primary_focus = [sorted_domains[0][0], sorted_domains[1][0]]  # 2 weakest
    secondary_focus = [sorted_domains[2][0], sorted_domains[3][0]]  # 2 middle
    maintenance = [sorted_domains[4][0], sorted_domains[5][0]]  # 2 strongest
    
    # Map tasks to domains
    recommended_tasks = {
        domain: DOMAIN_TASK_MAPPING[domain] for domain in domains.keys()
    }
    
    # Calculate initial difficulty based on baseline score
    # Score < 50 → difficulty 1-2
    # Score 50-70 → difficulty 3-5
    # Score 70-85 → difficulty 6-8
    # Score > 85 → difficulty 9-10
    initial_difficulty = {
        domain: _score_to_difficulty(score) for domain, score in domains.items()
    }
    
    # Create new training plan
    training_plan = TrainingPlan(
        user_id=user_id,
        baseline_assessment_id=baseline.id,
        primary_focus=json.dumps(primary_focus),
        secondary_focus=json.dumps(secondary_focus),
        maintenance=json.dumps(maintenance),
        recommended_tasks=json.dumps(recommended_tasks),
        initial_difficulty=json.dumps(initial_difficulty),
        current_difficulty=json.dumps(initial_difficulty),  # Start with initial
        is_active=True
    )
    
    session.add(training_plan)
    session.commit()
    session.refresh(training_plan)
    
    return {
        "id": training_plan.id,
        "user_id": user_id,
        "baseline_id": baseline.id,
        "primary_focus": primary_focus,
        "secondary_focus": secondary_focus,
        "maintenance": maintenance,
        "recommended_tasks": recommended_tasks,
        "initial_difficulty": initial_difficulty,
        "current_difficulty": initial_difficulty,
        "domain_scores": domains,
        "created_at": training_plan.created_at.isoformat(),
        "session_constraints": _build_session_constraints(training_plan),
        "session_pacing": {
            "completed_sessions_today": 0,
            "remaining_sessions_today": training_plan.max_sessions_per_day,
            "completed_sessions_this_week": 0,
            "recommended_sessions_per_week": training_plan.recommended_sessions_per_week,
            "weekly_recommendation_met": False,
            "current_session_in_progress": False,
            "cooldown_active": False,
            "cooldown_remaining_seconds": 0,
            "next_session_available_at": None,
        },
    }

@router.get("/training-plan/{user_id}")
def get_training_plan(user_id: int, session: Session = Depends(get_session)):
    """Get active training plan for user"""
    
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
        .order_by(desc(TrainingPlan.created_at))
    ).first()
    
    if not plan:
        return _empty_training_plan_response("No active training plan found yet.")

    session_pacing = _build_session_pacing_status(plan, session, user_id)
    
    return {
        "has_plan": True,
        "message": "Training plan available.",
        "id": plan.id,
        "user_id": plan.user_id,
        "baseline_id": plan.baseline_assessment_id,
        "primary_focus": plan.get_primary_focus(),
        "secondary_focus": plan.get_secondary_focus(),
        "maintenance": plan.get_maintenance(),
        "recommended_tasks": plan.get_recommended_tasks(),
        "initial_difficulty": plan.get_initial_difficulty(),
        "current_difficulty": plan.get_current_difficulty(),
        "total_sessions": plan.total_sessions_completed,
        "last_session": plan.last_session_date.isoformat() if plan.last_session_date else None,
        "created_at": plan.created_at.isoformat(),
        "session_constraints": _build_session_constraints(plan),
        "session_pacing": session_pacing,
    }

@router.get("/training-plan/{user_id}/streak")
def get_streak_info(user_id: int, session: Session = Depends(get_session)):
    """
    Get streak and consistency statistics.
    
    Returns:
    - current_streak: consecutive days trained
    - longest_streak: personal best record
    - total_training_days: lifetime training days
    - streak_freeze_available: whether freeze is available
    - days_until_streak_break: how many days until streak is broken
    - streak_percentage: current/longest as percentage
    """
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        return {
            "has_plan": False,
            "message": "No active training plan",
            "current_streak": 0,
            "longest_streak": 0,
            "total_training_days": 0,
            "streak_freeze_available": True,
            "days_until_streak_break": 0,
            "streak_percentage": 0,
            "last_session_date": None,
            "last_streak_reset": None,
        }
    
    # Calculate days until streak breaks
    if plan.last_session_date:
        days_since_last = (datetime.utcnow().date() - plan.last_session_date.date()).days
        if plan.streak_freeze_available:
            days_until_break = 2 - days_since_last  # 2 days grace with freeze
        else:
            days_until_break = 1 - days_since_last  # 1 day without freeze
        days_until_break = max(0, days_until_break)
    else:
        days_until_break = 0
    
    # Calculate streak percentage
    streak_percentage = 0
    if plan.longest_streak > 0:
        streak_percentage = (plan.current_streak / plan.longest_streak) * 100
    
    return {
        "has_plan": True,
        "message": "Streak information available.",
        "current_streak": plan.current_streak,
        "longest_streak": plan.longest_streak,
        "total_training_days": plan.total_training_days,
        "streak_freeze_available": plan.streak_freeze_available,
        "days_until_streak_break": days_until_break,
        "streak_percentage": round(streak_percentage, 1),
        "last_session_date": plan.last_session_date.isoformat() if plan.last_session_date else None,
        "last_streak_reset": plan.last_streak_reset.isoformat() if plan.last_streak_reset else None
    }

@router.get("/training-plan/{user_id}/next-tasks")
def get_next_training_tasks(user_id: int, session: Session = Depends(get_session)):
    """
    Get recommended tasks for current training session with smart rotation.
    
    Returns 4 tasks with completion status:
    - 2 from primary focus (weakest domains)
    - 2 from secondary focus (middle domains)
    
    Uses TaskRotationService to select varied tasks and prevent repetition.
    Session only advances after all 4 tasks are completed.
    """
    
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        return _empty_next_tasks_response("No active training plan. Generate one first.")

    reference_data = get_reference_data_status(session)
    if not reference_data["cognitive_tasks_seeded"]:
        return _empty_next_tasks_response(
            "Training task catalog is missing. Seed the cognitive task reference data.",
            has_plan=True,
            system_ready=False,
        )
    
    primary = plan.get_primary_focus()
    secondary = plan.get_secondary_focus()
    difficulty = plan.get_current_difficulty()
    completed_tasks = plan.get_current_session_tasks_completed()
    
    # Initialize task rotation service
    rotation_service = TaskRotationService(session)
    
    # Build session task list with smart rotation
    next_tasks = []
    task_index = 0
    
    # Add 2 primary focus tasks (with smart rotation)
    for domain in primary:
        # Use rotation service to select varied task for this domain
        selected_task = rotation_service.select_task_for_session(user_id, domain, is_baseline=False)
        
        if selected_task:
            # Create unique task identifier: domain_taskindex
            task_id = f"{domain}_{task_index}"
            task_key = normalize_task_key(selected_task.task_code)
            next_tasks.append({
                "domain": domain,
                "task_id": task_id,  # Unique identifier for this specific task slot
                "task_type": task_key,
                "task_key": task_key,
                "task_name": selected_task.task_name,  # e.g., 'Digit Span Test'
                "task_description": selected_task.description,
                "difficulty": difficulty.get(domain, 5),
                "priority": "primary",
                "focus_reason_key": "weakest_area",
                "focus_reason": "Weakest area - needs most attention",
                "completed": task_id in completed_tasks,
                "requires_audio": selected_task.requires_audio,
                "estimated_duration": selected_task.estimated_duration_seconds
            })
            task_index += 1
    
    # Add 2 secondary focus tasks (with smart rotation)
    for domain in secondary:
        selected_task = rotation_service.select_task_for_session(user_id, domain, is_baseline=False)
        
        if selected_task:
            # Create unique task identifier: domain_taskindex
            task_id = f"{domain}_{task_index}"
            task_key = normalize_task_key(selected_task.task_code)
            next_tasks.append({
                "domain": domain,
                "task_id": task_id,  # Unique identifier for this specific task slot
                "task_type": task_key,
                "task_key": task_key,
                "task_name": selected_task.task_name,
                "task_description": selected_task.description,
                "difficulty": difficulty.get(domain, 5),
                "priority": "secondary",
                "focus_reason_key": "growth_area",
                "focus_reason": "Moderate area - room for improvement",
                "completed": task_id in completed_tasks,
                "requires_audio": selected_task.requires_audio,
                "estimated_duration": selected_task.estimated_duration_seconds
            })
            task_index += 1
    
    # Check if session is complete
    all_completed = len(completed_tasks) >= 4
    
    return {
        "has_plan": True,
        "system_ready": True,
        "message": "Recommended tasks available.",
        "training_plan_id": plan.id,
        "session_number": plan.current_session_number,
        "tasks": next_tasks,
        "total_tasks": len(next_tasks),
        "completed_tasks": len(completed_tasks),
        "session_complete": all_completed,
        "rotation_info": "Tasks selected using smart rotation to prevent repetition"
    }

@router.post("/training-session/submit")
def submit_training_session(
    user_id: int,
    training_plan_id: int,
    domain: str,
    task_type: str,
    task_code: Optional[str] = None,  # NEW: Specific task variant (e.g., 'digit_span', 'sdmt')
    task_id: Optional[str] = None,  # NEW: Unique task identifier (e.g., 'working_memory_0')
    score: float = 0,
    accuracy: float = 0,
    average_reaction_time: float = 0,
    consistency: float = 0,
    errors: int = 0,
    duration: int = 0,
    raw_data: dict = {},
    session: Session = Depends(get_session)
):
    """
    Submit results from a training session and apply adaptive difficulty.
    
    Now supports task_code for tracking specific task variants.
    
    Adaptive Algorithm:
    - If accuracy >= 85% → increase difficulty by 1
    - If accuracy < 65% → decrease difficulty by 1
    - Otherwise → keep same difficulty
    
    Difficulty is clamped between 1-10.
    """
    
    print(f"\n╔══════════════════════════════════════════════════════════╗")
    print(f"║  TRAINING SESSION SUBMISSION RECEIVED                   ║")
    print(f"╠══════════════════════════════════════════════════════════╣")
    print(f"  User ID: {user_id}")
    print(f"  Plan ID: {training_plan_id}")
    print(f"  Domain: {domain}")
    print(f"  Task Code: {task_code or task_type}")
    print(f"  Score: {score}%")
    print(f"  Accuracy: {accuracy}%")
    print(f"╚══════════════════════════════════════════════════════════╝\n")
    
    # Get training plan
    plan = session.exec(
        select(TrainingPlan).where(TrainingPlan.id == training_plan_id)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Training plan not found")
    
    # Get current difficulty for this domain
    current_difficulty_map = plan.get_current_difficulty()
    current_difficulty = current_difficulty_map.get(domain, 5)
    
    # Use task_code if provided, otherwise fall back to task_type
    final_task_code = normalize_task_key(task_code if task_code else task_type)
    
    # Create training session record (store current difficulty, will update after full session)
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=training_plan_id,
        domain=domain,
        task_type=task_type,
        task_code=final_task_code,  # Store specific task variant
        score=score,
        accuracy=accuracy,
        average_reaction_time=average_reaction_time,
        consistency=consistency,
        errors=errors,
        difficulty_level=current_difficulty,  # Current difficulty for this task
        difficulty_before=current_difficulty,
        difficulty_after=current_difficulty,  # Will be updated after session completes
        duration=duration,
        raw_data=json.dumps(raw_data),
        adaptation_reason="Task completed - difficulty will be adjusted after full session"
    )
    
    session.add(training_session)
    
    # Mark this task as completed in current session
    # Use task_id if provided (new system), otherwise use domain (backward compatibility)
    completed_tasks = plan.get_current_session_tasks_completed()
    task_identifier = task_id if task_id else domain
    if task_identifier not in completed_tasks:
        completed_tasks.append(task_identifier)
        plan.current_session_tasks_completed = json.dumps(completed_tasks)
        session.add(plan)  # Mark plan as modified immediately
    
    # Check if all 4 tasks in session are completed
    required_tasks = max(plan.tasks_per_session, 1)
    session_complete = len(completed_tasks) >= required_tasks
    newly_earned_badges = []
    
    print(f"[DEBUG] Task completed: {task_identifier}, Completed tasks: {completed_tasks}, Session complete: {session_complete}")
    
    if session_complete:
        print(f"[DEBUG] SESSION COMPLETE! Adjusting difficulty for all domains...")
        
        # NOW adjust difficulty for ALL domains based on their performance in this session
        # Get all tasks from this session
        session_tasks = session.exec(
            select(TrainingSession)
            .where(TrainingSession.user_id == user_id)
            .where(TrainingSession.training_plan_id == training_plan_id)
            .order_by(desc(TrainingSession.created_at))
            .limit(4)  # Get the 4 most recent tasks (this session)
        ).all()
        
        # Apply adaptive difficulty logic for each domain
        for task in session_tasks:
            task_domain = task.domain
            task_accuracy = task.accuracy
            task_current_diff = current_difficulty_map.get(task_domain, 5)
            
            # Determine new difficulty
            new_difficulty = task_current_diff
            adaptation_reason = "Maintained difficulty"
            
            if task_accuracy >= 85:
                new_difficulty = min(task_current_diff + 1, 10)
                adaptation_reason = f"Increased difficulty (accuracy {task_accuracy:.1f}% >= 85%)"
            elif task_accuracy < 65:
                new_difficulty = max(task_current_diff - 1, 1)
                adaptation_reason = f"Decreased difficulty (accuracy {task_accuracy:.1f}% < 65%)"
            else:
                adaptation_reason = f"Maintained difficulty (accuracy {task_accuracy:.1f}% in 65-85% range)"
            
            # Update difficulty map
            current_difficulty_map[task_domain] = new_difficulty
            
            # Update the task record with new difficulty
            task.difficulty_after = new_difficulty
            task.adaptation_reason = adaptation_reason
            session.add(task)
            
            print(f"[DEBUG] {task_domain}: {task_current_diff} -> {new_difficulty} ({adaptation_reason})")
        
        # Save updated difficulty map to plan
        plan.current_difficulty = json.dumps(current_difficulty_map)
        
        # Session is complete - increment total sessions completed and reset current session
        plan.total_sessions_completed += 1
        plan.current_session_tasks_completed = "[]"  # Reset for next session
        # Note: current_session_number stays the same - it represents which session you're on (e.g., always "1" for ongoing training)
        
        # Update streak tracking
        update_streak(plan)
        print(f"[DEBUG] Streak updated! Current: {plan.current_streak}, Longest: {plan.longest_streak}")
        
        # Check for new badges
        newly_earned_badges = BadgeService.check_and_award_badges(session, user_id, plan)
        if newly_earned_badges:
            print(f"[DEBUG] New badges earned: {newly_earned_badges}")
        
        # Check if we should rebalance focus areas (every 4 sessions)
        if plan.total_sessions_completed % 4 == 0:
            rebalance_focus_areas(plan, session)
    
    plan.last_updated = datetime.utcnow()
    
    # Explicitly mark plan as modified
    session.add(plan)
    session.flush()  # Flush changes before commit
    session.commit()
    session.refresh(training_session)
    session.refresh(plan)
    
    # Get badge details for newly earned badges
    badge_details = []
    for badge_id in newly_earned_badges:
        badge_def = BadgeDefinition.get_badge(badge_id)
        if badge_def:
            badge_details.append({
                "id": badge_id,
                "badge_id": badge_id,
                "name": badge_def["name"],
                "description": badge_def["description"],
                "icon": badge_def["icon"]
            })
    
    # Get final difficulty after session completion (if complete)
    final_difficulty = current_difficulty
    final_adaptation_reason = "Task completed - difficulty will be adjusted after full session"
    
    if session_complete:
        # Get updated difficulty from the refreshed plan
        updated_difficulty_map = plan.get_current_difficulty()
        final_difficulty = updated_difficulty_map.get(domain, current_difficulty)
        final_adaptation_reason = training_session.adaptation_reason
    
    return {
        "id": training_session.id,
        "domain": domain,
        "score": score,
        "accuracy": accuracy,
        "difficulty_before": current_difficulty,
        "difficulty_after": final_difficulty,
        "adaptation_reason": final_adaptation_reason,
        "session_complete": session_complete,
        "completed_tasks": len(completed_tasks),
        "total_tasks": 4,
        "current_session_number": plan.current_session_number,
        "newly_earned_badges": badge_details,
        "created_at": training_session.created_at.isoformat()
    }

@router.get("/training-session/history/{user_id}")
def get_training_history(
    user_id: int, 
    limit: int = 50,
    session: Session = Depends(get_session)
):
    """Get training session history for a user"""
    
    sessions = session.exec(
        select(TrainingSession)
        .where(TrainingSession.user_id == user_id)
        .order_by(desc(TrainingSession.created_at))
        .limit(limit)
    ).all()
    
    return [
        {
            "id": s.id,
            "domain": s.domain,
            "task_type": s.task_type,
            "score": s.score,
            "accuracy": s.accuracy,
            "difficulty": s.difficulty_level,
            "difficulty_before": s.difficulty_before,
            "difficulty_after": s.difficulty_after,
            "adaptation_reason": s.adaptation_reason,
            "errors": s.errors,
            "duration": s.duration,
            "created_at": s.created_at.isoformat()
        }
        for s in sessions
    ]

@router.get("/training-session/metrics/{user_id}")
def get_performance_metrics(user_id: int, session: Session = Depends(get_session)):
    """
    Get comprehensive performance metrics for a user.
    
    Returns:
    - Total sessions completed
    - Average scores per domain
    - Current difficulty levels per domain
    - Recent performance trends
    - Improvement rate
    """
    
    # Get active training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        return _empty_training_metrics("No active training plan found.")
    
    # Get all training sessions
    all_sessions = session.exec(
        select(TrainingSession).where(TrainingSession.user_id == user_id)
    ).all()
    
    if not all_sessions:
        return {
            "has_data": False,
            "message": "Training plan exists, but no training sessions have been completed yet.",
            "total_sessions": 0,
            "total_tasks": 0,
            "metrics_by_domain": {},
            "current_difficulty": plan.get_current_difficulty(),
            "recent_sessions": [],
            "last_training_date": None,
        }
    
    # Calculate metrics per domain
    metrics_by_domain = {}
    domain_sessions = {}
    
    for s in all_sessions:
        if s.domain not in domain_sessions:
            domain_sessions[s.domain] = []
        domain_sessions[s.domain].append(s)
    
    for domain, sessions_list in domain_sessions.items():
        scores = [s.score for s in sessions_list]
        accuracies = [s.accuracy for s in sessions_list]
        
        # Calculate improvement (compare last 5 vs first 5 sessions)
        improvement = 0
        if len(sessions_list) >= 10:
            early_avg = sum(scores[:5]) / 5
            recent_avg = sum(scores[-5:]) / 5
            improvement = recent_avg - early_avg
        
        metrics_by_domain[domain] = {
            "total_sessions": len(sessions_list),
            "average_score": sum(scores) / len(scores),
            "average_accuracy": sum(accuracies) / len(accuracies),
            "current_difficulty": sessions_list[-1].difficulty_level,
            "improvement": improvement,
            "trend": "improving" if improvement > 5 else "stable" if improvement > -5 else "declining"
        }
    
    # Recent sessions (last 10)
    recent = sorted(all_sessions, key=lambda x: x.created_at, reverse=True)[:10]
    recent_sessions = [
        {
            "domain": s.domain,
            "score": s.score,
            "accuracy": s.accuracy,
            "difficulty": s.difficulty_level,
            "date": s.created_at.strftime("%Y-%m-%d")
        }
        for s in recent
    ]
    
    return {
        "has_data": True,
        "message": "Performance metrics available.",
        "total_sessions": plan.total_sessions_completed,  # Use completed sessions count from plan (4 tasks = 1 session)
        "total_tasks": len(all_sessions),  # Total individual tasks completed
        "metrics_by_domain": metrics_by_domain,
        "current_difficulty": plan.get_current_difficulty(),
        "recent_sessions": recent_sessions,
        "last_training_date": plan.last_session_date.isoformat() if plan.last_session_date else None
    }

def update_streak(plan: TrainingPlan):
    """
    Update streak tracking when a session is completed.
    
    Logic:
    - If trained today already: no change
    - If trained yesterday: increment current_streak
    - If missed 1 day + freeze available: use freeze, maintain streak
    - If missed 2+ days or no freeze: reset streak to 1
    - Update longest_streak if current exceeds it
    """
    now = datetime.utcnow()
    today = now.date()
    
    # First session ever
    if plan.last_session_date is None:
        plan.current_streak = 1
        plan.longest_streak = 1
        plan.total_training_days = 1
        plan.last_session_date = now
        return
    
    last_session_date = plan.last_session_date.date()
    days_since_last = (today - last_session_date).days
    
    # Already trained today - update last_session_date but no streak change
    if days_since_last == 0:
        plan.last_session_date = now  # Update to latest session time
        return
    
    # Trained yesterday - increment streak
    if days_since_last == 1:
        plan.current_streak += 1
        plan.total_training_days += 1
        # Don't reset freeze - it should only reset weekly or when broken
        
    # Missed exactly 1 day - check if freeze available
    elif days_since_last == 2 and plan.streak_freeze_available:
        plan.current_streak += 1  # Maintain streak with freeze
        plan.total_training_days += 1
        plan.streak_freeze_available = False  # Use up the freeze
        
    # Missed 2+ days or no freeze - reset streak
    else:
        plan.current_streak = 1
        plan.total_training_days += 1
        plan.streak_freeze_available = True  # Get a new freeze when streak breaks
        plan.last_streak_reset = now
    
    # Update longest streak if current is higher
    if plan.current_streak > plan.longest_streak:
        plan.longest_streak = plan.current_streak
    
    plan.last_session_date = now

def rebalance_focus_areas(plan: TrainingPlan, db_session: Session):
    """
    Rebalance focus areas based on recent training performance.
    Called every 4 sessions to update primary/secondary/maintenance focus.
    """
    # Get recent training sessions (last 12 sessions = 3 full cycles of 4)
    recent_sessions = db_session.exec(
        select(TrainingSession)
        .where(TrainingSession.training_plan_id == plan.id)
        .order_by(desc(TrainingSession.created_at))
        .limit(12)
    ).all()
    
    if not recent_sessions:
        return  # No sessions yet, keep current focus
    
    # Calculate average score per domain from recent sessions
    domain_scores = {}
    domain_counts = {}
    
    for ts in recent_sessions:
        if ts.domain not in domain_scores:
            domain_scores[ts.domain] = 0
            domain_counts[ts.domain] = 0
        domain_scores[ts.domain] += ts.score
        domain_counts[ts.domain] += 1
    
    # Calculate averages
    domain_averages = {
        domain: domain_scores[domain] / domain_counts[domain]
        for domain in domain_scores.keys()
    }
    
    # Sort domains by current performance (weakest first)
    sorted_domains = sorted(domain_averages.items(), key=lambda x: x[1])
    
    # Update focus areas based on current performance
    if len(sorted_domains) >= 6:
        new_primary = [sorted_domains[0][0], sorted_domains[1][0]]
        new_secondary = [sorted_domains[2][0], sorted_domains[3][0]]
        new_maintenance = [sorted_domains[4][0], sorted_domains[5][0]]
    elif len(sorted_domains) >= 4:
        new_primary = [sorted_domains[0][0], sorted_domains[1][0]]
        new_secondary = [sorted_domains[2][0], sorted_domains[3][0]]
        new_maintenance = []
    else:
        return  # Not enough data, keep current focus
    
    # Update the plan
    plan.primary_focus = json.dumps(new_primary)
    plan.secondary_focus = json.dumps(new_secondary)
    plan.maintenance = json.dumps(new_maintenance)
    
    db_session.add(plan)

@router.get("/training-session/performance-comparison/{user_id}")
def get_performance_comparison(user_id: int, session: Session = Depends(get_session)):
    """
    Compare baseline scores vs current training performance.
    Shows improvement/decline per domain.
    """
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        return {
            "has_data": False,
            "message": "No active training plan.",
            "comparison": {},
            "total_sessions_completed": 0,
            "baseline_date": None,
            "last_training_date": None,
        }
    
    # Get baseline scores
    baseline = session.exec(
        select(BaselineAssessment)
        .where(BaselineAssessment.id == plan.baseline_assessment_id)
    ).first()
    
    if not baseline:
        return {
            "has_data": False,
            "message": "No baseline assessment found for the active training plan.",
            "comparison": {},
            "total_sessions_completed": plan.total_sessions_completed,
            "baseline_date": None,
            "last_training_date": plan.last_session_date.isoformat() if plan.last_session_date else None,
        }
    
    baseline_scores = {
        "working_memory": baseline.working_memory_score,
        "attention": baseline.attention_score,
        "flexibility": baseline.flexibility_score,
        "planning": baseline.planning_score,
        "processing_speed": baseline.processing_speed_score,
        "visual_scanning": baseline.visual_scanning_score
    }
    
    # Get all training sessions
    all_sessions = session.exec(
        select(TrainingSession)
        .where(TrainingSession.training_plan_id == plan.id)
        .order_by(desc(TrainingSession.created_at))
    ).all()
    
    # Calculate current average scores per domain
    domain_scores = {}
    domain_counts = {}
    
    for ts in all_sessions:
        if ts.domain not in domain_scores:
            domain_scores[ts.domain] = 0
            domain_counts[ts.domain] = 0
        domain_scores[ts.domain] += ts.score
        domain_counts[ts.domain] += 1
    
    current_scores = {
        domain: domain_scores[domain] / domain_counts[domain]
        for domain in domain_scores.keys()
    }
    
    # Calculate improvement
    comparison = {}
    for domain in baseline_scores.keys():
        baseline_score = baseline_scores[domain]
        current_score = current_scores.get(domain, baseline_score)
        improvement = current_score - baseline_score
        improvement_pct = (improvement / baseline_score * 100) if baseline_score > 0 else 0
        
        comparison[domain] = {
            "baseline": baseline_score,
            "current": current_score,
            "improvement": improvement,
            "improvement_percentage": improvement_pct,
            "sessions_completed": domain_counts.get(domain, 0)
        }
    
    return {
        "has_data": True,
        "message": "Performance comparison available.",
        "user_id": user_id,
        "total_sessions_completed": plan.total_sessions_completed,
        "baseline_date": baseline.created_at.isoformat(),
        "last_training_date": plan.last_session_date.isoformat() if plan.last_session_date else None,
        "comparison": comparison
    }

# ============================================================================
# HELPER FUNCTION FOR SESSION TRACKING
# ============================================================================

def track_session_completion(
    training_plan: TrainingPlan,
    domain: str,
    session: Session,
    user_id: int,
    task_id: Optional[str] = None
) -> dict:
    """
    Helper function to track session completion across all tasks.
    Returns session completion info to be included in task response.
    
    Args:
        training_plan: The user's training plan
        domain: The cognitive domain just completed
        session: Database session
        user_id: User ID for badge checking
        task_id: Unique identifier for this specific task instance (e.g., "processing_speed_0")
        
    Returns:
        dict with session_complete, completed_tasks, total_tasks
    """
    # Mark this task as completed in current session
    # If task_id provided, use it for tracking (supports multiple tasks from same domain)
    # Otherwise fall back to domain tracking (backward compatibility)
    completed_tasks = training_plan.get_current_session_tasks_completed()
    task_identifier = task_id if task_id else domain
    if task_identifier not in completed_tasks:
        completed_tasks.append(task_identifier)
        training_plan.current_session_tasks_completed = json.dumps(completed_tasks)
        session.add(training_plan)  # Mark plan as modified
    
    # Check if all tasks in session are completed
    required_tasks = max(training_plan.tasks_per_session, 1)
    session_complete = len(completed_tasks) >= required_tasks
    newly_earned_badges = []
    
    if session_complete:
        # Session is complete - increment total sessions completed and reset
        training_plan.total_sessions_completed += 1
        training_plan.current_session_tasks_completed = "[]"  # Reset for next session
        training_plan.last_session_date = datetime.utcnow()
        
        # Update streak tracking
        update_streak(training_plan)
        
        # Check for badge awards
        newly_earned_badges = BadgeService.check_and_award_badges(session, user_id, training_plan)
    
    return {
        "session_complete": session_complete,
        "completed_tasks": len(completed_tasks),
        "total_tasks": required_tasks,
        "newly_earned_badges": newly_earned_badges
    }

# ============================================================================
# TASK-SPECIFIC ENDPOINTS - Individual task implementations
# ============================================================================

@router.post("/tasks/digit-span/generate/{user_id}")
def generate_digit_span_session(
    user_id: int,
    difficulty: int = 5,
    num_trials: int = 8,
    session: Session = Depends(get_session)
):
    """
    Generate Digit Span task session
    
    Returns sequence of trials for the user to complete
    """
    from app.services.digit_span_task import DigitSpanTask
    
    # Validate difficulty
    if not 1 <= difficulty <= 10:
        raise HTTPException(status_code=400, detail="Difficulty must be between 1 and 10")
    
    # Get user's training plan to verify they exist
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan found")
    
    # Generate trials
    trials = DigitSpanTask.generate_session(difficulty, num_trials)
    
    return {
        "task_code": "digit_span",
        "domain": "working_memory",
        "difficulty": difficulty,
        "num_trials": num_trials,
        "trials": trials,
        "instructions": {
            "title": "Digit Span Test",
            "description": "Remember and repeat sequences of digits",
            "forward": "Type the digits in the same order you see them",
            "backward": "Type the digits in REVERSE order",
            "tips": [
                "Take your time to remember the sequence",
                "Use memory strategies that work for you",
                "Don't worry if you make mistakes - that's how we find the right difficulty"
            ]
        }
    }

@router.post("/tasks/digit-span/submit/{user_id}")
def submit_digit_span_session(
    user_id: int,
    session_data: dict,
    session: Session = Depends(get_session)
):
    """
    Submit completed Digit Span session and save results
    
    Expected session_data:
    {
        "difficulty": 5,
        "trials": [
            {
                "sequence": [3, 7, 2, 9],
                "span_type": "forward",
                "length": 4,
                "user_response": [3, 7, 2, 9],
                "reaction_time": 3500
            },
            ...
        ]
    }
    """
    from app.services.digit_span_task import DigitSpanTask
    from app.services.badge_service import BadgeService
    
    # Get training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan or plan.id is None:
        raise HTTPException(status_code=404, detail="No active training plan found")

    enforce_session_limits(plan, session, user_id)
    
    # Extract task_id for session tracking
    task_id = session_data.get("task_id")
    print(f"[DIGIT SPAN DEBUG] Received task_id: {task_id}")
    print(f"[DIGIT SPAN DEBUG] Full session_data keys: {session_data.keys()}")
    
    # Score each trial
    trials = session_data.get('trials', [])
    scored_trials = []
    
    for trial in trials:
        score_result = DigitSpanTask.score_response(
            trial['sequence'],
            trial.get('user_response', []),
            trial['span_type']
        )
        
        scored_trial = {**trial, **score_result}
        scored_trials.append(scored_trial)
    
    # Calculate session metrics
    metrics = DigitSpanTask.calculate_session_metrics(scored_trials)
    avg_rt = DigitSpanTask.calculate_average_reaction_time(scored_trials)
    
    # Determine difficulty adaptation
    difficulty = session_data.get('difficulty', 5)
    accuracy = metrics['accuracy']
    
    if accuracy >= 85:
        new_difficulty = min(difficulty + 1, 10)
        adaptation_reason = f"Increased difficulty (accuracy {accuracy:.1f}% >= 85%)"
    elif accuracy < 65:
        new_difficulty = max(difficulty - 1, 1)
        adaptation_reason = f"Decreased difficulty (accuracy {accuracy:.1f}% < 65%)"
    else:
        new_difficulty = difficulty
        adaptation_reason = f"Maintained difficulty (accuracy {accuracy:.1f}% in 65-85% range)"
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="working_memory",
        task_type="digit_span",  # Legacy field
        task_code="digit_span",  # NEW: Specific task variant
        score=metrics['score'],
        accuracy=metrics['accuracy'],
        average_reaction_time=avg_rt,
        consistency=metrics['consistency'],
        errors=metrics['total_trials'] - metrics['correct_count'],
        difficulty_level=new_difficulty,
        difficulty_before=difficulty,
        difficulty_after=new_difficulty,
        duration=sum(t.get('reaction_time', 0) for t in scored_trials) // 1000,  # Convert ms to seconds
        raw_data=json.dumps({
            'trials': scored_trials,
            'metrics': metrics
        }),
        adaptation_reason=adaptation_reason,
        completed=True
    )
    
    session.add(training_session)
    
    # Update training plan's current difficulty for working_memory
    current_difficulty = json.loads(plan.current_difficulty)
    current_difficulty['working_memory'] = new_difficulty
    plan.current_difficulty = json.dumps(current_difficulty)
    plan.last_updated = datetime.utcnow()
    
    session.add(plan)
    
    # Track session completion BEFORE commit
    session_info = track_session_completion(plan, "working_memory", session, user_id, task_id)
    
    # Now commit all changes including the completion tracking
    session.commit()
    session.refresh(training_session)
    session.refresh(plan)
    
    return {
        "success": True,
        "session_id": training_session.id,
        "metrics": metrics,
        "difficulty_before": difficulty,
        "difficulty_after": new_difficulty,
        "adaptation_reason": adaptation_reason,
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"],
        "performance_summary": {
            "score": metrics['score'],
            "accuracy": metrics['accuracy'],
            "longest_span": metrics['longest_span'],
            "forward_accuracy": metrics['forward_accuracy'],
            "backward_accuracy": metrics['backward_accuracy']
        }
    }

@router.post("/tasks/spatial-span/generate/{user_id}")
def generate_spatial_span_session(
    user_id: int, 
    difficulty: int = 5,
    num_trials: int = 8,
    session: Session = Depends(get_session)
):
    """
    Generate Spatial Span (Corsi Block) task session
    
    Returns sequence of trials for the user to complete
    """
    from app.services.spatial_span_task import SpatialSpanTask
    
    # Validate difficulty
    if not 1 <= difficulty <= 10:
        raise HTTPException(status_code=400, detail="Difficulty must be between 1 and 10")
    
    # Get user's training plan to verify they exist
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan found")
    
    # Generate trials
    trials = SpatialSpanTask.generate_session(difficulty, num_trials)
    
    return {
        "task_code": "spatial_span",
        "domain": "working_memory",
        "difficulty": difficulty,
        "num_trials": num_trials,
        "trials": trials,
        "instructions": {
            "title": "Spatial Span Test (Corsi Blocks)",
            "description": "Remember the sequence of highlighted blocks",
            "forward": "Click the blocks in the same order they lit up",
            "backward": "Click the blocks in REVERSE order",
            "tips": [
                "Focus on the spatial pattern, not individual positions",
                "Use visual imagery to remember the path",
                "Practice makes perfect - your brain will adapt"
            ]
        }
    }

@router.post("/tasks/spatial-span/submit/{user_id}")
def submit_spatial_span_session(
    user_id: int,
    session_data: dict,
    session: Session = Depends(get_session)
):
    """
    Submit completed Spatial Span session and save results
    
    Expected session_data:
    {
        "difficulty": 5,
        "trials": [
            {
                "sequence": [0, 4, 7],
                "grid_size": 3,
                "span_type": "forward",
                "length": 3,
                "user_response": [0, 4, 7],
                "reaction_time": 4500
            },
            ...
        ]
    }
    """
    from app.services.spatial_span_task import SpatialSpanTask
    from app.services.badge_service import BadgeService
    
    # Get training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan or plan.id is None:
        raise HTTPException(status_code=404, detail="No active training plan found")

    enforce_session_limits(plan, session, user_id)
    
    # Extract task_id for session tracking
    task_id = session_data.get("task_id")
    
    # Score each trial — pass reaction_time and par_ms for speed bonus
    trials = session_data.get('trials', [])
    scored_trials = []

    for trial in trials:
        score_result = SpatialSpanTask.score_response(
            trial['sequence'],
            trial.get('user_response', []),
            trial['span_type'],
            reaction_time_ms=trial.get('reaction_time', 0),
            par_ms=trial.get('par_ms', 9000),
        )
        scored_trial = {**trial, **score_result}
        scored_trials.append(scored_trial)

    # Calculate session metrics
    metrics = SpatialSpanTask.calculate_session_metrics(scored_trials)
    avg_rt = SpatialSpanTask.calculate_average_reaction_time(scored_trials)

    # Difficulty adaptation uses session score + class thresholds
    difficulty    = session_data.get('difficulty', 5)
    session_score = metrics['score']

    if session_score >= SpatialSpanTask.ADVANCE_THRESHOLD:
        new_difficulty = min(difficulty + 1, 10)
        adaptation_reason = f"Increased difficulty (score {session_score:.1f} >= {SpatialSpanTask.ADVANCE_THRESHOLD})"
    elif session_score < SpatialSpanTask.REGRESS_THRESHOLD:
        new_difficulty = max(difficulty - 1, 1)
        adaptation_reason = f"Decreased difficulty (score {session_score:.1f} < {SpatialSpanTask.REGRESS_THRESHOLD})"
    else:
        new_difficulty = difficulty
        adaptation_reason = f"Maintained difficulty (score {session_score:.1f} in {SpatialSpanTask.REGRESS_THRESHOLD}–{SpatialSpanTask.ADVANCE_THRESHOLD} range)"

    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="working_memory",
        task_type="spatial_span",
        task_code="spatial_span",
        score=metrics['score'],
        accuracy=metrics['accuracy'],
        average_reaction_time=avg_rt,
        consistency=metrics['consistency'],
        errors=metrics['total_trials'] - metrics['correct_count'],
        difficulty_level=new_difficulty,
        difficulty_before=difficulty,
        difficulty_after=new_difficulty,
        duration=sum(t.get('reaction_time', 0) for t in scored_trials) // 1000,
        raw_data=json.dumps({
            'trials': scored_trials,
            'metrics': metrics
        }),
        adaptation_reason=adaptation_reason,
        completed=True
    )
    
    session.add(training_session)
    
    # Update training plan's current difficulty for working_memory
    current_difficulty = json.loads(plan.current_difficulty)
    current_difficulty['working_memory'] = new_difficulty
    plan.current_difficulty = json.dumps(current_difficulty)
    plan.last_updated = datetime.utcnow()
    
    session.add(plan)
    
    # Track session completion BEFORE commit
    session_info = track_session_completion(plan, "working_memory", session, user_id, task_id)
    
    # Now commit all changes including the completion tracking
    session.commit()
    session.refresh(training_session)
    session.refresh(plan)
    
    return {
        "success": True,
        "session_id": training_session.id,
        "metrics": metrics,
        "difficulty_before": difficulty,
        "difficulty_after": new_difficulty,
        "adaptation_reason": adaptation_reason,
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"],
        "performance_summary": {
            "score": metrics['score'],
            "accuracy": metrics['accuracy'],
            "longest_span": metrics['longest_span'],
            "forward_accuracy": metrics['forward_accuracy'],
            "backward_accuracy": metrics['backward_accuracy']
        }
    }

@router.post("/tasks/letter-number-sequencing/generate/{user_id}")
def generate_letter_number_sequencing_session(
    user_id: int, 
    difficulty: int = 5,
    num_trials: int = 8,
    session: Session = Depends(get_session)
):
    """
    Generate Letter-Number Sequencing task session
    
    Returns sequence of mixed letters and numbers for the user to reorder
    """
    from app.services.letter_number_sequencing_task import LetterNumberSequencingTask
    
    # Validate difficulty
    if not 1 <= difficulty <= 10:
        raise HTTPException(status_code=400, detail="Difficulty must be between 1 and 10")
    
    # Get user's training plan to verify they exist
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan found")
    
    # Generate trials
    trials = LetterNumberSequencingTask.generate_session(difficulty, num_trials)
    
    return {
        "task_code": "letter_number_sequencing",
        "domain": "working_memory",
        "difficulty": difficulty,
        "num_trials": num_trials,
        "trials": trials,
        "instructions": {
            "title": "Letter-Number Sequencing",
            "description": "Reorder mixed letters and numbers",
            "task": "Put numbers in ascending order (1, 2, 3...) then letters alphabetically (A, B, C...)",
            "example": "Given: B-3-A-1 → Answer: 1-3-A-B",
            "tips": [
                "Take your time to view the sequence",
                "Remember: Numbers first (low to high), then letters (A to Z)",
                "Use mental rehearsal to organize the items"
            ]
        }
    }

@router.post("/tasks/letter-number-sequencing/submit/{user_id}")
def submit_letter_number_sequencing_session(
    user_id: int,
    session_data: dict,
    session: Session = Depends(get_session)
):
    """
    Submit completed Letter-Number Sequencing session and save results
    
    Expected session_data:
    {
        "difficulty": 5,
        "trials": [
            {
                "sequence": ["B", "3", "A", "1"],
                "correct_numbers": ["1", "3"],
                "correct_letters": ["A", "B"],
                "user_numbers": ["1", "3"],
                "user_letters": ["A", "B"],
                "reaction_time": 5500
            },
            ...
        ]
    }
    """
    from app.services.letter_number_sequencing_task import LetterNumberSequencingTask
    from app.services.badge_service import BadgeService
    
    # Get training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan or plan.id is None:
        raise HTTPException(status_code=404, detail="No active training plan found")

    enforce_session_limits(plan, session, user_id)
    
    # Extract task_id for session tracking
    task_id = session_data.get("task_id")
    
    # Score each trial
    trials = session_data.get('trials', [])
    scored_trials = []

    for trial in trials:
        score_result = LetterNumberSequencingTask.score_response(
            trial['correct_numbers'],
            trial['correct_letters'],
            trial.get('user_numbers', []),
            trial.get('user_letters', []),
            reaction_time_ms=trial.get('reaction_time', 0),
            par_ms=trial.get('par_ms', 18000),
        )
        scored_trial = {**trial, **score_result}
        scored_trials.append(scored_trial)

    # Calculate session metrics
    metrics = LetterNumberSequencingTask.calculate_session_metrics(scored_trials)
    avg_rt = LetterNumberSequencingTask.calculate_average_reaction_time(scored_trials)

    # Determine difficulty adaptation using weighted score and clinical thresholds
    difficulty = session_data.get('difficulty', 5)
    session_score = metrics['score']
    advance_threshold = LetterNumberSequencingTask.ADVANCE_THRESHOLD
    regress_threshold = LetterNumberSequencingTask.REGRESS_THRESHOLD

    if session_score >= advance_threshold:
        new_difficulty = min(difficulty + 1, 10)
        adaptation_reason = f"Increased difficulty (score {session_score:.1f} >= {advance_threshold})"
    elif session_score < regress_threshold:
        new_difficulty = max(difficulty - 1, 1)
        adaptation_reason = f"Decreased difficulty (score {session_score:.1f} < {regress_threshold})"
    else:
        new_difficulty = difficulty
        adaptation_reason = f"Maintained difficulty (score {session_score:.1f} in {regress_threshold}–{advance_threshold} range)"

    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="working_memory",
        task_type="letter_number_sequencing",
        task_code="letter_number_sequencing",
        score=metrics['score'],
        accuracy=metrics['binary_accuracy'],
        average_reaction_time=avg_rt,
        consistency=metrics['consistency'],
        errors=metrics['total_trials'] - metrics['correct_count'],
        difficulty_level=new_difficulty,
        difficulty_before=difficulty,
        difficulty_after=new_difficulty,
        duration=sum(t.get('reaction_time', 0) for t in scored_trials) // 1000,
        raw_data=json.dumps({
            'trials': scored_trials,
            'metrics': metrics
        }),
        adaptation_reason=adaptation_reason,
        completed=True
    )
    
    session.add(training_session)
    
    # Update training plan's current difficulty for working_memory
    current_difficulty = json.loads(plan.current_difficulty)
    current_difficulty['working_memory'] = new_difficulty
    plan.current_difficulty = json.dumps(current_difficulty)
    plan.last_updated = datetime.utcnow()
    
    session.add(plan)
    session.commit()
    session.refresh(training_session)
    session.refresh(plan)
    
    # Track session completion
    session_info = track_session_completion(plan, "working_memory", session, user_id, task_id)
    
    return {
        "success": True,
        "session_id": training_session.id,
        "metrics": metrics,
        "difficulty_before": difficulty,
        "difficulty_after": new_difficulty,
        "adaptation_reason": adaptation_reason,
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"],
        "performance_summary": {
            "score":                   metrics['score'],
            "binary_accuracy":         metrics['binary_accuracy'],
            "longest_sequence":        metrics['longest_sequence'],
            "consistency":             metrics['consistency'],
            "speed_trend":             metrics['speed_trend'],
            "avg_set_accuracy":        metrics['avg_set_accuracy'],
            "avg_order_accuracy":      metrics['avg_order_accuracy'],
            "avg_speed_bonus":         metrics['avg_speed_bonus'],
            "avg_penalty":             metrics['avg_penalty'],
            "numbers_set_accuracy":    metrics['numbers_set_accuracy'],
            "letters_set_accuracy":    metrics['letters_set_accuracy'],
            "numbers_order_accuracy":  metrics['numbers_order_accuracy'],
            "letters_order_accuracy":  metrics['letters_order_accuracy'],
        }
    }

@router.post("/tasks/operation-span/generate/{user_id}")
def generate_operation_span_session(
    user_id: int,
    difficulty: int = 5,
    num_trials: int = 6,
    session: Session = Depends(get_session)
):
    """
    Generate Operation Span (OSPAN) task session

    Returns trials with math problems and letters to remember
    """
    from app.services.operation_span_task import OperationSpanTask
    
    # Validate difficulty
    if not 1 <= difficulty <= 10:
        raise HTTPException(status_code=400, detail="Difficulty must be between 1 and 10")
    
    # Get user's training plan to verify they exist
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan found")
    
    # Generate trials
    trials = OperationSpanTask.generate_session(difficulty, num_trials)
    
    return {
        "task_code": "operation_span",
        "domain": "working_memory",
        "difficulty": difficulty,
        "num_trials": num_trials,
        "trials": trials,
        "instructions": {
            "title": "Operation Span (OSPAN)",
            "description": "Solve math problems while remembering letters",
            "task": "Answer whether each math equation is correct, then recall all the letters in order",
            "example": "Is 2+3=5? ✓ Remember F → Is 4+2=7? ✗ Remember Q → Recall: F, Q",
            "tips": [
                "Focus equally on both tasks - math AND letters",
                "Use mental rehearsal to keep letters fresh",
                "Don't sacrifice math accuracy for letter recall",
                "Take the full time to verify each equation"
            ]
        }
    }

@router.post("/tasks/operation-span/submit/{user_id}")
def submit_operation_span_session(
    user_id: int,
    session_data: dict,
    session: Session = Depends(get_session)
):
    """
    Submit completed Operation Span session and save results
    
    Expected session_data:
    {
        "difficulty": 5,
        "trials": [
            {
                "set_size": 3,
                "items": [...],
                "correct_letters": ["F", "K", "M"],
                "user_letters": ["F", "K", "M"],
                "math_responses": [true, false, true],
                "math_correct": [true, false, true],
                "reaction_time": 15000
            },
            ...
        ]
    }
    """
    from app.services.operation_span_task import OperationSpanTask
    from app.services.badge_service import BadgeService
    
    # Get training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan or plan.id is None:
        raise HTTPException(status_code=404, detail="No active training plan found")

    enforce_session_limits(plan, session, user_id)
    
    # Extract task_id for session tracking
    task_id = session_data.get("task_id")
    
    # Score each trial
    trials = session_data.get('trials', [])
    scored_trials = []
    
    for trial in trials:
        score_result = OperationSpanTask.score_response(
            trial['correct_letters'],
            trial.get('user_letters', []),
            trial.get('math_responses', []),
            [item['is_correct'] for item in trial['items']]
        )
        
        scored_trial = {**trial, **score_result}
        scored_trials.append(scored_trial)
    
    # Calculate session metrics
    metrics = OperationSpanTask.calculate_session_metrics(scored_trials)
    avg_rt = OperationSpanTask.calculate_average_reaction_time(scored_trials)
    
    # Determine difficulty adaptation (more stringent for dual-task)
    difficulty = session_data.get('difficulty', 5)
    dual_task_performance = metrics['dual_task_performance']
    
    if dual_task_performance >= 80:
        new_difficulty = min(difficulty + 1, 10)
        adaptation_reason = f"Increased difficulty (dual-task performance {dual_task_performance:.1f}% >= 80%)"
    elif dual_task_performance < 60:
        new_difficulty = max(difficulty - 1, 1)
        adaptation_reason = f"Decreased difficulty (dual-task performance {dual_task_performance:.1f}% < 60%)"
    else:
        new_difficulty = difficulty
        adaptation_reason = f"Maintained difficulty (dual-task performance {dual_task_performance:.1f}% in 60-80% range)"
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="working_memory",
        task_type="operation_span",
        task_code="operation_span",
        score=metrics['score'],
        accuracy=metrics['accuracy'],
        average_reaction_time=avg_rt,
        consistency=metrics['consistency'],
        errors=metrics['total_trials'] - metrics['correct_count'],
        difficulty_level=new_difficulty,
        difficulty_before=difficulty,
        difficulty_after=new_difficulty,
        duration=sum(t.get('reaction_time', 0) for t in scored_trials) // 1000,
        raw_data=json.dumps({
            'trials': scored_trials,
            'metrics': metrics
        }),
        adaptation_reason=adaptation_reason,
        completed=True
    )
    
    session.add(training_session)
    
    # Update training plan's current difficulty for working_memory
    current_difficulty = json.loads(plan.current_difficulty)
    current_difficulty['working_memory'] = new_difficulty
    plan.current_difficulty = json.dumps(current_difficulty)
    plan.last_updated = datetime.utcnow()
    
    session.add(plan)
    
    # Track session completion BEFORE commit
    session_info = track_session_completion(plan, "working_memory", session, user_id, task_id)
    
    # Now commit all changes including the completion tracking
    session.commit()
    session.refresh(training_session)
    session.refresh(plan)
    
    return {
        "success": True,
        "session_id": training_session.id,
        "metrics": metrics,
        "difficulty_before": difficulty,
        "difficulty_after": new_difficulty,
        "adaptation_reason": adaptation_reason,
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"],
        "performance_summary": {
            "score": metrics['score'],
            "accuracy": metrics['accuracy'],
            "letter_recall_accuracy": metrics['letter_recall_accuracy'],
            "math_accuracy": metrics['math_accuracy'],
            "dual_task_performance": metrics['dual_task_performance']
        }
    }


# ============================================================================
# Dual N-Back - Dual-modality working memory training
# ============================================================================

@router.post("/tasks/dual-n-back/generate/{user_id}")
def generate_dual_n_back_session(
    user_id: int,
    difficulty: int = 5,
    num_trials: int = 4,
    session: Session = Depends(get_session)
):
    """
    Generate Dual N-Back task session.

    Returns trial streams combining visual positions and auditory letter cues.
    """
    from app.services.dual_n_back_task import DualNBackTask

    if not 1 <= difficulty <= 10:
        raise HTTPException(status_code=400, detail="Difficulty must be between 1 and 10")

    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()

    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan found")

    trials = DualNBackTask.generate_session(difficulty, num_trials)
    max_n_level = max(trial["n_level"] for trial in trials) if trials else 1

    return {
        "task_code": "dual_n_back",
        "domain": "working_memory",
        "difficulty": difficulty,
        "num_trials": num_trials,
        "trials": trials,
        "instructions": {
            "title": "Dual N-Back",
            "description": "Track a visual square and a spoken letter at the same time.",
            "task": "Press the visual and audio match controls when the current item matches the one shown N steps back.",
            "n_level": max_n_level,
            "controls": {
                "visual": "V key or Visual Match button",
                "audio": "A key or Audio Match button"
            },
            "tips": [
                "You do not need to respond during the first few warm-up items before N-back comparison starts.",
                "Visual and audio matches can happen separately or together.",
                "Prioritize accuracy first, then speed once the pattern feels familiar.",
                "The task adapts to your performance across rounds."
            ]
        }
    }


@router.post("/tasks/dual-n-back/submit/{user_id}")
def submit_dual_n_back_session(
    user_id: int,
    session_data: dict,
    session: Session = Depends(get_session)
):
    """
    Submit completed Dual N-Back session and save results.
    """
    from app.services.dual_n_back_task import DualNBackTask

    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()

    if not plan or plan.id is None:
        raise HTTPException(status_code=404, detail="No active training plan found")

    enforce_session_limits(plan, session, user_id)

    task_id = session_data.get("task_id")
    submitted_trials = session_data.get("trials", [])
    scored_trials = []

    for submitted_trial in submitted_trials:
        metrics = DualNBackTask.score_trial(submitted_trial)
        scored_trials.append({**submitted_trial, "metrics": metrics})

    metrics = DualNBackTask.calculate_session_metrics(scored_trials)
    avg_rt = DualNBackTask.calculate_average_reaction_time(scored_trials)

    difficulty = session_data.get("difficulty", 5)
    score = metrics["score"]
    false_alarm_pressure = max(metrics["visual_false_alarm_rate"], metrics["audio_false_alarm_rate"])

    if score >= DualNBackTask.ADVANCE_THRESHOLD and false_alarm_pressure <= 22:
        new_difficulty = min(difficulty + 1, 10)
        adaptation_reason = (
            f"Increased difficulty (score {score:.1f} >= {DualNBackTask.ADVANCE_THRESHOLD} with controlled false alarms)"
        )
    elif score < DualNBackTask.REGRESS_THRESHOLD:
        new_difficulty = max(difficulty - 1, 1)
        adaptation_reason = f"Decreased difficulty (score {score:.1f} < {DualNBackTask.REGRESS_THRESHOLD})"
    else:
        new_difficulty = difficulty
        adaptation_reason = f"Maintained difficulty (score {score:.1f} within target range)"

    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="working_memory",
        task_type="dual_n_back",
        task_code="dual_n_back",
        score=metrics["score"],
        accuracy=metrics["accuracy"],
        average_reaction_time=avg_rt,
        consistency=metrics["consistency"],
        errors=metrics["total_decisions"] - metrics["correct_decisions"],
        difficulty_level=new_difficulty,
        difficulty_before=difficulty,
        difficulty_after=new_difficulty,
        duration=session_data.get("duration_seconds", 0),
        raw_data=json.dumps({
            "trials": scored_trials,
            "metrics": metrics
        }),
        adaptation_reason=adaptation_reason,
        completed=True
    )

    session.add(training_session)

    current_difficulty = json.loads(plan.current_difficulty)
    current_difficulty["working_memory"] = new_difficulty
    plan.current_difficulty = json.dumps(current_difficulty)
    plan.last_updated = datetime.utcnow()

    session.add(plan)

    session_info = track_session_completion(plan, "working_memory", session, user_id, task_id)

    session.commit()
    session.refresh(training_session)
    session.refresh(plan)

    return {
        "success": True,
        "session_id": training_session.id,
        "metrics": metrics,
        "difficulty_before": difficulty,
        "difficulty_after": new_difficulty,
        "adaptation_reason": adaptation_reason,
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"],
        "performance_summary": {
            "score": metrics["score"],
            "accuracy": metrics["accuracy"],
            "visual_accuracy": metrics["visual_accuracy"],
            "audio_accuracy": metrics["audio_accuracy"],
            "dual_accuracy": metrics["dual_accuracy"],
            "n_level": metrics["n_level"]
        }
    }


# ============================================================================
# SDMT (Symbol Digit Modalities Test) - GOLD STANDARD for MS
# ============================================================================

@router.post("/tasks/sdmt/generate/{user_id}")
def generate_sdmt_task(
    user_id: int,
    difficulty: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """
    Generate SDMT trial with symbol-digit mappings
    ⭐⭐⭐⭐⭐ Most sensitive test for MS cognitive impairment
    """
    from app.services.sdmt_task import SDMTTask
    
    # Get user's training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        return {
            "has_data": False,
            "message": "No active training plan.",
            "user_id": user_id,
            "period_days": days,
            "total_sessions": 0,
            "trends_by_domain": {},
            "overall_trend": [],
            "domains": [],
        }
    
    # Determine difficulty
    if difficulty is None:
        current_diff = json.loads(plan.current_difficulty) if isinstance(plan.current_difficulty, str) else plan.current_difficulty
        difficulty = current_diff.get('processing_speed', 5)
    
    # Ensure difficulty is an int (type narrowing)
    difficulty_level: int = difficulty if isinstance(difficulty, int) else 5
    
    # Generate trial
    trial = SDMTTask.generate_trial(difficulty_level)
    
    return {
        "trial": trial,
        "difficulty": difficulty_level
    }


@router.post("/tasks/sdmt/submit/{user_id}")
def submit_sdmt_task(
    user_id: int,
    request: dict,
    session: Session = Depends(get_session)
):
    """
    Submit SDMT trial results and update difficulty
    """
    from app.services.sdmt_task import SDMTTask
    from app.services.badge_service import BadgeService
    
    difficulty = request.get('difficulty')
    trial = request.get('trial')
    user_responses = request.get('user_responses', [])
    response_times = request.get('response_times', [])
    completed_count = request.get('completed_count', 0)
    task_id = request.get('task_id')  # Extract task_id for session tracking
    
    # Validate required fields
    if difficulty is None or trial is None:
        raise HTTPException(status_code=400, detail="Missing difficulty or trial data")
    
    # Score the trial
    metrics = SDMTTask.score_response(
        trial=trial,
        user_responses=user_responses,
        response_times=response_times,
        completed_count=completed_count
    )
    
    # Determine difficulty adjustment
    new_difficulty, adaptation_reason = SDMTTask.determine_difficulty_adjustment(
        score=metrics['score'],
        difficulty=difficulty,
        target=trial['target_responses']
    )
    
    # Get training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")

    enforce_session_limits(plan, session, user_id)
    
    # Update difficulty
    current_diff = json.loads(plan.current_difficulty) if isinstance(plan.current_difficulty, str) else plan.current_difficulty
    current_diff['processing_speed'] = new_difficulty
    plan.current_difficulty = json.dumps(current_diff)
    
    # Ensure plan.id is not None
    if plan.id is None:
        raise HTTPException(status_code=500, detail="Training plan has no ID")
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="processing_speed",
        task_type="sdmt",
        task_code="sdmt",
        score=metrics['score'],
        accuracy=metrics['accuracy'],
        average_reaction_time=metrics['avg_response_time'],
        consistency=metrics['consistency'],
        errors=metrics['incorrect_count'],
        difficulty_level=difficulty,
        difficulty_before=difficulty,
        difficulty_after=new_difficulty,
        duration=trial['duration_seconds'],
        adaptation_reason=adaptation_reason,
        raw_data=json.dumps({
            "correct_count": metrics['correct_count'],
            "incorrect_count": metrics['incorrect_count'],
            "total_attempted": metrics['total_attempted'],
            "processing_speed": metrics['processing_speed'],
            "user_responses": user_responses,
            "response_times": response_times
        })
    )
    
    session.add(training_session)
    
    # Track session completion
    session_info = track_session_completion(plan, "processing_speed", session, user_id, task_id)
    
    session.commit()
    session.refresh(training_session)
    
    return {
        "success": True,
        "session_id": training_session.id,
        "metrics": metrics,
        "difficulty_before": difficulty,
        "difficulty_after": new_difficulty,
        "adaptation_reason": adaptation_reason,
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"],
        "performance_summary": {
            "score": metrics['score'],
            "correct_count": metrics['correct_count'],
            "processing_speed": metrics['processing_speed'],
            "accuracy": metrics['accuracy']
        }
    }


# ============================================================================
# Trail Making Test Part A (TMT-A) - Classic Neuropsych Test
# ============================================================================

@router.post("/tasks/trail-making-a/generate/{user_id}")
def generate_trail_making_a_task(
    user_id: int,
    difficulty: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """
    Generate Trail Making Test Part A trial with circle positions
    Classic neuropsychological test for psychomotor speed
    """
    from app.services.trail_making_a_task import TrailMakingATask
    
    # Get user's training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")
    
    # Determine difficulty
    if difficulty is None:
        current_diff = json.loads(plan.current_difficulty) if isinstance(plan.current_difficulty, str) else plan.current_difficulty
        difficulty = current_diff.get('processing_speed', 5)
    
    # Ensure difficulty is an int
    difficulty_level: int = difficulty if isinstance(difficulty, int) else 5
    
    # Generate trial
    trial = TrailMakingATask.generate_trial(difficulty_level)
    
    return {
        "trial": trial,
        "difficulty": difficulty_level
    }


@router.post("/tasks/trail-making-a/submit/{user_id}")
def submit_trail_making_a_task(
    user_id: int,
    request: dict,
    session: Session = Depends(get_session)
):
    """
    Submit Trail Making Test Part A results and update difficulty
    """
    from app.services.trail_making_a_task import TrailMakingATask
    
    difficulty = request.get('difficulty')
    trial = request.get('trial')
    completion_time = request.get('completion_time', 0)
    errors = request.get('errors', [])
    clicks = request.get('clicks', [])
    task_id = request.get('task_id')  # Extract task_id for session tracking
    
    # Validate required fields
    if difficulty is None or trial is None:
        raise HTTPException(status_code=400, detail="Missing difficulty or trial data")
    
    # Score the trial
    metrics = TrailMakingATask.score_response(
        trial=trial,
        completion_time=completion_time,
        errors=errors,
        clicks=clicks
    )
    
    # Determine difficulty adjustment
    new_difficulty, adaptation_reason = TrailMakingATask.determine_difficulty_adjustment(
        normalized_time=metrics['normalized_time'],
        errors=metrics['errors'],
        difficulty=difficulty
    )
    
    # Get training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")

    enforce_session_limits(plan, session, user_id)
    
    # Update difficulty
    current_diff = json.loads(plan.current_difficulty) if isinstance(plan.current_difficulty, str) else plan.current_difficulty
    current_diff['processing_speed'] = new_difficulty
    plan.current_difficulty = json.dumps(current_diff)
    
    # Ensure plan.id is not None
    if plan.id is None:
        raise HTTPException(status_code=500, detail="Training plan has no ID")
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="processing_speed",
        task_type="trail_making_a",
        task_code="trail_making_a",
        score=metrics['score'],
        accuracy=metrics['accuracy'],
        average_reaction_time=metrics['completion_time'] * 1000,  # Convert to ms
        consistency=metrics['path_efficiency'],
        errors=metrics['errors'],
        difficulty_level=difficulty,
        difficulty_before=difficulty,
        difficulty_after=new_difficulty,
        duration=int(metrics['completion_time']),
        adaptation_reason=adaptation_reason,
        raw_data=json.dumps({
            "completion_time": metrics['completion_time'],
            "normalized_time": metrics['normalized_time'],
            "performance_level": metrics['performance_level'],
            "processing_speed": metrics['processing_speed'],
            "path_efficiency": metrics['path_efficiency'],
            "total_clicks": metrics['total_clicks'],
            "errors": errors,
            "clicks": clicks
        })
    )
    
    session.add(training_session)
    
    # Track session completion
    session_info = track_session_completion(plan, "processing_speed", session, user_id, task_id)
    
    session.commit()
    session.refresh(training_session)
    
    return {
        "success": True,
        "session_id": training_session.id,
        "metrics": metrics,
        "difficulty_before": difficulty,
        "difficulty_after": new_difficulty,
        "adaptation_reason": adaptation_reason,
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"],
        "performance_summary": {
            "score": metrics['score'],
            "completion_time": metrics['completion_time'],
            "performance_level": metrics['performance_level'],
            "errors": metrics['errors']
        }
    }


# ============================================================================
# Pattern Comparison Task (Task 2.3 - Processing Speed)
# ============================================================================

@router.post("/tasks/pattern-comparison/generate/{user_id}")
def generate_pattern_comparison_session(
    user_id: int,
    difficulty: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """
    Generate a Pattern Comparison (Visual Matching) session.
    Returns multiple trials with pattern pairs to compare.
    """
    from app.services.pattern_comparison_task import PatternComparisonTask
    
    # Get user's training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan found")
    
    # Get difficulty from plan if not provided
    if difficulty is None:
        current_difficulty = plan.current_difficulty
        if isinstance(current_difficulty, str):
            current_difficulty = json.loads(current_difficulty)
        difficulty = current_difficulty.get("processing_speed", 5)
    
    # Ensure difficulty is valid
    difficulty_level: int = difficulty if isinstance(difficulty, int) else 5
    difficulty_level = max(1, min(10, difficulty_level))
    
    # Generate session
    task_service = PatternComparisonTask()
    session_data = task_service.generate_session(difficulty_level)
    
    return {
        "session": session_data,
        "difficulty": difficulty_level,
        "user_id": user_id
    }


@router.post("/tasks/pattern-comparison/submit/{user_id}")
def submit_pattern_comparison_session(
    user_id: int,
    request_data: dict,
    session: Session = Depends(get_session)
):
    """
    Submit completed Pattern Comparison session and record results.
    
    Expected request_data:
    - difficulty: int (1-10)
    - session_data: dict (session info from generate)
    - responses: list of {trial_index, user_answer, reaction_time}
    """
    from app.services.pattern_comparison_task import PatternComparisonTask
    from app.services.badge_service import BadgeService
    
    # Extract data from request
    difficulty = request_data.get("difficulty")
    session_data = request_data.get("session_data")
    responses = request_data.get("responses", [])
    task_id = request_data.get("task_id")  # Extract task_id for session tracking
    
    # Validate inputs
    if difficulty is None:
        raise HTTPException(status_code=400, detail="Difficulty is required")
    if session_data is None:
        raise HTTPException(status_code=400, detail="Session data is required")
    
    # Get user's training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan found")

    enforce_session_limits(plan, session, user_id)
    
    # Validate plan has an id
    if plan.id is None:
        raise HTTPException(status_code=500, detail="Training plan ID is missing")
    
    # Score the session
    task_service = PatternComparisonTask()
    
    # Recreate session in service
    session_id = session_data.get("session_id")
    
    # Validate session_id
    if session_id is None:
        raise HTTPException(status_code=400, detail="Session ID is required")
    
    task_service.session_data[session_id] = {
        "trials": session_data.get("trials", []),
        "difficulty": difficulty
    }
    
    results = task_service.score_session(session_id, responses, difficulty)
    
    if "error" in results:
        raise HTTPException(status_code=400, detail=results["error"])
    
    metrics = results["metrics"]
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="processing_speed",
        task_type="pattern_comparison",
        task_code="pattern_comparison",
        score=metrics["score"],
        accuracy=metrics["accuracy"],
        average_reaction_time=metrics["average_reaction_time"],
        consistency=metrics["consistency"],
        errors=metrics["timeout_count"],
        difficulty_level=difficulty,
        difficulty_before=difficulty,
        difficulty_after=results["difficulty_adjustment"],
        duration=int(metrics["total_time"]),
        raw_data=json.dumps({
            "responses": responses,
            "correct_count": metrics["correct_count"],
            "total_trials": metrics["total_trials"],
            "processing_speed": metrics["processing_speed"],
            "timeout_count": metrics["timeout_count"],
            "performance_level": metrics["performance_level"]
        }),
        adaptation_reason=results["adaptation_reason"]
    )
    
    session.add(training_session)
    
    # Update training plan difficulty
    current_difficulty = plan.current_difficulty
    if isinstance(current_difficulty, str):
        current_difficulty = json.loads(current_difficulty)
    
    current_difficulty["processing_speed"] = results["difficulty_adjustment"]
    plan.current_difficulty = json.dumps(current_difficulty)
    
    # Track session completion
    session_info = track_session_completion(plan, "processing_speed", session, user_id, task_id)
    
    session.commit()
    session.refresh(training_session)
    
    return {
        "session_id": training_session.id,
        "metrics": metrics,
        "difficulty_before": difficulty,
        "difficulty_after": results["difficulty_adjustment"],
        "adaptation_reason": results["adaptation_reason"],
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"]
    }


# ============================================================================
# INSPECTION TIME TASK - Processing Speed
# ============================================================================

@router.post("/tasks/inspection-time/generate/{user_id}")
def generate_inspection_time_session(
    user_id: int,
    session: Session = Depends(get_session)
):
    """Generate an Inspection Time task session - pure perceptual speed."""
    from app.services.inspection_time_task import InspectionTimeTask
    
    # Get user's active training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")
    
    # Get current difficulty from plan
    current_difficulty = plan.current_difficulty
    if isinstance(current_difficulty, str):
        current_difficulty = json.loads(current_difficulty)
    
    difficulty = current_difficulty.get("processing_speed", 3)
    
    # Generate session
    task = InspectionTimeTask()
    session_data = task.generate_session(difficulty)
    
    return {
        "session_data": session_data,
        "difficulty": difficulty,
        "user_id": user_id
    }


@router.post("/tasks/inspection-time/submit/{user_id}")
def submit_inspection_time_session(
    user_id: int,
    request_data: dict,
    session: Session = Depends(get_session)
):
    """Submit and score an Inspection Time task session."""
    from app.services.inspection_time_task import InspectionTimeTask
    from typing import List, Dict, Any
    
    # Extract and validate data from request
    difficulty = request_data.get("difficulty")
    session_data = request_data.get("session_data")
    responses = request_data.get("responses")
    task_id = request_data.get("task_id")  # Extract task_id for session tracking
    
    if difficulty is None or session_data is None or responses is None:
        raise HTTPException(status_code=400, detail="difficulty, session_data, and responses are required")
    
    if not isinstance(difficulty, int):
        raise HTTPException(status_code=400, detail="difficulty must be an integer")
    
    if not isinstance(responses, list):
        raise HTTPException(status_code=400, detail="responses must be a list")
    
    # Get user's active training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")

    enforce_session_limits(plan, session, user_id)
    
    if plan.id is None:
        raise HTTPException(status_code=500, detail="Invalid training plan")
    
    # Score the session
    task = InspectionTimeTask()
    session_id = session_data.get("session_id")
    
    if session_id is None:
        raise HTTPException(status_code=400, detail="session_id is required")
    
    # Restore session data
    task.session_data[session_id] = {
        "trials": session_data["trials"],
        "started_at": datetime.utcnow(),
        "difficulty": difficulty
    }
    
    # Type-safe casting for responses
    typed_responses: List[Dict[str, Any]] = responses
    
    results = task.score_session(session_id, typed_responses, difficulty)
    
    if "error" in results:
        raise HTTPException(status_code=400, detail=results["error"])
    
    metrics = results["metrics"]
    
    # Calculate duration safely
    duration_seconds = int(sum(r["reaction_time"] for r in typed_responses) / 1000)
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="processing_speed",
        task_type="inspection_time",
        task_code="IT",
        score=metrics["score"],
        accuracy=metrics["accuracy"],
        average_reaction_time=metrics["average_reaction_time"],
        consistency=metrics["consistency"],
        errors=metrics["total_trials"] - metrics["correct_count"],
        difficulty_level=difficulty,
        difficulty_before=difficulty,
        difficulty_after=results["difficulty_adjustment"],
        duration=duration_seconds,
        raw_data=json.dumps({
            "responses": typed_responses,
            "presentation_time_ms": metrics["presentation_time_ms"],
            "perceptual_speed_index": metrics["perceptual_speed_index"]
        }),
        adaptation_reason=results["adaptation_reason"]
    )
    
    session.add(training_session)
    
    # Update training plan difficulty
    current_difficulty = plan.current_difficulty
    if isinstance(current_difficulty, str):
        current_difficulty = json.loads(current_difficulty)
    
    current_difficulty["processing_speed"] = results["difficulty_adjustment"]
    plan.current_difficulty = json.dumps(current_difficulty)
    
    # Track session completion
    session_info = track_session_completion(plan, "processing_speed", session, user_id, task_id)
    
    session.commit()
    session.refresh(training_session)
    
    return {
        "session_id": training_session.id,
        "metrics": metrics,
        "difficulty_before": difficulty,
        "difficulty_after": results["difficulty_adjustment"],
        "adaptation_reason": results["adaptation_reason"],
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"]
    }


# ============================================================================
# CHOICE REACTION TIME - Processing Speed (Decision speed)
# ============================================================================

@router.post("/tasks/choice-reaction-time/generate/{user_id}")
def generate_choice_reaction_time_session(
    user_id: int,
    difficulty: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """Generate a Choice Reaction Time session."""
    from app.services.choice_reaction_time_task import ChoiceReactionTimeTask

    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()

    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")

    if difficulty is None:
        current_difficulty = plan.current_difficulty
        if isinstance(current_difficulty, str):
            current_difficulty = json.loads(current_difficulty)
        difficulty = current_difficulty.get("processing_speed", 5)

    difficulty_level: int = difficulty if isinstance(difficulty, int) else 5
    difficulty_level = max(1, min(10, difficulty_level))

    session_data = ChoiceReactionTimeTask.generate_session(difficulty_level)

    return {
        "task_code": "choice_reaction_time",
        "domain": "processing_speed",
        "session": session_data,
        "difficulty": difficulty_level,
        "user_id": user_id
    }


@router.post("/tasks/choice-reaction-time/submit/{user_id}")
def submit_choice_reaction_time_session(
    user_id: int,
    request_data: dict,
    session: Session = Depends(get_session)
):
    """Submit and score a Choice Reaction Time session."""
    from app.services.choice_reaction_time_task import ChoiceReactionTimeTask

    difficulty = request_data.get("difficulty")
    session_data = request_data.get("session_data")
    responses = request_data.get("responses", [])
    task_id = request_data.get("task_id")

    if difficulty is None or session_data is None:
        raise HTTPException(status_code=400, detail="difficulty and session_data are required")
    if not isinstance(responses, list):
        raise HTTPException(status_code=400, detail="responses must be a list")

    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()

    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")

    enforce_session_limits(plan, session, user_id)

    if plan.id is None:
        raise HTTPException(status_code=500, detail="Invalid training plan")

    results = ChoiceReactionTimeTask.score_session(session_data, responses)
    metrics = results["metrics"]
    total_duration_ms = sum(float(response.get("reaction_time", 0) or 0) for response in responses)
    duration_seconds = max(1, int(total_duration_ms / 1000)) if responses else 1

    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="processing_speed",
        task_type="choice_reaction_time",
        task_code="choice_reaction_time",
        score=metrics["score"],
        accuracy=metrics["accuracy"],
        average_reaction_time=metrics["average_reaction_time"],
        consistency=metrics["consistency"],
        errors=metrics["total_trials"] - metrics["correct_count"],
        difficulty_level=difficulty,
        difficulty_before=difficulty,
        difficulty_after=results["difficulty_adjustment"],
        duration=duration_seconds,
        raw_data=json.dumps({
            "session_data": session_data,
            "responses": responses,
            "scored_trials": results["scored_trials"],
            "processing_speed": metrics["processing_speed"],
            "decision_efficiency": metrics["decision_efficiency"],
        }),
        adaptation_reason=results["adaptation_reason"]
    )

    session.add(training_session)

    current_difficulty = plan.current_difficulty
    if isinstance(current_difficulty, str):
        current_difficulty = json.loads(current_difficulty)

    current_difficulty["processing_speed"] = results["difficulty_adjustment"]
    plan.current_difficulty = json.dumps(current_difficulty)

    session_info = track_session_completion(plan, "processing_speed", session, user_id, task_id)

    session.commit()
    session.refresh(training_session)

    return {
        "session_id": training_session.id,
        "metrics": metrics,
        "difficulty_before": difficulty,
        "difficulty_after": results["difficulty_adjustment"],
        "adaptation_reason": results["adaptation_reason"],
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"]
    }


# ============================================================================
# STROOP COLOR-WORD TEST - Attention (Classic Inhibitory Control)
# ============================================================================

@router.post("/tasks/stroop/generate/{user_id}")
def generate_stroop_session(
    user_id: int,
    session: Session = Depends(get_session)
):
    """
    Generate Stroop Color-Word Test session.
    Three conditions: baseline (color patches), congruent (matching), incongruent (conflicting).
    """
    from app.services.stroop_task import StroopTask
    
    # Get user's active training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")
    
    # Get current difficulty for attention domain (parse JSON)
    current_diff = json.loads(plan.current_difficulty) if isinstance(plan.current_difficulty, str) else plan.current_difficulty
    difficulty = current_diff.get("attention", 1)
    
    # Generate session
    task = StroopTask()
    session_data = task.generate_session(difficulty)
    
    return {
        "session_data": session_data,
        "difficulty": difficulty
    }


@router.post("/tasks/stroop/submit/{user_id}")
def submit_stroop_session(
    user_id: int,
    request_data: dict,
    session: Session = Depends(get_session)
):
    """
    Submit Stroop session results and calculate interference metrics.
    """
    from app.services.stroop_task import StroopTask
    
    # Validate request data
    if not isinstance(request_data, dict):
        raise HTTPException(status_code=400, detail="Request data must be an object")
    
    difficulty = request_data.get("difficulty")
    session_data = request_data.get("session_data")
    responses = request_data.get("responses")
    task_id = request_data.get("task_id")  # Extract task_id for session tracking
    
    if not isinstance(difficulty, int):
        raise HTTPException(status_code=400, detail="difficulty must be an integer")
    
    if not isinstance(responses, list):
        raise HTTPException(status_code=400, detail="responses must be an array")
    
    if not isinstance(session_data, dict):
        raise HTTPException(status_code=400, detail="session_data must be an object")
    
    # Get user's active training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")
    
    if plan.id is None:
        raise HTTPException(status_code=500, detail="Invalid training plan")

    enforce_session_limits(plan, session, user_id)
    
    # Score the session
    task = StroopTask()
    typed_responses: List[Dict[str, Any]] = responses
    results = task.score_session(session_data, typed_responses)
    
    # Calculate duration based on total trials and timeouts
    presentation_time_ms = session_data.get("presentation_time_ms", 2000)
    response_timeout_ms = session_data.get("response_timeout_ms", 3000)
    total_trials = session_data.get("total_trials", 30)
    duration_seconds = int((presentation_time_ms + response_timeout_ms) * total_trials / 1000)
    
    # Determine difficulty adjustment
    adjustment = task.determine_difficulty_adjustment(results)
    new_difficulty = max(1, min(10, difficulty + adjustment))
    
    # Adaptation reason
    if adjustment > 0:
        adaptation_reason = f"Excellent interference control (accuracy: {results['overall_accuracy']:.1f}%, interference cost: {results['interference_cost']:.1f}%) - Increasing challenge"
    elif adjustment < 0:
        adaptation_reason = f"High interference effect (cost: {results['interference_cost']:.1f}%) - Reducing difficulty for better practice"
    else:
        adaptation_reason = f"Maintaining difficulty for consistent practice (performance: {results['performance_level']})"
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="attention",
        task_type="stroop",
        task_code="STROOP",
        score=results["performance_score"],
        accuracy=results["overall_accuracy"],
        average_reaction_time=int(results["incongruent_rt"]),  # Use incongruent RT as primary measure
        consistency=results["consistency"],
        errors=total_trials - results["correct_trials"],
        difficulty_level=new_difficulty,
        difficulty_before=difficulty,
        difficulty_after=new_difficulty,
        duration=duration_seconds,
        raw_data=json.dumps({
            "baseline_accuracy": results["baseline_accuracy"],
            "baseline_rt": results["baseline_rt"],
            "congruent_accuracy": results["congruent_accuracy"],
            "congruent_rt": results["congruent_rt"],
            "incongruent_accuracy": results["incongruent_accuracy"],
            "incongruent_rt": results["incongruent_rt"],
            "stroop_effect": results["stroop_effect"],
            "interference_cost": results["interference_cost"],
            "facilitation_effect": results["facilitation_effect"],
            "performance_level": results["performance_level"]
        }),
        adaptation_reason=adaptation_reason
    )
    
    session.add(training_session)
    
    # Update difficulty in training plan (handle JSON string)
    current_diff = json.loads(plan.current_difficulty) if isinstance(plan.current_difficulty, str) else plan.current_difficulty
    if current_diff is None:
        current_diff = {}
    current_diff["attention"] = new_difficulty
    plan.current_difficulty = json.dumps(current_diff)
    
    # Track session completion
    session_info = track_session_completion(plan, "attention", session, user_id, task_id)
    
    session.commit()
    session.refresh(training_session)
    
    return {
        "session_id": training_session.id,
        "metrics": results,
        "difficulty_before": difficulty,
        "difficulty_after": new_difficulty,
        "adaptation_reason": adaptation_reason,
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"]
    }


# ============================================================================
# GO/NO-GO TASK - Attention (Response Inhibition)
# ============================================================================

@router.post("/tasks/gonogo/generate/{user_id}")
def generate_gonogo_session(
    user_id: int,
    session: Session = Depends(get_session)
):
    """
    Generate Go/No-Go task session.
    Tests response inhibition and impulse control.
    """
    from app.services.go_nogo_task import GoNoGoTask
    
    # Get user's active training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")
    
    # Get current difficulty from plan
    current_difficulty = plan.current_difficulty
    if isinstance(current_difficulty, str):
        current_difficulty = json.loads(current_difficulty)
    
    difficulty = current_difficulty.get("attention", 4)
    
    # Generate session
    task = GoNoGoTask()
    session_data = task.generate_session(difficulty)
    
    return {
        "session_data": session_data,
        "difficulty": difficulty
    }


class GoNoGoSubmitRequest(BaseModel):
    difficulty: int
    session_data: dict
    responses: List[dict]


@router.post("/tasks/gonogo/submit/{user_id}")
def submit_gonogo_session(
    user_id: int,
    request: GoNoGoSubmitRequest,
    session: Session = Depends(get_session)
):
    """
    Submit Go/No-Go session results and calculate inhibition metrics.
    
    Key Metrics:
    - Go trial accuracy & speed (processing)
    - No-Go accuracy (inhibition)
    - Commission errors (false alarms)
    - d-prime (signal detection)
    """
    from app.services.go_nogo_task import GoNoGoTask
    from app.services.badge_service import BadgeService
    
    # Extract data from request
    difficulty = request.difficulty
    session_data = request.session_data
    responses = request.responses
    task_id = getattr(request, "task_id", None)  # Extract task_id for session tracking
    
    
    # Get training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")

    enforce_session_limits(plan, session, user_id)
    
    # Score the session
    task = GoNoGoTask()
    results = task.score_session(session_data, responses)
    
    # Determine difficulty adjustment
    adjustment = task.determine_difficulty_adjustment(results)
    new_difficulty = max(1, min(10, difficulty + adjustment))
    
    # Adaptation reason
    if adjustment > 0:
        adaptation_reason = "Excellent inhibitory control - increasing difficulty"
    elif adjustment < 0:
        adaptation_reason = "Reducing difficulty for better success rate"
    else:
        adaptation_reason = "Performance appropriate for current level"
    
    # Calculate duration
    total_time_ms = (session_data['presentation_time_ms'] + session_data['inter_stimulus_interval_ms']) * session_data['total_trials']
    duration_seconds = int(total_time_ms / 1000)
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id if plan.id else 0,  # Type safety: plan.id should exist since we fetched from DB
        domain="attention",
        task_type="go_nogo",
        task_code="GONOGO",
        difficulty_level=difficulty,
        difficulty_before=difficulty,
        difficulty_after=new_difficulty,
        score=int(results["performance_score"]),
        accuracy=results["overall_accuracy"],
        average_reaction_time=results["go_mean_rt"],
        consistency=results["nogo_accuracy"],  # Using No-Go accuracy as consistency measure
        errors=results["nogo_commission_errors"],
        duration=duration_seconds,
        raw_data=json.dumps({
            "go_accuracy": results["go_accuracy"],
            "go_mean_rt": results["go_mean_rt"],
            "nogo_accuracy": results["nogo_accuracy"],
            "commission_errors": results["nogo_commission_errors"],
            "d_prime": results["d_prime"],
            "hit_rate": results["hit_rate"],
            "false_alarm_rate": results["false_alarm_rate"],
            "performance_level": results["performance_level"]
        }),
        adaptation_reason=adaptation_reason
    )
    
    session.add(training_session)
    
    # Update difficulty in training plan
    current_diff = json.loads(plan.current_difficulty) if isinstance(plan.current_difficulty, str) else plan.current_difficulty
    if current_diff is None:
        current_diff = {}
    current_diff["attention"] = new_difficulty
    plan.current_difficulty = json.dumps(current_diff)
    
    # Track session completion
    session_info = track_session_completion(plan, "attention", session, user_id, task_id)
    
    session.commit()
    session.refresh(training_session)
    
    return {
        "session_id": training_session.id,
        "metrics": results,
        "difficulty_before": difficulty,
        "difficulty_after": new_difficulty,
        "adaptation_reason": adaptation_reason,
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"]
    }


# ============================================================================
# SART - Sustained Attention to Response Task
# ============================================================================

@router.post("/tasks/sart/generate/{user_id}")
def generate_sart_session(
    user_id: int,
    difficulty: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """Generate a SART session."""
    from app.services.sart_task import SARTTask

    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()

    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")

    if difficulty is None:
        current_difficulty = plan.current_difficulty
        if isinstance(current_difficulty, str):
            current_difficulty = json.loads(current_difficulty)
        difficulty = current_difficulty.get("attention", 5)

    difficulty_level: int = difficulty if isinstance(difficulty, int) else 5
    difficulty_level = max(1, min(10, difficulty_level))

    session_data = SARTTask.generate_session(difficulty_level)

    return {
        "task_code": "sart",
        "domain": "attention",
        "session_data": session_data,
        "difficulty": difficulty_level,
        "user_id": user_id
    }


@router.post("/tasks/sart/submit/{user_id}")
def submit_sart_session(
    user_id: int,
    request_data: dict,
    session: Session = Depends(get_session)
):
    """Submit and score a SART session."""
    from app.services.sart_task import SARTTask

    difficulty = request_data.get("difficulty")
    session_data = request_data.get("session_data")
    responses = request_data.get("responses", [])
    task_id = request_data.get("task_id")

    if difficulty is None or session_data is None:
        raise HTTPException(status_code=400, detail="difficulty and session_data are required")
    if not isinstance(responses, list):
        raise HTTPException(status_code=400, detail="responses must be a list")

    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()

    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")

    enforce_session_limits(plan, session, user_id)

    if plan.id is None:
        raise HTTPException(status_code=500, detail="Invalid training plan")

    results = SARTTask.score_session(session_data, responses)
    metrics = results["metrics"]
    total_duration_ms = sum(float(response.get("reaction_time_ms", 0) or 0) for response in responses)
    duration_seconds = max(1, int(total_duration_ms / 1000)) if responses else 1

    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="attention",
        task_type="sart",
        task_code="sart",
        score=metrics["score"],
        accuracy=metrics["accuracy"],
        average_reaction_time=metrics["average_reaction_time"],
        consistency=metrics["consistency"],
        errors=metrics["commission_errors"] + metrics["omission_errors"],
        difficulty_level=difficulty,
        difficulty_before=difficulty,
        difficulty_after=results["difficulty_adjustment"],
        duration=duration_seconds,
        raw_data=json.dumps({
            "session_data": session_data,
            "responses": responses,
            "scored_trials": results["scored_trials"],
            "go_accuracy": metrics["go_accuracy"],
            "nogo_accuracy": metrics["nogo_accuracy"],
            "vigilance_index": metrics["vigilance_index"],
        }),
        adaptation_reason=results["adaptation_reason"]
    )

    session.add(training_session)

    current_difficulty = plan.current_difficulty
    if isinstance(current_difficulty, str):
        current_difficulty = json.loads(current_difficulty)

    current_difficulty["attention"] = results["difficulty_adjustment"]
    plan.current_difficulty = json.dumps(current_difficulty)

    session_info = track_session_completion(plan, "attention", session, user_id, task_id)

    session.commit()
    session.refresh(training_session)

    return {
        "session_id": training_session.id,
        "metrics": metrics,
        "difficulty_before": difficulty,
        "difficulty_after": results["difficulty_adjustment"],
        "adaptation_reason": results["adaptation_reason"],
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"]
    }


# ============================================================================
# FLANKER TASK - Attention (Selective Attention & Conflict Resolution)
# ============================================================================

class FlankerSubmitRequest(BaseModel):
    difficulty: int
    session_data: dict
    responses: List[dict]
    task_id: Optional[str] = None


@router.post("/tasks/flanker/generate/{user_id}")
def generate_flanker_session(
    user_id: int,
    session: Session = Depends(get_session)
):
    """
    Generate Flanker task session (Eriksen Flanker Test).
    Tests selective attention and conflict resolution.
    """
    from app.services.flanker_task import FlankerTask
    
    # Get user's active training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")
    
    # Get current difficulty from plan
    current_difficulty = plan.current_difficulty
    if isinstance(current_difficulty, str):
        current_difficulty = json.loads(current_difficulty)
    
    difficulty = current_difficulty.get("attention", 4)
    
    # Generate session
    task = FlankerTask()
    session_data = task.generate_session(difficulty)
    
    return {
        "session_data": session_data,
        "difficulty": difficulty
    }


@router.post("/tasks/flanker/submit/{user_id}")
def submit_flanker_session(
    user_id: int,
    request: FlankerSubmitRequest,
    session: Session = Depends(get_session)
):
    """
    Submit Flanker session results and calculate attention metrics.
    
    Key Metrics:
    - Overall accuracy & RT
    - Congruent vs Incongruent performance
    - Flanker/Conflict Effect (Incongruent RT - Congruent RT)
    - Interference error rate
    """
    from app.services.flanker_task import FlankerTask
    from app.services.badge_service import BadgeService
    
    # Extract data from request
    difficulty = request.difficulty
    session_data = request.session_data
    responses = request.responses
    task_id = getattr(request, "task_id", None)  # Extract task_id for session tracking
    
    
    # Get training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")

    enforce_session_limits(plan, session, user_id)
    
    # Score the session
    task = FlankerTask()
    results = task.score_session(session_data, responses)
    
    # Determine difficulty adjustment
    adjustment = task.determine_difficulty_adjustment(results)
    new_difficulty = max(1, min(10, difficulty + adjustment))
    
    # Adaptation reason
    if adjustment > 0:
        adaptation_reason = "Excellent selective attention - increasing difficulty"
    elif adjustment < 0:
        adaptation_reason = "Reducing difficulty for better conflict resolution"
    else:
        adaptation_reason = "Performance appropriate for current level"
    
    # Calculate duration
    total_time_ms = (session_data['presentation_time_ms'] + session_data['inter_stimulus_interval_ms']) * session_data['total_trials']
    duration_seconds = int(total_time_ms / 1000)
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id if plan.id else 0,
        domain="attention",
        task_type="flanker",
        task_code="FLANKER",
        difficulty_level=difficulty,
        difficulty_before=difficulty,
        difficulty_after=new_difficulty,
        score=int(results["performance_score"]),
        accuracy=results["overall_accuracy"],
        average_reaction_time=results["mean_rt"],
        consistency=results["congruent_accuracy"],  # Congruent trial accuracy as baseline
        errors=results["total_trials"] - results["total_correct"],
        duration=duration_seconds,
        raw_data=json.dumps({
            "overall_accuracy": results["overall_accuracy"],
            "mean_rt": results["mean_rt"],
            "congruent_accuracy": results["congruent_accuracy"],
            "congruent_mean_rt": results["congruent_mean_rt"],
            "incongruent_accuracy": results["incongruent_accuracy"],
            "incongruent_mean_rt": results["incongruent_mean_rt"],
            "conflict_effect_ms": results["conflict_effect_ms"],
            "interference_error_rate": results["interference_error_rate"],
            "performance_level": results["performance_level"]
        }),
        adaptation_reason=adaptation_reason
    )
    
    session.add(training_session)
    
    # Update difficulty in training plan
    current_diff = json.loads(plan.current_difficulty) if isinstance(plan.current_difficulty, str) else plan.current_difficulty
    if current_diff is None:
        current_diff = {}
    current_diff["attention"] = new_difficulty
    plan.current_difficulty = json.dumps(current_diff)
    
    # Track session completion
    session_info = track_session_completion(plan, "attention", session, user_id, task_id)
    
    session.commit()
    session.refresh(training_session)
    
    return {
        "session_id": training_session.id,
        "metrics": results,
        "difficulty_before": difficulty,
        "difficulty_after": new_difficulty,
        "adaptation_reason": adaptation_reason,
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"]
    }


# ============================================================================
# PASAT TASK - Attention (MS Gold Standard)
# ============================================================================

@router.post("/tasks/pasat/generate/{user_id}")
def generate_pasat_session(
    user_id: int,
    visual_mode: bool = True,
    session: Session = Depends(get_session)
):
    """Generate a PASAT task session - MS gold standard attention test."""
    from app.services.pasat_task import PASATTask
    
    # Get user's active training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")
    
    # Get current difficulty from plan
    current_difficulty = plan.current_difficulty
    if isinstance(current_difficulty, str):
        current_difficulty = json.loads(current_difficulty)
    
    difficulty = current_difficulty.get("attention", 4)
    
    # Generate session
    task = PASATTask()
    session_data = task.generate_session(difficulty, visual_mode)
    
    return {
        "session_data": session_data,
        "difficulty": difficulty,
        "user_id": user_id
    }


@router.post("/tasks/pasat/submit/{user_id}")
def submit_pasat_session(
    user_id: int,
    request_data: dict,
    session: Session = Depends(get_session)
):
    """Submit and score a PASAT task session."""
    from app.services.pasat_task import PASATTask
    from typing import List, Dict, Any
    
    # Extract and validate data from request
    difficulty = request_data.get("difficulty")
    session_data = request_data.get("session_data")
    responses = request_data.get("responses")
    task_id = request_data.get("task_id")  # Extract task_id for session tracking
    
    if difficulty is None or session_data is None or responses is None:
        raise HTTPException(status_code=400, detail="difficulty, session_data, and responses are required")
    
    if not isinstance(difficulty, int):
        raise HTTPException(status_code=400, detail="difficulty must be an integer")
    
    if not isinstance(responses, list):
        raise HTTPException(status_code=400, detail="responses must be a list")
    
    # Get user's active training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")
    
    if plan.id is None:
        raise HTTPException(status_code=500, detail="Invalid training plan")

    enforce_session_limits(plan, session, user_id)
    
    # Score the session
    task = PASATTask()
    session_id = session_data.get("session_id")
    
    if session_id is None:
        raise HTTPException(status_code=400, detail="session_id is required")
    
    # Restore session data
    task.session_data[session_id] = {
        "digits": session_data["digits"],
        "correct_answers": session_data["correct_answers"],
        "started_at": datetime.utcnow(),
        "difficulty": difficulty,
        "interval_seconds": session_data["interval_seconds"]
    }
    
    # Type-safe casting for responses
    typed_responses: List[Dict[str, Any]] = responses
    
    results = task.score_session(session_id, typed_responses, difficulty)
    
    if "error" in results:
        raise HTTPException(status_code=400, detail=results["error"])
    
    metrics = results["metrics"]
    
    # Calculate duration safely
    duration_seconds = int(session_data["interval_seconds"] * session_data["total_trials"])
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="attention",
        task_type="pasat",
        task_code="PASAT",
        score=metrics["score"],
        accuracy=metrics["accuracy"],
        average_reaction_time=metrics["average_reaction_time"],
        consistency=metrics["consistency"],
        errors=metrics["total_trials"] - metrics["correct_count"],
        difficulty_level=difficulty,
        difficulty_before=difficulty,
        difficulty_after=results["difficulty_adjustment"],
        duration=duration_seconds,
        raw_data=json.dumps({
            "responses": typed_responses,
            "interval_seconds": metrics["interval_seconds"],
            "sustained_attention": metrics["sustained_attention"],
            "fatigue_effect": metrics["fatigue_effect"]
        }),
        adaptation_reason=results["adaptation_reason"]
    )
    
    session.add(training_session)
    
    # Update training plan difficulty
    current_difficulty = plan.current_difficulty
    if isinstance(current_difficulty, str):
        current_difficulty = json.loads(current_difficulty)
    
    current_difficulty["attention"] = results["difficulty_adjustment"]
    plan.current_difficulty = json.dumps(current_difficulty)
    
    # Track session completion
    session_info = track_session_completion(plan, "attention", session, user_id, task_id)
    
    session.commit()
    session.refresh(training_session)
    
    return {
        "session_id": training_session.id,
        "metrics": metrics,
        "difficulty_before": difficulty,
        "difficulty_after": results["difficulty_adjustment"],
        "adaptation_reason": results["adaptation_reason"],
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"]
    }


# ============================================================================
# DEV/TESTING ENDPOINTS - For quick testing during development
# ============================================================================

@router.post("/dev/complete-session/{user_id}")
def dev_complete_session(user_id: int, session: Session = Depends(get_session)):
    """
    DEV TOOL: Instantly complete the current session with auto-generated data.
    Adds all 4 tasks with realistic scores.
    """
    import random
    
    plan = _ensure_dev_training_plan(user_id, session)
    
    domains = ['working_memory', 'processing_speed', 'attention', 'flexibility']
    task_types = ['n_back', 'reaction_time', 'continuous_performance', 'task_switching']
    
    completed = plan.get_current_session_tasks_completed()
    now = datetime.utcnow()
    
    tasks_added = 0
    for i, (domain, task_type) in enumerate(zip(domains, task_types)):
        if domain not in completed:
            score = random.uniform(65, 95)
            accuracy = random.uniform(70, 100)
            
            # Randomize difficulty levels for variety
            difficulty_before = random.randint(3, 8)
            
            # Calculate difficulty_after based on accuracy (adaptive logic)
            if accuracy >= 85:
                difficulty_after = min(difficulty_before + 1, 10)
            elif accuracy < 65:
                difficulty_after = max(difficulty_before - 1, 1)
            else:
                difficulty_after = difficulty_before
            
            # Type assertion: plan.id cannot be None here since we retrieved the plan
            assert plan.id is not None
            
            training_session = TrainingSession(
                user_id=user_id,
                training_plan_id=plan.id,
                domain=domain,
                task_type=task_type,
                score=score,
                accuracy=accuracy,
                average_reaction_time=random.uniform(400, 800),
                consistency=random.uniform(70, 90),
                errors=random.randint(0, 5),
                difficulty_level=difficulty_after,
                difficulty_before=difficulty_before,
                difficulty_after=difficulty_after,
                duration=random.randint(60, 180),  # 1-3 minutes per task
                adaptation_reason=f"{'Increased' if difficulty_after > difficulty_before else 'Decreased' if difficulty_after < difficulty_before else 'Maintained'} difficulty (accuracy {accuracy:.1f}%)",
                raw_data=json.dumps({}),
                created_at=now + timedelta(seconds=i * 10),
                completed=True
            )
            
            session.add(training_session)
            completed.append(domain)
            tasks_added += 1
    
    # Save completed tasks
    plan.current_session_tasks_completed = json.dumps(completed)
    
    # If session complete, increment counters
    if len(completed) >= 4:
        plan.total_sessions_completed += 1
        plan.current_session_number += 1
        plan.current_session_tasks_completed = "[]"
        update_streak(plan)
    
    plan.last_updated = datetime.utcnow()
    session.add(plan)
    session.commit()
    session.refresh(plan)
    
    return {
        "success": True,
        "message": f"Added {tasks_added} tasks",
        "session_complete": len(completed) >= 4,
        "total_sessions": plan.total_sessions_completed,
        "current_streak": plan.current_streak
    }

@router.post("/dev/complete-single-session/{user_id}")
def dev_complete_single_session(user_id: int, session: Session = Depends(get_session)):
    """
    DEV TOOL: Complete a single session with realistic, adaptive data.
    """
    import random
    
    plan = _ensure_dev_training_plan(user_id, session)
    
    domains = ['working_memory', 'processing_speed', 'attention', 'flexibility']
    task_types = ['n_back', 'reaction_time', 'continuous_performance', 'task_switching']
    
    # Type assertion: plan.id cannot be None here since we retrieved the plan
    assert plan.id is not None
    
    now = datetime.utcnow()
    
    for i, (domain, task_type) in enumerate(zip(domains, task_types)):
        score = random.uniform(65, 95)
        accuracy = random.uniform(70, 100)
        
        # Randomize difficulty levels for variety
        difficulty_before = random.randint(3, 8)
        
        # Calculate difficulty_after based on accuracy (adaptive logic)
        if accuracy >= 85:
            difficulty_after = min(difficulty_before + 1, 10)
        elif accuracy < 65:
            difficulty_after = max(difficulty_before - 1, 1)
        else:
            difficulty_after = difficulty_before
        
        training_session = TrainingSession(
            user_id=user_id,
            training_plan_id=plan.id,
            domain=domain,
            task_type=task_type,
            score=score,
            accuracy=accuracy,
            average_reaction_time=random.uniform(400, 900),
            consistency=random.uniform(70, 95),
            errors=random.randint(0, 6),
            difficulty_level=difficulty_after,
            difficulty_before=difficulty_before,
            difficulty_after=difficulty_after,
            duration=random.randint(60, 180),  # 1-3 minutes per task
            adaptation_reason=f"{'Increased' if difficulty_after > difficulty_before else 'Decreased' if difficulty_after < difficulty_before else 'Maintained'} difficulty (accuracy {accuracy:.1f}%)",
            raw_data=json.dumps({}),
            created_at=now + timedelta(minutes=i * 3),
            completed=True
        )
        
        session.add(training_session)
    
    # Mark session as complete
    plan.total_sessions_completed += 1
    plan.current_session_number += 1
    plan.current_session_tasks_completed = "[]"
    plan.last_session_date = datetime.utcnow()
    update_streak(plan)
    
    plan.last_updated = datetime.utcnow()
    session.add(plan)
    session.commit()
    session.refresh(plan)
    
    return {
        "success": True,
        "message": "Session completed with 4 tasks",
        "total_sessions": plan.total_sessions_completed,
        "current_streak": plan.current_streak
    }

@router.post("/dev/generate-sessions/{user_id}")
def dev_generate_sessions(user_id: int, num_sessions: int = 2, session: Session = Depends(get_session)):
    """
    DEV TOOL: Generate multiple completed sessions with realistic data.
    """
    import random
    
    plan = _ensure_dev_training_plan(user_id, session)
    
    domains = ['working_memory', 'processing_speed', 'attention', 'flexibility']
    task_types = ['n_back', 'reaction_time', 'continuous_performance', 'task_switching']
    
    # Type assertion: plan.id cannot be None here since we retrieved the plan
    assert plan.id is not None
    
    sessions_created = 0
    for session_num in range(num_sessions):
        base_time = datetime.utcnow() - timedelta(days=num_sessions - session_num - 1, hours=random.randint(0, 12))
        
        for i, (domain, task_type) in enumerate(zip(domains, task_types)):
            score = random.uniform(60, 95)
            accuracy = random.uniform(70, 100)
            
            # Randomize difficulty levels for variety
            difficulty_before = random.randint(3, 8)
            
            # Calculate difficulty_after based on accuracy (adaptive logic)
            if accuracy >= 85:
                difficulty_after = min(difficulty_before + 1, 10)
            elif accuracy < 65:
                difficulty_after = max(difficulty_before - 1, 1)
            else:
                difficulty_after = difficulty_before
            
            training_session = TrainingSession(
                user_id=user_id,
                training_plan_id=plan.id,
                domain=domain,
                task_type=task_type,
                score=score,
                accuracy=accuracy,
                average_reaction_time=random.uniform(400, 1200),
                consistency=random.uniform(60, 95),
                errors=random.randint(0, 10),
                difficulty_level=difficulty_after,
                difficulty_before=difficulty_before,
                difficulty_after=difficulty_after,
                duration=random.randint(60, 180),  # 1-3 minutes per task
                adaptation_reason=f"{'Increased' if difficulty_after > difficulty_before else 'Decreased' if difficulty_after < difficulty_before else 'Maintained'} difficulty (accuracy {accuracy:.1f}%)",
                raw_data=json.dumps({}),
                created_at=base_time + timedelta(minutes=i * 3),
                completed=True
            )
            
            session.add(training_session)
        
        sessions_created += 1
    
    plan.total_sessions_completed += num_sessions
    plan.current_session_tasks_completed = "[]"
    plan.last_session_date = datetime.utcnow()
    plan.current_streak = 1
    plan.total_training_days = max(plan.total_training_days or 0, 1)
    
    session.add(plan)
    session.commit()
    session.refresh(plan)
    
    return {
        "success": True,
        "sessions_generated": sessions_created,
        "total_sessions": plan.total_sessions_completed,
        "message": f"Generated {sessions_created} sessions with {sessions_created * 4} tasks"
    }

@router.post("/dev/set-streak/{user_id}")
def dev_set_streak(user_id: int, days: int, session: Session = Depends(get_session)):
    """
    DEV TOOL: Set streak to specific number of days.
    """
    plan = _ensure_dev_training_plan(user_id, session)
    
    plan.current_streak = days
    plan.longest_streak = max(plan.longest_streak or 0, days)
    plan.total_training_days = max(plan.total_training_days or 0, days)
    
    session.add(plan)
    session.commit()
    
    return {
        "success": True,
        "current_streak": days,
        "longest_streak": plan.longest_streak,
        "message": f"Streak set to {days} days 🔥"
    }

@router.post("/dev/set-domain-difficulty/{user_id}")
def dev_set_domain_difficulty(user_id: int, request: dict = Body(...), session: Session = Depends(get_session)):
    """
    DEV TOOL: Set difficulty for a specific cognitive domain.
    This allows testing tasks at different difficulty levels without modifying core app code.

    Body:
        domain: str - The domain key (working_memory, attention, flexibility, etc.)
        difficulty: int - Difficulty level (1-10)
    """
    domain = request.get("domain")
    difficulty = request.get("difficulty", 5)
    if not domain:
        raise HTTPException(status_code=400, detail="Domain is required")

    # Validate difficulty
    difficulty = max(1, min(10, int(difficulty)))

    plan = _ensure_dev_training_plan(user_id, session)

    # Parse current difficulty
    current_diff = plan.current_difficulty
    if isinstance(current_diff, str):
        current_diff = json.loads(current_diff)
    if current_diff is None:
        current_diff = {}

    # Update the specific domain
    if domain in current_diff:
        old_difficulty = current_diff[domain]
        current_diff[domain] = difficulty
        plan.current_difficulty = json.dumps(current_diff)

        session.add(plan)
        session.commit()

        return {
            "success": True,
            "domain": domain,
            "old_difficulty": old_difficulty,
            "new_difficulty": difficulty,
            "training_plan_id": plan.id,
            "message": f"Set {domain} difficulty to {difficulty}"
        }
    else:
        # Domain not found, but add it anyway
        current_diff[domain] = difficulty
        plan.current_difficulty = json.dumps(current_diff)

        session.add(plan)
        session.commit()

        return {
            "success": True,
            "domain": domain,
            "old_difficulty": None,
            "new_difficulty": difficulty,
            "training_plan_id": plan.id,
            "message": f"Added {domain} with difficulty {difficulty}"
        }

@router.delete("/dev/clear-sessions/{user_id}")
def dev_clear_sessions(user_id: int, session: Session = Depends(get_session)):
    """
    DEV TOOL: Clear all training sessions and reset plan.
    """
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        return {
            "success": True,
            "sessions_deleted": 0,
            "message": "No active training plan to clear"
        }
    
    # Delete all sessions
    result = session.exec(
        select(TrainingSession).where(TrainingSession.training_plan_id == plan.id)
    ).all()
    
    for ts in result:
        session.delete(ts)
    
    # Reset plan
    plan.total_sessions_completed = 0
    plan.current_session_tasks_completed = "[]"
    plan.current_session_number = 1
    plan.current_streak = 0
    plan.longest_streak = 0
    plan.total_training_days = 0
    plan.last_session_date = None
    
    session.add(plan)
    session.commit()
    
    return {
        "success": True,
        "sessions_deleted": len(result),
        "message": "All sessions cleared"
    }

# ============================================================================
# BADGE ENDPOINTS
# ============================================================================

@router.get("/badges/{user_id}")
def get_user_badges(user_id: int, session: Session = Depends(get_session)):
    """
    Get all badges earned by the user.
    Returns list of earned badges with details and timestamp.
    """
    badges = BadgeService.get_user_badges(session, user_id)
    
    return {
        "total_earned": len(badges),
        "badges": badges
    }

@router.get("/badges/available/{user_id}")
def get_available_badges(user_id: int, session: Session = Depends(get_session)):
    """
    Get all available badges with earned/locked status.
    Useful for displaying badge gallery/showcase.
    """
    return BadgeService.get_available_badges(session, user_id)

@router.get("/badges/recent/{user_id}")
def get_recent_badges(user_id: int, limit: int = 5, session: Session = Depends(get_session)):
    """
    Get recently earned badges.
    """
    badges = BadgeService.get_user_badges(session, user_id)
    
    # Already sorted by earned_at desc
    recent = badges[:limit]
    
    return {
        "count": len(recent),
        "badges": recent
    }

@router.post("/dev/check-badges/{user_id}")
def dev_check_badges(user_id: int, session: Session = Depends(get_session)):
    """
    DEV TOOL: Check what badges would be earned and award them.
    Returns list of newly earned badges.
    """
    plan = _ensure_dev_training_plan(user_id, session)
    
    # Check and award badges
    newly_earned = BadgeService.check_and_award_badges(session, user_id, plan)
    
    # Get badge details
    badge_details = []
    for badge_id in newly_earned:
        badge_def = BadgeDefinition.get_badge(badge_id)
        if badge_def:
            badge_details.append({
                "id": badge_id,
                "badge_id": badge_id,
                "name": badge_def["name"],
                "description": badge_def["description"],
                "icon": badge_def["icon"],
                "category": badge_def["category"]
            })
    
    # Get all user badges
    all_badges = BadgeService.get_user_badges(session, user_id)
    
    return {
        "success": True,
        "newly_earned": newly_earned,
        "new_badge_details": badge_details,
        "total_earned": len(all_badges),
        "message": f"Checked badges! {len(newly_earned)} new badges earned" if newly_earned else "No new badges earned"
    }

# ============================================================================
# PERFORMANCE TRENDS ENDPOINTS
# ============================================================================

@router.get("/trends/{user_id}")
def get_performance_trends(
    user_id: int, 
    days: int = 30,
    session: Session = Depends(get_session)
):
    """
    Get performance trends over time for visualizing progress.
    Returns time-series data for scores, accuracy, and difficulty per domain.
    """
    # Get training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")
    
    # Get sessions from last N days
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    sessions = session.exec(
        select(TrainingSession)
        .where(TrainingSession.training_plan_id == plan.id)
        .where(TrainingSession.created_at >= cutoff_date)
        .order_by(col(TrainingSession.created_at))
    ).all()
    
    # Group by domain and date
    trends_by_domain = {}
    
    for s in sessions:
        domain = s.domain
        date = s.created_at.date().isoformat()
        
        if domain not in trends_by_domain:
            trends_by_domain[domain] = {
                "domain": domain,
                "data_points": []
            }
        
        trends_by_domain[domain]["data_points"].append({
            "date": s.created_at.isoformat(),
            "score": s.score,
            "accuracy": s.accuracy,
            "difficulty": s.difficulty_level,
            "reaction_time": s.average_reaction_time,
            "errors": s.errors
        })
    
    # Calculate overall trend (all domains combined)
    overall_trend = []
    sessions_by_date = {}
    
    for s in sessions:
        date = s.created_at.date().isoformat()
        if date not in sessions_by_date:
            sessions_by_date[date] = {
                "scores": [],
                "accuracies": [],
                "difficulties": []
            }
        
        sessions_by_date[date]["scores"].append(s.score)
        sessions_by_date[date]["accuracies"].append(s.accuracy)
        sessions_by_date[date]["difficulties"].append(s.difficulty_level)
    
    for date, data in sorted(sessions_by_date.items()):
        overall_trend.append({
            "date": date,
            "avg_score": sum(data["scores"]) / len(data["scores"]),
            "avg_accuracy": sum(data["accuracies"]) / len(data["accuracies"]),
            "avg_difficulty": sum(data["difficulties"]) / len(data["difficulties"]),
            "sessions_count": len(data["scores"])
        })
    
    return {
        "has_data": True,
        "message": "Performance trends available.",
        "user_id": user_id,
        "period_days": days,
        "total_sessions": len(sessions),
        "trends_by_domain": trends_by_domain,
        "overall_trend": overall_trend,
        "domains": list(trends_by_domain.keys())
    }

# ============================================================================
# WEEKLY SUMMARY
# ============================================================================

@router.get("/weekly-summary/{user_id}")
def get_weekly_summary(
    user_id: int,
    session: Session = Depends(get_session)
):
    """
    Get weekly summary showing last 7 days of training activity.
    Includes sessions count, average performance, streak status, and most improved domain.
    """
    # Get training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        return {
            "has_data": False,
            "message": "No active training plan"
        }
    
    # Get sessions from last 7 days
    cutoff_date = datetime.utcnow() - timedelta(days=7)
    
    weekly_sessions = session.exec(
        select(TrainingSession)
        .where(TrainingSession.training_plan_id == plan.id)
        .where(TrainingSession.created_at >= cutoff_date)
        .order_by(col(TrainingSession.created_at))
    ).all()
    
    if not weekly_sessions:
        return {
            "has_data": False,
            "message": "No sessions in the last 7 days"
        }
    
    # Calculate weekly statistics
    total_sessions = len(weekly_sessions)
    avg_score = sum(s.score for s in weekly_sessions) / total_sessions
    avg_accuracy = sum(s.accuracy for s in weekly_sessions) / total_sessions
    total_time = sum(s.duration for s in weekly_sessions)
    
    # Group by domain to find most improved
    domain_stats = {}
    for s in weekly_sessions:
        if s.domain not in domain_stats:
            domain_stats[s.domain] = {
                "scores": [],
                "first_score": s.score,
                "last_score": s.score
            }
        domain_stats[s.domain]["scores"].append(s.score)
        domain_stats[s.domain]["last_score"] = s.score
    
    # Calculate improvement for each domain
    most_improved = None
    max_improvement = 0
    
    for domain, stats in domain_stats.items():
        if len(stats["scores"]) >= 2:
            # Compare first half vs second half of week
            mid = len(stats["scores"]) // 2
            first_half_avg = sum(stats["scores"][:mid]) / len(stats["scores"][:mid])
            second_half_avg = sum(stats["scores"][mid:]) / len(stats["scores"][mid:])
            improvement = second_half_avg - first_half_avg
            
            if improvement > max_improvement:
                max_improvement = improvement
                most_improved = {
                    "domain": domain,
                    "improvement": improvement,
                    "sessions": len(stats["scores"])
                }
    
    # Get daily session counts for the week
    daily_counts = {}
    for i in range(7):
        date = (datetime.utcnow() - timedelta(days=6-i)).date()
        daily_counts[date.isoformat()] = 0
    
    for s in weekly_sessions:
        date_key = s.created_at.date().isoformat()
        if date_key in daily_counts:
            daily_counts[date_key] += 1
    
    # Count active days (days with at least 1 session)
    active_days = sum(1 for count in daily_counts.values() if count > 0)
    
    # Get previous week data for comparison
    previous_week_cutoff = datetime.utcnow() - timedelta(days=14)
    previous_week_sessions = session.exec(
        select(TrainingSession)
        .where(TrainingSession.training_plan_id == plan.id)
        .where(TrainingSession.created_at >= previous_week_cutoff)
        .where(TrainingSession.created_at < cutoff_date)
    ).all()
    
    prev_week_avg_score = 0
    score_change = 0
    if previous_week_sessions:
        prev_week_avg_score = sum(s.score for s in previous_week_sessions) / len(previous_week_sessions)
        score_change = avg_score - prev_week_avg_score
    
    return {
        "has_data": True,
        "week_start": cutoff_date.date().isoformat(),
        "week_end": datetime.utcnow().date().isoformat(),
        "total_sessions": total_sessions,
        "active_days": active_days,
        "avg_score": round(avg_score, 1),
        "avg_accuracy": round(avg_accuracy, 1),
        "total_time_minutes": round(total_time / 60, 1),
        "current_streak": plan.current_streak,
        "most_improved": most_improved,
        "daily_counts": daily_counts,
        "score_change_from_last_week": round(score_change, 1),
        "domains_trained": list(domain_stats.keys())
    }


# ============================================================================
# TRAIL MAKING TEST - PART B (Cognitive Flexibility)
# ============================================================================

from app.services.trail_making_b_task import TrailMakingBTask

@router.post("/tasks/trail-making-b/generate/{user_id}")
def generate_trail_making_b_session(user_id: int, session: Session = Depends(get_session)):
    """
    Generate a Trail Making Test - Part B session.
    Alternating number-letter sequence task for cognitive flexibility.
    """
    # Get training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No training plan found for user")
    
    # Get current difficulty for flexibility domain from JSON
    current_difficulty = plan.get_current_difficulty()
    difficulty = current_difficulty.get("flexibility", 1)
    
    # Get user's TMT-A baseline time if available (for B-A calculation)
    baseline = session.exec(
        select(BaselineAssessment)
        .where(BaselineAssessment.user_id == user_id)
        .order_by(desc(BaselineAssessment.created_at))
    ).first()
    
    baseline_tmt_a_time = None
    if baseline and baseline.raw_metrics:
        # Extract TMT-A time from baseline raw_metrics if it exists
        try:
            metrics = json.loads(baseline.raw_metrics)
            baseline_tmt_a_time = metrics.get("trail_making_a_time")
        except:
            baseline_tmt_a_time = None
    
    # Generate session
    task_service = TrailMakingBTask()
    session_data = task_service.generate_session(
        difficulty=difficulty,
        user_baseline_time=baseline_tmt_a_time
    )
    
    return {
        "session_data": session_data,
        "difficulty": difficulty,
        "user_id": user_id,
        "task_type": "trail_making_b"
    }


class TrailMakingBSubmission(BaseModel):
    difficulty: int
    session_data: dict
    user_sequence: List[str]  # IDs of circles clicked in order
    completion_time_seconds: float
    errors: List[Dict[str, Any]]  # Error log with details
    completed: bool


@router.post("/tasks/trail-making-b/submit/{user_id}")
def submit_trail_making_b_session(
    user_id: int, 
    submission: TrailMakingBSubmission,
    session: Session = Depends(get_session)
):
    """
    Submit completed Trail Making Test - Part B session for scoring.
    """
    # Get training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No training plan found")
    
    if not plan.id:
        raise HTTPException(status_code=500, detail="Invalid training plan")

    enforce_session_limits(plan, session, user_id)
    
    # Extract task_id for session tracking
    task_id = submission.session_data.get("task_id")
    
    # Score the session
    task_service = TrailMakingBTask()
    result = task_service.score_session(
        session_data=submission.session_data,
        user_sequence=submission.user_sequence,
        completion_time_seconds=submission.completion_time_seconds,
        errors=submission.errors
    )
    
    metrics = result["metrics"]
    
    # Calculate score (0-100 scale)
    # Higher score = better (faster time + fewer errors)
    time_score = max(0, 100 - (metrics["completion_time_seconds"] / 3))  # Penalty for time
    error_penalty = metrics["total_errors"] * 5  # -5 points per error
    accuracy_bonus = metrics["accuracy"]  # 0-100
    
    final_score = max(0, min(100, (time_score + accuracy_bonus) / 2 - error_penalty))
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,  # Add user_id
        training_plan_id=plan.id,
        domain="flexibility",
        task_type="trail_making_b",
        difficulty_level=submission.difficulty,  # Correct field name
        difficulty_before=submission.difficulty,
        difficulty_after=submission.difficulty,  # Will be updated below
        score=round(final_score, 1),
        accuracy=metrics["accuracy"],
        average_reaction_time=int(metrics["completion_time_seconds"] * 1000),
        consistency=100.0,  # Can be calculated if needed
        errors=metrics["total_errors"],
        duration=int(metrics["completion_time_seconds"]),
        completed=metrics["completed"],
        raw_data=json.dumps(submission.session_data),
        created_at=datetime.utcnow()
    )
    
    session.add(training_session)
    
    # Update difficulty based on performance
    new_difficulty = submission.difficulty
    
    if metrics["performance_level"] in ["Excellent", "Good"] and metrics["total_errors"] <= 2:
        new_difficulty = min(10, submission.difficulty + 1)
    elif metrics["performance_level"] in ["Needs Improvement", "Struggling"]:
        new_difficulty = max(1, submission.difficulty - 1)
    
    # Update the session record with new difficulty
    training_session.difficulty_after = new_difficulty
    training_session.adaptation_reason = f"Performance: {metrics['performance_level']}, Errors: {metrics['total_errors']}"
    
    # Update current difficulty in JSON
    current_difficulty = plan.get_current_difficulty()
    current_difficulty["flexibility"] = new_difficulty
    plan.current_difficulty = json.dumps(current_difficulty)
    
    # Update plan statistics
    plan.last_session_date = datetime.utcnow()
    
    # Track session completion
    session_info = track_session_completion(plan, "flexibility", session, user_id, task_id)
    
    session.commit()
    
    return {
        "success": True,
        "metrics": metrics,
        "interpretation": result["interpretation"],
        "clinical_note": result["clinical_note"],
        "score": round(final_score, 1),
        "new_difficulty": new_difficulty,
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"],
        "session_id": training_session.id
    }


# ==================== Wisconsin Card Sorting Test (WCST) ====================

@router.post("/tasks/wcst/generate/{user_id}")
def generate_wcst_session(user_id: int, session: Session = Depends(get_session)):
    """
    Generate Wisconsin Card Sorting Test (WCST) session
    
    WCST measures:
    - Set-shifting and cognitive flexibility
    - Rule learning and adaptation
    - Perseverative errors (getting stuck on old rules)
    - Executive function
    """
    from app.services.wcst_task import WCSTTask
    
    # Get user's training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .order_by(desc(TrainingPlan.created_at))
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No training plan found")
    
    # Get flexibility difficulty from JSON field
    try:
        difficulty = plan.get_current_difficulty()["flexibility"]
    except (KeyError, TypeError):
        difficulty = 1
    
    # Get baseline for context
    baseline = session.exec(
        select(BaselineAssessment)
        .where(BaselineAssessment.user_id == user_id)
        .order_by(desc(BaselineAssessment.created_at))
    ).first()
    
    baseline_flexibility = None
    if baseline and baseline.raw_metrics:
        try:
            metrics = json.loads(baseline.raw_metrics)
            baseline_flexibility = metrics.get("flexibility", {}).get("score", 50)
        except:
            baseline_flexibility = None
    
    # Generate WCST session
    wcst_task = WCSTTask()
    session_data = wcst_task.generate_session(difficulty=difficulty)
    
    return {
        "success": True,
        "session_data": session_data,
        "difficulty": difficulty,
        "baseline_flexibility": baseline_flexibility,
        "instructions": {
            "title": "Wisconsin Card Sorting Test",
            "description": "Sort cards by matching them to one of the four piles. The sorting rule (color, shape, or number) will change without warning. Use the feedback to figure out the current rule.",
            "tips": [
                "Pay attention to whether your sorts are correct or wrong",
                "When you get several 'Wrong' feedback in a row, the rule has probably changed",
                "Try different rules (color, shape, number) to discover the current one",
                "Don't get stuck on a rule that's no longer working"
            ]
        }
    }


class WCSTSubmission(BaseModel):
    session_data: Dict[str, Any]
    responses: List[Dict[str, Any]]  # trial_index, selected_pile, response_time
    total_time: int


@router.post("/tasks/wcst/submit/{user_id}")
def submit_wcst_session(
    user_id: int,
    submission: WCSTSubmission,
    session: Session = Depends(get_session)
):
    """
    Score and save WCST session results
    
    Tracks:
    - Categories achieved
    - Perseverative errors (stuck on old rule)
    - Non-perseverative errors
    - Trials to first category
    - Set-shifting ability
    """
    from app.services.wcst_task import WCSTTask
    from app.services.badge_service import BadgeService
    
    # Get user's training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .order_by(desc(TrainingPlan.created_at))
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No training plan found")
    if not plan.id:
        raise HTTPException(status_code=500, detail="Invalid training plan")

    enforce_session_limits(plan, session, user_id)
    
    # Extract task_id for session tracking
    task_id = submission.session_data.get("task_id")
    
    # Get baseline for context
    baseline = session.exec(
        select(BaselineAssessment)
        .where(BaselineAssessment.user_id == user_id)
        .order_by(desc(BaselineAssessment.created_at))
    ).first()
    
    baseline_flexibility: Optional[float] = None
    if baseline and baseline.raw_metrics:
        try:
            metrics = json.loads(baseline.raw_metrics)
            score = metrics.get("flexibility", {}).get("score", 50)
            baseline_flexibility = float(score) if score is not None else None
        except:
            baseline_flexibility = None
    
    # Score session
    wcst_task = WCSTTask()
    result = wcst_task.score_session(
        session_data=submission.session_data,
        responses=submission.responses,
        baseline_flexibility=baseline_flexibility
    )
    
    # Get current difficulty
    current_difficulty = submission.session_data["difficulty"]
    
    # Adaptive difficulty adjustment
    # Excellent/Good + low errors → increase
    # Needs Improvement/Struggling → decrease
    new_difficulty = current_difficulty
    
    if result["performance_category"] in ["Excellent", "Good"] and result["total_errors"] <= 10:
        new_difficulty = min(10, current_difficulty + 1)
    elif result["performance_category"] in ["Needs Improvement", "Struggling"]:
        new_difficulty = max(1, current_difficulty - 1)
    
    # Update training plan difficulty
    current_difficulties = plan.get_current_difficulty()
    current_difficulties["flexibility"] = new_difficulty
    plan.current_difficulty = json.dumps(current_difficulties)
    session.add(plan)
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="flexibility",
        task_type="wcst",
        difficulty_level=current_difficulty,
        difficulty_before=current_difficulty,
        difficulty_after=new_difficulty,
        score=result["score"],
        accuracy=result["accuracy"],
        average_reaction_time=result["average_response_time"],
        consistency=100 - result["perseverative_error_rate"],  # Inverse of perseveration
        errors=result["total_errors"],
        duration=submission.total_time,
        completed=True,
        raw_data=json.dumps({
            "categories_achieved": result["categories_achieved"],
            "trials_to_first_category": result["trials_to_first_category"],
            "perseverative_errors": result["perseverative_errors"],
            "non_perseverative_errors": result["non_perseverative_errors"],
            "perseverative_error_rate": result["perseverative_error_rate"],
            "rule_changes": result["rule_changes"],
            "rule_change_details": result["rule_change_details"],
            "performance_category": result["performance_category"],
            "feedback": result["feedback"],
            "total_trials": result["total_trials"],
        })
    )
    
    session.add(training_session)
    
    # Track session completion
    session_info = track_session_completion(plan, "flexibility", session, user_id, task_id)
    
    session.commit()
    session.refresh(training_session)
    
    return {
        "success": True,
        "score": result["score"],
        "accuracy": result["accuracy"],
        "categories_achieved": result["categories_achieved"],
        "trials_to_first_category": result["trials_to_first_category"],
        "perseverative_errors": result["perseverative_errors"],
        "non_perseverative_errors": result["non_perseverative_errors"],
        "perseverative_error_rate": result["perseverative_error_rate"],
        "total_errors": result["total_errors"],
        "total_trials": result["total_trials"],
        "average_response_time": result["average_response_time"],
        "performance_category": result["performance_category"],
        "feedback": result["feedback"],
        "new_difficulty": new_difficulty,
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"],
        "session_id": training_session.id
    }


# ============================================================================
# STOCKINGS OF CAMBRIDGE (SOC) - Planning Task
# ============================================================================

@router.post("/tasks/soc/generate/{user_id}")
def generate_soc_session(
    user_id: int,
    session: Session = Depends(get_session)
):
    """Generate a Stockings of Cambridge task session."""
    from app.services.soc_task import soc_task_service
    
    # Get user's training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")
    
    # Get current difficulty
    current_difficulty = plan.current_difficulty
    if isinstance(current_difficulty, str):
        current_difficulty = json.loads(current_difficulty)
    
    difficulty = current_difficulty.get("planning", 1)
    
    # Generate session
    session_data = soc_task_service.generate_session(difficulty)
    
    return {
        "session_data": session_data,
        "difficulty": difficulty,
        "user_id": user_id
    }


@router.post("/tasks/soc/submit/{user_id}")
def submit_soc_session(
    user_id: int,
    request_data: dict = Body(...),
    session: Session = Depends(get_session)
):
    """Submit and score a Stockings of Cambridge session."""
    from app.services.soc_task import soc_task_service
    from app.services.badge_service import BadgeService
    
    # Get user's training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .order_by(desc(TrainingPlan.created_at))
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No training plan found")
    if not plan.id:
        raise HTTPException(status_code=500, detail="Invalid training plan")

    enforce_session_limits(plan, session, user_id)
    
    # Get baseline
    baseline = session.exec(
        select(BaselineAssessment)
        .where(BaselineAssessment.user_id == user_id)
        .order_by(desc(BaselineAssessment.created_at))
    ).first()
    
    baseline_planning: Optional[float] = None
    if baseline:
        baseline_planning = baseline.planning_score
    
    # Extract task_id for session tracking
    task_id = request_data.get("task_id")
    
    # Score the session
    session_data = request_data.get("session_data")
    user_solutions = request_data.get("user_solutions")
    
    if not session_data or not user_solutions:
        raise HTTPException(status_code=400, detail="Missing session_data or user_solutions")
    
    results = soc_task_service.score_session(session_data, user_solutions)
    
    difficulty = session_data.get("difficulty", 1)
    
    # Adaptive difficulty calculation (before creating session)
    new_difficulty = difficulty
    if results["score"] >= 85 and difficulty < 10:
        new_difficulty = difficulty + 1
    elif results["score"] < 65 and difficulty > 1:
        new_difficulty = difficulty - 1
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="planning",
        task_type="stockings_of_cambridge",
        score=results["score"],
        accuracy=results["planning_efficiency"] * 100,
        average_reaction_time=int(results.get("average_time_per_problem", 0) * 1000),
        consistency=0,
        errors=results["total_problems"] - results["problems_solved"],
        duration=int(results.get("total_time", 0)),
        difficulty_level=new_difficulty,
        difficulty_before=difficulty,
        difficulty_after=new_difficulty,
        raw_data=json.dumps(results)
    )
    session.add(training_session)
    
    # Adaptive difficulty
    current_diff = plan.current_difficulty
    if isinstance(current_diff, str):
        current_diff = json.loads(current_diff)
    else:
        current_diff = {}
    
    old_difficulty = difficulty
    new_difficulty = difficulty
    adaptation_reason = "Maintaining difficulty"
    
    if results["score"] >= 85 and difficulty < 10:
        new_difficulty = difficulty + 1
        adaptation_reason = f"Excellent performance! ({results['score']}%)"
    elif results["score"] < 65 and difficulty > 1:
        new_difficulty = difficulty - 1
        adaptation_reason = f"Adjusting for better success ({results['score']}%)"
    
    current_diff["planning"] = new_difficulty
    plan.current_difficulty = json.dumps(current_diff)
    
    # Update plan stats
    plan.last_session_date = datetime.utcnow()
    
    # Track session completion
    session_info = track_session_completion(plan, "planning", session, user_id, task_id)
    
    session.commit()
    session.refresh(training_session)
    
    return {
        "success": True,
        "score": results["score"],
        "problems_solved": results["problems_solved"],
        "perfect_solutions": results["perfect_solutions"],
        "planning_efficiency": results["planning_efficiency"],
        "new_difficulty": new_difficulty,
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"],
        "session_id": training_session.id
    }


# ============================================================================
# VERBAL FLUENCY (COWAT) - Planning/Executive Function
# ============================================================================

@router.post("/tasks/verbal-fluency/generate/{user_id}")
def generate_verbal_fluency_session(
    user_id: int,
    locale: str = "en",
    session: Session = Depends(get_session)
):
    """Generate a Verbal Fluency (COWAT) task session."""
    from app.services.verbal_fluency_task import verbal_fluency_task_service
    
    # Get user's training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")
    
    # Get current difficulty
    current_difficulty = plan.current_difficulty
    if isinstance(current_difficulty, str):
        current_difficulty = json.loads(current_difficulty)
    
    difficulty = current_difficulty.get("planning", 1)
    
    # Generate session
    session_data = verbal_fluency_task_service.generate_session(difficulty, locale=locale)
    
    return {
        "session_data": session_data,
        "difficulty": difficulty,
        "user_id": user_id
    }


@router.post("/tasks/verbal-fluency/submit/{user_id}")
def submit_verbal_fluency_session(
    user_id: int,
    request_data: dict = Body(...),
    session: Session = Depends(get_session)
):
    """Submit and score a Verbal Fluency session."""
    from app.services.verbal_fluency_task import verbal_fluency_task_service
    from app.services.badge_service import BadgeService
    
    # Get user's training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .order_by(desc(TrainingPlan.created_at))
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No training plan found")
    if not plan.id:
        raise HTTPException(status_code=500, detail="Invalid training plan")

    enforce_session_limits(plan, session, user_id)
    
    # Get baseline
    baseline = session.exec(
        select(BaselineAssessment)
        .where(BaselineAssessment.user_id == user_id)
        .order_by(desc(BaselineAssessment.created_at))
    ).first()
    
    baseline_planning: Optional[float] = None
    if baseline:
        baseline_planning = baseline.planning_score
    
    # Score the session
    session_data = request_data.get("session_data")
    user_responses = request_data.get("user_responses")
    task_id = request_data.get("task_id")  # Extract task_id for session tracking
    
    if not session_data or not user_responses:
        raise HTTPException(status_code=400, detail="Missing session_data or user_responses")
    
    results = verbal_fluency_task_service.score_session(session_data, user_responses)
    
    difficulty = session_data.get("difficulty", 1)
    
    # Adaptive difficulty calculation (before creating session)
    new_difficulty = difficulty
    if results["score"] >= 85 and difficulty < 10:
        new_difficulty = difficulty + 1
    elif results["score"] < 65 and difficulty > 1:
        new_difficulty = difficulty - 1
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="planning",
        task_type="verbal_fluency",
        score=results["score"],
        accuracy=results["score"],  # Use score as accuracy for verbal tasks
        average_reaction_time=0,  # Not applicable for verbal fluency
        consistency=0,
        errors=results["total_invalid_words"],
        duration=len(results["letter_results"]) * session_data.get("time_per_letter_seconds", 60),
        difficulty_level=new_difficulty,
        difficulty_before=difficulty,
        difficulty_after=new_difficulty,
        raw_data=json.dumps(results)
    )
    session.add(training_session)
    
    # Adaptive difficulty
    current_diff = plan.current_difficulty
    if isinstance(current_diff, str):
        current_diff = json.loads(current_diff)
    else:
        current_diff = {}
    
    old_difficulty = difficulty
    new_difficulty = difficulty
    adaptation_reason = "Maintaining difficulty"
    
    if results["score"] >= 85 and difficulty < 10:
        new_difficulty = difficulty + 1
        adaptation_reason = f"Excellent performance! ({results['score']}%)"
    elif results["score"] < 65 and difficulty > 1:
        new_difficulty = difficulty - 1
        adaptation_reason = f"Adjusting for better success ({results['score']}%)"
    
    current_diff["planning"] = new_difficulty
    plan.current_difficulty = json.dumps(current_diff)
    
    # Update plan stats
    plan.last_session_date = datetime.utcnow()
    
    # Track session completion
    session_info = track_session_completion(plan, "planning", session, user_id, task_id)
    
    session.commit()
    session.refresh(training_session)
    
    return {
        "success": True,
        "score": results["score"],
        "total_valid_words": results["total_valid_words"],
        "avg_words_per_letter": results["avg_words_per_letter"],
        "performance": results["performance"],
        "new_difficulty": new_difficulty,
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"],
        "session_id": training_session.id
    }


# ============================================================================
# DCCS - Cognitive Flexibility
# ============================================================================

@router.post("/tasks/dccs/generate/{user_id}")
def generate_dccs_session(
    user_id: int,
    session: Session = Depends(get_session)
):
    """Generate a DCCS task session."""
    from app.services.dccs_task import dccs_task_service
    
    # Get user's training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")
    
    # Get current difficulty
    current_difficulty = plan.current_difficulty
    if isinstance(current_difficulty, str):
        current_difficulty = json.loads(current_difficulty)
    
    difficulty = current_difficulty.get("flexibility", 1)
    
    # Generate session
    session_data = dccs_task_service.generate_session(difficulty)
    
    return {
        "session_data": session_data,
        "difficulty": difficulty,
        "user_id": user_id
    }


@router.post("/tasks/dccs/submit/{user_id}")
def submit_dccs_session(
    user_id: int,
    request_data: dict = Body(...),
    session: Session = Depends(get_session)
):
    """Submit and score a DCCS session."""
    from app.services.dccs_task import dccs_task_service
    from app.services.badge_service import BadgeService
    
    # Get user's training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .order_by(desc(TrainingPlan.created_at))
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No training plan found")
    if not plan.id:
        raise HTTPException(status_code=500, detail="Invalid training plan")

    enforce_session_limits(plan, session, user_id)
    
    # Score the session
    session_data = request_data.get("session_data")
    user_responses = request_data.get("user_responses")
    task_id = request_data.get("task_id")  # Extract task_id for session tracking
    
    if not session_data or not user_responses:
        raise HTTPException(status_code=400, detail="Missing session_data or user_responses")
    
    results = dccs_task_service.score_session(session_data, user_responses)
    
    difficulty = session_data.get("difficulty", 1)
    
    # Adaptive difficulty calculation (before creating session)
    new_difficulty = difficulty
    if results["score"] >= 85 and difficulty < 10:
        new_difficulty = difficulty + 1
    elif results["score"] < 65 and difficulty > 1:
        new_difficulty = difficulty - 1
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="flexibility",
        task_type="dccs",
        score=results["score"],
        accuracy=results["accuracy"],
        average_reaction_time=int(results["mean_rt"]),
        consistency=0,
        errors=results["total_trials"] - results["correct_trials"],
        duration=int(results.get("total_time", 0)),
        difficulty_level=new_difficulty,
        difficulty_before=difficulty,
        difficulty_after=new_difficulty,
        raw_data=json.dumps(results)
    )
    session.add(training_session)
    
    # Adaptive difficulty
    current_diff = plan.current_difficulty
    if isinstance(current_diff, str):
        current_diff = json.loads(current_diff)
    else:
        current_diff = {}
    
    new_difficulty = difficulty
    adaptation_reason = "Maintaining difficulty"
    
    if results["score"] >= 85 and difficulty < 10:
        new_difficulty = difficulty + 1
        adaptation_reason = f"Excellent performance! ({results['score']}%)"
    elif results["score"] < 65 and difficulty > 1:
        new_difficulty = difficulty - 1
        adaptation_reason = f"Adjusting for better success ({results['score']}%)"
    
    current_diff["flexibility"] = new_difficulty
    plan.current_difficulty = json.dumps(current_diff)
    
    # Update plan stats
    plan.last_session_date = datetime.utcnow()
    
    # Track session completion
    session_info = track_session_completion(plan, "flexibility", session, user_id, task_id)
    
    session.commit()
    session.refresh(training_session)
    
    return {
        "success": True,
        "score": results["score"],
        "accuracy": results["accuracy"],
        "overall_accuracy": results["accuracy"],
        "switch_cost_rt": results["switch_cost"],
        "switch_accuracy": results["phases"].get("phase3", {}).get("accuracy", 0.0) if "phase3" in results["phases"] else 0.0,
        "phases": results["phases"],
        "new_difficulty": new_difficulty,
        "newly_earned_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"],
        "session_id": training_session.id
    }


# ============================================================================
# RULE SHIFT TASK - Cognitive Flexibility
# ============================================================================

@router.post("/tasks/rule-shift/generate/{user_id}")
def generate_rule_shift_session(
    user_id: int,
    difficulty: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """Generate a Rule Shift task session."""
    from app.services.rule_shift_task import RuleShiftTask

    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()

    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")

    if difficulty is None:
        current_difficulty = plan.current_difficulty
        if isinstance(current_difficulty, str):
            current_difficulty = json.loads(current_difficulty)
        if current_difficulty is None:
            current_difficulty = {}
        difficulty = current_difficulty.get("flexibility", 5)

    difficulty_level = difficulty if isinstance(difficulty, int) else 5
    difficulty_level = max(1, min(10, difficulty_level))

    session_data = RuleShiftTask.generate_session(difficulty_level)

    return {
        "task_code": "rule_shift",
        "domain": "flexibility",
        "session_data": session_data,
        "difficulty": difficulty_level,
        "user_id": user_id
    }


@router.post("/tasks/rule-shift/submit/{user_id}")
def submit_rule_shift_session(
    user_id: int,
    request_data: dict,
    session: Session = Depends(get_session)
):
    """Submit and score a Rule Shift session."""
    from app.services.rule_shift_task import RuleShiftTask

    difficulty = request_data.get("difficulty")
    session_data = request_data.get("session_data")
    responses = request_data.get("responses", [])
    task_id = request_data.get("task_id")

    if difficulty is None or session_data is None:
        raise HTTPException(status_code=400, detail="difficulty and session_data are required")
    if not isinstance(responses, list):
        raise HTTPException(status_code=400, detail="responses must be a list")

    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()

    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")

    enforce_session_limits(plan, session, user_id)

    if plan.id is None:
        raise HTTPException(status_code=500, detail="Invalid training plan")

    results = RuleShiftTask.score_session(session_data, responses)
    metrics = results["metrics"]
    total_duration_ms = sum(float(response.get("reaction_time_ms", 0) or 0) for response in responses)
    duration_seconds = max(1, int(total_duration_ms / 1000)) if responses else 1

    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="flexibility",
        task_type="rule_shift",
        task_code="rule_shift",
        score=metrics["score"],
        accuracy=metrics["accuracy"],
        average_reaction_time=metrics["average_reaction_time"],
        consistency=metrics["consistency"],
        errors=metrics["total_trials"] - metrics["correct_count"],
        difficulty_level=difficulty,
        difficulty_before=difficulty,
        difficulty_after=results["difficulty_adjustment"],
        duration=duration_seconds,
        raw_data=json.dumps({
            "session_data": session_data,
            "responses": responses,
            "scored_trials": results["scored_trials"],
            "switch_accuracy": metrics["switch_accuracy"],
            "stay_accuracy": metrics["stay_accuracy"],
            "shift_cost_ms": metrics["shift_cost_ms"],
            "perseverative_errors": metrics["perseverative_errors"],
            "flexibility_index": metrics["flexibility_index"],
        }),
        adaptation_reason=results["adaptation_reason"]
    )
    session.add(training_session)

    current_difficulty = plan.current_difficulty
    if isinstance(current_difficulty, str):
        current_difficulty = json.loads(current_difficulty)
    if current_difficulty is None:
        current_difficulty = {}

    current_difficulty["flexibility"] = results["difficulty_adjustment"]
    plan.current_difficulty = json.dumps(current_difficulty)

    session_info = track_session_completion(plan, "flexibility", session, user_id, task_id)

    session.commit()
    session.refresh(training_session)

    return {
        "session_id": training_session.id,
        "metrics": metrics,
        "difficulty_before": difficulty,
        "difficulty_after": results["difficulty_adjustment"],
        "adaptation_reason": results["adaptation_reason"],
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"]
    }


# ============================================================================
# PLUS-MINUS TASK - Cognitive Flexibility
# ============================================================================

@router.post("/tasks/plus-minus/generate/{user_id}")
def generate_plus_minus_session(
    user_id: int,
    session: Session = Depends(get_session)
):
    """Generate a Plus-Minus task session."""
    from app.services.plus_minus_task import plus_minus_task_service
    
    # Get user's training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")
    
    # Get current difficulty
    current_difficulty = plan.current_difficulty
    if isinstance(current_difficulty, str):
        current_difficulty = json.loads(current_difficulty)
    
    difficulty = current_difficulty.get("flexibility", 1)
    
    # Generate session
    session_data = plus_minus_task_service.generate_session(difficulty)
    
    return {
        "session_data": session_data,
        "difficulty": difficulty,
        "user_id": user_id
    }


@router.post("/tasks/plus-minus/submit/{user_id}")
def submit_plus_minus_session(
    user_id: int,
    request_data: dict = Body(...),
    session: Session = Depends(get_session)
):
    """Submit and score a Plus-Minus session."""
    from app.services.plus_minus_task import plus_minus_task_service
    from app.services.badge_service import BadgeService
    
    # Get user's training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .order_by(desc(TrainingPlan.created_at))
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No training plan found")
    if not plan.id:
        raise HTTPException(status_code=500, detail="Invalid training plan")

    enforce_session_limits(plan, session, user_id)
    
    # Score the session
    session_data = request_data.get("session_data")
    user_responses = request_data.get("user_responses")
    total_time = request_data.get("total_time", 0)  # Get total elapsed time from frontend
    task_id = request_data.get("task_id")  # Extract task_id for session tracking
    
    if not session_data or not user_responses:
        raise HTTPException(status_code=400, detail="Missing session_data or user_responses")
    
    results = plus_minus_task_service.score_session(session_data, user_responses)
    
    # Add total_time to results
    results["total_time"] = total_time

    difficulty = session_data.get("difficulty", 1)
    
    # Adaptive difficulty calculation (before creating session)
    new_difficulty = difficulty
    if results["score"] >= 85 and difficulty < 10:
        new_difficulty = difficulty + 1
    elif results["score"] < 65 and difficulty > 1:
        new_difficulty = difficulty - 1
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="flexibility",
        task_type="plus_minus",
        score=results["score"],
        accuracy=results["overall_accuracy"],
        average_reaction_time=int(results["average_rt"]),
        consistency=0,
        errors=results["total_errors"],
        duration=int(results.get("total_time", 0)),
        difficulty_level=new_difficulty,
        difficulty_before=difficulty,
        difficulty_after=new_difficulty,
        raw_data=json.dumps(results)
    )
    session.add(training_session)
    
    # Adaptive difficulty
    current_diff = plan.current_difficulty
    if isinstance(current_diff, str):
        current_diff = json.loads(current_diff)
    else:
        current_diff = {}
    
    new_difficulty = difficulty
    adaptation_reason = "Maintaining difficulty"
    
    if results["score"] >= 85 and difficulty < 10:
        new_difficulty = difficulty + 1
        adaptation_reason = f"Excellent performance! ({results['score']}%)"
    elif results["score"] < 65 and difficulty > 1:
        new_difficulty = difficulty - 1
        adaptation_reason = f"Adjusting for better success ({results['score']}%)"
    
    current_diff["flexibility"] = new_difficulty
    plan.current_difficulty = json.dumps(current_diff)
    
    # Update plan stats
    plan.last_session_date = datetime.utcnow()
    
    # Track session completion
    session_info = track_session_completion(plan, "flexibility", session, user_id, task_id)
    
    session.commit()
    session.refresh(training_session)
    
    return {
        "success": True,
        "score": results["score"],
        "accuracy": results["accuracy"],
        "overall_accuracy": results["overall_accuracy"],
        "switching_cost": results["switching_cost"],
        "switching_cost_accuracy": results["switching_cost_accuracy"],
        "switch_accuracy": results["switch_accuracy"],
        "average_rt": results["average_rt"],
        "total_errors": results["total_errors"],
        "blocks": results["blocks"],  # Include block-level results for frontend
        "new_difficulty": new_difficulty,
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"],
        "session_id": training_session.id
    }


# ============================================================================
# CATEGORY FLUENCY (Semantic Fluency) - Planning/Executive Function
# ============================================================================

@router.post("/tasks/category-fluency/generate/{user_id}")
def generate_category_fluency_trial(
    user_id: int,
    session: Session = Depends(get_session)
):
    """Generate a Category Fluency (Semantic Fluency) trial."""
    from app.services.category_fluency_task import CategoryFluencyTask
    
    # Get user's training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")
    
    # Get current difficulty
    current_difficulty = plan.current_difficulty
    if isinstance(current_difficulty, str):
        current_difficulty = json.loads(current_difficulty)
    
    difficulty = current_difficulty.get("planning", 1)
    
    # Generate trial
    trial_data = CategoryFluencyTask.generate_trial(difficulty)
    
    return {
        "trial_data": trial_data,
        "difficulty": difficulty,
        "user_id": user_id
    }


@router.post("/tasks/category-fluency/submit/{user_id}")
def submit_category_fluency_trial(
    user_id: int,
    request_data: dict = Body(...),
    session: Session = Depends(get_session)
):
    """Submit and score a Category Fluency trial."""
    from app.services.category_fluency_task import CategoryFluencyTask
    from app.services.badge_service import BadgeService
    
    # Get user's training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .order_by(desc(TrainingPlan.created_at))
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No training plan found")
    if not plan.id:
        raise HTTPException(status_code=500, detail="Invalid training plan")

    enforce_session_limits(plan, session, user_id)
    
    # Get baseline
    baseline = session.exec(
        select(BaselineAssessment)
        .where(BaselineAssessment.user_id == user_id)
        .order_by(desc(BaselineAssessment.created_at))
    ).first()
    
    baseline_planning: Optional[float] = None
    if baseline:
        baseline_planning = baseline.planning_score
    
    # Get trial data
    submitted_words = request_data.get("submitted_words", [])
    time_taken_seconds = request_data.get("time_taken_seconds", 60)
    difficulty = request_data.get("difficulty", 1)
    category_name = request_data.get("category_name", "Unknown")
    task_id = request_data.get("task_id")  # Extract task_id for session tracking
    
    if not isinstance(submitted_words, list):
        raise HTTPException(status_code=400, detail="submitted_words must be a list")
    
    # Score the trial
    results = CategoryFluencyTask.score_response(
        submitted_words=submitted_words,
        time_taken_seconds=time_taken_seconds,
        difficulty=difficulty
    )
    
    # Calculate new difficulty using the task's adaptive algorithm
    new_difficulty = CategoryFluencyTask.calculate_difficulty_adjustment(
        current_difficulty=difficulty,
        performance=results
    )
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="planning",
        task_type="category_fluency",
        score=results["normalized_score"],
        accuracy=results["normalized_score"],  # Use score as accuracy for fluency tasks
        average_reaction_time=0,  # Not applicable for fluency tasks
        consistency=0,
        errors=results["invalid_count"] + results["duplicate_count"],
        duration=int(time_taken_seconds),
        difficulty_level=new_difficulty,
        difficulty_before=difficulty,
        difficulty_after=new_difficulty,
        raw_data=json.dumps({
            "category": category_name,
            "unique_count": results["unique_count"],
            "total_submitted": results["total_submitted"],
            "duplicate_count": results["duplicate_count"],
            "invalid_count": results["invalid_count"],
            "performance_rating": results["performance_rating"],
            "words_per_second": results["words_per_second"],
            "unique_words": results["unique_words"]
        })
    )
    session.add(training_session)
    
    # Update training plan difficulty
    current_diff = plan.current_difficulty
    if isinstance(current_diff, str):
        current_diff = json.loads(current_diff)
    else:
        current_diff = {}
    
    old_difficulty = difficulty
    adaptation_reason = "Maintaining difficulty"
    
    if new_difficulty > old_difficulty:
        adaptation_reason = f"Excellent performance! ({results['unique_count']} unique words)"
    elif new_difficulty < old_difficulty:
        adaptation_reason = f"Adjusting for better success ({results['unique_count']} unique words)"
    
    current_diff["planning"] = new_difficulty
    plan.current_difficulty = json.dumps(current_diff)
    
    # Update plan stats
    plan.last_session_date = datetime.utcnow()
    
    # Track session completion
    session_info = track_session_completion(plan, "planning", session, user_id, task_id)
    
    session.commit()
    session.refresh(training_session)
    
    return {
        "success": True,
        "score": results["normalized_score"],
        "unique_count": results["unique_count"],
        "total_submitted": results["total_submitted"],
        "duplicate_count": results["duplicate_count"],
        "performance_rating": results["performance_rating"],
        "words_per_second": results["words_per_second"],
        "feedback": results["feedback"],
        "new_difficulty": new_difficulty,
        "old_difficulty": old_difficulty,
        "adaptation_reason": adaptation_reason,
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"],
        "session_id": training_session.id
    }


# ============================================================================
# TWENTY QUESTIONS - Planning/Executive Function (Strategic Problem-Solving)
# ============================================================================

@router.post("/tasks/twenty-questions/generate/{user_id}")
def generate_twenty_questions_game(
    user_id: int,
    session: Session = Depends(get_session)
):
    """Generate a Twenty Questions game."""
    from app.services.twenty_questions_task import TwentyQuestionsTask
    
    # Get user's training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")
    
    # Get current difficulty
    current_difficulty = plan.current_difficulty
    if isinstance(current_difficulty, str):
        current_difficulty = json.loads(current_difficulty)
    
    difficulty = current_difficulty.get("planning", 1)
    
    # Generate game
    game_data = TwentyQuestionsTask.generate_game(difficulty)
    
    return {
        "game_data": game_data,
        "difficulty": difficulty,
        "user_id": user_id
    }


@router.post("/tasks/twenty-questions/ask/{user_id}")
def ask_question_twenty_questions(
    user_id: int,
    request_data: dict = Body(...),
    session: Session = Depends(get_session)
):
    """
    Answer a question in the Twenty Questions game.
    This endpoint allows the user to ask a question and get an answer.
    """
    from app.services.twenty_questions_task import TwentyQuestionsTask
    
    question = request_data.get("question", "")
    target_attributes = request_data.get("target_attributes", {})
    target_object_name = request_data.get("target_object_name", None)
    
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    
    if not target_attributes:
        raise HTTPException(status_code=400, detail="Target attributes are required")
    
    # Get answer from the task service
    answer_data = TwentyQuestionsTask.answer_question(question, target_attributes, target_object_name)
    
    return {
        "question": question,
        "answer": answer_data["answer"],
        "confidence": answer_data["confidence"]
    }


@router.post("/tasks/twenty-questions/submit/{user_id}")
def submit_twenty_questions_game(
    user_id: int,
    request_data: dict = Body(...),
    session: Session = Depends(get_session)
):
    """Submit and score a Twenty Questions game."""
    from app.services.twenty_questions_task import TwentyQuestionsTask
    from app.services.badge_service import BadgeService
    
    # Get user's training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .order_by(desc(TrainingPlan.created_at))
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No training plan found")
    if not plan.id:
        raise HTTPException(status_code=500, detail="Invalid training plan")

    enforce_session_limits(plan, session, user_id)
    
    # Get baseline
    baseline = session.exec(
        select(BaselineAssessment)
        .where(BaselineAssessment.user_id == user_id)
        .order_by(desc(BaselineAssessment.created_at))
    ).first()
    
    baseline_planning: Optional[float] = None
    if baseline:
        baseline_planning = baseline.planning_score
    
    # Get game data
    questions_asked = request_data.get("questions_asked", 0)
    correctly_identified = request_data.get("correctly_identified", False)
    difficulty = request_data.get("difficulty", 1)
    questions_history = request_data.get("questions_history", [])
    target_object_name = request_data.get("target_object_name", "Unknown")
    user_guess = request_data.get("user_guess", "")
    task_id = request_data.get("task_id")  # Extract task_id for session tracking
    
    # Score the game
    results = TwentyQuestionsTask.score_game(
        questions_asked=questions_asked,
        correctly_identified=correctly_identified,
        difficulty=difficulty,
        questions_history=questions_history
    )
    
    # Calculate new difficulty using the task's adaptive algorithm
    new_difficulty = TwentyQuestionsTask.calculate_difficulty_adjustment(
        current_difficulty=difficulty,
        performance=results
    )
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=plan.id,
        domain="planning",
        task_type="twenty_questions",
        score=results["normalized_score"],
        accuracy=results["normalized_score"],  # Use score as accuracy
        average_reaction_time=0,  # Not applicable for this task
        consistency=0,
        errors=questions_asked if not correctly_identified else max(0, questions_asked - 10),
        duration=questions_asked * 30,  # Estimate 30 seconds per question
        difficulty_level=new_difficulty,
        difficulty_before=difficulty,
        difficulty_after=new_difficulty,
        raw_data=json.dumps({
            "target_object": target_object_name,
            "user_guess": user_guess,
            "questions_asked": questions_asked,
            "correctly_identified": correctly_identified,
            "strategy_score": results["strategy_score"],
            "constraint_seeking_questions": results["constraint_seeking_questions"],
            "specific_guesses": results["specific_guesses"],
            "questions_history": questions_history
        })
    )
    session.add(training_session)
    
    # Update training plan difficulty
    current_diff = plan.current_difficulty
    
    if isinstance(current_diff, str):
        current_diff = json.loads(current_diff)
    else:
        current_diff = {}
    
    old_difficulty = difficulty
    adaptation_reason = "Maintaining difficulty"
    
    if new_difficulty > old_difficulty:
        adaptation_reason = f"Excellent efficiency! ({questions_asked} questions)"
    elif new_difficulty < old_difficulty:
        if not correctly_identified:
            adaptation_reason = "Did not identify correctly"
        else:
            adaptation_reason = f"Adjusting for better efficiency ({questions_asked} questions)"
    
    current_diff["planning"] = new_difficulty
    plan.current_difficulty = json.dumps(current_diff)
    
    # Update plan stats
    plan.last_session_date = datetime.utcnow()
    
    # Track session completion
    session_info = track_session_completion(plan, "planning", session, user_id, task_id)
    
    session.commit()
    session.refresh(training_session)
    
    return {
        "success": True,
        "score": results["normalized_score"],
        "performance_rating": results["performance_rating"],
        "questions_asked": questions_asked,
        "correctly_identified": correctly_identified,
        "question_efficiency": results["question_efficiency"],
        "strategy_score": results["strategy_score"],
        "constraint_seeking_questions": results["constraint_seeking_questions"],
        "specific_guesses": results["specific_guesses"],
        "feedback": results["feedback"],
        "tips": results["tips"],
        "new_difficulty": new_difficulty,
        "old_difficulty": old_difficulty,
        "adaptation_reason": adaptation_reason,
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"],
        "session_id": training_session.id
    }


# ============================================================================
# LANDMARK TASK ENDPOINTS
# ============================================================================

@router.post("/tasks/landmark-task/generate/{user_id}")
def generate_landmark_task_session(
    user_id: int,
    difficulty: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """Generate a Landmark Task session."""
    from app.services.landmark_task import LandmarkTask

    training_plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .order_by(desc(TrainingPlan.created_at))
    ).first()

    if not training_plan:
        raise HTTPException(status_code=404, detail="No training plan found")

    if difficulty is None:
        current_difficulty = training_plan.current_difficulty
        if isinstance(current_difficulty, str):
            current_difficulty = json.loads(current_difficulty)
        if current_difficulty is None:
            current_difficulty = {}
        difficulty = current_difficulty.get("visual_scanning", 5)

    difficulty_level = difficulty if isinstance(difficulty, int) else 5
    difficulty_level = max(1, min(10, difficulty_level))
    session_data = LandmarkTask.generate_session(difficulty_level)

    return {
        "task_code": "landmark_task",
        "domain": "visual_scanning",
        "session_data": session_data,
        "difficulty": difficulty_level,
        "user_id": user_id
    }


@router.post("/tasks/landmark-task/submit/{user_id}")
def submit_landmark_task_session(
    user_id: int,
    request_data: dict = Body(...),
    session: Session = Depends(get_session)
):
    """Submit and score a Landmark Task session."""
    from app.services.landmark_task import LandmarkTask

    difficulty = request_data.get("difficulty")
    session_data = request_data.get("session_data")
    responses = request_data.get("responses", [])
    task_id = request_data.get("task_id")

    if difficulty is None or session_data is None:
        raise HTTPException(status_code=400, detail="difficulty and session_data are required")
    if not isinstance(responses, list):
        raise HTTPException(status_code=400, detail="responses must be a list")

    training_plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .order_by(desc(TrainingPlan.created_at))
    ).first()

    if not training_plan:
        raise HTTPException(status_code=404, detail="No training plan found")

    enforce_session_limits(training_plan, session, user_id)

    if training_plan.id is None:
        raise HTTPException(status_code=500, detail="Invalid training plan")

    results = LandmarkTask.score_session(session_data, responses)
    metrics = results["metrics"]
    total_duration_ms = sum(float(response.get("reaction_time_ms", 0) or 0) for response in responses)
    duration_seconds = max(1, int(total_duration_ms / 1000)) if responses else 1

    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=training_plan.id,
        domain="visual_scanning",
        task_type="landmark_task",
        task_code="landmark_task",
        score=metrics["score"],
        accuracy=metrics["accuracy"],
        average_reaction_time=metrics["average_reaction_time"],
        consistency=metrics["consistency"],
        errors=metrics["total_trials"] - metrics["correct_count"],
        duration=duration_seconds,
        difficulty_level=results["difficulty_adjustment"],
        difficulty_before=difficulty,
        difficulty_after=results["difficulty_adjustment"],
        raw_data=json.dumps({
            "session_data": session_data,
            "responses": responses,
            "scored_trials": results["scored_trials"],
            "offset_accuracy": metrics["offset_accuracy"],
            "centered_accuracy": metrics["centered_accuracy"],
            "spatial_bias_index": metrics["spatial_bias_index"],
            "left_bias_errors": metrics["left_bias_errors"],
            "right_bias_errors": metrics["right_bias_errors"],
            "center_misses": metrics["center_misses"],
        }),
        adaptation_reason=results["adaptation_reason"]
    )

    session.add(training_session)

    current_difficulty = training_plan.current_difficulty
    if isinstance(current_difficulty, str):
        current_difficulty = json.loads(current_difficulty)
    if current_difficulty is None:
        current_difficulty = {}

    current_difficulty["visual_scanning"] = results["difficulty_adjustment"]
    training_plan.current_difficulty = json.dumps(current_difficulty)

    session_info = track_session_completion(training_plan, "visual_scanning", session, user_id, task_id)

    session.commit()
    session.refresh(training_session)

    return {
        "session_id": training_session.id,
        "metrics": metrics,
        "difficulty_before": difficulty,
        "difficulty_after": results["difficulty_adjustment"],
        "adaptation_reason": results["adaptation_reason"],
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"]
    }


# ============================================================================
# CANCELLATION TEST ENDPOINTS
# ============================================================================

@router.post("/tasks/cancellation-test/generate/{user_id}")
def generate_cancellation_test(
    user_id: int,
    session: Session = Depends(get_session)
):
    """
    Generate a Cancellation Test trial for visual scanning and attention.
    Adapted to user's current difficulty level.
    """
    from app.services.cancellation_test_task import CancellationTestTask
    
    # Get user's current difficulty for visual scanning domain
    training_plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .order_by(desc(TrainingPlan.created_at))
    ).first()
    
    if not training_plan:
        raise HTTPException(status_code=404, detail="No training plan found. Complete baseline assessment first.")
    
    # Get difficulty for visual scanning domain from JSON
    current_difficulty_map = training_plan.get_current_difficulty()
    difficulty = current_difficulty_map.get("visual_scanning", 5)
    
    # Randomly choose between letters and symbols
    use_symbols = random.choice([True, False])
    
    # Generate trial
    trial_data = CancellationTestTask.generate_trial(difficulty, use_symbols)
    
    return {
        "trial_data": trial_data,
        "difficulty": difficulty,
        "user_id": user_id
    }


@router.post("/tasks/cancellation-test/submit/{user_id}")
def submit_cancellation_test(
    user_id: int,
    request_data: dict = Body(...),
    session: Session = Depends(get_session)
):
    """
    Submit Cancellation Test response and get scoring with difficulty adaptation.
    Tracks visual scanning performance and awards badges.
    No time limits - focuses on accuracy.
    """
    from app.services.cancellation_test_task import CancellationTestTask
    
    # Extract request data
    marked_positions = request_data.get("marked_positions", [])
    target_positions = request_data.get("target_positions", [])
    completion_time = request_data.get("completion_time", 0)
    suggested_time = request_data.get("suggested_time", 180)  # Changed from time_limit
    difficulty = request_data.get("difficulty", 5)
    task_id = request_data.get("task_id")  # Extract task_id for session tracking
    
    if not marked_positions:
        raise HTTPException(status_code=400, detail="Marked positions are required")
    
    if not target_positions:
        raise HTTPException(status_code=400, detail="Target positions are required")
    
    # Score the response
    results = CancellationTestTask.score_response(
        marked_positions,
        target_positions,
        completion_time,
        suggested_time,  # Changed from time_limit
        difficulty
    )
    
    # Get training plan
    training_plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .order_by(desc(TrainingPlan.created_at))
    ).first()
    
    if not training_plan:
        raise HTTPException(status_code=404, detail="No training plan found")

    enforce_session_limits(training_plan, session, user_id)
    
    # Get current difficulty from JSON
    current_difficulty_map = training_plan.get_current_difficulty()
    old_difficulty = current_difficulty_map.get("visual_scanning", 5)
    
    # Update difficulty based on performance
    adjustment = results["difficulty_adjustment"]
    new_difficulty = max(1, min(10, old_difficulty + adjustment))
    
    # Ensure training_plan.id is not None
    if training_plan.id is None:
        raise HTTPException(status_code=500, detail="Training plan ID is invalid")
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=training_plan.id,
        domain="visual_scanning",
        task_type="cancellation_test",
        score=results["score"],
        accuracy=results["accuracy"],
        average_reaction_time=int(completion_time * 1000),  # Convert to ms
        consistency=100 - (results["false_alarms"] / max(1, results["total_targets"]) * 100),
        errors=results["targets_missed"] + results["false_alarms"],
        duration=int(completion_time),
        difficulty_level=new_difficulty,
        difficulty_before=old_difficulty,
        difficulty_after=new_difficulty,
        completed=True,
        raw_data=json.dumps({
            "targets_found": results["targets_found"],
            "targets_missed": results["targets_missed"],
            "false_alarms": results["false_alarms"],
            "total_targets": results["total_targets"],
            "spatial_analysis": results["spatial_analysis"],
            "completion_time": results["completion_time"],
            "performance_rating": results["performance_rating"]
        })
    )
    
    session.add(training_session)
    
    # Update difficulty in training plan if changed
    if new_difficulty != old_difficulty:
        current_difficulty_map["visual_scanning"] = new_difficulty
        training_plan.current_difficulty = json.dumps(current_difficulty_map)
    
    # Adaptation feedback
    if adjustment > 0:
        adaptation_reason = f"Great visual scanning! Increasing difficulty from {old_difficulty} to {new_difficulty}"
    elif adjustment < 0:
        adaptation_reason = f"Adjusting difficulty from {old_difficulty} to {new_difficulty} to optimize training"
    else:
        adaptation_reason = f"Maintaining difficulty at {old_difficulty}"
    
    # Update training plan stats
    training_plan.last_session_date = datetime.utcnow()
    
    # Track session completion
    session_info = track_session_completion(training_plan, "visual_scanning", session, user_id, task_id)
    
    session.commit()
    session.refresh(training_session)
    
    return {
        "score": results["score"],
        "accuracy": results["accuracy"],
        "targets_found": results["targets_found"],
        "targets_missed": results["targets_missed"],
        "false_alarms": results["false_alarms"],
        "total_targets": results["total_targets"],
        "completion_time": results["completion_time"],
        "time_limit": results["time_limit"],
        "performance_rating": results["performance_rating"],
        "spatial_analysis": results["spatial_analysis"],
        "feedback": results["feedback"],
        "new_difficulty": new_difficulty,
        "old_difficulty": old_difficulty,
        "adaptation_reason": adaptation_reason,
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"],
        "session_id": training_session.id
    }


@router.get("/tasks/visual-search/generate/{user_id}")
def generate_visual_search_trial(user_id: int, session: Session = Depends(get_session)):
    """
    Generate Visual Search trial (Feature vs. Conjunction Search).
    Based on Treisman & Gelade (1980) attention theory.
    
    Feature search: Target differs by single feature (fast, parallel)
    Conjunction search: Target requires multiple features (slow, serial)
    """
    from app.services.visual_search_task import VisualSearchTask
    
    # Get user's training plan
    training_plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .order_by(desc(TrainingPlan.created_at))
    ).first()
    
    if not training_plan:
        raise HTTPException(status_code=404, detail="No training plan found for user")
    
    # Get current difficulty for visual_scanning domain
    current_difficulty_map = training_plan.get_current_difficulty()
    difficulty = current_difficulty_map.get("visual_scanning", 5)
    
    # Generate trial
    trial_data = VisualSearchTask.generate_trial(difficulty)
    
    return {
        "trial_data": trial_data,
        "difficulty": difficulty,
        "user_id": user_id
    }


@router.post("/tasks/visual-search/submit/{user_id}")
def submit_visual_search_response(
    user_id: int,
    request_data: dict = Body(...),
    session: Session = Depends(get_session)
):
    """
    Submit Visual Search response and get scoring with difficulty adaptation.
    Tracks visual attention performance and awards badges.
    """
    from app.services.visual_search_task import VisualSearchTask
    
    # Extract request data
    trial_data = request_data.get("trial_data", {})
    user_response = request_data.get("user_response", {})
    task_id = request_data.get("task_id")  # Get task identifier for session tracking
    
    if not trial_data:
        raise HTTPException(status_code=400, detail="Trial data is required")
    
    if not user_response:
        raise HTTPException(status_code=400, detail="User response is required")
    
    # Score the response
    results = VisualSearchTask.score_response(trial_data, user_response)
    
    # Get training plan
    training_plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .order_by(desc(TrainingPlan.created_at))
    ).first()
    
    if not training_plan:
        raise HTTPException(status_code=404, detail="No training plan found")

    enforce_session_limits(training_plan, session, user_id)
    
    # Get current difficulty from JSON
    current_difficulty_map = training_plan.get_current_difficulty()
    old_difficulty = current_difficulty_map.get("visual_scanning", 5)
    
    # Get recent session scores for adaptation
    recent_sessions = session.exec(
        select(TrainingSession)
        .where(TrainingSession.user_id == user_id)
        .where(TrainingSession.domain == "visual_scanning")
        .where(TrainingSession.task_type == "visual_search")
        .order_by(desc(TrainingSession.created_at))
        .limit(5)
    ).all()
    
    recent_scores = [s.score for s in recent_sessions]
    
    # Calculate difficulty adjustment
    new_difficulty = VisualSearchTask.calculate_difficulty_adjustment(
        recent_scores,
        old_difficulty,
        results["accuracy"],
        results["reaction_time"],
        trial_data["time_limit"]
    )
    
    # Ensure training_plan.id is not None
    if training_plan.id is None:
        raise HTTPException(status_code=500, detail="Training plan ID is invalid")
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=training_plan.id,
        domain="visual_scanning",
        task_type="visual_search",
        score=results["score"],
        accuracy=results["accuracy"],
        average_reaction_time=int(results["reaction_time"] * 1000),  # Convert to ms
        consistency=results["accuracy"] * 100,  # Consistency based on accuracy
        errors=0 if results["correct"] else 1,
        duration=int(results["reaction_time"]),
        difficulty_level=new_difficulty,
        difficulty_before=old_difficulty,
        difficulty_after=new_difficulty,
        completed=True,
        raw_data=json.dumps({
            "search_type": results["search_type"],
            "set_size": results["set_size"],
            "target_present": results["target_present"],
            "user_answer": results["user_answer"],
            "response_type": results["response_type"],
            "search_efficiency": results["search_efficiency"],
            "search_slope_ms": results["search_slope_ms"],
            "performance": results["performance"]
        })
    )
    
    session.add(training_session)
    
    # Track session completion using helper function with task_id
    session_info = track_session_completion(training_plan, "visual_scanning", session, user_id, task_id)
    
    # Update difficulty in training plan
    current_difficulty_map["visual_scanning"] = new_difficulty
    training_plan.current_difficulty = json.dumps(current_difficulty_map)
    
    session.add(training_plan)
    session.commit()
    session.refresh(training_session)
    
    # Adaptation feedback
    adjustment = new_difficulty - old_difficulty
    if adjustment > 0:
        adaptation_reason = f"Excellent visual attention! Increasing difficulty from {old_difficulty} to {new_difficulty}"
    elif adjustment < 0:
        adaptation_reason = f"Adjusting difficulty from {old_difficulty} to {new_difficulty} to optimize training"
    else:
        adaptation_reason = f"Maintaining difficulty at {old_difficulty}"
    
    return {
        "score": results["score"],
        "accuracy": results["accuracy"],
        "correct": results["correct"],
        "reaction_time": results["reaction_time"],
        "search_efficiency": results["search_efficiency"],
        "search_slope_ms": results["search_slope_ms"],
        "performance": results["performance"],
        "response_type": results["response_type"],
        "search_type": results["search_type"],
        "set_size": results["set_size"],
        "target_present": results["target_present"],
        "user_answer": results["user_answer"],
        "new_difficulty": new_difficulty,
        "old_difficulty": old_difficulty,
        "adaptation_reason": adaptation_reason,
        "new_badges": session_info["newly_earned_badges"],
        "session_id": training_session.id,
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"]
    }


@router.get("/tasks/multiple-object-tracking/generate/{user_id}")
def generate_mot_trial(user_id: int, session: Session = Depends(get_session)):
    """
    Generate Multiple Object Tracking (MOT) trial.
    Based on Pylyshyn & Storm (2006) - Dynamic visual attention.
    
    Track 2-5 moving objects among identical distractors.
    Measures sustained visual attention relevant for driving safety.
    """
    from app.services.multiple_object_tracking_task import MultipleObjectTrackingTask
    
    # Get user's training plan
    training_plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .order_by(desc(TrainingPlan.created_at))
    ).first()
    
    if not training_plan:
        raise HTTPException(status_code=404, detail="No training plan found for user")
    
    # Get current difficulty for visual_scanning domain
    current_difficulty_map = training_plan.get_current_difficulty()
    difficulty = current_difficulty_map.get("visual_scanning", 3)
    
    # Generate trial
    trial_data = MultipleObjectTrackingTask.generate_trial(difficulty)
    
    return {
        "trial_data": trial_data,
        "difficulty": difficulty,
        "user_id": user_id
    }


@router.post("/tasks/multiple-object-tracking/submit/{user_id}")
def submit_mot_response(
    user_id: int,
    request_data: dict = Body(...),
    session: Session = Depends(get_session)
):
    """
    Submit Multiple Object Tracking response and get scoring with difficulty adaptation.
    Tracks dynamic visual attention performance and awards badges.
    """
    from app.services.multiple_object_tracking_task import MultipleObjectTrackingTask
    
    # Extract request data
    trial_data = request_data.get("trial_data", {})
    user_response = request_data.get("user_response", {})
    task_id = request_data.get("task_id")  # Extract task_id for session tracking
    
    if not trial_data:
        raise HTTPException(status_code=400, detail="Trial data is required")
    
    if not user_response:
        raise HTTPException(status_code=400, detail="User response is required")
    
    # Score the response
    results = MultipleObjectTrackingTask.score_response(trial_data, user_response)
    
    # Get training plan
    training_plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .order_by(desc(TrainingPlan.created_at))
    ).first()
    
    if not training_plan:
        raise HTTPException(status_code=404, detail="No training plan found")

    enforce_session_limits(training_plan, session, user_id)
    
    # Get current difficulty from JSON
    current_difficulty_map = training_plan.get_current_difficulty()
    old_difficulty = current_difficulty_map.get("visual_scanning", 3)
    
    # Get recent session scores for adaptation
    recent_sessions = session.exec(
        select(TrainingSession)
        .where(TrainingSession.user_id == user_id)
        .where(TrainingSession.domain == "visual_scanning")
        .where(TrainingSession.task_type == "multiple_object_tracking")
        .order_by(desc(TrainingSession.created_at))
        .limit(5)
    ).all()
    
    recent_scores = [s.score for s in recent_sessions]
    
    # Calculate difficulty adjustment
    new_difficulty = MultipleObjectTrackingTask.calculate_difficulty_adjustment(
        recent_scores,
        old_difficulty,
        results["accuracy"],
        results["precision"]
    )
    
    # Ensure training_plan.id is not None
    if training_plan.id is None:
        raise HTTPException(status_code=500, detail="Training plan ID is invalid")
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=training_plan.id,
        domain="visual_scanning",
        task_type="multiple_object_tracking",
        score=results["score"],
        accuracy=results["accuracy"],
        average_reaction_time=int(results["response_time"] * 1000),  # Convert to ms
        consistency=results["tracking_efficiency"] * 100,
        errors=results["false_positives"] + results["false_negatives"],
        duration=trial_data["tracking_duration"],
        difficulty_level=new_difficulty,
        difficulty_before=old_difficulty,
        difficulty_after=new_difficulty,
        completed=True,
        raw_data=json.dumps({
            "num_objects": results["num_objects"],
            "targets_found": results["targets_found"],
            "targets_missed": results["targets_missed"],
            "false_positives": results["false_positives"],
            "precision": results["precision"],
            "recall": results["recall"],
            "f1_score": results["f1_score"],
            "tracking_efficiency": results["tracking_efficiency"],
            "performance": results["performance"],
            "tracking_duration": results["tracking_duration"]
        })
    )
    
    session.add(training_session)
    
    # Update difficulty in training plan if changed
    if new_difficulty != old_difficulty:
        current_difficulty_map["visual_scanning"] = new_difficulty
        training_plan.current_difficulty = json.dumps(current_difficulty_map)
    
    # Adaptation feedback
    adjustment = new_difficulty - old_difficulty
    if adjustment > 0:
        adaptation_reason = f"Excellent tracking! Increasing difficulty from {old_difficulty} to {new_difficulty}"
    elif adjustment < 0:
        adaptation_reason = f"Adjusting difficulty from {old_difficulty} to {new_difficulty} to optimize training"
    else:
        adaptation_reason = f"Maintaining difficulty at {old_difficulty}"
    
    # Update training plan stats
    training_plan.last_session_date = datetime.utcnow()
    
    # Track session completion
    session_info = track_session_completion(training_plan, "visual_scanning", session, user_id, task_id)
    
    session.commit()
    session.refresh(training_session)
    
    # Generate feedback message
    feedback_message = MultipleObjectTrackingTask.get_feedback_message(results)
    
    return {
        "score": results["score"],
        "accuracy": results["accuracy"],
        "precision": results["precision"],
        "recall": results["recall"],
        "f1_score": results["f1_score"],
        "targets_found": results["targets_found"],
        "targets_missed": results["targets_missed"],
        "false_positives": results["false_positives"],
        "total_targets": results["total_targets"],
        "tracking_efficiency": results["tracking_efficiency"],
        "performance": results["performance"],
        "response_time": results["response_time"],
        "num_objects": results["num_objects"],
        "tracking_duration": results["tracking_duration"],
        "feedback_message": feedback_message,
        "new_difficulty": new_difficulty,
        "old_difficulty": old_difficulty,
        "adaptation_reason": adaptation_reason,
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"],
        "session_id": training_session.id
    }


# ============================================================================
# USEFUL FIELD OF VIEW (UFOV) TASK ENDPOINTS
# ============================================================================

@router.get("/tasks/useful-field-of-view/generate/{user_id}")
def generate_ufov_trial(user_id: int, session: Session = Depends(get_session)):
    """
    Generate a Useful Field of View (UFOV) trial
    
    UFOV measures visual processing speed and divided attention
    Critical for driving safety assessment in MS patients
    
    Three subtests:
    1. Central ID only (processing speed)
    2. Central + Peripheral (divided attention)
    3. Central + Peripheral + Distractors (selective attention)
    """
    from app.services.useful_field_of_view_task import generate_trial
    
    # Get user's training plan
    training_plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(col(TrainingPlan.is_active) == True)
    ).first()
    
    if not training_plan:
        raise HTTPException(status_code=404, detail="No active training plan found")
    
    # Get current difficulty from training plan (use visual_scanning domain)
    current_difficulty_map = training_plan.get_current_difficulty()
    current_difficulty = current_difficulty_map.get("visual_scanning", 1)
    
    # Generate trial
    trial = generate_trial(current_difficulty)
    
    return {
        "trial": trial,
        "current_difficulty": current_difficulty,
        "task_type": "useful_field_of_view",
        "domain": "visual_scanning"
    }


@router.post("/tasks/useful-field-of-view/submit/{user_id}")
def submit_ufov_response(
    user_id: int,
    central_response: str = Body(..., description="User's answer for central target (car or truck)"),
    peripheral_response: Optional[str] = Body(None, description="User's answer for peripheral position"),
    trial_data: Dict = Body(..., description="Original trial configuration"),
    response_time: int = Body(..., description="Time taken to respond (ms)"),
    session: Session = Depends(get_session)
):
    """
    Submit UFOV response and calculate score
    """
    from app.services.useful_field_of_view_task import (
        score_response,
        calculate_difficulty_adjustment,
        get_feedback_message
    )
    
    # Extract task_id for session tracking (from trial_data)
    task_id = trial_data.get("task_id")
    
    # Get user's training plan
    training_plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(col(TrainingPlan.is_active) == True)
    ).first()
    
    if not training_plan:
        raise HTTPException(status_code=404, detail="No active training plan found")

    enforce_session_limits(training_plan, session, user_id)
    
    # Score the response
    results = score_response(trial_data, central_response, peripheral_response)
    results["response_time"] = response_time
    
    # Get current difficulty from JSON
    current_difficulty_map = training_plan.get_current_difficulty()
    old_difficulty = current_difficulty_map.get("visual_scanning", 1)
    
    # Get recent performance for difficulty adjustment
    recent_sessions = session.exec(
        select(TrainingSession)
        .where(TrainingSession.user_id == user_id)
        .where(TrainingSession.domain == "visual_scanning")
        .where(TrainingSession.task_type == "useful_field_of_view")
        .order_by(desc(TrainingSession.created_at))
        .limit(5)
    ).all()
    
    recent_scores = []
    for s in recent_sessions:
        raw_data = json.loads(s.raw_data)
        if "accuracy" in raw_data:
            recent_scores.append(raw_data)
    
    # Calculate difficulty adjustment
    new_difficulty, adaptation_reason = calculate_difficulty_adjustment(recent_scores, old_difficulty)
    
    # Ensure training_plan.id is not None
    if training_plan.id is None:
        raise HTTPException(status_code=500, detail="Training plan ID is invalid")
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=training_plan.id,
        domain="visual_scanning",
        task_type="useful_field_of_view",
        score=results["score"],
        accuracy=results["accuracy"],
        average_reaction_time=response_time,
        consistency=results["accuracy"] * 100,  # Use accuracy as consistency metric
        errors=0 if results["central_correct"] and results.get("peripheral_correct", True) else 1,
        duration=trial_data["presentation_time_ms"] // 1000 + 1,  # Convert to seconds
        difficulty_level=new_difficulty,
        difficulty_before=old_difficulty,
        difficulty_after=new_difficulty,
        completed=True,
        raw_data=json.dumps({
            "central_correct": results["central_correct"],
            "peripheral_correct": results["peripheral_correct"],
            "performance": results["performance"],
            "subtest": results["subtest"],
            "presentation_time_ms": results["presentation_time_ms"],
            "processing_speed_score": results["processing_speed_score"],
            "accuracy": results["accuracy"]
        })
    )
    
    session.add(training_session)
    session.commit()
    session.refresh(training_session)
    
    # Update difficulty in training plan if changed
    if new_difficulty != old_difficulty:
        current_difficulty_map["visual_scanning"] = new_difficulty
        training_plan.current_difficulty = json.dumps(current_difficulty_map)
        adaptation_reason = f"Adjusted from level {old_difficulty} to {new_difficulty}: {adaptation_reason}"
    else:
        adaptation_reason = f"Maintaining difficulty at level {old_difficulty}"
    
    # Update training plan stats
    training_plan.last_session_date = datetime.utcnow()
    
    # Track session completion
    session_info = track_session_completion(training_plan, "visual_scanning", session, user_id, task_id)
    
    session.add(training_plan)
    session.commit()
    
    # Generate feedback message
    feedback_message = get_feedback_message(results)
    
    return {
        "score": results["score"],
        "accuracy": results["accuracy"],
        "central_correct": results["central_correct"],
        "peripheral_correct": results["peripheral_correct"],
        "performance": results["performance"],
        "subtest": results["subtest"],
        "presentation_time_ms": results["presentation_time_ms"],
        "processing_speed_score": results["processing_speed_score"],
        "response_time": response_time,
        "feedback_message": feedback_message,
        "new_difficulty": new_difficulty,
        "old_difficulty": old_difficulty,
        "adaptation_reason": adaptation_reason,
        "new_badges": session_info["newly_earned_badges"],
        "session_complete": session_info["session_complete"],
        "completed_tasks": session_info["completed_tasks"],
        "total_tasks": session_info["total_tasks"],
        "session_id": training_session.id
    }
