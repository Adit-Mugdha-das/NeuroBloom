from fastapi import APIRouter, HTTPException, Depends, Body
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
from app.models.progress_report import ProgressReport
from app.models.notification import Notification
from app.schemas.doctor import PatientAssignmentCreate, DoctorInterventionCreate, MessageCreate, MessageRead
from app.core.config import engine
import statistics
import json
import traceback

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


@router.get("/{doctor_id}/patient/{patient_id}/trends")
def get_doctor_patient_trends(
    doctor_id: int,
    patient_id: int,
    days: int = 30,
    session: Session = Depends(get_session)
):
    """Get patient performance trends for the doctor-facing report workspace"""
    try:
        assignment = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.doctor_id == doctor_id)
            .where(PatientAssignment.patient_id == patient_id)
            .where(PatientAssignment.is_active == True)
        ).first()

        if not assignment:
            raise HTTPException(status_code=403, detail="No access to this patient")

        plan = session.exec(
            select(TrainingPlan)
            .where(TrainingPlan.user_id == patient_id)
            .where(TrainingPlan.is_active == True)
        ).first()

        if not plan:
            raise HTTPException(status_code=404, detail="No active training plan")

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        sessions_data = session.exec(
            select(TrainingSession)
            .where(TrainingSession.training_plan_id == plan.id)
            .where(TrainingSession.created_at >= cutoff_date)
            .order_by(col(TrainingSession.created_at))
        ).all()

        trends_by_domain = {}
        sessions_by_date = {}

        for session_record in sessions_data:
            domain = session_record.domain
            date_key = session_record.created_at.date().isoformat()

            if domain not in trends_by_domain:
                trends_by_domain[domain] = {
                    "domain": domain,
                    "data_points": []
                }

            trends_by_domain[domain]["data_points"].append({
                "date": session_record.created_at.isoformat(),
                "score": session_record.score,
                "accuracy": session_record.accuracy,
                "difficulty": session_record.difficulty_level,
                "reaction_time": session_record.average_reaction_time,
                "errors": session_record.errors
            })

            if date_key not in sessions_by_date:
                sessions_by_date[date_key] = {
                    "scores": [],
                    "accuracies": [],
                    "difficulties": []
                }

            sessions_by_date[date_key]["scores"].append(session_record.score)
            sessions_by_date[date_key]["accuracies"].append(session_record.accuracy)
            sessions_by_date[date_key]["difficulties"].append(session_record.difficulty_level)

        overall_trend = []
        for date_key, metrics in sorted(sessions_by_date.items()):
            overall_trend.append({
                "date": date_key,
                "avg_score": sum(metrics["scores"]) / len(metrics["scores"]),
                "avg_accuracy": sum(metrics["accuracies"]) / len(metrics["accuracies"]),
                "avg_difficulty": sum(metrics["difficulties"]) / len(metrics["difficulties"]),
                "sessions_count": len(metrics["scores"])
            })

        return {
            "user_id": patient_id,
            "period_days": days,
            "total_sessions": len(sessions_data),
            "trends_by_domain": trends_by_domain,
            "overall_trend": overall_trend,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_doctor_patient_trends: {e}")
        traceback.print_exc()
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
        print(f"DEBUG: Checking assignment for patient_id: {patient_id}")
        
        # Get patient info for debugging
        patient = session.get(User, patient_id)
        if not patient:
            print(f"DEBUG: Patient with ID {patient_id} not found!")
            return {"assigned": False, "doctor": None, "error": "Patient not found"}
        
        print(f"DEBUG: Patient found: {patient.email}")
        
        # Get active assignment
        assignment = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.patient_id == patient_id)
            .where(PatientAssignment.is_active == True)
        ).first()
        
        if not assignment:
            print(f"DEBUG: No active assignment found for patient {patient_id}")
            return {"assigned": False, "doctor": None}
        
        print(f"DEBUG: Assignment found! Doctor ID: {assignment.doctor_id}")
        
        # Get doctor details
        doctor = session.get(Doctor, assignment.doctor_id)
        if not doctor:
            print(f"DEBUG: Doctor {assignment.doctor_id} not found!")
            return {"assigned": False, "doctor": None}
        
        print(f"DEBUG: Doctor found: {doctor.full_name if doctor.full_name else doctor.email}")
        
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
        import traceback
        traceback.print_exc()
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


