from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc
import json
from datetime import datetime

from app.models.training_plan import TrainingPlan
from app.models.training_session import TrainingSession
from app.models.baseline_assessment import BaselineAssessment
from app.core.config import engine

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

# Task type mapping for each cognitive domain
DOMAIN_TASK_MAPPING = {
    "working_memory": "n_back",
    "attention": "continuous_performance",
    "flexibility": "task_switching",
    "planning": "tower_of_hanoi",
    "processing_speed": "reaction_time",
    "visual_scanning": "target_search"
}

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
    
    # Get latest baseline assessment
    baseline = session.exec(
        select(BaselineAssessment)
        .where(BaselineAssessment.user_id == user_id)
        .order_by(desc(BaselineAssessment.created_at))
    ).first()
    
    if not baseline or baseline.id is None:
        raise HTTPException(status_code=404, detail="No baseline assessment found. Complete baseline first.")
    
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
    def score_to_difficulty(score):
        if score < 50:
            return 2
        elif score < 70:
            return 4
        elif score < 85:
            return 7
        else:
            return 9
    
    initial_difficulty = {
        domain: score_to_difficulty(score) for domain, score in domains.items()
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
        "created_at": training_plan.created_at.isoformat()
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
        raise HTTPException(status_code=404, detail="No active training plan found. Generate one first.")
    
    return {
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
        "created_at": plan.created_at.isoformat()
    }

@router.get("/training-plan/{user_id}/next-tasks")
def get_next_training_tasks(user_id: int, session: Session = Depends(get_session)):
    """
    Get recommended tasks for current training session.
    
    Returns 4 tasks with completion status:
    - 2 from primary focus (weakest domains)
    - 2 from secondary focus (middle domains)
    
    Session only advances after all 4 tasks are completed.
    """
    
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan. Generate one first.")
    
    primary = plan.get_primary_focus()
    secondary = plan.get_secondary_focus()
    tasks = plan.get_recommended_tasks()
    difficulty = plan.get_current_difficulty()
    completed_tasks = plan.get_current_session_tasks_completed()
    
    # Build session task list (always the same 4 tasks per session)
    next_tasks = []
    
    # Add 2 primary focus tasks
    for domain in primary:
        next_tasks.append({
            "domain": domain,
            "task_type": tasks[domain],
            "difficulty": difficulty[domain],
            "priority": "primary",
            "focus_reason": "Weakest area - needs most attention",
            "completed": domain in completed_tasks
        })
    
    # Add 2 secondary focus tasks
    for domain in secondary:
        next_tasks.append({
            "domain": domain,
            "task_type": tasks[domain],
            "difficulty": difficulty[domain],
            "priority": "secondary",
            "focus_reason": "Moderate area - room for improvement",
            "completed": domain in completed_tasks
        })
    
    # Check if session is complete
    all_completed = len(completed_tasks) >= 4
    
    return {
        "training_plan_id": plan.id,
        "session_number": plan.current_session_number,
        "tasks": next_tasks,
        "total_tasks": len(next_tasks),
        "completed_tasks": len(completed_tasks),
        "session_complete": all_completed
    }

@router.post("/training-session/submit")
def submit_training_session(
    user_id: int,
    training_plan_id: int,
    domain: str,
    task_type: str,
    score: float,
    accuracy: float,
    average_reaction_time: float,
    consistency: float,
    errors: int,
    duration: int,
    raw_data: dict = {},
    session: Session = Depends(get_session)
):
    """
    Submit results from a training session and apply adaptive difficulty.
    
    Adaptive Algorithm:
    - If accuracy >= 85% → increase difficulty by 1
    - If accuracy < 65% → decrease difficulty by 1
    - Otherwise → keep same difficulty
    
    Difficulty is clamped between 1-10.
    """
    
    # Get training plan
    plan = session.exec(
        select(TrainingPlan).where(TrainingPlan.id == training_plan_id)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Training plan not found")
    
    # Get current difficulty for this domain
    current_difficulty_map = plan.get_current_difficulty()
    current_difficulty = current_difficulty_map.get(domain, 5)
    
    # Apply adaptive difficulty logic
    new_difficulty = current_difficulty
    adaptation_reason = "Maintained difficulty"
    
    if accuracy >= 85:
        new_difficulty = min(current_difficulty + 1, 10)
        adaptation_reason = f"Increased difficulty (accuracy {accuracy:.1f}% >= 85%)"
    elif accuracy < 65:
        new_difficulty = max(current_difficulty - 1, 1)
        adaptation_reason = f"Decreased difficulty (accuracy {accuracy:.1f}% < 65%)"
    else:
        adaptation_reason = f"Maintained difficulty (accuracy {accuracy:.1f}% in 65-85% range)"
    
    # Create training session record
    training_session = TrainingSession(
        user_id=user_id,
        training_plan_id=training_plan_id,
        domain=domain,
        task_type=task_type,
        score=score,
        accuracy=accuracy,
        average_reaction_time=average_reaction_time,
        consistency=consistency,
        errors=errors,
        difficulty_level=new_difficulty,
        difficulty_before=current_difficulty,
        difficulty_after=new_difficulty,
        duration=duration,
        raw_data=json.dumps(raw_data),
        adaptation_reason=adaptation_reason
    )
    
    session.add(training_session)
    
    # Update training plan's current difficulty
    current_difficulty_map[domain] = new_difficulty
    plan.current_difficulty = json.dumps(current_difficulty_map)
    
    # Mark this task as completed in current session
    completed_tasks = plan.get_current_session_tasks_completed()
    if domain not in completed_tasks:
        completed_tasks.append(domain)
        plan.current_session_tasks_completed = json.dumps(completed_tasks)
    
    # Check if all 4 tasks in session are completed
    session_complete = len(completed_tasks) >= 4
    
    if session_complete:
        # Session is complete - increment session count and reset
        plan.total_sessions_completed += 1
        plan.current_session_number += 1
        plan.current_session_tasks_completed = "[]"  # Reset for next session
        plan.last_session_date = datetime.utcnow()
    
    plan.last_updated = datetime.utcnow()
    
    # Explicitly mark plan as modified
    session.add(plan)
    session.flush()  # Flush changes before commit
    session.commit()
    session.refresh(training_session)
    session.refresh(plan)
    
    return {
        "id": training_session.id,
        "domain": domain,
        "score": score,
        "accuracy": accuracy,
        "difficulty_before": current_difficulty,
        "difficulty_after": new_difficulty,
        "adaptation_reason": adaptation_reason,
        "session_complete": session_complete,
        "completed_tasks": len(completed_tasks),
        "total_tasks": 4,
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
        raise HTTPException(status_code=404, detail="No active training plan found")
    
    # Get all training sessions
    all_sessions = session.exec(
        select(TrainingSession).where(TrainingSession.user_id == user_id)
    ).all()
    
    if not all_sessions:
        return {
            "total_sessions": 0,
            "metrics_by_domain": {},
            "current_difficulty": plan.get_current_difficulty(),
            "recent_sessions": []
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
        "total_sessions": len(all_sessions),
        "metrics_by_domain": metrics_by_domain,
        "current_difficulty": plan.get_current_difficulty(),
        "recent_sessions": recent_sessions,
        "last_training_date": plan.last_session_date.isoformat() if plan.last_session_date else None
    }
