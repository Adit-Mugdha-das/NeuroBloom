from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select, col
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from app.models.doctor import Doctor
from app.models.user import User
from app.models.patient_assignment import PatientAssignment
from app.models.training_session import TrainingSession
from app.models.training_plan import TrainingPlan
from app.models.baseline_assessment import BaselineAssessment
from app.models.doctor_intervention import DoctorIntervention
from app.models.assignment_request import AssignmentRequest, RequestStatus
from app.schemas.doctor import PatientAssignmentCreate, DoctorInterventionCreate
from app.core.config import engine
import statistics
import json

router = APIRouter(prefix="/doctor", tags=["doctor"])

def get_session():
    with Session(engine) as session:
        yield session

# ========== PATIENT MANAGEMENT ==========
@router.get("/{doctor_id}/patients")
def get_doctor_patients(doctor_id: int, session: Session = Depends(get_session)):
    """Get list of all patients assigned to this doctor"""
    try:
        # Verify doctor exists
        doctor = session.get(Doctor, doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        # Get all active patient assignments
        assignments = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.doctor_id == doctor_id)
            .where(PatientAssignment.is_active == True)
        ).all()
        
        patients_data = []
        for assignment in assignments:
            patient = session.get(User, assignment.patient_id)
            if not patient:
                continue
            
            # Get latest training session
            latest_session = session.exec(
                select(TrainingSession)
                .where(TrainingSession.user_id == patient.id)
                .order_by(col(TrainingSession.created_at).desc())
            ).first()
            
            # Get baseline assessment
            baseline = session.exec(
                select(BaselineAssessment)
                .where(BaselineAssessment.user_id == patient.id)
            ).first()
            
            patients_data.append({
                "patient_id": patient.id,
                "email": patient.email,
                "full_name": patient.full_name if patient.full_name else patient.email,
                "diagnosis": assignment.diagnosis,
                "assigned_at": assignment.assigned_at,
                "last_activity": latest_session.created_at if latest_session else None,
                "baseline_completed": baseline is not None,
                "treatment_goal": assignment.treatment_goal
            })
        
        return {"patients": patients_data, "total": len(patients_data)}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_doctor_patients: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{doctor_id}/assign-patient")
