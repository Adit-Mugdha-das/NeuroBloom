"""
Script to verify/approve doctor accounts
Usage: python verify_doctor.py <email>
"""
import sys
from sqlmodel import Session, select
from app.core.config import engine
from app.models.doctor import Doctor

def verify_doctor(email: str):
    """Verify a doctor account by email"""
    with Session(engine) as session:
        # Find doctor by email
        doctor = session.exec(select(Doctor).where(Doctor.email == email)).first()
        
        if not doctor:
            print(f"❌ No doctor found with email: {email}")
            return False
        
        if doctor.is_verified:
            print(f"✅ Doctor {email} is already verified")
            return True
        
        # Verify the doctor
        doctor.is_verified = True
        session.add(doctor)
        session.commit()
        
        print(f"✅ Doctor {email} has been verified successfully!")
        print(f"   Name: {doctor.full_name}")
        print(f"   License: {doctor.license_number}")
        print(f"   Specialization: {doctor.specialization}")
        print(f"   Institution: {doctor.institution or 'N/A'}")
        return True

def list_all_doctors():
    """List all doctors in the system"""
    with Session(engine) as session:
        doctors = session.exec(select(Doctor)).all()
        
        if not doctors:
            print("No doctors found in the system")
            return
        
        print("\n📋 All Doctors:")
        print("-" * 80)
        for doctor in doctors:
            status = "✅ Verified" if doctor.is_verified else "⏳ Pending"
            active = "Active" if doctor.is_active else "Inactive"
            print(f"{status} | {active}")
            print(f"  Email: {doctor.email}")
            print(f"  Name: {doctor.full_name}")
            print(f"  License: {doctor.license_number}")
            print(f"  Specialization: {doctor.specialization}")
            print(f"  Institution: {doctor.institution or 'N/A'}")
            print("-" * 80)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Verify a doctor:  python verify_doctor.py <email>")
        print("  List all doctors: python verify_doctor.py --list")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        list_all_doctors()
    else:
        email = sys.argv[1]
        verify_doctor(email)
