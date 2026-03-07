"""
Create the default hospital administrator account.
Credentials:  email: admin   password: admin123
Run once: python create_admin.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select
from app.core.config import engine
from app.models.admin import Admin
from app.core.security import hash_password


def create_admin():
    with Session(engine) as session:
        existing = session.exec(select(Admin).where(Admin.email == "admin")).first()
        if existing:
            print("Admin account already exists (email: admin)")
            return

        admin = Admin(
            email="admin",
            password_hash=hash_password("admin123"),
            full_name="Hospital Administrator",
            is_active=True,
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
        print(f"✓ Admin account created  (id={admin.id}, email=admin, password=admin123)")


if __name__ == "__main__":
    create_admin()
