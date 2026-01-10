"""
Verify patient assignments are properly created from approved requests
"""
from sqlmodel import Session, select, create_engine
from app.core.config import settings
from app.models.assignment_request import AssignmentRequest, RequestStatus
from app.models.patient_assignment import PatientAssignment
from app.models.user import User
from app.models.doctor import Doctor

def verify_and_fix_assignments():
    """Check approved requests and create missing assignments"""
    engine = create_engine(settings.DATABASE_URL)
    
    with Session(engine) as session:
        # Get all approved requests
        approved_requests = session.exec(
            select(AssignmentRequest)
            .where(AssignmentRequest.status == RequestStatus.APPROVED.value)
        ).all()
        
        print(f"Found {len(approved_requests)} approved requests")
        
        for req in approved_requests:
            # Check if assignment exists
            assignment = session.exec(
                select(PatientAssignment)
                .where(PatientAssignment.doctor_id == req.doctor_id)
                .where(PatientAssignment.patient_id == req.patient_id)
                .where(PatientAssignment.is_active == True)
            ).first()
            
            patient = session.get(User, req.patient_id)
            doctor = session.get(Doctor, req.doctor_id)
            
            patient_email = patient.email if patient else "Unknown"
            doctor_name = doctor.full_name if doctor and doctor.full_name else "Unknown"
            
            if assignment:
                print(f"✓ Assignment exists: {patient_email} -> Dr. {doctor_name}")
            else:
                print(f"✗ Missing assignment for approved request!")
                print(f"  Patient: {patient_email}")
                print(f"  Doctor: {doctor_name}")
                print(f"  Creating assignment...")
                
                # Create the missing assignment
                new_assignment = PatientAssignment(
                    doctor_id=req.doctor_id,
                    patient_id=req.patient_id,
                    diagnosis=req.diagnosis or "Not specified",
                    treatment_goal="Improve cognitive function through targeted training",
                    is_active=True
                )
                
                # Enable patient consent
                if patient:
                    patient.consent_to_share = True
                    session.add(patient)
                
                session.add(new_assignment)
                session.commit()
                session.refresh(new_assignment)
                
                print(f"  ✓ Created assignment ID: {new_assignment.id}")

if __name__ == "__main__":
    verify_and_fix_assignments()
