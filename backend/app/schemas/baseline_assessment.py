from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BaselineAssessmentCreate(BaseModel):
    user_id: int
    working_memory_score: float = 0.0
    attention_score: float = 0.0
    flexibility_score: float = 0.0
    planning_score: float = 0.0
    processing_speed_score: float = 0.0
    visual_scanning_score: float = 0.0
    raw_metrics: str = "{}"
    assessment_duration_minutes: int = 0

class BaselineAssessmentRead(BaseModel):
    id: int
    user_id: int
    assessment_date: datetime
    working_memory_score: float
    attention_score: float
    flexibility_score: float
    planning_score: float
    processing_speed_score: float
    visual_scanning_score: float
    overall_score: float
    is_baseline: bool
    
    class Config:
        from_attributes = True
