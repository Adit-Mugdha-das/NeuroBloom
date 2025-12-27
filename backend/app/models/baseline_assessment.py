from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class BaselineAssessment(SQLModel, table=True):
    """Store baseline cognitive assessment results"""
    __tablename__ = "baseline_assessments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    assessment_date: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Domain Scores (0-100)
    working_memory_score: float = Field(default=0.0)
    attention_score: float = Field(default=0.0)
    flexibility_score: float = Field(default=0.0)
    planning_score: float = Field(default=0.0)
    processing_speed_score: float = Field(default=0.0)
    visual_scanning_score: float = Field(default=0.0)
    
    # Overall metrics
    overall_score: float = Field(default=0.0)
    
    # Raw metrics (JSON string)
    raw_metrics: str = Field(default="{}")
    
    # Flags
    is_baseline: bool = Field(default=True)
    assessment_duration_minutes: int = Field(default=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "working_memory_score": 75.5,
                "attention_score": 82.0,
                "flexibility_score": 68.5
            }
        }
