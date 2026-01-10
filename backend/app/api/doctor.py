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
from app.models.message import Message
from app.schemas.doctor import PatientAssignmentCreate, DoctorInterventionCreate, MessageCreate, MessageRead
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

@router.get("/{doctor_id}/patient/{patient_id}/progress-monitoring")
def get_progress_monitoring(
    doctor_id: int,
    patient_id: int,
    session: Session = Depends(get_session)
):
    """Get comprehensive progress monitoring data with trends and comparisons"""
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
        
        # Get baseline assessment
        baseline = session.exec(
            select(BaselineAssessment)
            .where(BaselineAssessment.user_id == patient_id)
        ).first()
        
        # Get all training sessions
        all_sessions = session.exec(
            select(TrainingSession)
            .where(TrainingSession.user_id == patient_id)
            .order_by(col(TrainingSession.created_at))
        ).all()
        
        if not all_sessions:
            return {
                "baseline_comparison": {},
                "trends": {},
                "adherence": {"status": "no_data"},
                "domain_improvements": {},
                "concerning_areas": []
            }
        
        # Calculate time periods
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        fourteen_days_ago = now - timedelta(days=14)
        seven_days_ago = now - timedelta(days=7)
        
        # Sessions by time period
        sessions_30d = [s for s in all_sessions if s.created_at >= thirty_days_ago]
        sessions_14d = [s for s in all_sessions if s.created_at >= fourteen_days_ago]
        sessions_7d = [s for s in all_sessions if s.created_at >= seven_days_ago]
        
        # 1. BASELINE vs CURRENT COMPARISON
        baseline_comparison = {}
        if baseline:
            domains = ["working_memory", "attention", "flexibility", "planning", "processing_speed", "visual_scanning"]
            for domain in domains:
                baseline_score = getattr(baseline, f"{domain}_score", None)
                if baseline_score:
                    domain_sessions = [s for s in sessions_30d if s.domain == domain]
                    if domain_sessions:
                        current_avg = statistics.mean([s.score for s in domain_sessions])
                        improvement = current_avg - baseline_score
                        improvement_pct = (improvement / baseline_score) * 100 if baseline_score > 0 else 0
                        
                        baseline_comparison[domain] = {
                            "baseline_score": round(baseline_score, 1),
                            "current_score": round(current_avg, 1),
                            "improvement": round(improvement, 1),
                            "improvement_percentage": round(improvement_pct, 1),
                            "session_count": len(domain_sessions),
                            "status": "improving" if improvement > 0 else "declining" if improvement < -2 else "stable"
                        }
        
        # 2. TREND ANALYSIS (comparing recent periods)
        trends = {}
        domains = ["working_memory", "attention", "flexibility", "planning", "processing_speed", "visual_scanning"]
        for domain in domains:
            domain_sessions_14d = [s for s in sessions_14d if s.domain == domain]
            domain_sessions_7d = [s for s in sessions_7d if s.domain == domain]
            
            if domain_sessions_14d and domain_sessions_7d:
                # Compare last 7 days vs previous 7 days
                prev_7d_sessions = [s for s in domain_sessions_14d if s not in domain_sessions_7d]
                
                if prev_7d_sessions:
                    recent_avg = statistics.mean([s.score for s in domain_sessions_7d])
                    previous_avg = statistics.mean([s.score for s in prev_7d_sessions])
                    trend_direction = recent_avg - previous_avg
                    
                    trends[domain] = {
                        "recent_avg": round(recent_avg, 1),
                        "previous_avg": round(previous_avg, 1),
                        "change": round(trend_direction, 1),
                        "direction": "upward" if trend_direction > 1 else "downward" if trend_direction < -1 else "stable",
                        "is_concerning": trend_direction < -3  # Decline of more than 3 points
                    }
        
        # 3. ADHERENCE TRACKING
        # Expected sessions per week based on assignment date
        weeks_since_assignment = (now - assignment.assigned_at).days / 7
        expected_sessions = max(1, int(weeks_since_assignment * 3))  # Expect ~3 sessions per week
        
        adherence_rate = (len(all_sessions) / expected_sessions) * 100 if expected_sessions > 0 else 0
        
        # Calculate session frequency
        if len(all_sessions) >= 2:
            session_dates = sorted([s.created_at for s in all_sessions])
            intervals = [(session_dates[i+1] - session_dates[i]).days for i in range(len(session_dates)-1)]
            avg_days_between = statistics.mean(intervals) if intervals else 0
        else:
            avg_days_between = 0
        
        adherence = {
            "total_sessions": len(all_sessions),
            "expected_sessions": expected_sessions,
            "adherence_rate": round(adherence_rate, 1),
            "sessions_last_7_days": len(sessions_7d),
            "sessions_last_14_days": len(sessions_14d),
            "sessions_last_30_days": len(sessions_30d),
            "avg_days_between_sessions": round(avg_days_between, 1),
            "status": "excellent" if adherence_rate >= 80 else "good" if adherence_rate >= 60 else "needs_improvement" if adherence_rate >= 40 else "concerning"
        }
        
        # 4. DOMAIN-SPECIFIC IMPROVEMENTS
        domain_improvements = {}
        for domain in domains:
            domain_sessions = [s for s in all_sessions if s.domain == domain]
            if len(domain_sessions) >= 5:
                # Split into first half and second half
                mid_point = len(domain_sessions) // 2
                first_half = domain_sessions[:mid_point]
                second_half = domain_sessions[mid_point:]
                
                first_avg = statistics.mean([s.score for s in first_half])
                second_avg = statistics.mean([s.score for s in second_half])
                improvement = second_avg - first_avg
                
                # Get recent performance trend (last 10 sessions)
                recent_domain = domain_sessions[-10:] if len(domain_sessions) >= 10 else domain_sessions
                recent_scores = [s.score for s in recent_domain]
                
                domain_improvements[domain] = {
                    "early_avg": round(first_avg, 1),
                    "recent_avg": round(second_avg, 1),
                    "overall_improvement": round(improvement, 1),
                    "total_sessions": len(domain_sessions),
                    "recent_scores": [round(s, 1) for s in recent_scores[-5:]],  # Last 5 scores
                    "trending": "up" if improvement > 1 else "down" if improvement < -1 else "stable"
                }
        
        # 5. CONCERNING AREAS (automatic identification)
        concerning_areas = []
        
        # Check for declining trends
        for domain, trend_data in trends.items():
            if trend_data.get("is_concerning", False):
                concerning_areas.append({
                    "domain": domain,
                    "issue": "declining_performance",
                    "severity": "high" if trend_data["change"] < -5 else "medium",
                    "details": f"Score decreased by {abs(trend_data['change'])} points in last 7 days"
                })
        
        # Check for poor adherence
        if adherence["status"] in ["needs_improvement", "concerning"]:
            concerning_areas.append({
                "domain": "adherence",
                "issue": "low_engagement",
                "severity": "high" if adherence["status"] == "concerning" else "medium",
                "details": f"Only {adherence['sessions_last_30_days']} sessions in last 30 days"
            })
        
        # Check for domains with no recent activity
        for domain in domains:
            domain_recent = [s for s in sessions_30d if s.domain == domain]
            if len(domain_recent) == 0:
                concerning_areas.append({
                    "domain": domain,
                    "issue": "no_recent_activity",
                    "severity": "low",
                    "details": "No sessions in this domain in the last 30 days"
                })
        
        return {
            "baseline_comparison": baseline_comparison,
            "trends": trends,
            "adherence": adherence,
            "domain_improvements": domain_improvements,
            "concerning_areas": concerning_areas
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_progress_monitoring: {e}")
        import traceback
        traceback.print_exc()
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
                "full_name": doctor.full_name if doctor.full_name else "Unknown",
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
            "full_name": doctor.full_name if doctor.full_name else "Unknown Doctor",
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
                    "patient_name": patient.full_name if patient.full_name else patient.email,
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
                    "doctor_name": doctor.full_name if doctor.full_name else "Unknown Doctor",
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

# ========== INTERVENTIONS & RECOMMENDATIONS ==========
@router.post("/{doctor_id}/patient/{patient_id}/intervention")
def create_intervention(
    doctor_id: int,
    patient_id: int,
    intervention_type: str,
    description: str,
    intervention_data: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Create a new intervention/recommendation for a patient"""
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
        
        # Create intervention
        intervention = DoctorIntervention(
            doctor_id=doctor_id,
            patient_id=patient_id,
            intervention_type=intervention_type,
            description=description,
            intervention_data=intervention_data
        )
        
        session.add(intervention)
        session.commit()
        session.refresh(intervention)
        
        return {
            "message": "Intervention created successfully",
            "intervention": {
                "id": intervention.id,
                "type": intervention.intervention_type,
                "description": intervention.description,
                "created_at": intervention.created_at
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in create_intervention: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{doctor_id}/patient/{patient_id}/interventions")
def get_patient_interventions(
    doctor_id: int,
    patient_id: int,
    limit: int = 20,
    session: Session = Depends(get_session)
):
    """Get all interventions for a patient"""
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
        
        # Get interventions
        interventions = session.exec(
            select(DoctorIntervention)
            .where(DoctorIntervention.patient_id == patient_id)
            .order_by(col(DoctorIntervention.created_at).desc())
            .limit(limit)
        ).all()
        
        return {
            "interventions": [
                {
                    "id": i.id,
                    "type": i.intervention_type,
                    "description": i.description,
                    "data": json.loads(i.intervention_data) if i.intervention_data else None,
                    "created_at": i.created_at
                }
                for i in interventions
            ],
            "total": len(interventions)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_patient_interventions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{doctor_id}/patient/{patient_id}/training-plan")
def update_training_plan(
    doctor_id: int,
    patient_id: int,
    difficulty_adjustments: Optional[str] = None,
    performance_goals: Optional[str] = None,
    notes: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Update patient's training plan (difficulty, goals, etc.)"""
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
        
        # Get training plan
        training_plan = session.exec(
            select(TrainingPlan)
            .where(TrainingPlan.user_id == patient_id)
            .where(TrainingPlan.is_active == True)
        ).first()
        
        if not training_plan:
            raise HTTPException(status_code=404, detail="No active training plan found")
        
        # Update difficulty if provided
        if difficulty_adjustments:
            current_diff = json.loads(training_plan.current_difficulty) if training_plan.current_difficulty else {}
            new_adjustments = json.loads(difficulty_adjustments)
            current_diff.update(new_adjustments)
            training_plan.current_difficulty = json.dumps(current_diff)
        
        training_plan.last_updated = datetime.now(timezone.utc)
        session.add(training_plan)
        
        # Create intervention record
        intervention_data = {
            "difficulty_adjustments": json.loads(difficulty_adjustments) if difficulty_adjustments else None,
            "performance_goals": json.loads(performance_goals) if performance_goals else None
        }
        
        intervention = DoctorIntervention(
            doctor_id=doctor_id,
            patient_id=patient_id,
            intervention_type="training_plan_adjustment",
            description=notes or "Training plan updated by doctor",
            intervention_data=json.dumps(intervention_data)
        )
        session.add(intervention)
        session.commit()
        
        return {
            "message": "Training plan updated successfully",
            "intervention_id": intervention.id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in update_training_plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== SECURE MESSAGING ==========
@router.post("/{doctor_id}/messages/send")
def send_message(
    doctor_id: int,
    message_data: MessageCreate,
    session: Session = Depends(get_session)
):
    """Doctor sends a message to a patient"""
    try:
        # Verify doctor exists
        doctor = session.get(Doctor, doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        # Verify the doctor has access to this patient
        if message_data.recipient_type == "patient":
            assignment = session.exec(
                select(PatientAssignment)
                .where(PatientAssignment.doctor_id == doctor_id)
                .where(PatientAssignment.patient_id == message_data.recipient_id)
                .where(PatientAssignment.is_active == True)
            ).first()
            
            if not assignment:
                raise HTTPException(status_code=403, detail="No access to this patient")
        
        # Create message
        message = Message(
            sender_id=doctor_id,
            sender_type="doctor",
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
        print(f"ERROR in send_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{doctor_id}/messages")
def get_doctor_messages(
    doctor_id: int,
    patient_id: Optional[int] = None,
    unread_only: bool = False,
    limit: int = 50,
    session: Session = Depends(get_session)
):
    """Get messages for a doctor (sent and received)"""
    try:
        # Verify doctor exists
        doctor = session.get(Doctor, doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        # Build query for messages where doctor is sender or recipient
        query = select(Message).where(
            (Message.sender_id == doctor_id) | (Message.recipient_id == doctor_id)
        )
        
        # Filter by specific patient if provided
        if patient_id:
            query = query.where(
                ((Message.sender_id == patient_id) & (Message.recipient_id == doctor_id)) |
                ((Message.sender_id == doctor_id) & (Message.recipient_id == patient_id))
            )
        
        # Filter unread messages
        if unread_only:
            query = query.where(
                (Message.recipient_id == doctor_id) & (Message.is_read == False)
            )
        
        # Order by most recent first
        query = query.order_by(col(Message.created_at).desc()).limit(limit)
        
        messages = session.exec(query).all()
        
        # Get sender/recipient details for each message
        messages_data = []
        for msg in messages:
            # Get sender name
            if msg.sender_type == "doctor":
                sender = session.get(Doctor, msg.sender_id)
                sender_name = sender.full_name if sender and sender.full_name else "Unknown"
            else:
                sender = session.get(User, msg.sender_id)
                if sender:
                    sender_name = sender.full_name or sender.email
                else:
                    sender_name = "Unknown"
            
            # Get recipient name
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
        
        # Count unread messages
        unread_count = session.exec(
            select(Message)
            .where(Message.recipient_id == doctor_id)
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
        print(f"ERROR in get_doctor_messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{doctor_id}/messages/{message_id}/mark-read")
def mark_message_read(
    doctor_id: int,
    message_id: int,
    session: Session = Depends(get_session)
):
    """Mark a message as read"""
    try:
        # Get message
        message = session.get(Message, message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Verify doctor is the recipient
        if message.recipient_id != doctor_id or message.recipient_type != "doctor":
            raise HTTPException(status_code=403, detail="Not authorized to mark this message as read")
        
        # Mark as read
        message.is_read = True
        message.read_at = datetime.utcnow()
        session.add(message)
        session.commit()
        
        return {"message": "Message marked as read"}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in mark_message_read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{doctor_id}/messages/conversation/{patient_id}")
def get_conversation(
    doctor_id: int,
    patient_id: int,
    session: Session = Depends(get_session)
):
    """Get full conversation thread between doctor and patient"""
    try:
        # Verify doctor has access
        assignment = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.doctor_id == doctor_id)
            .where(PatientAssignment.patient_id == patient_id)
            .where(PatientAssignment.is_active == True)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=403, detail="No access to this patient")
        
        # Get all messages between doctor and patient
        messages = session.exec(
            select(Message)
            .where(
                ((Message.sender_id == doctor_id) & (Message.sender_type == "doctor") & (Message.recipient_id == patient_id)) |
                ((Message.sender_id == patient_id) & (Message.sender_type == "patient") & (Message.recipient_id == doctor_id))
            )
            .order_by(col(Message.created_at))
        ).all()
        
        # Get participant names
        doctor = session.get(Doctor, doctor_id)
        patient = session.get(User, patient_id)
        
        # Get names safely
        doctor_name = (doctor.full_name if doctor and doctor.full_name else "Unknown")
        patient_name = ((patient.full_name or patient.email) if patient else "Unknown")
        
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
            "doctor_name": doctor_name,
            "patient_name": patient_name,
            "messages": messages_data,
            "total": len(messages_data)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

