from pydantic import BaseModel, EmailStr
from typing import Optional
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
