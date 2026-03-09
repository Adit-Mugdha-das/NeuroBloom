from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, col
from typing import Optional
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient_assignment import PatientAssignment
from app.models.doctor_intervention import DoctorIntervention
from app.models.message import Message
from app.models.notification import Notification
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.schemas.doctor import DoctorCreate, DoctorLogin, DoctorRead, MessageCreate
from app.core.config import engine
from app.core.prescriptions import generate_prescription_pdf_bytes, parse_prescription_data, serialize_prescription_intervention
from app.core.security import hash_password, verify_password
from datetime import datetime
import json
import io
import traceback

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

def _parse_prescription_data(value: Optional[str]):
    return parse_prescription_data(value)


def _participant_exists(session: Session, participant_id: int, participant_type: str) -> bool:
    if participant_type == "doctor":
        return session.get(Doctor, participant_id) is not None
    if participant_type == "patient":
        return session.get(User, participant_id) is not None
    return False

@router.post("/register", response_model=UserRead)
def register(user: UserCreate, session: Session = Depends(get_session)):
    try:
        existing = session.exec(select(User).where(User.email == user.email)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        user_db = User(
            email=user.email,
            password_hash=hash_password(user.password),
            full_name=user.full_name
        )
        session.add(user_db)
        session.commit()
        session.refresh(user_db)
        return user_db
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in register: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
def login(user: UserLogin, session: Session = Depends(get_session)):
    try:
        # Debug: Check all users in database
        all_users = session.exec(select(User)).all()
        print(f"DEBUG: Total users in DB: {len(all_users)}")
        print(f"DEBUG: Login attempt for: {user.email}")
        
        user_db = session.exec(select(User).where(User.email == user.email)).first()
        
        if not user_db:
            print(f"DEBUG: User not found: {user.email}")
            print(f"DEBUG: Available emails: {[u.email for u in all_users]}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        print(f"DEBUG: User found: {user_db.email}, ID: {user_db.id}")
        
        if not verify_password(user.password, user_db.password_hash):
            print(f"DEBUG: Password verification failed for {user.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        print(f"DEBUG: Login successful for {user.email}")
        return {
            "message": "Login successful",
            "email": user_db.email,
            "id": user_db.id,
            "role": "patient",
            "full_name": user_db.full_name
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in login: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# ========== DOCTOR ENDPOINTS ==========
@router.post("/doctor/register", response_model=DoctorRead)
def register_doctor(doctor: DoctorCreate, session: Session = Depends(get_session)):
    """Register new doctor (requires admin approval)"""
    try:
        # Check if email already exists in doctors
        existing = session.exec(select(Doctor).where(Doctor.email == doctor.email)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered as doctor")
        
        # Also check in patient table
        existing_patient = session.exec(select(User).where(User.email == doctor.email)).first()
        if existing_patient:
            raise HTTPException(status_code=400, detail="Email already registered as patient")

        doctor_db = Doctor(
            email=doctor.email,
            password_hash=hash_password(doctor.password),
            full_name=doctor.full_name,
            license_number=doctor.license_number,
            specialization=doctor.specialization,
            institution=doctor.institution,
            is_verified=False  # Requires admin approval
        )
        session.add(doctor_db)
        session.commit()
        session.refresh(doctor_db)
        return doctor_db
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in register_doctor: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/doctor/login")
def login_doctor(doctor: DoctorLogin, session: Session = Depends(get_session)):
    """Doctor login endpoint"""
    try:
        doctor_db = session.exec(select(Doctor).where(Doctor.email == doctor.email)).first()
        
        if not doctor_db:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not doctor_db.is_active:
            raise HTTPException(status_code=403, detail="Account deactivated")
        
        if not doctor_db.is_verified:
            raise HTTPException(status_code=403, detail="Account pending verification. Please contact administrator.")
        
        if not verify_password(doctor.password, doctor_db.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Update last login
        doctor_db.last_login = datetime.utcnow()
        session.add(doctor_db)
        session.commit()
        
        return {
            "message": "Login successful",
            "email": doctor_db.email,
            "id": doctor_db.id,
            "role": "doctor",
            "full_name": doctor_db.full_name,
            "is_verified": doctor_db.is_verified
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in login_doctor: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# ========== PATIENT PROFILE & CONSENT ==========
@router.patch("/patient/{patient_id}/consent")
def update_patient_consent(
    patient_id: int,
    consent: bool,
    session: Session = Depends(get_session)
):
    """Update patient's consent to share data with healthcare providers"""
    try:
        patient = session.get(User, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        patient.consent_to_share = consent
        session.add(patient)
        session.commit()
        session.refresh(patient)
        
        return {
            "message": "Consent updated successfully",
            "consent_to_share": patient.consent_to_share
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in update_patient_consent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patient/{patient_id}/profile")
def get_patient_profile(patient_id: int, session: Session = Depends(get_session)):
    """Get patient profile information"""
    try:
        patient = session.get(User, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return {
            "id": patient.id,
            "email": patient.email,
            "full_name": patient.full_name,
            "date_of_birth": patient.date_of_birth,
            "diagnosis": patient.diagnosis,
            "consent_to_share": patient.consent_to_share
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_patient_profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/patient/{patient_id}/profile")
def update_patient_profile(
    patient_id: int,
    full_name: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    diagnosis: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Update patient profile information"""
    try:
        patient = session.get(User, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        if full_name is not None:
            patient.full_name = full_name
        if date_of_birth is not None:
            patient.date_of_birth = date_of_birth
        if diagnosis is not None:
            patient.diagnosis = diagnosis
        
        session.add(patient)
        session.commit()
        session.refresh(patient)
        
        return {
            "message": "Profile updated successfully",
            "full_name": patient.full_name,
            "date_of_birth": patient.date_of_birth,
            "diagnosis": patient.diagnosis
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in update_patient_profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== PATIENT MESSAGING ==========
@router.post("/patient/{patient_id}/messages/send")
def send_patient_message(
    patient_id: int,
    message_data: MessageCreate,
    session: Session = Depends(get_session)
):
    """Patient sends a message to their assigned doctor"""
    try:
        # Verify patient exists
        patient = session.get(User, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        if message_data.recipient_type not in {"doctor", "patient"}:
            raise HTTPException(status_code=400, detail="recipient_type must be doctor or patient")

        if not _participant_exists(session, message_data.recipient_id, message_data.recipient_type):
            raise HTTPException(status_code=404, detail="Recipient not found")
        
        # Verify patient is assigned to this doctor
        if message_data.recipient_type == "doctor":
            assignment = session.exec(
                select(PatientAssignment)
                .where(PatientAssignment.patient_id == patient_id)
                .where(PatientAssignment.doctor_id == message_data.recipient_id)
                .where(PatientAssignment.is_active == True)
            ).first()
            
            if not assignment:
                raise HTTPException(status_code=403, detail="You are not assigned to this doctor")
        
        # Create message
        message = Message(
            sender_id=patient_id,
            sender_type="patient",
            recipient_id=message_data.recipient_id,
            recipient_type=message_data.recipient_type,
            subject=message_data.subject,
            message=message_data.message,
            parent_message_id=message_data.parent_message_id
        )
        
        session.add(message)
        session.commit()
        session.refresh(message)
        
        return {
            "message": "Message sent successfully",
            "message_id": message.id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in send_patient_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patient/{patient_id}/messages")
def get_patient_messages(
    patient_id: int,
    unread_only: bool = False,
    limit: int = 50,
    session: Session = Depends(get_session)
):
    """Get messages for a patient"""
    try:
        # Verify patient exists
        patient = session.get(User, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Build query
        query = select(Message).where(
            ((Message.sender_type == "patient") & (Message.sender_id == patient_id)) |
            ((Message.recipient_type == "patient") & (Message.recipient_id == patient_id))
        )
        
        # Filter unread
        if unread_only:
            query = query.where(
                (Message.recipient_type == "patient") & (Message.recipient_id == patient_id) & (Message.is_read == False)
            )
        
        query = query.order_by(col(Message.created_at).desc()).limit(limit)
        
        messages = session.exec(query).all()
        
        # Get sender/recipient details
        messages_data = []
        for msg in messages:
            if msg.sender_type == "doctor":
                sender = session.get(Doctor, msg.sender_id)
                sender_name = sender.full_name if sender and sender.full_name else "Unknown"
            else:
                sender = session.get(User, msg.sender_id)
                if sender:
                    sender_name = sender.full_name or sender.email
                else:
                    sender_name = "Unknown"
            
            if msg.recipient_type == "doctor":
                recipient = session.get(Doctor, msg.recipient_id)
                recipient_name = recipient.full_name if recipient and recipient.full_name else "Unknown"
            else:
                recipient = session.get(User, msg.recipient_id)
                if recipient:
                    recipient_name = recipient.full_name or recipient.email
                else:
                    recipient_name = "Unknown"
            
            messages_data.append({
                "id": msg.id,
                "sender_id": msg.sender_id,
                "sender_type": msg.sender_type,
                "sender_name": sender_name,
                "recipient_id": msg.recipient_id,
                "recipient_type": msg.recipient_type,
                "recipient_name": recipient_name,
                "subject": msg.subject,
                "message": msg.message,
                "parent_message_id": msg.parent_message_id,
                "is_read": msg.is_read,
                "read_at": msg.read_at,
                "created_at": msg.created_at
            })
        
        # Count unread
        unread_count = session.exec(
            select(Message)
            .where(Message.recipient_type == "patient")
            .where(Message.recipient_id == patient_id)
            .where(Message.is_read == False)
        ).all()
        
        return {
            "messages": messages_data,
            "total": len(messages_data),
            "unread_count": len(unread_count)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_patient_messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patient/{patient_id}/notifications")
def get_patient_notifications(patient_id: int, session: Session = Depends(get_session)):
    """Get active admin notifications for a patient."""
    patient = session.get(User, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    notifications = list(session.exec(
        select(Notification)
        .where(Notification.is_active == True)
        .where((Notification.audience == "all") | (Notification.audience == "patient"))
        .order_by(col(Notification.created_at).desc())
    ).all())

    return {
        "notifications": [
            {
                "id": notification.id,
                "notification_type": notification.notification_type,
                "title": notification.title,
                "message": notification.message,
                "created_at": notification.created_at.isoformat(),
            }
            for notification in notifications
        ]
    }

@router.get("/patient/{patient_id}/prescriptions")
def get_patient_prescriptions(patient_id: int, session: Session = Depends(get_session)):
    """Get digital prescriptions issued by the patient's assigned doctor."""
    try:
        patient = session.get(User, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        assignment = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.patient_id == patient_id)
            .where(PatientAssignment.is_active == True)
        ).first()

        if not assignment:
            return {
                "has_doctor": False,
                "prescriptions": [],
                "summary": {"total": 0, "active": 0}
            }

        doctor = session.get(Doctor, assignment.doctor_id)
        prescriptions = session.exec(
            select(DoctorIntervention)
            .where(DoctorIntervention.patient_id == patient_id)
            .where(DoctorIntervention.doctor_id == assignment.doctor_id)
            .where(DoctorIntervention.intervention_type == "digital_prescription")
            .order_by(col(DoctorIntervention.created_at).desc())
        ).all()

        items = []
        for intervention in prescriptions:
            item = serialize_prescription_intervention(
                intervention,
                doctor=doctor,
                patient=patient,
                diagnosis=patient.diagnosis,
            )
            if not item.get("doctor_name"):
                item["doctor_name"] = "Assigned doctor"
            items.append(item)

        return {
            "has_doctor": True,
            "doctor": {
                "id": doctor.id if doctor else assignment.doctor_id,
                "name": doctor.full_name if doctor and doctor.full_name else "Assigned doctor",
                "specialization": doctor.specialization if doctor else None
            },
            "prescriptions": items,
            "summary": {
                "total": len(items),
                "active": sum(1 for item in items if item["status"] == "active")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_patient_prescriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patient/{patient_id}/prescriptions/{prescription_id}/pdf")
def download_patient_prescription_pdf(
    patient_id: int,
    prescription_id: int,
    session: Session = Depends(get_session)
):
    """Allow a patient to view or download an issued prescription PDF."""
    try:
        patient = session.get(User, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        assignment = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.patient_id == patient_id)
            .where(PatientAssignment.is_active == True)
        ).first()

        if not assignment:
            raise HTTPException(status_code=404, detail="No assigned doctor found")

        doctor = session.get(Doctor, assignment.doctor_id)
        intervention = session.get(DoctorIntervention, prescription_id)

        if not intervention:
            raise HTTPException(status_code=404, detail="Prescription not found")

        if intervention.patient_id != patient_id or intervention.doctor_id != assignment.doctor_id or intervention.intervention_type != "digital_prescription":
            raise HTTPException(status_code=403, detail="Not authorized")

        prescription_payload = serialize_prescription_intervention(
            intervention,
            doctor=doctor,
            patient=patient,
            diagnosis=patient.diagnosis,
        )
        pdf_bytes = generate_prescription_pdf_bytes(prescription_payload)
        filename = f"prescription-{prescription_payload['verification_id']}.pdf"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'}
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in download_patient_prescription_pdf: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/patient/{patient_id}/messages/{message_id}/mark-read")
def mark_patient_message_read(
    patient_id: int,
    message_id: int,
    session: Session = Depends(get_session)
):
    """Mark a message as read (patient side)"""
    try:
        message = session.get(Message, message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        if message.recipient_id != patient_id or message.recipient_type != "patient":
            raise HTTPException(status_code=403, detail="Not authorized")
        
        message.is_read = True
        message.read_at = datetime.utcnow()
        session.add(message)
        session.commit()
        
        return {"message": "Message marked as read"}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in mark_patient_message_read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patient/{patient_id}/messages/with-doctor")
def get_patient_conversation_with_doctor(
    patient_id: int,
    session: Session = Depends(get_session)
):
    """Get conversation between patient and their assigned doctor"""
    try:
        # Get patient's doctor assignment
        assignment = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.patient_id == patient_id)
            .where(PatientAssignment.is_active == True)
        ).first()
        
        if not assignment:
            return {
                "has_doctor": False,
                "messages": [],
                "total": 0
            }
        
        doctor_id = assignment.doctor_id
        
        # Get all messages
        messages = session.exec(
            select(Message)
            .where(
                ((Message.sender_id == patient_id) & (Message.sender_type == "patient") & (Message.recipient_type == "doctor") & (Message.recipient_id == doctor_id)) |
                ((Message.sender_id == doctor_id) & (Message.sender_type == "doctor") & (Message.recipient_type == "patient") & (Message.recipient_id == patient_id))
            )
            .order_by(col(Message.created_at))
        ).all()
        
        doctor = session.get(Doctor, doctor_id)
        patient = session.get(User, patient_id)
        
        # Get names safely
        doctor_name = doctor.full_name if doctor and doctor.full_name else "Unknown"
        patient_name = (patient.full_name or patient.email) if patient else "Unknown"
        
        messages_data = [{
            "id": msg.id,
            "sender_id": msg.sender_id,
            "sender_type": msg.sender_type,
            "sender_name": doctor_name if msg.sender_type == "doctor" else patient_name,
            "subject": msg.subject,
            "message": msg.message,
            "parent_message_id": msg.parent_message_id,
            "is_read": msg.is_read,
            "read_at": msg.read_at,
            "created_at": msg.created_at
        } for msg in messages]
        
        return {
            "has_doctor": True,
            "doctor_id": doctor_id,
            "doctor_name": doctor_name,
            "patient_name": patient_name,
            "messages": messages_data,
            "total": len(messages_data)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_patient_conversation_with_doctor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

