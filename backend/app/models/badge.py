from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class UserBadge(SQLModel, table=True):
    """Tracks badges earned by users"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    badge_id: str = Field(index=True)  # e.g., "first_session", "streak_7"
    earned_at: datetime = Field(default_factory=datetime.utcnow)
    progress: int = Field(default=0)  # For badges with progress tracking
    
class BadgeDefinition:
    """Defines all available badges and their unlock criteria"""
    
    BADGES = {
        # Getting Started Badges
        "first_session": {
            "name": "First Steps",
            "description": "Complete your first training session",
            "icon": "🎯",
            "category": "getting_started",
            "requirement": 1,
            "type": "session_count"
        },
        "sessions_5": {
            "name": "Dedicated Learner",
            "description": "Complete 5 training sessions",
            "icon": "📚",
            "category": "getting_started",
            "requirement": 5,
            "type": "session_count"
        },
        "sessions_10": {
            "name": "Consistent Trainer",
            "description": "Complete 10 training sessions",
            "icon": "💪",
            "category": "milestone",
            "requirement": 10,
            "type": "session_count"
        },
        "sessions_25": {
            "name": "Brain Athlete",
            "description": "Complete 25 training sessions",
            "icon": "🏃",
            "category": "milestone",
            "requirement": 25,
            "type": "session_count"
        },
        "sessions_50": {
            "name": "Mental Warrior",
            "description": "Complete 50 training sessions",
            "icon": "⚔️",
            "category": "milestone",
            "requirement": 50,
            "type": "session_count"
        },
        "sessions_100": {
            "name": "Master Trainer",
            "description": "Complete 100 training sessions",
            "icon": "👑",
            "category": "milestone",
            "requirement": 100,
            "type": "session_count"
        },
        
        # Streak Badges
        "streak_3": {
            "name": "Hot Start",
            "description": "Maintain a 3-day training streak",
            "icon": "🔥",
            "category": "streak",
            "requirement": 3,
            "type": "streak"
        },
        "streak_7": {
            "name": "Week Warrior",
            "description": "Maintain a 7-day training streak",
            "icon": "🌟",
            "category": "streak",
            "requirement": 7,
            "type": "streak"
        },
        "streak_14": {
            "name": "Fortnight Champion",
            "description": "Maintain a 14-day training streak",
            "icon": "💫",
            "category": "streak",
            "requirement": 14,
            "type": "streak"
        },
        "streak_30": {
            "name": "Monthly Master",
            "description": "Maintain a 30-day training streak",
            "icon": "🌙",
            "category": "streak",
            "requirement": 30,
            "type": "streak"
        },
        "streak_100": {
            "name": "Unstoppable",
            "description": "Maintain a 100-day training streak",
            "icon": "🚀",
            "category": "streak",
            "requirement": 100,
            "type": "streak"
        },
        
        # Performance Badges
        "perfect_score": {
            "name": "Perfectionist",
            "description": "Achieve a perfect score in any task",
            "icon": "💯",
            "category": "performance",
            "requirement": 1,
            "type": "perfect_score"
        },
        "high_accuracy": {
            "name": "Sharpshooter",
            "description": "Achieve 95% accuracy in a session",
            "icon": "🎯",
            "category": "performance",
            "requirement": 95,
            "type": "session_accuracy"
        },
        "difficulty_5": {
            "name": "Rising Star",
            "description": "Reach difficulty level 5 in any domain",
            "icon": "⭐",
            "category": "performance",
            "requirement": 5,
            "type": "difficulty"
        },
        "difficulty_7": {
            "name": "Advanced Learner",
            "description": "Reach difficulty level 7 in any domain",
            "icon": "🌟",
            "category": "performance",
            "requirement": 7,
            "type": "difficulty"
        },
        "difficulty_10": {
            "name": "Elite Mind",
            "description": "Reach maximum difficulty in any domain",
            "icon": "💎",
            "category": "performance",
            "requirement": 10,
            "type": "difficulty"
        },
        
        # Domain Mastery Badges
        "all_domains": {
            "name": "Well Rounded",
            "description": "Complete at least one task in all 6 domains",
            "icon": "🎨",
            "category": "mastery",
            "requirement": 6,
            "type": "domain_diversity"
        },
        "domain_expert": {
            "name": "Domain Expert",
            "description": "Complete 20 tasks in a single domain",
            "icon": "🎓",
            "category": "mastery",
            "requirement": 20,
            "type": "domain_tasks"
        },
        
        # Speed Badges
        "fast_completion": {
            "name": "Speed Demon",
            "description": "Complete a session in under 10 minutes",
            "icon": "⚡",
            "category": "speed",
            "requirement": 600,  # seconds
            "type": "session_duration"
        },
        
        # Improvement Badges
        "big_improvement": {
            "name": "Growth Mindset",
            "description": "Improve score by 20 points in any domain",
            "icon": "📈",
            "category": "improvement",
            "requirement": 20,
            "type": "score_improvement"
        }
    }
    
    @classmethod
    def get_badge(cls, badge_id: str):
        """Get badge definition by ID"""
        return cls.BADGES.get(badge_id)
    
    @classmethod
    def get_all_badges(cls):
        """Get all badge definitions"""
        return cls.BADGES
    
    @classmethod
    def get_by_category(cls, category: str):
        """Get all badges in a category"""
        return {
            badge_id: badge 
            for badge_id, badge in cls.BADGES.items() 
            if badge["category"] == category
        }
