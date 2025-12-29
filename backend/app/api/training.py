from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc, col
import json
from datetime import datetime, timedelta

from app.models.training_plan import TrainingPlan
from app.models.training_session import TrainingSession
from app.models.baseline_assessment import BaselineAssessment
from app.models.badge import UserBadge, BadgeDefinition
from app.services.badge_service import BadgeService
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
        raise HTTPException(status_code=404, detail="No active training plan")
    
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
    
    print(f"\n╔══════════════════════════════════════════════════════════╗")
    print(f"║  TRAINING SESSION SUBMISSION RECEIVED                   ║")
    print(f"╠══════════════════════════════════════════════════════════╣")
    print(f"  User ID: {user_id}")
    print(f"  Plan ID: {training_plan_id}")
    print(f"  Domain: {domain}")
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
    newly_earned_badges = []
    
    print(f"[DEBUG] Domain: {domain}, Completed tasks: {completed_tasks}, Session complete: {session_complete}")
    
    if session_complete:
        print(f"[DEBUG] SESSION COMPLETE! Updating streak...")
        # Session is complete - increment session count and reset
        plan.total_sessions_completed += 1
        plan.current_session_number += 1
        plan.current_session_tasks_completed = "[]"  # Reset for next session
        
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
                "name": badge_def["name"],
                "description": badge_def["description"],
                "icon": badge_def["icon"]
            })
    
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
    
    # Already trained today - no streak change
    if days_since_last == 0:
        return
    
    # Trained yesterday - increment streak
    if days_since_last == 1:
        plan.current_streak += 1
        plan.total_training_days += 1
        plan.streak_freeze_available = True  # Reset freeze for new week
        
    # Missed exactly 1 day - check if freeze available
    elif days_since_last == 2 and plan.streak_freeze_available:
        plan.current_streak += 1  # Maintain streak with freeze
        plan.total_training_days += 1
        plan.streak_freeze_available = False  # Use up the freeze
        
    # Missed 2+ days or no freeze - reset streak
    else:
        plan.current_streak = 1
        plan.total_training_days += 1
        plan.streak_freeze_available = True
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
        raise HTTPException(status_code=404, detail="No active training plan")
    
    # Get baseline scores
    baseline = session.exec(
        select(BaselineAssessment)
        .where(BaselineAssessment.id == plan.baseline_assessment_id)
    ).first()
    
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline assessment not found")
    
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
        "user_id": user_id,
        "total_sessions_completed": plan.total_sessions_completed,
        "baseline_date": baseline.created_at.isoformat(),
        "last_training_date": plan.last_session_date.isoformat() if plan.last_session_date else None,
        "comparison": comparison
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
    
    # Get active training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")
    
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
    
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")
    
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
    
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")
    
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
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")
    
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
        raise HTTPException(status_code=404, detail="No active training plan")
    
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
    # Get training plan
    plan = session.exec(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user_id)
        .where(TrainingPlan.is_active == True)
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="No active training plan")
    
    # Check and award badges
    newly_earned = BadgeService.check_and_award_badges(session, user_id, plan)
    
    # Get badge details
    badge_details = []
    for badge_id in newly_earned:
        badge_def = BadgeDefinition.get_badge(badge_id)
        if badge_def:
            badge_details.append({
                "id": badge_id,
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
