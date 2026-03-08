from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from typing import List
from datetime import datetime

class DoctorCreate(BaseModel):
    """Schema for doctor registration"""
    email: EmailStr
    password: str
    full_name: str
    license_number: Optional[str] = None
    specialization: Optional[str] = None
    institution: Optional[str] = None

class DoctorLogin(BaseModel):
    """Schema for doctor login"""
    email: EmailStr
    password: str

class DoctorRead(BaseModel):
    """Schema for reading doctor data"""
    id: int
    email: str
    full_name: str
    specialization: Optional[str]
    institution: Optional[str]
    is_verified: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class PatientAssignmentCreate(BaseModel):
    """Schema for assigning a patient to a doctor"""
    patient_email: str  # Will lookup patient by email
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    treatment_goal: Optional[str] = None

class DoctorInterventionCreate(BaseModel):
    """Schema for creating a doctor intervention"""
    intervention_type: str  # "training_plan_adjustment", "note", "recommendation"
    description: str
    intervention_data: Optional[str] = None

class PrescriptionMedication(BaseModel):
    """Structured medication or instruction item within a digital prescription."""
    name: str
    dosage: str
    frequency: str
    duration: Optional[str] = None
    instructions: Optional[str] = None

class PrescriptionCreate(BaseModel):
    """Schema for creating a structured digital prescription."""
    title: str
    summary: Optional[str] = None
    patient_instructions: str
    clinician_notes: Optional[str] = None
    medications: List[PrescriptionMedication] = Field(default_factory=list)
    lifestyle_plan: List[str] = Field(default_factory=list)
    status: str = "active"
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    review_date: Optional[datetime] = None
    follow_up_plan: Optional[str] = None


class PrescriptionStatusUpdate(BaseModel):
    """Schema for retiring or reactivating an issued prescription."""
    status: str
    reason: Optional[str] = None

class MessageCreate(BaseModel):
    """Schema for creating a message"""
    recipient_id: int
    recipient_type: str  # "doctor" or "patient"
    subject: Optional[str] = None
    message: str
    parent_message_id: Optional[int] = None

class MessageRead(BaseModel):
    """Schema for reading a message"""
    id: int
    sender_id: int
    sender_type: str
    recipient_id: int
    recipient_type: str
    subject: Optional[str]
    message: str
    parent_message_id: Optional[int]
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True
