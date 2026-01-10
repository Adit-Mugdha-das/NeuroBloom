from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models.doctor import Doctor

class PatientAssignment(SQLModel, table=True):
    """Links doctors to their patients"""
    __tablename__ = "patient_assignments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    doctor_id: int = Field(foreign_key="doctors.id", index=True)
    patient_id: int = Field(foreign_key="user.id", index=True)  # References User table
    
    # Assignment details
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: Optional[int] = Field(default=None)  # Admin who made assignment
    is_active: bool = Field(default=True)
    
    # Clinical context
    diagnosis: Optional[str] = Field(default=None)  # "RRMS", "PPMS", etc.
    notes: Optional[str] = Field(default=None)
    treatment_goal: Optional[str] = Field(default=None)
    
    # Relationships
    doctor: Optional["Doctor"] = Relationship(back_populates="patient_assignments")