def assign_patient(
    doctor_id: int,
    assignment_data: PatientAssignmentCreate,
    session: Session = Depends(get_session)
):
    """Assign a patient to this doctor"""
    try:
        # Verify doctor exists
        doctor = session.get(Doctor, doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        # Find patient by email
        patient = session.exec(select(User).where(User.email == assignment_data.patient_email)).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Check if patient has given consent (optional, but good practice)
        if not patient.consent_to_share:
            raise HTTPException(
                status_code=403,
                detail="Patient has not consented to data sharing with healthcare providers"
            )
        
        # Check if already assigned
        existing = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.doctor_id == doctor_id)
            .where(PatientAssignment.patient_id == patient.id)
            .where(PatientAssignment.is_active == True)
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Patient already assigned to this doctor")
        
        # Create assignment
        if patient.id is None:
            raise HTTPException(status_code=500, detail="Invalid patient ID")
        
        assignment = PatientAssignment(
            doctor_id=doctor_id,
            patient_id=patient.id,
            diagnosis=assignment_data.diagnosis,
            notes=assignment_data.notes,
            treatment_goal=assignment_data.treatment_goal
        )
        session.add(assignment)
        session.commit()
        session.refresh(assignment)
        
        return {
            "message": "Patient assigned successfully",
            "assignment_id": assignment.id,
            "patient_email": patient.email
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in assign_patient: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== PATIENT ANALYTICS ==========
@router.get("/{doctor_id}/patient/{patient_id}/overview")
def get_patient_overview(
    doctor_id: int,
    patient_id: int,
    session: Session = Depends(get_session)
):
    """Get comprehensive overview of a patient's progress"""
    try:
        # Verify doctor has access to this patient
        assignment = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.doctor_id == doctor_id)
            .where(PatientAssignment.patient_id == patient_id)
            .where(PatientAssignment.is_active == True)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=403, detail="No access to this patient")
        
        # Get patient info
        patient = session.get(User, patient_id)
        if not patient or patient.id is None:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Get baseline assessment
        baseline = session.exec(
            select(BaselineAssessment)
            .where(BaselineAssessment.user_id == patient_id)
        ).first()
        
        # Get training plan
        training_plan = session.exec(
            select(TrainingPlan)
            .where(TrainingPlan.user_id == patient_id)
        ).first()
        
        # Get all training sessions
        all_sessions = session.exec(
            select(TrainingSession)
            .where(TrainingSession.user_id == patient_id)
            .order_by(col(TrainingSession.created_at).desc())
        ).all()
        
        # Calculate statistics
        total_sessions = len(all_sessions)
        
        # Recent performance (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_sessions = [s for s in all_sessions if s.created_at >= seven_days_ago]
        
        avg_recent_score = statistics.mean([s.score for s in recent_sessions]) if recent_sessions else 0
        avg_recent_accuracy = statistics.mean([s.accuracy for s in recent_sessions]) if recent_sessions else 0
        
        # Domain-specific performance
        domain_stats = {}
        for domain in ["working_memory", "attention", "flexibility", "planning", "processing_speed", "visual_scanning"]:
            domain_sessions = [s for s in all_sessions if s.domain == domain]
            if domain_sessions:
                domain_stats[domain] = {
                    "count": len(domain_sessions),
                    "avg_score": statistics.mean([s.score for s in domain_sessions]),
                    "avg_accuracy": statistics.mean([s.accuracy for s in domain_sessions]),
                    "baseline_score": getattr(baseline, f"{domain}_score", None) if baseline else None
                }
        
        return {
            "patient_info": {
                "id": patient.id,
                "email": patient.email,
                "full_name": patient.full_name or "N/A",
                "diagnosis": assignment.diagnosis,
                "treatment_goal": assignment.treatment_goal
            },
            "baseline": {
                "completed": baseline is not None,
                "date": baseline.assessment_date if baseline else None,
                "overall_score": baseline.overall_score if baseline else None,
                "domain_scores": {
                    "working_memory": baseline.working_memory_score if baseline else None,
                    "attention": baseline.attention_score if baseline else None,
                    "flexibility": baseline.flexibility_score if baseline else None,
                    "planning": baseline.planning_score if baseline else None,
                    "processing_speed": baseline.processing_speed_score if baseline else None,
                    "visual_scanning": baseline.visual_scanning_score if baseline else None
                } if baseline else None
            },
            "training_summary": {
                "total_sessions": total_sessions,
                "current_streak": training_plan.current_streak if training_plan else 0,
                "longest_streak": training_plan.longest_streak if training_plan else 0,
                "last_session": all_sessions[0].created_at if all_sessions else None
            },
            "recent_performance": {
                "sessions_last_7_days": len(recent_sessions),
                "avg_score": round(avg_recent_score, 1),
                "avg_accuracy": round(avg_recent_accuracy, 1)
            },
            "domain_performance": domain_stats,
            "focus_areas": {
                "primary": json.loads(training_plan.primary_focus) if training_plan and training_plan.primary_focus else [],
                "secondary": json.loads(training_plan.secondary_focus) if training_plan and training_plan.secondary_focus else [],
                "maintenance": json.loads(training_plan.maintenance) if training_plan and training_plan.maintenance else []
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_patient_overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{doctor_id}/patient/{patient_id}/sessions")
def get_patient_sessions(
    doctor_id: int,
    patient_id: int,
    limit: int = 50,
    session: Session = Depends(get_session)
):
    """Get detailed session history for a patient"""
    try:
        # Verify access
        assignment = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.doctor_id == doctor_id)
            .where(PatientAssignment.patient_id == patient_id)
            .where(PatientAssignment.is_active == True)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=403, detail="No access to this patient")
        
        # Get sessions
        sessions = session.exec(
            select(TrainingSession)
            .where(TrainingSession.user_id == patient_id)
            .order_by(col(TrainingSession.created_at).desc())
            .limit(limit)
        ).all()
        
        sessions_data = [{
            "id": s.id,
            "domain": s.domain,
            "task_type": s.task_type,
            "task_code": s.task_code,
            "difficulty": s.difficulty_level,
            "score": s.score,
            "accuracy": s.accuracy,
            "reaction_time": s.average_reaction_time,
            "completed_at": s.created_at,
            "duration_seconds": s.duration
        } for s in sessions]
        
        return {"sessions": sessions_data, "total": len(sessions_data)}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_patient_sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== CLINICAL INTERVENTIONS ==========
