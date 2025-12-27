from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional, ClassVar
import json

class TrainingSession(SQLModel, table=True):
    """
    Tracks individual training sessions for each cognitive task.
    Stores performance metrics for adaptive difficulty and progress tracking.
    """
    __tablename__: ClassVar[str] = "training_sessions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    training_plan_id: int = Field(foreign_key="training_plans.id", index=True)
    
    # Task information
    domain: str = Field(index=True)  # e.g., "working_memory", "attention"
    task_type: str  # e.g., "n_back", "track_moving", "rule_switch"
    
    # Performance metrics
    score: float  # 0-100 performance score
    accuracy: float  # 0-100 accuracy percentage
    average_reaction_time: float  # milliseconds
    consistency: float  # 0-100 consistency score
    errors: int  # number of mistakes
    
    # Difficulty tracking
    difficulty_level: int = Field(default=1)  # 1-10 scale
    difficulty_before: int  # difficulty at start of session
    difficulty_after: int  # adjusted difficulty for next session
    
    # Session metadata
    duration: int  # seconds spent on task
    completed: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Raw task data (for detailed analysis)
    raw_data: str = Field(default="{}")  # JSON with trial-by-trial data
    
    # Adaptation decision
    adaptation_reason: Optional[str] = Field(default=None)  # why difficulty changed
    
    def get_raw_data(self):
        """Parse raw data from JSON"""
        return json.loads(self.raw_data)
