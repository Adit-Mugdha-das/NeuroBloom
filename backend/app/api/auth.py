from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import Optional
from app.models.user import User
from app.models.doctor import Doctor
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.schemas.doctor import DoctorCreate, DoctorLogin, DoctorRead
from app.core.config import engine
from app.core.security import hash_password, verify_password
from datetime import datetime
import traceback

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

@router.post("/register", response_model=UserRead)
def register(user: UserCreate, session: Session = Depends(get_session)):
    try:
        existing = session.exec(select(User).where(User.email == user.email)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        user_db = User(email=user.email, password_hash=hash_password(user.password))
        session.add(user_db)
        session.commit()
        session.refresh(user_db)
        return user_db
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in register: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
def login(user: UserLogin, session: Session = Depends(get_session)):
    try:
        # Debug: Check all users in database
        all_users = session.exec(select(User)).all()
        print(f"DEBUG: Total users in DB: {len(all_users)}")
        print(f"DEBUG: Login attempt for: {user.email}")
        
        user_db = session.exec(select(User).where(User.email == user.email)).first()
        
        if not user_db:
            print(f"DEBUG: User not found: {user.email}")
            print(f"DEBUG: Available emails: {[u.email for u in all_users]}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        print(f"DEBUG: User found: {user_db.email}, ID: {user_db.id}")
        
        if not verify_password(user.password, user_db.password_hash):
            print(f"DEBUG: Password verification failed for {user.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        print(f"DEBUG: Login successful for {user.email}")
        return {
            "message": "Login successful",
            "email": user_db.email,
            "id": user_db.id,
            "role": "patient"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in login: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# ========== DOCTOR ENDPOINTS ==========
@router.post("/doctor/register", response_model=DoctorRead)
def register_doctor(doctor: DoctorCreate, session: Session = Depends(get_session)):
    """Register new doctor (requires admin approval)"""
    try:
        # Check if email already exists in doctors
        existing = session.exec(select(Doctor).where(Doctor.email == doctor.email)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered as doctor")
        
        # Also check in patient table
        existing_patient = session.exec(select(User).where(User.email == doctor.email)).first()
        if existing_patient:
            raise HTTPException(status_code=400, detail="Email already registered as patient")

        doctor_db = Doctor(
            email=doctor.email,
            password_hash=hash_password(doctor.password),
            full_name=doctor.full_name,
            license_number=doctor.license_number,
            specialization=doctor.specialization,
            institution=doctor.institution,
            is_verified=False  # Requires admin approval
        )
        session.add(doctor_db)
        session.commit()
        session.refresh(doctor_db)
        return doctor_db
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in register_doctor: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/doctor/login")
def login_doctor(doctor: DoctorLogin, session: Session = Depends(get_session)):
    """Doctor login endpoint"""
    try:
        doctor_db = session.exec(select(Doctor).where(Doctor.email == doctor.email)).first()
        
        if not doctor_db:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not doctor_db.is_active:
            raise HTTPException(status_code=403, detail="Account deactivated")
        
        if not doctor_db.is_verified:
            raise HTTPException(status_code=403, detail="Account pending verification. Please contact administrator.")
        
        if not verify_password(doctor.password, doctor_db.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Update last login
        doctor_db.last_login = datetime.utcnow()
        session.add(doctor_db)
        session.commit()
        
        return {
            "message": "Login successful",
            "email": doctor_db.email,
            "id": doctor_db.id,
            "role": "doctor",
            "full_name": doctor_db.full_name,
            "is_verified": doctor_db.is_verified
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in login_doctor: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# ========== PATIENT PROFILE & CONSENT ==========
@router.patch("/patient/{patient_id}/consent")
def update_patient_consent(
    patient_id: int,
    consent: bool,
    session: Session = Depends(get_session)
):
    """Update patient's consent to share data with healthcare providers"""
    try:
        patient = session.get(User, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        patient.consent_to_share = consent
        session.add(patient)
        session.commit()
        session.refresh(patient)
        
        return {
            "message": "Consent updated successfully",
            "consent_to_share": patient.consent_to_share
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in update_patient_consent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patient/{patient_id}/profile")
def get_patient_profile(patient_id: int, session: Session = Depends(get_session)):
    """Get patient profile information"""
    try:
        patient = session.get(User, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return {
            "id": patient.id,
            "email": patient.email,
            "full_name": patient.full_name,
            "date_of_birth": patient.date_of_birth,
            "diagnosis": patient.diagnosis,
            "consent_to_share": patient.consent_to_share
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_patient_profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/patient/{patient_id}/profile")
def update_patient_profile(
    patient_id: int,
    full_name: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    diagnosis: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Update patient profile information"""
    try:
        patient = session.get(User, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        if full_name is not None:
            patient.full_name = full_name
        if date_of_birth is not None:
            patient.date_of_birth = date_of_birth
        if diagnosis is not None:
            patient.diagnosis = diagnosis
        
        session.add(patient)
        session.commit()
        session.refresh(patient)
        
        return {
            "message": "Profile updated successfully",
            "full_name": patient.full_name,
            "date_of_birth": patient.date_of_birth,
            "diagnosis": patient.diagnosis
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in update_patient_profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))