@router.post("/{doctor_id}/patient/{patient_id}/intervention")
def add_intervention(
    doctor_id: int,
    patient_id: int,
    intervention: DoctorInterventionCreate,
    session: Session = Depends(get_session)
):
    """Add a clinical note or intervention for a patient"""
    try:
        # Verify access
        assignment = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.doctor_id == doctor_id)
            .where(PatientAssignment.patient_id == patient_id)
            .where(PatientAssignment.is_active == True)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=403, detail="No access to this patient")
        
        intervention_db = DoctorIntervention(
            doctor_id=doctor_id,
            patient_id=patient_id,
            intervention_type=intervention.intervention_type,
            description=intervention.description,
            intervention_data=intervention.intervention_data
        )
        session.add(intervention_db)
        session.commit()
        session.refresh(intervention_db)
        
        return {
            "message": "Intervention recorded successfully",
            "intervention_id": intervention_db.id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in add_intervention: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{doctor_id}/patient/{patient_id}/interventions")
def get_patient_interventions(
    doctor_id: int,
    patient_id: int,
    session: Session = Depends(get_session)
):
    """Get all interventions for a patient"""
    try:
        # Verify access
        assignment = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.doctor_id == doctor_id)
            .where(PatientAssignment.patient_id == patient_id)
            .where(PatientAssignment.is_active == True)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=403, detail="No access to this patient")
        
        # Get interventions
        interventions = session.exec(
            select(DoctorIntervention)
            .where(DoctorIntervention.patient_id == patient_id)
            .order_by(col(DoctorIntervention.created_at).desc())
        ).all()
        
        interventions_data = [{
            "id": i.id,
            "intervention_type": i.intervention_type,
            "description": i.description,
            "created_at": i.created_at
        } for i in interventions]
        
        return {"interventions": interventions_data, "total": len(interventions_data)}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_patient_interventions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== PATIENT ENDPOINTS (for patients to view their doctor) ==========
