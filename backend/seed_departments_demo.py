"""
Seed demo doctors and patients assigned to departments.

Idempotent – safe to run multiple times (skips existing records).

Run from the backend/ directory:
    python seed_departments_demo.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select
from app.core.config import engine, init_db
from app.core.security import hash_password
from app.models.doctor import Doctor
from app.models.user import User
from app.models.department import Department
from app.models.patient_assignment import PatientAssignment

init_db()

DOCTORS = [
    # (full_name, email, specialization, department_name, license_number)
    ("Dr. Arefin Kabir",      "arefin.kabir@neuro.com",      "Neuropsychology",     "Neurology",   "LN-1001"),
    ("Dr. Priya Sharma",      "priya.sharma@neuro.com",       "Neurology",           "Neurology",   "LN-1002"),
    ("Dr. James Okonkwo",     "james.okonkwo@neuro.com",      "Cognitive Neurology", "Neurology",   "LN-1003"),
    ("Dr. Layla Hassan",      "layla.hassan@psych.com",       "Psychiatry",          "Psychiatry",  "PS-2001"),
    ("Dr. Marcus Reyes",      "marcus.reyes@psych.com",       "Clinical Psychology", "Psychiatry",  "PS-2002"),
    ("Dr. Sofia Lindström",   "sofia.lindstrom@psych.com",    "Neuropsychiatry",     "Psychiatry",  "PS-2003"),
    ("Dr. Omar Farouk",       "omar.farouk@neuro.com",        "Neurorehabilitation", "Neurology",   "LN-1004"),
    ("Dr. Amara Nwosu",       "amara.nwosu@psych.com",        "Geriatric Psychiatry","Psychiatry",  "PS-2004"),
]

PATIENTS = [
    # (full_name, email, diagnosis, doctor_email)
    ("Alice Tan",        "alice.tan@patient.com",       "RRMS",              "arefin.kabir@neuro.com"),
    ("Benjamin Clarke",  "benjamin.clarke@patient.com", "PPMS",              "arefin.kabir@neuro.com"),
    ("Chloe Nguyen",     "chloe.nguyen@patient.com",    "RRMS",              "priya.sharma@neuro.com"),
    ("Daniel Osei",      "daniel.osei@patient.com",     "Epilepsy",          "james.okonkwo@neuro.com"),
    ("Eva Martinez",     "eva.martinez@patient.com",    "MCI",               "james.okonkwo@neuro.com"),
    ("Farhan Islam",     "farhan.islam@patient.com",    "Major Depression",  "layla.hassan@psych.com"),
    ("Grace Kim",        "grace.kim@patient.com",       "Bipolar I",         "layla.hassan@psych.com"),
    ("Hina Patel",       "hina.patel@patient.com",      "Schizophrenia",     "marcus.reyes@psych.com"),
    ("Ivan Sokolov",     "ivan.sokolov@patient.com",    "PTSD",              "marcus.reyes@psych.com"),
    ("Jasmine Wu",       "jasmine.wu@patient.com",      "Anxiety Disorder",  "sofia.lindstrom@psych.com"),
    ("Kevin Adeyemi",    "kevin.adeyemi@patient.com",   "RRMS",              "omar.farouk@neuro.com"),
    ("Luna Ferreira",    "luna.ferreira@patient.com",   "Parkinson's",       "amara.nwosu@psych.com"),
]

with Session(engine) as session:
    # ── Departments ────────────────────────────────────────────────────────────
    dept_map: dict[str, Department] = {}
    for dept_name in ("Neurology", "Psychiatry"):
        dept = session.exec(select(Department).where(Department.name == dept_name)).first()
        if not dept:
            dept = Department(name=dept_name)
            session.add(dept)
            session.commit()
            session.refresh(dept)
            print(f"  + Department created: {dept_name}")
        else:
            print(f"  ✓ Department exists:  {dept_name} (id={dept.id})")
        dept_map[dept_name] = dept

    # ── Doctors ────────────────────────────────────────────────────────────────
    doctor_map: dict[str, Doctor] = {}
    for full_name, email, specialization, dept_name, license_no in DOCTORS:
        doc = session.exec(select(Doctor).where(Doctor.email == email)).first()
        if doc:
            # Ensure department is set even for pre-existing rows
            dept = dept_map[dept_name]
            if doc.department_id != dept.id:
                doc.department_id = dept.id
                session.add(doc)
                session.commit()
                print(f"  ↺ Updated dept for {full_name}")
            else:
                print(f"  ✓ Doctor exists: {full_name}")
        else:
            dept = dept_map[dept_name]
            doc = Doctor(
                email=email,
                password_hash=hash_password("Doctor123!"),
                full_name=full_name,
                specialization=specialization,
                institution="NeuroBloom Hospital",
                license_number=license_no,
                department_id=dept.id,
                is_active=True,
                is_verified=True,
            )
            session.add(doc)
            session.commit()
            session.refresh(doc)
            print(f"  + Doctor created:  {full_name}  →  {dept_name}")
        doctor_map[email] = doc

    # ── Patients ───────────────────────────────────────────────────────────────
    patient_map: dict[str, User] = {}
    for full_name, email, diagnosis, doctor_email in PATIENTS:
        patient = session.exec(select(User).where(User.email == email)).first()
        if not patient:
            patient = User(
                email=email,
                password_hash=hash_password("Patient123!"),
                full_name=full_name,
                diagnosis=diagnosis,
                consent_to_share=True,
                is_active=True,
            )
            session.add(patient)
            session.commit()
            session.refresh(patient)
            print(f"  + Patient created: {full_name}")
        else:
            print(f"  ✓ Patient exists:  {full_name}")
        patient_map[email] = patient

    # ── Assignments ────────────────────────────────────────────────────────────
    for _, patient_email, _, doctor_email in PATIENTS:
        doctor = doctor_map.get(doctor_email)
        patient = patient_map.get(patient_email)
        if not doctor or not patient:
            continue
        existing = session.exec(
            select(PatientAssignment).where(
                PatientAssignment.doctor_id == doctor.id,
                PatientAssignment.patient_id == patient.id,
                PatientAssignment.is_active == True,
            )
        ).first()
        if existing:
            print(f"  ✓ Assignment exists: {patient.full_name} → {doctor.full_name}")
        else:
            assignment = PatientAssignment(
                doctor_id=doctor.id,
                patient_id=patient.id,
                is_active=True,
                diagnosis=patient.diagnosis,
                notes="Demo data seeded automatically",
            )
            session.add(assignment)
            session.commit()
            print(f"  + Assigned: {patient.full_name} → {doctor.full_name}")

print("\n✅ Department demo data seeded successfully.")
print("   Neurology:  4 doctors, 5 patients")
print("   Psychiatry: 4 doctors, 7 patients")
