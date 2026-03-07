from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from datetime import datetime
from app.models.admin import Admin
from app.models.doctor import Doctor
from app.models.user import User
from app.models.patient_assignment import PatientAssignment
from app.schemas.admin import AdminLogin, AdminRead
from app.core.config import engine
from app.core.security import verify_password, hash_password
from pydantic import BaseModel
import traceback

router = APIRouter(prefix="/admin", tags=["admin"])


class ResetPasswordBody(BaseModel):
    new_password: str


class TransferPatientBody(BaseModel):
    new_doctor_id: int


def get_session():
    with Session(engine) as session:
        yield session


def _require_admin(admin_id: int, session: Session) -> Admin:
    """Verify admin exists and is active (consistent with existing auth pattern)."""
    admin = session.get(Admin, admin_id)
    if not admin or not admin.is_active:
        raise HTTPException(status_code=403, detail="Admin access required")
    return admin


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────

@router.post("/login")
def admin_login(credentials: AdminLogin, session: Session = Depends(get_session)):
    """Authenticate hospital administrator."""
    try:
        admin = session.exec(select(Admin).where(Admin.email == credentials.email)).first()
        if not admin or not verify_password(credentials.password, admin.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not admin.is_active:
            raise HTTPException(status_code=403, detail="Admin account is deactivated")

        admin.last_login = datetime.utcnow()
        session.add(admin)
        session.commit()

        return {
            "message": "Login successful",
            "id": admin.id,
            "email": admin.email,
            "full_name": admin.full_name,
            "role": "admin",
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in admin_login: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# DASHBOARD STATS
# ─────────────────────────────────────────────

@router.get("/stats")
def get_stats(admin_id: int, session: Session = Depends(get_session)):
    """Overview numbers for the admin dashboard."""
    _require_admin(admin_id, session)
    total_patients = len(session.exec(select(User)).all())
    active_patients = len(session.exec(select(User).where(User.is_active == True)).all())
    total_doctors = len(session.exec(select(Doctor)).all())
    pending_doctors = len(
        session.exec(select(Doctor).where(Doctor.is_verified == False).where(Doctor.is_active == True)).all()
    )
    active_doctors = len(
        session.exec(select(Doctor).where(Doctor.is_verified == True).where(Doctor.is_active == True)).all()
    )
    return {
        "total_patients": total_patients,
        "active_patients": active_patients,
        "total_doctors": total_doctors,
        "pending_doctors": pending_doctors,
        "active_doctors": active_doctors,
    }


# ─────────────────────────────────────────────
# DOCTOR MANAGEMENT
# ─────────────────────────────────────────────

@router.get("/doctors")
def list_doctors(admin_id: int, session: Session = Depends(get_session)):
    """List all doctors with their current status."""
    _require_admin(admin_id, session)
    doctors = session.exec(select(Doctor)).all()
    return {
        "doctors": [
            {
                "id": d.id,
                "email": d.email,
                "full_name": d.full_name,
                "license_number": d.license_number,
                "specialization": d.specialization,
                "institution": d.institution,
                "is_active": d.is_active,
                "is_verified": d.is_verified,
                "created_at": d.created_at,
                "last_login": d.last_login,
            }
            for d in doctors
        ],
        "total": len(doctors),
    }


@router.patch("/doctors/{doctor_id}/approve")
def approve_doctor(doctor_id: int, admin_id: int, session: Session = Depends(get_session)):
    """Approve a doctor's registration so they can log in."""
    _require_admin(admin_id, session)
    doctor = session.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor.is_verified = True
    doctor.is_active = True
    session.add(doctor)
    session.commit()
    return {"message": f"Doctor {doctor.full_name} has been approved", "doctor_id": doctor_id}


@router.patch("/doctors/{doctor_id}/suspend")
def suspend_doctor(doctor_id: int, admin_id: int, session: Session = Depends(get_session)):
    """Suspend a doctor account (sets is_active=False)."""
    _require_admin(admin_id, session)
    doctor = session.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor.is_active = False
    session.add(doctor)
    session.commit()
    return {"message": f"Doctor {doctor.full_name} has been suspended", "doctor_id": doctor_id}


@router.patch("/doctors/{doctor_id}/activate")
def activate_doctor(doctor_id: int, admin_id: int, session: Session = Depends(get_session)):
    """Re-activate a previously suspended doctor."""
    _require_admin(admin_id, session)
    doctor = session.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor.is_active = True
    session.add(doctor)
    session.commit()
    return {"message": f"Doctor {doctor.full_name} has been activated", "doctor_id": doctor_id}


# ─────────────────────────────────────────────
# PATIENT MANAGEMENT
# ─────────────────────────────────────────────

@router.get("/patients")
def list_patients(admin_id: int, session: Session = Depends(get_session)):
    """List all patient accounts."""
    _require_admin(admin_id, session)
    patients = session.exec(select(User)).all()
    return {
        "patients": [
            {
                "id": p.id,
                "email": p.email,
                "full_name": p.full_name,
                "date_of_birth": p.date_of_birth,
                "diagnosis": p.diagnosis,
                "is_active": p.is_active,
                "consent_to_share": p.consent_to_share,
            }
            for p in patients
        ],
        "total": len(patients),
    }


@router.patch("/patients/{patient_id}/deactivate")
def deactivate_patient(patient_id: int, admin_id: int, session: Session = Depends(get_session)):
    """Deactivate a patient account."""
    _require_admin(admin_id, session)
    patient = session.get(User, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient.is_active = False
    session.add(patient)
    session.commit()
    return {"message": f"Patient account deactivated", "patient_id": patient_id}


@router.patch("/patients/{patient_id}/activate")
def activate_patient(patient_id: int, admin_id: int, session: Session = Depends(get_session)):
    """Re-activate a patient account."""
    _require_admin(admin_id, session)
    patient = session.get(User, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient.is_active = True
    session.add(patient)
    session.commit()
    return {"message": f"Patient account activated", "patient_id": patient_id}


# ─────────────────────────────────────────────
# RESET PASSWORDS
# ─────────────────────────────────────────────

@router.post("/doctors/{doctor_id}/reset-password")
def reset_doctor_password(doctor_id: int, admin_id: int, body: ResetPasswordBody, session: Session = Depends(get_session)):
    """Reset a doctor's password."""
    _require_admin(admin_id, session)
    if not body.new_password or len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    doctor = session.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctor.password_hash = hash_password(body.new_password)
    session.add(doctor)
    session.commit()
    return {"message": f"Password reset for Dr. {doctor.full_name}", "doctor_id": doctor_id}


@router.post("/patients/{patient_id}/reset-password")
def reset_patient_password(patient_id: int, admin_id: int, body: ResetPasswordBody, session: Session = Depends(get_session)):
    """Reset a patient's password."""
    _require_admin(admin_id, session)
    if not body.new_password or len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    patient = session.get(User, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient.password_hash = hash_password(body.new_password)
    session.add(patient)
    session.commit()
    return {"message": "Patient password reset successfully", "patient_id": patient_id}


# ─────────────────────────────────────────────
# TRANSFER PATIENT TO ANOTHER DOCTOR
# ─────────────────────────────────────────────

@router.post("/patients/{patient_id}/transfer")
def transfer_patient(patient_id: int, admin_id: int, body: TransferPatientBody, session: Session = Depends(get_session)):
    """Transfer a patient's active assignment to a different doctor."""
    _require_admin(admin_id, session)

    patient = session.get(User, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    new_doctor = session.get(Doctor, body.new_doctor_id)
    if not new_doctor or not new_doctor.is_active or not new_doctor.is_verified:
        raise HTTPException(status_code=400, detail="Target doctor not found or not active/verified")

    # Find current active assignment
    assignment = session.exec(
        select(PatientAssignment)
        .where(PatientAssignment.patient_id == patient_id)
        .where(PatientAssignment.is_active == True)
    ).first()

    if not assignment:
        raise HTTPException(status_code=404, detail="No active assignment found for this patient")

    if assignment.doctor_id == body.new_doctor_id:
        raise HTTPException(status_code=400, detail="Patient is already assigned to this doctor")

    old_doctor = session.get(Doctor, assignment.doctor_id)
    old_name = old_doctor.full_name if old_doctor else f"Doctor #{assignment.doctor_id}"

    assignment.doctor_id = body.new_doctor_id
    assignment.assigned_at = datetime.utcnow()
    assignment.assigned_by = admin_id
    session.add(assignment)
    session.commit()

    return {
        "message": f"Patient transferred from {old_name} to Dr. {new_doctor.full_name}",
        "patient_id": patient_id,
        "new_doctor_id": body.new_doctor_id,
    }