@router.get("/patient/{patient_id}/assigned-doctor")
def get_assigned_doctor(patient_id: int, session: Session = Depends(get_session)):
    """Get the doctor assigned to this patient"""
    try:
        # Get active assignment
        assignment = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.patient_id == patient_id)
            .where(PatientAssignment.is_active == True)
        ).first()
        
        if not assignment:
            return {"assigned": False, "doctor": None}
        
        # Get doctor details
        doctor = session.get(Doctor, assignment.doctor_id)
        if not doctor:
            return {"assigned": False, "doctor": None}
        
        return {
            "assigned": True,
            "doctor": {
                "id": doctor.id,
                "full_name": doctor.full_name,
                "email": doctor.email,
                "specialization": doctor.specialization,
                "institution": doctor.institution,
                "assigned_at": assignment.assigned_at,
                "diagnosis": assignment.diagnosis,
                "treatment_goal": assignment.treatment_goal
            }
        }
    
    except Exception as e:
        print(f"ERROR in get_assigned_doctor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== DOCTOR BROWSING & REQUESTS ==========
@router.get("/available-doctors")
def get_available_doctors(session: Session = Depends(get_session)):
    """Get list of all verified, active doctors (public endpoint)"""
    try:
        doctors = session.exec(
            select(Doctor)
            .where(Doctor.is_verified == True)
            .where(Doctor.is_active == True)
        ).all()
        
        doctors_data = [{
            "id": doctor.id,
            "full_name": doctor.full_name,
            "specialization": doctor.specialization,
            "institution": doctor.institution,
            "created_at": doctor.created_at
        } for doctor in doctors]
        
        return {"doctors": doctors_data, "total": len(doctors_data)}
    
    except Exception as e:
        print(f"ERROR in get_available_doctors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/request-assignment")
def request_assignment(
    patient_id: int,
    doctor_id: int,
    reason: Optional[str] = None,
    message: Optional[str] = None,
    diagnosis: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Patient requests assignment to a doctor"""
    try:
        # Verify patient exists
        patient = session.get(User, patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Verify doctor exists and is verified
        doctor = session.get(Doctor, doctor_id)
        if not doctor or not doctor.is_verified or not doctor.is_active:
            raise HTTPException(status_code=404, detail="Doctor not available")
        
        # Check if already assigned
        existing_assignment = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.patient_id == patient_id)
            .where(PatientAssignment.doctor_id == doctor_id)
            .where(PatientAssignment.is_active == True)
        ).first()
        
        if existing_assignment:
            raise HTTPException(status_code=400, detail="Already assigned to this doctor")
        
        # Check for existing pending request
        pending_request = session.exec(
            select(AssignmentRequest)
            .where(AssignmentRequest.patient_id == patient_id)
            .where(AssignmentRequest.doctor_id == doctor_id)
            .where(AssignmentRequest.status == RequestStatus.PENDING.value)
        ).first()
        
        if pending_request:
            raise HTTPException(status_code=400, detail="Request already pending")
        
        # Create request
        request = AssignmentRequest(
            patient_id=patient_id,
            doctor_id=doctor_id,
            reason=reason,
            message=message,
            diagnosis=diagnosis,
            status=RequestStatus.PENDING.value
        )
        session.add(request)
        session.commit()
        session.refresh(request)
        
        return {
            "message": "Assignment request sent successfully",
            "request_id": request.id,
            "status": request.status
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in request_assignment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{doctor_id}/pending-requests")
def get_pending_requests(doctor_id: int, session: Session = Depends(get_session)):
    """Get all pending assignment requests for a doctor"""
    try:
        # Verify doctor exists
        doctor = session.get(Doctor, doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        # Get pending requests
        requests = session.exec(
            select(AssignmentRequest)
            .where(AssignmentRequest.doctor_id == doctor_id)
            .where(AssignmentRequest.status == RequestStatus.PENDING.value)
            .order_by(col(AssignmentRequest.created_at).desc())
        ).all()
        
        requests_data = []
        for req in requests:
            patient = session.get(User, req.patient_id)
            if patient:
                requests_data.append({
                    "id": req.id,
                    "patient_id": patient.id,
                    "patient_email": patient.email,
                    "patient_name": patient.full_name,
                    "reason": req.reason,
                    "message": req.message,
                    "diagnosis": req.diagnosis,
                    "created_at": req.created_at
                })
        
        return {"requests": requests_data, "total": len(requests_data)}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_pending_requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/request/{request_id}/approve")
def approve_request(
    request_id: int,
    doctor_id: int,
    treatment_goal: Optional[str] = None,
    notes: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Doctor approves an assignment request"""
    try:
        # Get the request
        request = session.get(AssignmentRequest, request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        if request.doctor_id != doctor_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        if request.status != RequestStatus.PENDING.value:
            raise HTTPException(status_code=400, detail="Request already processed")
        
        # Update request status
        request.status = RequestStatus.APPROVED.value
        request.doctor_notes = notes
        request.responded_at = datetime.now(timezone.utc)
        
        # Create actual assignment
        assignment = PatientAssignment(
            doctor_id=doctor_id,
            patient_id=request.patient_id,
            diagnosis=request.diagnosis or "Not specified",
            treatment_goal=treatment_goal or "Improve cognitive function",
            is_active=True
        )
        
        # Enable patient consent
        patient = session.get(User, request.patient_id)
        if patient:
            patient.consent_to_share = True
            session.add(patient)
        
        session.add(request)
        session.add(assignment)
        session.commit()
        
        return {"message": "Request approved and patient assigned"}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in approve_request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/request/{request_id}/reject")
def reject_request(
    request_id: int,
    doctor_id: int,
    notes: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Doctor rejects an assignment request"""
    try:
        # Get the request
        request = session.get(AssignmentRequest, request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        if request.doctor_id != doctor_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        if request.status != RequestStatus.PENDING.value:
            raise HTTPException(status_code=400, detail="Request already processed")
        
        # Update request status
        request.status = RequestStatus.REJECTED.value
        request.doctor_notes = notes
        request.responded_at = datetime.now(timezone.utc)
        
        session.add(request)
        session.commit()
        
        return {"message": "Request rejected"}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in reject_request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patient/{patient_id}/requests")
def get_patient_requests(patient_id: int, session: Session = Depends(get_session)):
    """Get all assignment requests made by a patient"""
    try:
        requests = session.exec(
            select(AssignmentRequest)
            .where(AssignmentRequest.patient_id == patient_id)
            .order_by(col(AssignmentRequest.created_at).desc())
        ).all()
        
        requests_data = []
        for req in requests:
            doctor = session.get(Doctor, req.doctor_id)
            if doctor:
                requests_data.append({
                    "id": req.id,
                    "doctor_id": doctor.id,
                    "doctor_name": doctor.full_name,
                    "doctor_specialization": doctor.specialization,
                    "status": req.status,
                    "reason": req.reason,
                    "message": req.message,
                    "created_at": req.created_at,
                    "responded_at": req.responded_at,
                    "doctor_notes": req.doctor_notes
                })
        
        return {"requests": requests_data, "total": len(requests_data)}
    
    except Exception as e:
        print(f"ERROR in get_patient_requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== PATIENT ASSIGNMENT MANAGEMENT ==========
@router.post("/{doctor_id}/unassign/{patient_id}")
def unassign_patient(
    doctor_id: int,
    patient_id: int,
    session: Session = Depends(get_session)
):
    """Unassign a patient from this doctor"""
    try:
        # Verify doctor exists
        doctor = session.get(Doctor, doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        # Find active assignment
        assignment = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.doctor_id == doctor_id)
            .where(PatientAssignment.patient_id == patient_id)
            .where(PatientAssignment.is_active == True)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="No active assignment found")
        
        # Deactivate assignment
        assignment.is_active = False
        assignment.unassigned_at = datetime.now(timezone.utc)
        session.add(assignment)
        session.commit()
        
        return {
            "message": "Patient unassigned successfully",
            "assignment_id": assignment.id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in unassign_patient: {e}")
        raise HTTPException(status_code=500, detail=str(e))
