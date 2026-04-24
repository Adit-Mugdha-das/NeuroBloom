"""
Seed all required initial data for a fresh database (local or Render).

Idempotent — safe to run multiple times; skips records that already exist.

Run from the backend/ directory:
    python seed_initial_data.py

What this seeds:
  1. Admin account       (admin@gmail.com / admin123)
  2. Departments         (Neurology, Psychiatry)
  3. Cognitive tasks     (full task library via seed_cognitive_tasks)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select

from app.core.config import engine, init_db
from app.core.security import hash_password
from app.models.admin import Admin
from app.models.department import Department
from seed_cognitive_tasks import seed_cognitive_tasks


# ── 1. Ensure tables exist ────────────────────────────────────────────────────
print("Initialising database tables...")
init_db()
print("  ✓ Tables ready")


# ── 2. Admin account ──────────────────────────────────────────────────────────
ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "admin123"

with Session(engine) as session:
    # Remove legacy "admin" (no @) entry if present
    legacy = session.exec(select(Admin).where(Admin.email == "admin")).first()
    if legacy:
        session.delete(legacy)
        session.commit()
        print("  Removed legacy admin account (email: admin)")

    existing_admin = session.exec(select(Admin).where(Admin.email == ADMIN_EMAIL)).first()
    if existing_admin:
        print(f"  ✓ Admin already exists (email: {ADMIN_EMAIL})")
    else:
        admin = Admin(
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            full_name="Hospital Administrator",
            is_active=True,
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
        print(f"  ✓ Admin created (id={admin.id}, email={ADMIN_EMAIL})")


# ── 3. Departments ─────────────────────────────────────────────────────────────
DEPARTMENTS = [
    {"name": "Neurology",   "description": "Neurological disorders and brain health"},
    {"name": "Psychiatry",  "description": "Mental health and psychiatric care"},
]

with Session(engine) as session:
    for dept_data in DEPARTMENTS:
        existing = session.exec(
            select(Department).where(Department.name == dept_data["name"])
        ).first()
        if existing:
            print(f"  ✓ Department already exists: {dept_data['name']}")
        else:
            dept = Department(name=dept_data["name"], description=dept_data["description"])
            session.add(dept)
            session.commit()
            session.refresh(dept)
            print(f"  ✓ Department created: {dept.name} (id={dept.id})")


# ── 4. Cognitive tasks ────────────────────────────────────────────────────────
print("Seeding cognitive tasks...")
seed_cognitive_tasks(verbose=False)
print("  ✓ Cognitive tasks ready")

print("\nAll initial data seeded successfully.")
