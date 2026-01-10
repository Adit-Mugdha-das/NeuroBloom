from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models.patient_assignment import PatientAssignment

class Doctor(SQLModel, table=True):
    """Healthcare provider/clinician model"""
    __tablename__ = "doctors"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    
    # Professional info
    full_name: str
    license_number: Optional[str] = Field(default=None)
    specialization: Optional[str] = Field(default=None)  # "Neurologist", "Neuropsychologist", etc.
    institution: Optional[str] = Field(default=None)
    
    # Account management
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)  # Require admin verification
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None)
    
    # Relationships
    patient_assignments: List["PatientAssignment"] = Relationship(back_populates="doctor")