@router.patch("/{doctor_id}/patient/{patient_id}/focus-areas")
def update_focus_areas(
    doctor_id: int,
    patient_id: int,
    primary_focus: Optional[str] = None,
    secondary_focus: Optional[str] = None,
    maintenance: Optional[str] = None,
    notes: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Update patient's training plan focus areas (cognitive domains priority)"""
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
        
        # Update focus areas if provided
        if primary_focus is not None:
            training_plan.primary_focus = primary_focus
        if secondary_focus is not None:
            training_plan.secondary_focus = secondary_focus
        if maintenance is not None:
            training_plan.maintenance = maintenance
        
        training_plan.last_updated = datetime.now(timezone.utc)
        session.add(training_plan)
        
        # Create intervention record
        intervention_data = {
            "primary_focus": json.loads(primary_focus) if primary_focus else None,
            "secondary_focus": json.loads(secondary_focus) if secondary_focus else None,
            "maintenance": json.loads(maintenance) if maintenance else None
        }
        
        intervention = DoctorIntervention(
            doctor_id=doctor_id,
            patient_id=patient_id,
            intervention_type="focus_area_adjustment",
            description=notes or "Focus areas updated by doctor",
            intervention_data=json.dumps(intervention_data)
        )
        session.add(intervention)
        session.commit()
        
        return {
            "message": "Focus areas updated successfully",
            "intervention_id": intervention.id,
            "focus_areas": {
                "primary": json.loads(training_plan.primary_focus),
                "secondary": json.loads(training_plan.secondary_focus),
                "maintenance": json.loads(training_plan.maintenance)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in update_focus_areas: {e}")
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


@router.get("/{doctor_id}/notifications")
def get_doctor_notifications(doctor_id: int, session: Session = Depends(get_session)):
    """Get active admin notifications for a doctor."""
    doctor = session.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    notifications = list(session.exec(
        select(Notification)
        .where(Notification.is_active == True)
        .where((Notification.audience == "all") | (Notification.audience == "doctor"))
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


# ============= PATIENT MESSAGING ENDPOINTS =============

@router.post("/patient/{patient_id}/messages/send")
def send_patient_message(
    patient_id: int,
    message_data: MessageCreate,
    session: Session = Depends(get_session)
):
    """Send a message from patient to their assigned doctor"""
    try:
        # Get patient's doctor assignment
        assignment = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.patient_id == patient_id)
            .where(PatientAssignment.is_active == True)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="No assigned doctor found")
        
        doctor_id = assignment.doctor_id
        
        # Create message
        message = Message(
            sender_id=patient_id,
            sender_type="patient",
            recipient_id=doctor_id,
            recipient_type="doctor",
            subject=message_data.subject,
            message=message_data.message,
            parent_message_id=message_data.parent_message_id
        )
        
        session.add(message)
        session.commit()
        session.refresh(message)
        
        return {
            "id": message.id,
            "message": "Message sent successfully",
            "created_at": message.created_at
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in send_patient_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patient/{patient_id}/messages")
def get_patient_messages(
    patient_id: int,
    limit: int = 50,
    session: Session = Depends(get_session)
):
    """Get all messages for a patient"""
    try:
        # Get patient's messages
        query = select(Message).where(
            (Message.sender_id == patient_id) | (Message.recipient_id == patient_id)
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
        print(f"DEBUG: Getting conversation for patient_id={patient_id}")
        
        # Get patient's doctor assignment
        assignment = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.patient_id == patient_id)
            .where(PatientAssignment.is_active == True)
        ).first()
        
        print(f"DEBUG: Assignment found: {assignment is not None}")
        
        if not assignment:
            print("DEBUG: No assignment found, returning has_doctor=False")
            return {
                "has_doctor": False,
                "messages": [],
                "total": 0
            }
        
        doctor_id = assignment.doctor_id
        print(f"DEBUG: Doctor ID from assignment: {doctor_id}")
        
        # Get all messages
        messages = session.exec(
            select(Message)
            .where(
                ((Message.sender_id == patient_id) & (Message.sender_type == "patient") & (Message.recipient_id == doctor_id)) |
                ((Message.sender_id == doctor_id) & (Message.sender_type == "doctor") & (Message.recipient_id == patient_id))
            )
            .order_by(col(Message.created_at))
        ).all()
        
        print(f"DEBUG: Found {len(messages)} messages")
        
        doctor = session.get(Doctor, doctor_id)
        patient = session.get(User, patient_id)
        
        # Get names safely
        doctor_name = doctor.full_name if doctor and doctor.full_name else "Unknown"
        patient_name = (patient.full_name or patient.email) if patient else "Unknown"
        
        print(f"DEBUG: Doctor name: {doctor_name}, Patient name: {patient_name}")
        
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
        
        result = {
            "has_doctor": True,
            "doctor_id": doctor_id,
            "doctor_name": doctor_name,
            "patient_name": patient_name,
            "messages": messages_data,
            "total": len(messages_data)
        }
        
        print(f"DEBUG: Returning result with has_doctor=True, {len(messages_data)} messages")
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_patient_conversation_with_doctor: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ========== PROGRESS REPORTS ==========
@router.post("/{doctor_id}/patients/{patient_id}/generate-report")
def generate_progress_report(
    doctor_id: int,
    patient_id: int,
    period_type: str = "weekly",  # "weekly" or "monthly"
    session: Session = Depends(get_session)
):
    """Generate an auto-generated progress report for a patient"""
    try:
        def safe_number(value: Optional[float], default: float = 0.0) -> float:
            return value if value is not None else default

        # Verify doctor exists
        doctor = session.get(Doctor, doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        # Verify patient is assigned to this doctor
        assignment = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.doctor_id == doctor_id)
            .where(PatientAssignment.patient_id == patient_id)
            .where(PatientAssignment.is_active == True)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=403, detail="Patient not assigned to this doctor")
        
        # Get baseline assessment
        baseline = session.exec(
            select(BaselineAssessment)
            .where(BaselineAssessment.user_id == patient_id)
        ).first()
        
        # Calculate period dates
        now = datetime.now(timezone.utc)
        if period_type == "weekly":
            period_end = now
            period_start = now - timedelta(days=7)
        elif period_type == "monthly":
            period_end = now
            period_start = now - timedelta(days=30)
        else:
            raise HTTPException(status_code=400, detail="Invalid period_type. Must be 'weekly' or 'monthly'")
        
        # Get all training sessions in this period
        sessions_data = session.exec(
            select(TrainingSession)
            .where(TrainingSession.user_id == patient_id)
            .where(TrainingSession.created_at >= period_start)
            .where(TrainingSession.created_at <= period_end)
            .where(TrainingSession.completed == True)
        ).all()
        
        # Aggregate data by domain
        domain_stats = {}
        task_performance = {}
        daily_activity = {}
        
        for session_record in sessions_data:
            # Domain statistics
            domain = session_record.domain
            if domain not in domain_stats:
                domain_stats[domain] = {
                    "sessions_count": 0,
                    "total_score": 0.0,
                    "total_accuracy": 0.0,
                    "total_reaction_time": 0.0,
                    "scores": [],
                    "difficulties": []
                }
            
            domain_stats[domain]["sessions_count"] += 1
            score = safe_number(session_record.score, 0.0)
            accuracy = safe_number(session_record.accuracy, 0.0)
            reaction_time = safe_number(session_record.average_reaction_time, 0.0)
            difficulty_level = safe_number(session_record.difficulty_level, 1.0)

            domain_stats[domain]["total_score"] += score
            domain_stats[domain]["total_accuracy"] += accuracy
            domain_stats[domain]["total_reaction_time"] += reaction_time
            domain_stats[domain]["scores"].append(score)
            domain_stats[domain]["difficulties"].append(difficulty_level)
            
            # Task performance
            task_key = session_record.task_code or session_record.task_type
            if task_key not in task_performance:
                task_performance[task_key] = {
                    "task_type": session_record.task_type,
                    "domain": domain,
                    "sessions": 0,
                    "avg_score": 0,
                    "scores": []
                }
            
            task_performance[task_key]["sessions"] += 1
            task_performance[task_key]["scores"].append(score)
            
            # Daily activity
            day_key = session_record.created_at.strftime("%Y-%m-%d")
            if day_key not in daily_activity:
                daily_activity[day_key] = {
                    "sessions": 0,
                    "total_duration": 0,
                    "avg_score": 0,
                    "scores": []
                }
            
            daily_activity[day_key]["sessions"] += 1
            daily_activity[day_key]["total_duration"] += safe_number(session_record.duration, 0.0)
            daily_activity[day_key]["scores"].append(score)
        
        # Calculate averages and trends
        for domain in domain_stats:
            stats = domain_stats[domain]
            count = stats["sessions_count"]
            if count > 0:
                stats["avg_score"] = round(stats["total_score"] / count, 2)
                stats["avg_accuracy"] = round(stats["total_accuracy"] / count, 2)
                stats["avg_reaction_time"] = round(stats["total_reaction_time"] / count, 2)
                stats["avg_difficulty"] = round(sum(stats["difficulties"]) / count, 2)
                
                # Add baseline score for comparison
                stats["baseline_score"] = getattr(baseline, f"{domain}_score", None) if baseline else None
                
                # Calculate improvement from baseline
                if stats["baseline_score"] is not None:
                    improvement = stats["avg_score"] - stats["baseline_score"]
                    stats["improvement"] = round(improvement, 2)
                    stats["improvement_percent"] = round((improvement / stats["baseline_score"]) * 100, 1) if stats["baseline_score"] > 0 else 0
                else:
                    stats["improvement"] = None
                    stats["improvement_percent"] = None
                
                # Calculate trend (improving/declining)
                if len(stats["scores"]) >= 2:
                    first_half = stats["scores"][:len(stats["scores"])//2]
                    second_half = stats["scores"][len(stats["scores"])//2:]
                    first_avg = sum(first_half) / len(first_half)
                    second_avg = sum(second_half) / len(second_half)
                    stats["trend"] = "improving" if second_avg > first_avg else "declining"
                    stats["trend_change"] = round(second_avg - first_avg, 2)
                else:
                    stats["trend"] = "stable"
                    stats["trend_change"] = 0
            
            # Remove raw arrays to reduce size
            del stats["scores"]
            del stats["difficulties"]
            del stats["total_score"]
            del stats["total_accuracy"]
            del stats["total_reaction_time"]
        
        # Calculate task averages
        for task_key in task_performance:
            task = task_performance[task_key]
            task["avg_score"] = round(sum(task["scores"]) / len(task["scores"]), 2)
            del task["scores"]
        
        # Calculate daily averages
        for day in daily_activity:
            day_data = daily_activity[day]
            if day_data["scores"]:
                day_data["avg_score"] = round(sum(day_data["scores"]) / len(day_data["scores"]), 2)
            del day_data["scores"]
        
        # Overall summary
        total_sessions = len(sessions_data)
        total_duration = sum(safe_number(s.duration, 0.0) for s in sessions_data)
        avg_overall_score = round(sum(safe_number(s.score, 0.0) for s in sessions_data) / total_sessions, 2) if total_sessions > 0 else 0
        
        # Add baseline information to report
        baseline_info = None
        if baseline:
            baseline_info = {
                "completed": True,
                "date": baseline.assessment_date.isoformat() if baseline.assessment_date else None,
                "overall_score": baseline.overall_score,
                "domain_scores": {
                    "working_memory": baseline.working_memory_score,
                    "attention": baseline.attention_score,
                    "flexibility": baseline.flexibility_score,
                    "planning": baseline.planning_score,
                    "processing_speed": baseline.processing_speed_score,
                    "visual_scanning": baseline.visual_scanning_score
                }
            }
        
        report_data = {
            "summary": {
                "total_sessions": total_sessions,
                "total_duration_minutes": round(total_duration / 60, 2),
                "avg_overall_score": avg_overall_score,
                "active_days": len(daily_activity),
                "period_days": (period_end - period_start).days
            },
            "baseline": baseline_info,
            "domain_stats": domain_stats,
            "task_performance": task_performance,
            "daily_activity": daily_activity,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat()
        }
        
        # Create or update progress report
        existing_report = session.exec(
            select(ProgressReport)
            .where(ProgressReport.patient_id == patient_id)
            .where(ProgressReport.doctor_id == doctor_id)
            .where(ProgressReport.period_type == period_type)
            .where(ProgressReport.period_start == period_start)
            .where(ProgressReport.period_end == period_end)
        ).first()
        
        if existing_report:
            existing_report.report_data = json.dumps(report_data)
            existing_report.updated_at = now
            session.add(existing_report)
            session.commit()
            session.refresh(existing_report)
            report = existing_report
        else:
            new_report = ProgressReport(
                patient_id=patient_id,
                doctor_id=doctor_id,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
                report_data=json.dumps(report_data),
                generated_at=now,
                updated_at=now
            )
            session.add(new_report)
            session.commit()
            session.refresh(new_report)
            report = new_report
        
        return {
            "id": report.id,
            "patient_id": report.patient_id,
            "doctor_id": report.doctor_id,
            "period_type": report.period_type,
            "period_start": report.period_start.isoformat(),
            "period_end": report.period_end.isoformat(),
            "report_data": report_data,
            "doctor_commentary": report.doctor_commentary,
            "generated_at": report.generated_at.isoformat(),
            "updated_at": report.updated_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in generate_progress_report: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doctor_id}/patients/{patient_id}/reports")
def get_patient_reports(
    doctor_id: int,
    patient_id: int,
    period_type: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Get all progress reports for a patient"""
    try:
        # Verify doctor exists
        doctor = session.get(Doctor, doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        # Verify patient is assigned to this doctor
        assignment = session.exec(
            select(PatientAssignment)
            .where(PatientAssignment.doctor_id == doctor_id)
            .where(PatientAssignment.patient_id == patient_id)
            .where(PatientAssignment.is_active == True)
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=403, detail="Patient not assigned to this doctor")
        
        # Build query
        query = select(ProgressReport).where(
            ProgressReport.patient_id == patient_id,
            ProgressReport.doctor_id == doctor_id
        )
        
        if period_type:
            query = query.where(ProgressReport.period_type == period_type)
        
        reports = session.exec(query.order_by(col(ProgressReport.period_start).desc())).all()
        
        result = []
        for report in reports:
            result.append({
                "id": report.id,
                "patient_id": report.patient_id,
                "doctor_id": report.doctor_id,
                "period_type": report.period_type,
                "period_start": report.period_start.isoformat(),
                "period_end": report.period_end.isoformat(),
                "report_data": json.loads(report.report_data),
                "doctor_commentary": report.doctor_commentary,
                "generated_at": report.generated_at.isoformat(),
                "updated_at": report.updated_at.isoformat()
            })
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_patient_reports: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{doctor_id}/reports/{report_id}/commentary")
def update_report_commentary(
    doctor_id: int,
    report_id: int,
    commentary: str = Body(..., embed=True),
    session: Session = Depends(get_session)
):
    """Update doctor commentary on a progress report"""
    try:
        # Verify doctor exists
        doctor = session.get(Doctor, doctor_id)
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")
        
        # Get report
        report = session.get(ProgressReport, report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Verify report belongs to this doctor
        if report.doctor_id != doctor_id:
            raise HTTPException(status_code=403, detail="This report does not belong to you")
        
        # Update commentary
        report.doctor_commentary = commentary
        report.updated_at = datetime.now(timezone.utc)
        session.add(report)
        session.commit()
        session.refresh(report)
        
        return {
            "id": report.id,
            "doctor_commentary": report.doctor_commentary,
            "updated_at": report.updated_at.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in update_report_commentary: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ========== ANALYTICS DASHBOARD ==========
@router.get("/{doctor_id}/analytics")
def get_doctor_analytics(doctor_id: int, session: Session = Depends(get_session)):
    """Get comprehensive analytics for all patients assigned to this doctor"""
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
        
        total_patients = len(assignments)
        
        if total_patients == 0:
            return {
                "overview": {
                    "total_patients": 0,
                    "active_patients": 0,
                    "baseline_completed": 0,
                    "baseline_completion_rate": 0
                },
                "adherence": {
                    "overall_adherence_rate": 0,
                    "adherence_breakdown": {
                        "excellent": 0,
                        "good": 0,
                        "fair": 0,
                        "poor": 0
                    }
                },
                "success_metrics": {
                    "avg_improvement": 0,
                    "patients_improving": 0,
                    "avg_session_score": 0,
                    "total_sessions_completed": 0
                },
                "high_risk_patients": [],
                "patient_summary": []
            }
        
        # Calculate metrics for each patient
        patient_summaries = []
        adherence_rates = []
        improvements = []
        all_scores = []
        all_accuracies = []
        total_sessions = 0
        active_count = 0
        baseline_completed_count = 0
        high_risk_patients = []
        
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        for assignment in assignments:
            patient = session.get(User, assignment.patient_id)
            if not patient:
                continue
            
            # Get baseline
            baseline = session.exec(
                select(BaselineAssessment)
                .where(BaselineAssessment.user_id == patient.id)
            ).first()
            
            if baseline:
                baseline_completed_count += 1
            
            # Get all training sessions
            all_patient_sessions = session.exec(
                select(TrainingSession)
                .where(TrainingSession.user_id == patient.id)
                .where(TrainingSession.completed == True)
            ).all()
            
            sessions_count = len(all_patient_sessions)
            total_sessions += sessions_count
            
            # Get recent sessions (last 7 days)
            recent_sessions = session.exec(
                select(TrainingSession)
                .where(TrainingSession.user_id == patient.id)
                .where(TrainingSession.completed == True)
                .where(TrainingSession.created_at >= seven_days_ago)
            ).all()
            
            # Check if active (session in last 7 days)
            is_active = len(recent_sessions) > 0
            if is_active:
                active_count += 1
            
            # Get sessions in last 30 days for adherence
            sessions_30_days = session.exec(
                select(TrainingSession)
                .where(TrainingSession.user_id == patient.id)
                .where(TrainingSession.completed == True)
                .where(TrainingSession.created_at >= thirty_days_ago)
            ).all()
            
            # Calculate adherence (expected: 3-5 sessions per week = ~12-20 per month)
            expected_sessions = 15  # mid-range expectation
            sessions_30_count = len(sessions_30_days)
            adherence_rate = min(100, (sessions_30_count / expected_sessions) * 100) if expected_sessions > 0 else 0
            adherence_rates.append(adherence_rate)
            
            # Determine adherence status
            if adherence_rate >= 80:
                adherence_status = "excellent"
            elif adherence_rate >= 60:
                adherence_status = "good"
            elif adherence_rate >= 40:
                adherence_status = "fair"
            else:
                adherence_status = "poor"
            
            # Calculate average scores
            if all_patient_sessions:
                scores = [s.score for s in all_patient_sessions if s.score is not None]
                accuracies = [s.accuracy for s in all_patient_sessions if s.accuracy is not None]
                all_scores.extend(scores)
                all_accuracies.extend(accuracies)
                avg_score = statistics.mean(scores) if scores else 0
                avg_accuracy = statistics.mean(accuracies) if accuracies else 0
                
                # Calculate improvement (compare first 5 vs last 5 sessions)
                if len(scores) >= 10:
                    early_scores = scores[:5]
                    recent_scores = scores[-5:]
                    improvement = statistics.mean(recent_scores) - statistics.mean(early_scores)
                    improvements.append(improvement)
                else:
                    improvement = 0
            else:
                avg_score = 0
                avg_accuracy = 0
                improvement = 0
            
            # Get latest session
            latest_session = session.exec(
                select(TrainingSession)
                .where(TrainingSession.user_id == patient.id)
                .order_by(col(TrainingSession.created_at).desc())
            ).first()
            
            last_activity = latest_session.created_at if latest_session else None
            
            # Identify risk factors
            risk_factors = []
            risk_level = "low"
            
            if adherence_rate < 40:
                risk_factors.append("Poor adherence")
                risk_level = "high"
            elif adherence_rate < 60:
                risk_factors.append("Fair adherence")
                risk_level = "medium" if risk_level == "low" else risk_level
            
            if not is_active:
                risk_factors.append("Inactive (no sessions in 7 days)")
                risk_level = "high"
            
            if improvement < -5 and len(all_patient_sessions) >= 10:
                risk_factors.append("Performance declining")
                risk_level = "high"
            
            if not baseline:
                risk_factors.append("Baseline not completed")
                risk_level = "medium" if risk_level == "low" else risk_level
            
            # Add to high-risk list if needed
            if risk_level in ["high", "medium"]:
                high_risk_patients.append({
                    "patient_id": patient.id,
                    "name": patient.full_name or patient.email,
                    "email": patient.email,
                    "risk_level": risk_level,
                    "risk_factors": risk_factors,
                    "adherence_rate": round(adherence_rate, 1),
                    "last_activity": last_activity.isoformat() if last_activity else None,
                    "sessions_30_days": sessions_30_count
                })
            
            patient_summaries.append({
                "patient_id": patient.id,
                "name": patient.full_name or patient.email,
                "email": patient.email,
                "diagnosis": assignment.diagnosis,
                "assigned_date": assignment.assigned_at.isoformat(),
                "is_active": is_active,
                "baseline_completed": baseline is not None,
                "total_sessions": sessions_count,
                "sessions_last_7_days": len(recent_sessions),
                "sessions_last_30_days": sessions_30_count,
                "adherence_rate": round(adherence_rate, 1),
                "adherence_status": adherence_status,
                "avg_score": round(avg_score, 1) if avg_score else 0,
                "avg_accuracy": round(avg_accuracy, 1) if avg_accuracy else 0,
                "improvement": round(improvement, 1),
                "last_activity": last_activity.isoformat() if last_activity else None,
                "risk_level": risk_level
            })
        
        # Calculate overall metrics
        overall_adherence = statistics.mean(adherence_rates) if adherence_rates else 0
        avg_improvement = statistics.mean(improvements) if improvements else 0
        patients_improving = len([i for i in improvements if i > 0])
        avg_session_score = statistics.mean(all_scores) if all_scores else 0
        avg_session_accuracy = statistics.mean(all_accuracies) if all_accuracies else 0
        
        # Adherence breakdown
        adherence_breakdown = {
            "excellent": len([r for r in adherence_rates if r >= 80]),
            "good": len([r for r in adherence_rates if 60 <= r < 80]),
            "fair": len([r for r in adherence_rates if 40 <= r < 60]),
            "poor": len([r for r in adherence_rates if r < 40])
        }
        
        # Sort high-risk patients by risk level
        high_risk_patients.sort(key=lambda x: (0 if x["risk_level"] == "high" else 1, -x["adherence_rate"]))
        
        return {
            "overview": {
                "total_patients": total_patients,
                "active_patients": active_count,
                "baseline_completed": baseline_completed_count,
                "baseline_completion_rate": round((baseline_completed_count / total_patients) * 100, 1) if total_patients > 0 else 0
            },
            "adherence": {
                "overall_adherence_rate": round(overall_adherence, 1),
                "adherence_breakdown": adherence_breakdown
            },
            "success_metrics": {
                "avg_improvement": round(avg_improvement, 1),
                "patients_improving": patients_improving,
                "patients_declining": len([i for i in improvements if i < 0]),
                "avg_session_score": round(avg_session_score, 1),
                "avg_session_accuracy": round(avg_session_accuracy, 1),
                "total_sessions_completed": total_sessions
            },
            "high_risk_patients": high_risk_patients[:10],  # Top 10 high-risk
            "patient_summary": patient_summaries
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_doctor_analytics: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doctor_id}/analytics/domains")
def get_domain_analytics(doctor_id: int, session: Session = Depends(get_session)):
    """Get domain-specific performance analytics across all patients"""
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
        
        patient_ids = [a.patient_id for a in assignments]
        
        if not patient_ids:
            return {"domains": {}}
        
        # Get all sessions for these patients
        sessions_query = select(TrainingSession).where(
            col(TrainingSession.user_id).in_(patient_ids),
            TrainingSession.completed == True
        )
        all_sessions = session.exec(sessions_query).all()
        
        # Group by domain
        domain_data = {}
        
        for train_session in all_sessions:
            domain = train_session.domain
            if not domain:
                continue
            
            if domain not in domain_data:
                domain_data[domain] = {
                    "scores": [],
                    "accuracies": [],
                    "reaction_times": [],
                    "sessions_count": 0,
                    "unique_patients": set()
                }
            
            domain_data[domain]["sessions_count"] += 1
            domain_data[domain]["unique_patients"].add(train_session.user_id)
            
            if train_session.score is not None:
                domain_data[domain]["scores"].append(train_session.score)
            if train_session.accuracy is not None:
                domain_data[domain]["accuracies"].append(train_session.accuracy)
            if train_session.average_reaction_time is not None:
                domain_data[domain]["reaction_times"].append(train_session.average_reaction_time)
        
        # Calculate statistics
        domain_stats = {}
        for domain, data in domain_data.items():
            domain_stats[domain] = {
                "sessions_count": data["sessions_count"],
                "patients_count": len(data["unique_patients"]),
                "avg_score": round(statistics.mean(data["scores"]), 1) if data["scores"] else 0,
                "avg_accuracy": round(statistics.mean(data["accuracies"]), 1) if data["accuracies"] else 0,
                "avg_reaction_time": round(statistics.mean(data["reaction_times"]), 0) if data["reaction_times"] else 0,
                "score_range": {
                    "min": round(min(data["scores"]), 1) if data["scores"] else 0,
                    "max": round(max(data["scores"]), 1) if data["scores"] else 0
                }
            }
        
        return {"domains": domain_stats}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_domain_analytics: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doctor_id}/analytics/trends")
def get_cohort_trends(doctor_id: int, days: int = 30, session: Session = Depends(get_session)):
    """Get performance trends over time for the entire patient cohort"""
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
        
        patient_ids = [a.patient_id for a in assignments]
        
        if not patient_ids:
            return {"trends": [], "summary": {}}
        
        # Get sessions for the specified period
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        sessions_query = select(TrainingSession).where(
            col(TrainingSession.user_id).in_(patient_ids),
            TrainingSession.completed == True,
            TrainingSession.created_at >= start_date
        ).order_by(col(TrainingSession.created_at))
        
        sessions_list = session.exec(sessions_query).all()
        
        # Group by week
        weekly_data = {}
        
        for train_session in sessions_list:
            # Get week number
            week_start = train_session.created_at - timedelta(days=train_session.created_at.weekday())
            week_key = week_start.strftime("%Y-%m-%d")
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {
                    "sessions": 0,
                    "scores": [],
                    "active_patients": set()
                }
            
            weekly_data[week_key]["sessions"] += 1
            weekly_data[week_key]["active_patients"].add(train_session.user_id)
            if train_session.score is not None:
                weekly_data[week_key]["scores"].append(train_session.score)
        
        # Calculate weekly trends
        trends = []
        for week, data in sorted(weekly_data.items()):
            trends.append({
                "week_starting": week,
                "sessions": data["sessions"],
                "active_patients": len(data["active_patients"]),
                "avg_score": round(statistics.mean(data["scores"]), 1) if data["scores"] else 0
            })
        
        # Calculate overall summary
        total_sessions = sum(d["sessions"] for d in weekly_data.values())
        all_scores = [s for data in weekly_data.values() for s in data["scores"]]
        
        summary = {
            "total_sessions": total_sessions,
            "avg_sessions_per_week": round(total_sessions / len(weekly_data), 1) if weekly_data else 0,
            "overall_avg_score": round(statistics.mean(all_scores), 1) if all_scores else 0,
            "weeks_tracked": len(weekly_data)
        }
        
        return {
            "trends": trends,
            "summary": summary,
            "period_days": days
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_cohort_trends: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

