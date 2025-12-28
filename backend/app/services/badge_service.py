from sqlmodel import Session, select, desc
from typing import List, Dict, Set, Sequence
from datetime import datetime, timedelta
from app.models.badge import UserBadge, BadgeDefinition
from app.models.training_plan import TrainingPlan
from app.models.training_session import TrainingSession

class BadgeService:
    """Service for checking and awarding badges"""
    
    @staticmethod
    def check_and_award_badges(db: Session, user_id: int, plan: TrainingPlan) -> List[str]:
        """
        Check if user earned any new badges after completing a session.
        Returns list of newly earned badge IDs.
        """
        newly_earned = []
        
        # Get all badges user already has
        existing_badges = BadgeService._get_user_badge_ids(db, user_id)
        
        # Check each badge type
        session_badges = BadgeService._check_session_count_badges(plan.total_sessions_completed, existing_badges)
        newly_earned.extend(session_badges)
        
        streak_badges = BadgeService._check_streak_badges(plan.current_streak, existing_badges)
        newly_earned.extend(streak_badges)
        
        # Get recent sessions for performance checks
        recent_sessions = db.exec(
            select(TrainingSession)
            .where(TrainingSession.training_plan_id == plan.id)
            .order_by(desc(TrainingSession.created_at))
            .limit(10)
        ).all()
        
        if recent_sessions:
            perf_badges = BadgeService._check_performance_badges(
                db, plan, recent_sessions, existing_badges
            )
            newly_earned.extend(perf_badges)
        
        # Award new badges
        for badge_id in newly_earned:
            BadgeService._award_badge(db, user_id, badge_id)
        
        return newly_earned
    
    @staticmethod
    def _get_user_badge_ids(db: Session, user_id: int) -> Set[str]:
        """Get set of badge IDs user already has"""
        badges = db.exec(
            select(UserBadge.badge_id).where(UserBadge.user_id == user_id)
        ).all()
        return set(badges)
    
    @staticmethod
    def _check_session_count_badges(total_sessions: int, existing: Set[str]) -> List[str]:
        """Check session count milestone badges"""
        newly_earned = []
        
        session_milestones = {
            "first_session": 1,
            "sessions_5": 5,
            "sessions_10": 10,
            "sessions_25": 25,
            "sessions_50": 50,
            "sessions_100": 100
        }
        
        for badge_id, required in session_milestones.items():
            if badge_id not in existing and total_sessions >= required:
                newly_earned.append(badge_id)
        
        return newly_earned
    
    @staticmethod
    def _check_streak_badges(current_streak: int, existing: Set[str]) -> List[str]:
        """Check streak milestone badges"""
        newly_earned = []
        
        streak_milestones = {
            "streak_3": 3,
            "streak_7": 7,
            "streak_14": 14,
            "streak_30": 30,
            "streak_100": 100
        }
        
        for badge_id, required in streak_milestones.items():
            if badge_id not in existing and current_streak >= required:
                newly_earned.append(badge_id)
        
        return newly_earned
    
    @staticmethod
    def _check_performance_badges(
        db: Session,
        plan: TrainingPlan,
        recent_sessions: Sequence[TrainingSession],
        existing: Set[str]
    ) -> List[str]:
        """Check performance-based badges"""
        newly_earned = []
        
        # Get the most recent session (4 tasks)
        last_session = recent_sessions[0]
        
        # Check perfect score (100% accuracy and max score)
        if "perfect_score" not in existing:
            if last_session.accuracy == 100 and last_session.score >= 95:
                newly_earned.append("perfect_score")
        
        # Check high accuracy (95%+)
        if "high_accuracy" not in existing:
            if last_session.accuracy >= 95:
                newly_earned.append("high_accuracy")
        
        # Check fast completion (session under 10 minutes = 600 seconds)
        if "fast_completion" not in existing:
            # Calculate total duration for the last session (4 tasks)
            # Get the 4 most recent tasks that belong to the same session
            session_tasks = [s for s in recent_sessions[:4]]
            total_duration = sum(s.duration for s in session_tasks)
            
            if len(session_tasks) == 4 and total_duration <= 600:  # 10 minutes
                newly_earned.append("fast_completion")
        
        # Check difficulty milestones
        difficulty_badges = {
            "difficulty_5": 5,
            "difficulty_7": 7,
            "difficulty_10": 10
        }
        
        # Get current difficulty from plan's JSON field
        difficulties = plan.get_current_difficulty()
        max_difficulty = max(difficulties.values()) if difficulties else 0
        
        for badge_id, required_diff in difficulty_badges.items():
            if badge_id not in existing and max_difficulty >= required_diff:
                newly_earned.append(badge_id)
        
        # Check domain diversity (all 6 domains)
        if "all_domains" not in existing:
            unique_domains = db.exec(
                select(TrainingSession.domain)
                .where(TrainingSession.training_plan_id == plan.id)
                .distinct()
            ).all()
            
            if len(unique_domains) >= 6:
                newly_earned.append("all_domains")
        
        # Check domain expert (20+ tasks in one domain)
        if "domain_expert" not in existing:
            for domain in ["working_memory", "attention", "flexibility", "planning", "processing_speed", "visual_scanning"]:
                count = db.exec(
                    select(TrainingSession)
                    .where(TrainingSession.training_plan_id == plan.id)
                    .where(TrainingSession.domain == domain)
                ).all()
                
                if len(count) >= 20:
                    newly_earned.append("domain_expert")
                    break
        
        # Check score improvement (20+ point increase in same domain)
        if "big_improvement" not in existing and len(recent_sessions) >= 10:
            # Check each domain for improvement
            for domain in ["working_memory", "attention", "flexibility", "planning", "processing_speed", "visual_scanning"]:
                domain_sessions = [
                    s for s in recent_sessions 
                    if s.domain == domain
                ]
                
                if len(domain_sessions) >= 6:
                    # Compare recent 3 to older 3 in same domain
                    recent_avg = sum(s.score for s in domain_sessions[:3]) / 3
                    older_avg = sum(s.score for s in domain_sessions[3:6]) / 3
                    
                    if recent_avg - older_avg >= 20:
                        newly_earned.append("big_improvement")
                        break
        
        return newly_earned
    
    @staticmethod
    def _award_badge(db: Session, user_id: int, badge_id: str):
        """Award a badge to user"""
        try:
            badge = UserBadge(
                user_id=user_id,
                badge_id=badge_id,
                earned_at=datetime.utcnow()
            )
            db.add(badge)
            db.commit()
        except Exception as e:
            # Badge might already exist (unique constraint)
            db.rollback()
    
    @staticmethod
    def get_user_badges(db: Session, user_id: int) -> List[Dict]:
        """Get all badges earned by user with full details"""
        user_badges = db.exec(
            select(UserBadge)
            .where(UserBadge.user_id == user_id)
            .order_by(desc(UserBadge.earned_at))
        ).all()
        
        result = []
        for ub in user_badges:
            badge_def = BadgeDefinition.get_badge(ub.badge_id)
            if badge_def:
                result.append({
                    "id": ub.badge_id,
                    "name": badge_def["name"],
                    "description": badge_def["description"],
                    "icon": badge_def["icon"],
                    "category": badge_def["category"],
                    "earned_at": ub.earned_at.isoformat(),
                    "progress": ub.progress
                })
        
        return result
    
    @staticmethod
    def get_available_badges(db: Session, user_id: int) -> Dict:
        """Get all badges with earned/locked status and progress"""
        earned_badge_ids = BadgeService._get_user_badge_ids(db, user_id)
        
        all_badges = []
        for badge_id, badge_def in BadgeDefinition.get_all_badges().items():
            badge_info = {
                "id": badge_id,
                "name": badge_def["name"],
                "description": badge_def["description"],
                "icon": badge_def["icon"],
                "category": badge_def["category"],
                "requirement": badge_def["requirement"],
                "type": badge_def["type"],
                "earned": badge_id in earned_badge_ids
            }
            all_badges.append(badge_info)
        
        # Group by category
        by_category = {}
        for badge in all_badges:
            category = badge["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(badge)
        
        return {
            "total_badges": len(BadgeDefinition.BADGES),
            "earned_count": len(earned_badge_ids),
            "badges_by_category": by_category,
            "all_badges": all_badges
        }
