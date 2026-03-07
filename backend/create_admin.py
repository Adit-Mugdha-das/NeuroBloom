"""
Create the default hospital administrator account.
Credentials:  email: admin@gmail.com   password: admin123
Run once: python create_admin.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select
from app.core.config import engine
from app.models.admin import Admin
from app.core.security import hash_password

ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "admin123"

def create_admin():
    with Session(engine) as session:
        # Remove legacy "admin" (no @) entry if present
        legacy = session.exec(select(Admin).where(Admin.email == "admin")).first()
        if legacy:
            session.delete(legacy)
            session.commit()
            print("Removed legacy admin account (email: admin)")

        existing = session.exec(select(Admin).where(Admin.email == ADMIN_EMAIL)).first()
        if existing:
            print(f"Admin account already exists (email: {ADMIN_EMAIL})")
            return

        admin = Admin(
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            full_name="Hospital Administrator",
            is_active=True,
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
        print(f"✓ Admin account created  (id={admin.id}, email={ADMIN_EMAIL}, password={ADMIN_PASSWORD})")


if __name__ == "__main__":
    create_admin()
