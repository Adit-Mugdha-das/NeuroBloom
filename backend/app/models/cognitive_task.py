"""
Cognitive Task model for task variety system
"""

from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel

class CognitiveTask(SQLModel, table=True):
    """
    Defines available cognitive tasks in the system.
    Supports both baseline assessment tasks and training variety tasks.
    """
    __tablename__ = "cognitive_tasks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    task_code: str = Field(unique=True, index=True, max_length=50)
    domain: str = Field(max_length=50)  # working_memory, attention, etc.
    task_name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None)
    clinical_validation: Optional[str] = Field(default=None)
    
    is_baseline_task: bool = Field(default=False)  # Original 6 tasks
    difficulty_min: int = Field(default=1)
    difficulty_max: int = Field(default=10)
    estimated_duration_seconds: int = Field(default=120)
    
    requires_audio: bool = Field(default=False)
    requires_keyboard: bool = Field(default=True)
    cognitive_load: str = Field(default="medium", max_length=20)  # low, medium, high
    
    instructions: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserTaskPreference(SQLModel, table=True):
    """
    Tracks user preferences for specific tasks
    """
    __tablename__ = "user_task_preferences"
    
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    task_code: str = Field(max_length=50, primary_key=True)
    preference: str = Field(default="neutral", max_length=20)  # favorite, neutral, dislike
    reason: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
