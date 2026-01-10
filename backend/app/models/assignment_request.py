from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum

class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class AssignmentRequest(SQLModel, table=True):
    """Patient requests for doctor assignment"""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="user.id", index=True)
    doctor_id: int = Field(foreign_key="doctors.id", index=True)
    
    # Request details
    status: str = Field(default=RequestStatus.PENDING.value)  # pending, approved, rejected, cancelled
    reason: Optional[str] = Field(default=None)  # Why patient wants this doctor
    message: Optional[str] = Field(default=None)  # Additional message from patient
    
    # Diagnosis info (patient provided)
    diagnosis: Optional[str] = Field(default=None)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Doctor response
    doctor_notes: Optional[str] = Field(default=None)  # Notes when accepting/rejecting
    responded_at: Optional[datetime] = Field(default=None)
