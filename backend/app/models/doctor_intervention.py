from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class DoctorIntervention(SQLModel, table=True):
    """Track doctor actions and recommendations"""
    __tablename__ = "doctor_interventions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    doctor_id: int = Field(foreign_key="doctors.id")
    patient_id: int = Field(foreign_key="user.id")
    
    intervention_type: str  # "training_plan_adjustment", "note", "recommendation"
    description: str
    intervention_data: Optional[str] = Field(default=None)  # JSON for structured data
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
