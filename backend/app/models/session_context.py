"""
Session Context Model - Pre-Task Questionnaire Data

Stores contextual factors that influence cognitive performance:
- Fatigue level
- Sleep quality
- Medication timing
- Time of day
- Subjective wellness

Critical for MS research: correlating performance with fatigue, medication, etc.
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class SessionContext(SQLModel, table=True):
    """
    Pre-task questionnaire responses to contextualize performance.
    
    Enables analysis like:
    - Performance vs fatigue correlation
    - Optimal medication timing
    - Sleep impact on cognition
    - Circadian performance patterns
    """
    __tablename__ = "session_contexts"  # type: ignore
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    training_session_id: Optional[int] = Field(default=None, foreign_key="training_sessions.id", index=True)
    
    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # === PRE-TASK QUESTIONNAIRE ===
    
    # Fatigue (1-10 scale)
    # 1 = Fully energized, 5 = Moderate fatigue, 10 = Completely exhausted
    # MS patients: average 6-7, relapse: 8-10
    fatigue_level: Optional[int] = Field(default=None, ge=1, le=10)
    
    # Sleep quality last night (1-10 scale)
    # 1 = Terrible sleep, 5 = Average, 10 = Excellent sleep
    # MS correlation: poor sleep → worse cognition
    sleep_quality: Optional[int] = Field(default=None, ge=1, le=10)
    
    # Hours of sleep last night
    sleep_hours: Optional[float] = Field(default=None, ge=0, le=24)
    
    # Medication adherence
    medication_taken_today: Optional[bool] = Field(default=None)
    
    # Hours since last medication dose
    # Important for MS DMTs (disease-modifying therapies)
    hours_since_medication: Optional[float] = Field(default=None, ge=0)
    
    # === ADDITIONAL CONTEXT ===
    
    # Pain level (1-10)
    # MS comorbidity that affects cognition
    pain_level: Optional[int] = Field(default=None, ge=1, le=10)
    
    # Stress level (1-10)
    # Psychosocial factor affecting performance
    stress_level: Optional[int] = Field(default=None, ge=1, le=10)
    
    # Time of day category
    # For circadian analysis
    time_of_day: Optional[str] = Field(default=None, max_length=20)  # 'morning', 'afternoon', 'evening', 'night'
    
    # Subjective "feeling ready" (1-10)
    # Self-assessment before task
    readiness_level: Optional[int] = Field(default=None, ge=1, le=10)
    
    # Free-text notes
    # Patient can report symptoms, concerns, etc.
    notes: Optional[str] = Field(default=None, max_length=500)
    
    # === ENVIRONMENTAL FACTORS ===
    
    # Distractions present (boolean)
    distractions_present: Optional[bool] = Field(default=None)
    
    # Location
    location: Optional[str] = Field(default=None, max_length=50)  # 'home', 'work', 'clinic', 'other'
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "fatigue_level": 6,
                "sleep_quality": 7,
                "sleep_hours": 7.5,
                "medication_taken_today": True,
                "hours_since_medication": 2.5,
                "pain_level": 3,
                "stress_level": 4,
                "time_of_day": "morning",
                "readiness_level": 8,
                "notes": "Feeling good today, slept well",
                "distractions_present": False,
                "location": "home"
            }
        }
