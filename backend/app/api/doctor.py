from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select, col
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.doctor import Doctor
from app.models.user import User
from app.models.patient_assignment import PatientAssignment
from app.models.training_session import TrainingSession
from app.models.training_plan import TrainingPlan
from app.models.baseline_assessment import BaselineAssessment
from app.models.doctor_intervention import DoctorIntervention
from app.schemas.doctor import PatientAssignmentCreate, DoctorInterventionCreate
from app.core.config import engine
import statistics

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
                "full_name": patient.full_name or "N/A",
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
                "primary": training_plan.primary_focus if training_plan else [],
                "secondary": training_plan.secondary_focus if training_plan else [],
                "maintenance": training_plan.maintenance if training_plan else []
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
