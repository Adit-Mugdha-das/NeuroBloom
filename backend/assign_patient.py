"""
Script to assign a patient to a doctor
Usage: python assign_patient.py <patient_email> <doctor_email> [diagnosis] [treatment_goal]
"""
import sys
from typing import Optional
from sqlmodel import Session, select
from app.core.config import engine
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient_assignment import PatientAssignment
from datetime import datetime, timezone

def assign_patient_to_doctor(patient_email: str, doctor_email: str, diagnosis: Optional[str] = None, treatment_goal: Optional[str] = None):
    """Assign a patient to a doctor"""
    with Session(engine) as session:
        # Find patient by email
        patient = session.exec(select(User).where(User.email == patient_email)).first()
        if not patient:
            print(f"❌ Patient not found: {patient_email}")
            return False
        
        # Find doctor by email
        doctor = session.exec(select(Doctor).where(Doctor.email == doctor_email)).first()
        if not doctor:
            print(f"❌ Doctor not found: {doctor_email}")
            return False
        
        # Check if already assigned
        existing = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.patient_id == patient.id)
            .where(PatientAssignment.doctor_id == doctor.id)
            .where(PatientAssignment.is_active == True)
        ).first()
        
        if existing:
            print(f"⚠️  Patient {patient_email} is already assigned to Dr. {doctor.full_name}")
            return False
        
        # Enable patient consent to share data with doctor
        patient.consent_to_share = True
        session.add(patient)
        
        # Validate IDs are not None
        if patient.id is None or doctor.id is None:
            print(f"❌ Error: Invalid patient or doctor ID")
            return False
        
        # Create assignment
        assignment = PatientAssignment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            diagnosis=diagnosis or "Not specified",
            treatment_goal=treatment_goal or "Improve cognitive function through targeted training",
            assigned_at=datetime.now(timezone.utc),
            is_active=True
        )
        session.add(assignment)
        session.commit()
        
        print(f"✅ Successfully assigned patient to doctor!")
        print(f"   Patient: {patient.email}")
        print(f"   Doctor: {doctor.full_name} ({doctor.email})")
        print(f"   Diagnosis: {assignment.diagnosis}")
        print(f"   Treatment Goal: {assignment.treatment_goal}")
        print(f"   Patient consent enabled: Yes")
        return True

def list_assignments():
    """List all active patient-doctor assignments"""
    with Session(engine) as session:
        assignments = session.exec(
            select(PatientAssignment).where(PatientAssignment.is_active == True)
        ).all()
        
        if not assignments:
            print("No active patient-doctor assignments found")
            return
        
        print("\n📋 Active Patient-Doctor Assignments:")
        print("-" * 100)
        for assignment in assignments:
            patient = session.get(User, assignment.patient_id)
            doctor = session.get(Doctor, assignment.doctor_id)
            
            if patient and doctor:
                print(f"Patient: {patient.email} → Doctor: {doctor.full_name} ({doctor.email})")
                print(f"  Diagnosis: {assignment.diagnosis}")
                print(f"  Treatment Goal: {assignment.treatment_goal}")
                print(f"  Assigned: {assignment.assigned_at.strftime('%Y-%m-%d')}")
                print("-" * 100)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Assign patient:        python assign_patient.py <patient_email> <doctor_email> [diagnosis] [treatment_goal]")
        print("  List all assignments:  python assign_patient.py --list")
        print("\nExamples:")
        print('  python assign_patient.py patient@test.com doctor@test.com "Multiple Sclerosis" "Improve memory and processing speed"')
        print("  python assign_patient.py patient@test.com doctor@test.com")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        list_assignments()
    elif len(sys.argv) >= 3:
        patient_email = sys.argv[1]
        doctor_email = sys.argv[2]
        diagnosis = sys.argv[3] if len(sys.argv) > 3 else None
        treatment_goal = sys.argv[4] if len(sys.argv) > 4 else None
        assign_patient_to_doctor(patient_email, doctor_email, diagnosis, treatment_goal)
    else:
        print("❌ Error: Please provide both patient email and doctor email")
        print("Usage: python assign_patient.py <patient_email> <doctor_email> [diagnosis] [treatment_goal]")
