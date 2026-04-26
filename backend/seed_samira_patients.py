"""
Seed three additional patients for Dr. Samira Rahman (dr.samira.rahman@gmail.com).

Idempotent — safe to run multiple times; skips any record that already exists.

Run from the backend/ directory:
    python seed_samira_patients.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date
from sqlmodel import Session, select

from app.core.config import engine
from app.core.security import hash_password
from app.models.doctor import Doctor
from app.models.user import User
from app.models.patient_assignment import PatientAssignment

# ── Target doctor ──────────────────────────────────────────────────────────────
DOCTOR_EMAIL = "dr.samira.rahman@gmail.com"

# ── New patients ───────────────────────────────────────────────────────────────
# Each entry: (full_name, email, date_of_birth, diagnosis, treatment_goal, notes)
NEW_PATIENTS = [
    (
        "Nadia Chowdhury",
        "nadia.chowdhury@patient.com",
        "1988-03-14",
        "Relapsing-Remitting Multiple Sclerosis",
        "Improve working-memory capacity and reduce cognitive fatigue",
        "Recently started DMT (Ocrelizumab). Mild cognitive symptoms. "
        "Highly motivated; works as a secondary-school teacher.",
    ),
    (
        "Tanvir Hossain",
        "tanvir.hossain@patient.com",
        "1975-09-27",
        "Mild Cognitive Impairment (amnestic)",
        "Slow cognitive decline through structured memory training",
        "Retired civil engineer. Subjective memory complaints confirmed on "
        "MoCA (score 22/30). Family support strong. No vascular risk factors.",
    ),
    (
        "Roksana Begum",
        "roksana.begum@patient.com",
        "1995-06-05",
        "Post-COVID Cognitive Syndrome",
        "Restore pre-illness attention and processing-speed baseline",
        "Long-COVID symptoms since 2022. Primary complaints: brain fog, "
        "word-finding difficulty, and attention lapses. Neuropsych eval pending.",
    ),
]


def run():
    with Session(engine) as session:
        # ── Look up doctor ─────────────────────────────────────────────────────
        doctor = session.exec(
            select(Doctor).where(Doctor.email == DOCTOR_EMAIL)
        ).first()

        if not doctor:
            print(f"ERROR: Doctor '{DOCTOR_EMAIL}' not found in the database.")
            sys.exit(1)

        print(f"Doctor: {doctor.full_name} (id={doctor.id})\n")

        # ── Create patients and assignments ────────────────────────────────────
        for full_name, email, dob, diagnosis, goal, notes in NEW_PATIENTS:

            # ── Patient record ─────────────────────────────────────────────────
            patient = session.exec(
                select(User).where(User.email == email)
            ).first()

            if patient:
                print(f"  ✓ Patient already exists:  {full_name} (id={patient.id})")
            else:
                patient = User(
                    email=email,
                    password_hash=hash_password("Patient123!"),
                    full_name=full_name,
                    date_of_birth=dob,
                    diagnosis=diagnosis,
                    consent_to_share=True,
                    is_active=True,
                )
                session.add(patient)
                session.commit()
                session.refresh(patient)
                print(f"  + Patient created:         {full_name} (id={patient.id})")

            # ── Assignment record ──────────────────────────────────────────────
            existing_assignment = session.exec(
                select(PatientAssignment).where(
                    PatientAssignment.doctor_id == doctor.id,
                    PatientAssignment.patient_id == patient.id,
                    PatientAssignment.is_active == True,
                )
            ).first()

            if existing_assignment:
                print(f"    ↳ Assignment already exists (id={existing_assignment.id})")
            else:
                assignment = PatientAssignment(
                    doctor_id=doctor.id,
                    patient_id=patient.id,
                    is_active=True,
                    diagnosis=diagnosis,
                    treatment_goal=goal,
                    notes=notes,
                )
                session.add(assignment)
                session.commit()
                session.refresh(assignment)
                print(f"    ↳ Assigned to {doctor.full_name} (assignment id={assignment.id})")

        # ── Summary ────────────────────────────────────────────────────────────
        total = session.exec(
            select(PatientAssignment).where(
                PatientAssignment.doctor_id == doctor.id,
                PatientAssignment.is_active == True,
            )
        ).all()
        print(f"\n✅ Done. Dr. {doctor.full_name} now has {len(total)} active patient(s).")


if __name__ == "__main__":
    run()
