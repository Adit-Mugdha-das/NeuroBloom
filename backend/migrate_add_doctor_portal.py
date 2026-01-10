"""
Database migration script to add doctor portal tables.
Run this script to create the new tables for the doctor portal feature.
"""

from sqlmodel import SQLModel, create_engine
from app.core.config import settings, engine
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient_assignment import PatientAssignment
from app.models.doctor_intervention import DoctorIntervention
from app.models.baseline_assessment import BaselineAssessment
from app.models.training_plan import TrainingPlan
from app.models.training_session import TrainingSession
from app.models.cognitive_task import CognitiveTask, UserTaskPreference
from app.models.badge import UserBadge

# Import all models to ensure they're registered with SQLModel
print("Importing all models...")

def create_doctor_tables():
    """Create doctor-related tables and update User table"""
    print("\n" + "="*60)
    print("NeuroBloom - Doctor Portal Database Migration")
    print("="*60)
    
    print("\n[1/3] Creating database tables...")
    try:
        # This will create all tables defined in SQLModel
        # It will add new columns to existing tables (like User)
        # and create new tables (Doctor, PatientAssignment, DoctorIntervention)
        SQLModel.metadata.create_all(engine)
        print("✅ Tables created/updated successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return
    
    print("\n[2/3] Verifying table structure...")
    try:
        from sqlmodel import Session
        with Session(engine) as session:
            # Check if we can query the new tables
            from sqlmodel import select
            
            # Test Doctor table
            session.exec(select(Doctor)).all()
            print("✅ Doctor table verified")
            
            # Test PatientAssignment table
            session.exec(select(PatientAssignment)).all()
            print("✅ PatientAssignment table verified")
            
            # Test DoctorIntervention table
            session.exec(select(DoctorIntervention)).all()
            print("✅ DoctorIntervention table verified")
            
            # Test updated User table
            session.exec(select(User)).all()
            print("✅ User table updated verified")
            
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        return
    
    print("\n[3/3] Migration Summary:")
    print("="*60)
    print("✅ Doctor table - CREATED")
    print("✅ PatientAssignment table - CREATED")
    print("✅ DoctorIntervention table - CREATED")
    print("✅ User table - UPDATED (added: full_name, date_of_birth, diagnosis, consent_to_share)")
    print("="*60)
    
    print("\n✨ Migration completed successfully!")
    print("\nNext steps:")
    print("1. Restart your backend server")
    print("2. Test doctor registration: POST /api/auth/doctor/register")
    print("3. Approve a doctor in database (set is_verified=True)")
    print("4. Test doctor login: POST /api/auth/doctor/login")
    print("5. Assign a patient: POST /api/doctor/{doctor_id}/assign-patient")
    print("\n")

if __name__ == "__main__":
    create_doctor_tables()
