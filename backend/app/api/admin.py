from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, col
from typing import List, Sequence, Literal
from datetime import datetime, timedelta
from time import perf_counter
from hashlib import sha256
import csv
import io
from app.models.admin import Admin
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.user import User
from app.models.patient_assignment import PatientAssignment
from app.models.baseline_assessment import BaselineAssessment
from app.models.training_session import TrainingSession
from app.models.session_context import SessionContext
from app.models.risk_alert import RiskAlert
from app.models.doctor_intervention import DoctorIntervention
from app.models.progress_report import ProgressReport
from app.models.message import Message
from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.schemas.admin import AdminLogin, AdminRead
from app.core.config import engine
from app.core.security import verify_password, hash_password
from pydantic import BaseModel
import json
import traceback
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

router = APIRouter(prefix="/admin", tags=["admin"])
PROCESS_STARTED_AT = datetime.utcnow()


class ResetPasswordBody(BaseModel):
    new_password: str


class TransferPatientBody(BaseModel):
    new_doctor_id: int


class NotificationCreateBody(BaseModel):
    notification_type: str
    audience: str
    title: str
    message: str


class CreateDepartmentBody(BaseModel):
    name: str
    description: str | None = None


class AssignDoctorDepartmentBody(BaseModel):
    department_id: int | None = None


def get_session():
    with Session(engine) as session:
        yield session


def _require_admin(admin_id: int, session: Session) -> Admin:
    """Verify admin exists and is active (consistent with existing auth pattern)."""
    admin = session.get(Admin, admin_id)
    if not admin or not admin.is_active:
        raise HTTPException(status_code=403, detail="Admin access required")
    return admin


def _summarize_risk_reasons(reasons: list[str]) -> str:
    if "declining from baseline" in reasons or "below baseline" in reasons or "low recent performance" in reasons:
        return "Cognitive decline detected"
    if "high fatigue" in reasons:
        return "Severe fatigue patterns"
    if "elevated fatigue" in reasons:
        return "Fatigue patterns detected"
    if "low completion rate" in reasons:
        return "Rapid performance drop"
    if "low baseline score" in reasons:
        return "Persistent cognitive risk detected"
    return "Clinical risk alert detected"


def _create_audit_log(
    session: Session,
    actor_type: str,
    actor_id: int | None,
    actor_name: str,
    action_type: str,
    category: str,
    summary: str,
    target_type: str | None = None,
    target_id: int | None = None,
    target_name: str | None = None,
    detail: str | None = None,
    metadata: dict | None = None,
):
    session.add(
        AuditLog(
            actor_type=actor_type,
            actor_id=actor_id,
            actor_name=actor_name,
            action_type=action_type,
            category=category,
            summary=summary,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            detail=detail,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
    )


def _format_task_name(training_session: TrainingSession) -> str:
    raw_name = training_session.task_code or training_session.task_type or training_session.domain
    return raw_name.replace("_", " ").title()


def _anonymized_patient_id(user: User) -> str:
    seed = f"{user.id}:{user.email}:neurobloom-research"
    return f"NB-{sha256(seed.encode()).hexdigest()[:12].upper()}"


def _safe_iso(value):
    return value.isoformat() if isinstance(value, datetime) else value


def _safe_float(value, digits: int = 2):
    if value is None:
        return None
    return round(float(value), digits)


def _parse_age_band(date_of_birth: str | None) -> str:
    if not date_of_birth:
        return "unknown"

    parsed_date = None
    for parser in (datetime.fromisoformat,):
        try:
            parsed_date = parser(date_of_birth)
            break
        except ValueError:
            continue

    if parsed_date is None:
        for date_format in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                parsed_date = datetime.strptime(date_of_birth, date_format)
                break
            except ValueError:
                continue

    if parsed_date is None:
        return "unknown"

    today = datetime.utcnow().date()
    age = today.year - parsed_date.date().year - (
        (today.month, today.day) < (parsed_date.date().month, parsed_date.date().day)
    )

    if age < 18:
        return "under_18"
    if age < 30:
        return "18_29"
    if age < 40:
        return "30_39"
    if age < 50:
        return "40_49"
    if age < 60:
        return "50_59"
    if age < 70:
        return "60_69"
    return "70_plus"


def _latest_baseline_by_user(session: Session):
    latest = {}
    for baseline in session.exec(select(BaselineAssessment)).all():
        current = latest.get(baseline.user_id)
        if current is None or baseline.created_at > current.created_at:
            latest[baseline.user_id] = baseline
    return latest


def _pdf_preview_line(record: dict) -> str:
    preview_parts = []
    for key, value in list(record.items())[:6]:
        preview_parts.append(f"{key}: {value}")
    return " | ".join(preview_parts)


def _write_pdf_lines(pdf: canvas.Canvas, lines: list[str], title: str):
    width, height = A4
    y = height - 48

    pdf.setTitle(title)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, y, title)
    y -= 28

    pdf.setFont("Helvetica", 9)
    for line in lines:
        if y < 48:
            pdf.showPage()
            y = height - 48
            pdf.setFont("Helvetica", 9)
        pdf.drawString(40, y, str(line)[:135])
        y -= 14


def _serialize_csv(rows: list[dict]) -> bytes:
    output = io.StringIO()
    fieldnames = list(rows[0].keys()) if rows else ["message"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    if rows:
        writer.writerows(rows)
    else:
        writer.writerow({"message": "No records available"})
    return output.getvalue().encode("utf-8")


def _serialize_json(summary: dict, rows: list[dict]) -> bytes:
    return json.dumps({"summary": summary, "records": rows}, indent=2, ensure_ascii=False).encode("utf-8")


def _serialize_pdf(title: str, summary: dict, rows: list[dict]) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    lines = [
        f"Generated at: {summary.get('generated_at')}",
        f"Dataset key: {summary.get('dataset_key')}",
        f"Total records: {summary.get('record_count')}",
        f"Unique patients: {summary.get('unique_patients')}",
        f"Date range start: {summary.get('date_range', {}).get('start') or '-'}",
        f"Date range end: {summary.get('date_range', {}).get('end') or '-'}",
        "",
        "Preview records:",
    ]

    preview_rows = rows[:18] if rows else [{"message": "No records available"}]
    lines.extend(_pdf_preview_line(row) for row in preview_rows)

    _write_pdf_lines(pdf, lines, title)
    pdf.save()
    buffer.seek(0)
    return buffer.read()


def _build_research_dataset(session: Session, dataset_key: str):
    patients = [patient for patient in session.exec(select(User)).all() if patient.id is not None]
    patient_by_id = {patient.id: patient for patient in patients if patient.id is not None}
    anonymized_ids = {patient.id: _anonymized_patient_id(patient) for patient in patients if patient.id is not None}
    training_sessions = [
        training_session
        for training_session in session.exec(
            select(TrainingSession).order_by(col(TrainingSession.created_at).desc())
        ).all()
        if training_session.user_id in patient_by_id
    ]
    session_contexts = [
        context
        for context in session.exec(
            select(SessionContext).order_by(col(SessionContext.created_at).desc())
        ).all()
        if context.user_id in patient_by_id
    ]
    latest_baselines = _latest_baseline_by_user(session)
    training_session_by_id = {
        training_session.id: training_session
        for training_session in training_sessions
        if training_session.id is not None
    }
    context_by_session_id = {
        context.training_session_id: context
        for context in session_contexts
        if context.training_session_id is not None
    }

    rows: list[dict] = []

    if dataset_key == "cognitive_performance":
        for training_session in training_sessions:
            patient = patient_by_id.get(training_session.user_id)
            if not patient or training_session.id is None:
                continue
            linked_context = context_by_session_id.get(training_session.id)
            rows.append({
                "anonymous_patient_id": anonymized_ids[training_session.user_id],
                "session_date": _safe_iso(training_session.created_at),
                "diagnosis": patient.diagnosis or "unspecified",
                "domain": training_session.domain,
                "task_type": training_session.task_type,
                "task_code": training_session.task_code or training_session.task_type,
                "score": _safe_float(training_session.score),
                "accuracy": _safe_float(training_session.accuracy),
                "consistency": _safe_float(training_session.consistency),
                "errors": training_session.errors,
                "duration_seconds": training_session.duration,
                "average_reaction_time_ms": _safe_float(training_session.average_reaction_time),
                "difficulty_before": training_session.difficulty_before,
                "difficulty_after": training_session.difficulty_after,
                "fatigue_level": linked_context.fatigue_level if linked_context else None,
                "sleep_quality": linked_context.sleep_quality if linked_context else None,
                "time_of_day": linked_context.time_of_day if linked_context else None,
            })

    elif dataset_key == "fatigue":
        for context in session_contexts:
            patient = patient_by_id.get(context.user_id)
            if not patient:
                continue
            linked_session = training_session_by_id.get(context.training_session_id) if context.training_session_id is not None else None
            rows.append({
                "anonymous_patient_id": anonymized_ids[context.user_id],
                "recorded_at": _safe_iso(context.created_at),
                "diagnosis": patient.diagnosis or "unspecified",
                "fatigue_level": context.fatigue_level,
                "sleep_quality": context.sleep_quality,
                "sleep_hours": context.sleep_hours,
                "medication_taken_today": context.medication_taken_today,
                "hours_since_medication": context.hours_since_medication,
                "pain_level": context.pain_level,
                "stress_level": context.stress_level,
                "readiness_level": context.readiness_level,
                "time_of_day": context.time_of_day,
                "distractions_present": context.distractions_present,
                "location": context.location,
                "linked_domain": linked_session.domain if linked_session else None,
                "linked_task_code": linked_session.task_code if linked_session else None,
                "linked_score": _safe_float(linked_session.score) if linked_session else None,
                "linked_accuracy": _safe_float(linked_session.accuracy) if linked_session else None,
                "linked_average_reaction_time_ms": _safe_float(linked_session.average_reaction_time) if linked_session else None,
            })

    elif dataset_key == "reaction_time":
        for training_session in training_sessions:
            patient = patient_by_id.get(training_session.user_id)
            if not patient:
                continue
            rows.append({
                "anonymous_patient_id": anonymized_ids[training_session.user_id],
                "session_date": _safe_iso(training_session.created_at),
                "diagnosis": patient.diagnosis or "unspecified",
                "domain": training_session.domain,
                "task_type": training_session.task_type,
                "task_code": training_session.task_code or training_session.task_type,
                "average_reaction_time_ms": _safe_float(training_session.average_reaction_time),
                "accuracy": _safe_float(training_session.accuracy),
                "score": _safe_float(training_session.score),
                "consistency": _safe_float(training_session.consistency),
                "difficulty_level": training_session.difficulty_level,
                "duration_seconds": training_session.duration,
                "errors": training_session.errors,
            })

    elif dataset_key == "anonymized_patients":
        sessions_by_user = {}
        fatigue_by_user = {}
        for training_session in training_sessions:
            sessions_by_user.setdefault(training_session.user_id, []).append(training_session)
        for context in session_contexts:
            if context.fatigue_level is not None:
                fatigue_by_user.setdefault(context.user_id, []).append(context.fatigue_level)

        for patient in patients:
            patient_id = patient.id
            if patient_id is None:
                continue
            user_sessions = sessions_by_user.get(patient.id, [])
            latest_baseline = latest_baselines.get(patient_id)
            avg_score = sum(session_row.score for session_row in user_sessions) / len(user_sessions) if user_sessions else None
            avg_accuracy = sum(session_row.accuracy for session_row in user_sessions) / len(user_sessions) if user_sessions else None
            avg_reaction_time = sum(session_row.average_reaction_time for session_row in user_sessions) / len(user_sessions) if user_sessions else None
            fatigue_values = fatigue_by_user.get(patient_id, [])
            rows.append({
                "anonymous_patient_id": anonymized_ids[patient_id],
                "age_band": _parse_age_band(patient.date_of_birth),
                "diagnosis": patient.diagnosis or "unspecified",
                "consent_to_share": patient.consent_to_share,
                "is_active": patient.is_active,
                "latest_baseline_score": _safe_float(latest_baseline.overall_score) if latest_baseline else None,
                "total_sessions": len(user_sessions),
                "average_score": _safe_float(avg_score),
                "average_accuracy": _safe_float(avg_accuracy),
                "average_reaction_time_ms": _safe_float(avg_reaction_time),
                "average_fatigue": _safe_float(sum(fatigue_values) / len(fatigue_values)) if fatigue_values else None,
                "first_session_at": _safe_iso(user_sessions[-1].created_at) if user_sessions else None,
                "last_session_at": _safe_iso(user_sessions[0].created_at) if user_sessions else None,
            })

    else:
        raise HTTPException(status_code=400, detail="Unsupported dataset")

    date_values = []
    for row in rows:
        for candidate_key in ("session_date", "recorded_at", "first_session_at", "last_session_at"):
            if row.get(candidate_key):
                date_values.append(row[candidate_key])
                break

    summary = {
        "dataset_key": dataset_key,
        "record_count": len(rows),
        "unique_patients": len({row["anonymous_patient_id"] for row in rows if row.get("anonymous_patient_id")}),
        "generated_at": datetime.utcnow().isoformat(),
        "date_range": {
            "start": min(date_values) if date_values else None,
            "end": max(date_values) if date_values else None,
        },
    }
    return rows, summary


def _build_risk_monitoring(
    session: Session,
    today_start: datetime,
    completed_training_sessions: Sequence[TrainingSession],
    all_training_sessions: Sequence[TrainingSession],
    session_contexts: Sequence[SessionContext],
):
    baselines = session.exec(select(BaselineAssessment)).all()
    baseline_by_user = {}
    for baseline in baselines:
        existing = baseline_by_user.get(baseline.user_id)
        if not existing or baseline.created_at > existing.created_at:
            baseline_by_user[baseline.user_id] = baseline

    patient_lookup = {patient.id: patient for patient in session.exec(select(User)).all() if patient.id is not None}
    doctors_by_id = {doctor.id: doctor for doctor in session.exec(select(Doctor)).all() if doctor.id is not None}
    active_assignments = session.exec(
        select(PatientAssignment).where(PatientAssignment.is_active == True)
    ).all()
    assignment_by_patient = {assignment.patient_id: assignment for assignment in active_assignments}
    existing_alerts = {
        alert.patient_id: alert
        for alert in session.exec(select(RiskAlert)).all()
    }

    recent_window_start = today_start - timedelta(days=13)
    risk_breakdown = {"high": 0, "moderate": 0, "stable": 0}
    high_risk_patients = []

    recent_sessions_by_user = {}
    for training_session in completed_training_sessions:
        if training_session.created_at >= recent_window_start:
            recent_sessions_by_user.setdefault(training_session.user_id, []).append(training_session)

    all_sessions_by_user = {}
    for training_session in all_training_sessions:
        if training_session.created_at >= recent_window_start:
            all_sessions_by_user.setdefault(training_session.user_id, []).append(training_session)

    recent_contexts_by_user = {}
    for context in session_contexts:
        if context.created_at >= recent_window_start:
            recent_contexts_by_user.setdefault(context.user_id, []).append(context)

    monitored_user_ids = set(baseline_by_user.keys()) | set(recent_sessions_by_user.keys()) | set(recent_contexts_by_user.keys())
    for user_id in monitored_user_ids:
        if user_id is None:
            continue
        patient = patient_lookup.get(user_id)
        if not patient:
            continue

        baseline = baseline_by_user.get(user_id)
        recent_sessions = recent_sessions_by_user.get(user_id, [])
        recent_all_sessions = all_sessions_by_user.get(user_id, [])
        recent_contexts = recent_contexts_by_user.get(user_id, [])
        active_assignment = assignment_by_patient.get(user_id)
        assigned_doctor = doctors_by_id.get(active_assignment.doctor_id) if active_assignment else None

        reasons = []
        risk_score = 0
        recent_scores: List[float] = [session_row.score for session_row in recent_sessions]
        fatigue_values: List[float] = [float(context.fatigue_level) for context in recent_contexts if context.fatigue_level is not None]
        recent_avg_score = round(sum(recent_scores) / len(recent_scores), 1) if recent_scores else None
        recent_avg_fatigue = round(sum(fatigue_values) / len(fatigue_values), 1) if fatigue_values else None
        completion_rate = round((len(recent_sessions) / len(recent_all_sessions)) * 100, 1) if recent_all_sessions else None

        if baseline and baseline.overall_score < 45:
            risk_score += 2
            reasons.append("low baseline score")

        if baseline and recent_avg_score is not None:
            score_delta = round(recent_avg_score - baseline.overall_score, 1)
            if score_delta <= -12:
                risk_score += 2
                reasons.append("declining from baseline")
            elif score_delta <= -6:
                risk_score += 1
                reasons.append("below baseline")

        if recent_avg_score is not None and recent_avg_score < 50:
            risk_score += 1
            reasons.append("low recent performance")

        if recent_avg_fatigue is not None:
            if recent_avg_fatigue >= 8:
                risk_score += 2
                reasons.append("high fatigue")
            elif recent_avg_fatigue >= 6.5:
                risk_score += 1
                reasons.append("elevated fatigue")

        if completion_rate is not None and len(recent_all_sessions) >= 3 and completion_rate < 60:
            risk_score += 1
            reasons.append("low completion rate")

        if risk_score >= 4:
            risk_level = "high"
        elif risk_score >= 2:
            risk_level = "moderate"
        else:
            risk_level = "stable"

        risk_breakdown[risk_level] += 1

        if risk_level == "high":
            existing_alert = existing_alerts.get(user_id)
            high_risk_patients.append({
                "id": patient.id,
                "name": patient.full_name or patient.email,
                "email": patient.email,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "alert_summary": _summarize_risk_reasons(reasons),
                "recent_avg_score": recent_avg_score,
                "recent_avg_fatigue": recent_avg_fatigue,
                "completion_rate": completion_rate,
                "reasons": reasons[:3],
                "assigned_doctor_id": assigned_doctor.id if assigned_doctor else None,
                "assigned_doctor_name": (assigned_doctor.full_name or assigned_doctor.email) if assigned_doctor else None,
                "alert_status": existing_alert.status if existing_alert else "open",
                "doctor_notified": bool(existing_alert and existing_alert.doctor_notified_at),
                "doctor_notified_at": existing_alert.doctor_notified_at.isoformat() if existing_alert and existing_alert.doctor_notified_at else None,
                "escalated_at": existing_alert.escalated_at.isoformat() if existing_alert and existing_alert.escalated_at else None,
                "reviewed_at": existing_alert.reviewed_at.isoformat() if existing_alert and existing_alert.reviewed_at else None,
            })

    high_risk_patients.sort(key=lambda patient: (-patient["risk_score"], patient["name"].lower()))

    return {
        "risk_breakdown": risk_breakdown,
        "high_risk_patients": high_risk_patients,
    }


def _get_current_risk_alert(session: Session, patient_id: int):
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    completed_training_sessions = list(session.exec(
        select(TrainingSession).where(TrainingSession.completed == True)
    ).all())
    all_training_sessions = list(session.exec(select(TrainingSession)).all())
    completed_session_ids = {
        training_session.id for training_session in completed_training_sessions if training_session.id is not None
    }
    session_contexts = [
        context
        for context in session.exec(select(SessionContext)).all()
        if context.training_session_id in completed_session_ids
    ] if completed_session_ids else []

    risk_monitoring = _build_risk_monitoring(
        session,
        today_start,
        completed_training_sessions,
        all_training_sessions,
        session_contexts,
    )
    risk_patient = next((patient for patient in risk_monitoring["high_risk_patients"] if patient["id"] == patient_id), None)
    if not risk_patient:
        raise HTTPException(status_code=404, detail="Patient is not currently flagged as high risk")

    alert = session.exec(select(RiskAlert).where(RiskAlert.patient_id == patient_id)).first()
    now = datetime.utcnow()
    if not alert:
        alert = RiskAlert(
            patient_id=patient_id,
            assigned_doctor_id=risk_patient["assigned_doctor_id"],
            risk_score=risk_patient["risk_score"],
            risk_level=risk_patient["risk_level"],
            alert_summary=risk_patient["alert_summary"],
            risk_reasons_json=json.dumps(risk_patient["reasons"]),
            status="open",
        )
    else:
        alert.assigned_doctor_id = risk_patient["assigned_doctor_id"]
        alert.risk_score = risk_patient["risk_score"]
        alert.risk_level = risk_patient["risk_level"]
        alert.alert_summary = risk_patient["alert_summary"]
        alert.risk_reasons_json = json.dumps(risk_patient["reasons"])
        alert.updated_at = now

    return alert, risk_patient


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────

@router.post("/login")
def admin_login(credentials: AdminLogin, session: Session = Depends(get_session)):
    """Authenticate hospital administrator."""
    try:
        admin = session.exec(select(Admin).where(Admin.email == credentials.email)).first()
        if not admin or not verify_password(credentials.password, admin.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not admin.is_active:
            raise HTTPException(status_code=403, detail="Admin account is deactivated")

        admin.last_login = datetime.utcnow()
        session.add(admin)
        session.commit()

        return {
            "message": "Login successful",
            "id": admin.id,
            "email": admin.email,
            "full_name": admin.full_name,
            "role": "admin",
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in admin_login: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# DASHBOARD STATS
# ─────────────────────────────────────────────

@router.get("/stats")
def get_stats(admin_id: int, session: Session = Depends(get_session)):
    """Overview numbers for the admin dashboard."""
    _require_admin(admin_id, session)
    total_patients = len(session.exec(select(User)).all())
    active_patients = len(session.exec(select(User).where(User.is_active == True)).all())
    total_doctors = len(session.exec(select(Doctor)).all())
    pending_doctors = len(
        session.exec(select(Doctor).where(Doctor.is_verified == False).where(Doctor.is_active == True)).all()
    )
    active_doctors = len(
        session.exec(select(Doctor).where(Doctor.is_verified == True).where(Doctor.is_active == True)).all()
    )
    total_departments = len(session.exec(select(Department)).all())

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    sessions_today = session.exec(
        select(TrainingSession).where(TrainingSession.created_at >= today_start)
    ).all()
    active_patients_today = len({training_session.user_id for training_session in sessions_today})

    completed_training_sessions = session.exec(
        select(TrainingSession).where(TrainingSession.completed == True)
    ).all()
    completed_sessions = len(completed_training_sessions)
    all_training_sessions = session.exec(select(TrainingSession)).all()

    completed_session_ids = {
        training_session.id for training_session in completed_training_sessions if training_session.id is not None
    }
    session_contexts = [
        context
        for context in session.exec(select(SessionContext)).all()
        if context.training_session_id in completed_session_ids
    ] if completed_session_ids else []
    context_by_session_id = {
        context.training_session_id: context
        for context in session_contexts
        if context.training_session_id is not None
    }

    activity_labels = []
    activity_sessions = []
    activity_patients = []
    for days_ago in range(6, -1, -1):
        day_start = (today_start - timedelta(days=days_ago))
        day_end = day_start + timedelta(days=1)
        day_sessions = session.exec(
            select(TrainingSession)
            .where(TrainingSession.created_at >= day_start)
            .where(TrainingSession.created_at < day_end)
        ).all()
        activity_labels.append(day_start.strftime("%b %d"))
        activity_sessions.append(len(day_sessions))
        activity_patients.append(len({training_session.user_id for training_session in day_sessions}))

    performance_labels = []
    performance_scores = []
    for days_ago in range(13, -1, -1):
        day_start = today_start - timedelta(days=days_ago)
        day_end = day_start + timedelta(days=1)
        day_scores = [
            training_session.score
            for training_session in completed_training_sessions
            if day_start <= training_session.created_at < day_end
        ]
        performance_labels.append(day_start.strftime("%b %d"))
        performance_scores.append(round(sum(day_scores) / len(day_scores), 1) if day_scores else 0)

    fatigue_labels = []
    fatigue_levels = []
    fatigue_scores = []
    completion_labels = []
    completion_rates = []
    completion_completed = []
    for days_ago in range(13, -1, -1):
        day_start = today_start - timedelta(days=days_ago)
        day_end = day_start + timedelta(days=1)

        day_all_sessions = [
            training_session
            for training_session in all_training_sessions
            if day_start <= training_session.created_at < day_end
        ]
        day_completed_sessions = [
            training_session
            for training_session in completed_training_sessions
            if day_start <= training_session.created_at < day_end
        ]
        day_contexts = [
            context
            for context in session_contexts
            if day_start <= context.created_at < day_end and context.fatigue_level is not None
        ]
        day_fatigue_levels: List[float] = [float(context.fatigue_level) for context in day_contexts if context.fatigue_level is not None]
        day_completed_scores: List[float] = [training_session.score for training_session in day_completed_sessions]

        fatigue_labels.append(day_start.strftime("%b %d"))
        fatigue_levels.append(
            round(sum(day_fatigue_levels) / len(day_fatigue_levels), 1) if day_fatigue_levels else 0
        )
        fatigue_scores.append(
            round(sum(day_completed_scores) / len(day_completed_scores), 1) if day_completed_scores else 0
        )

        completion_labels.append(day_start.strftime("%b %d"))
        completion_completed.append(len(day_completed_sessions))
        completion_rates.append(
            round((len(day_completed_sessions) / len(day_all_sessions)) * 100, 1) if day_all_sessions else 0
        )

    task_counts = {}
    for training_session in completed_training_sessions:
        task_name = training_session.task_code or training_session.task_type
        task_counts[task_name] = task_counts.get(task_name, 0) + 1

    most_used_tasks = [
        {"task": task_name, "count": count}
        for task_name, count in sorted(task_counts.items(), key=lambda item: item[1], reverse=True)[:5]
    ]

    baselines = session.exec(select(BaselineAssessment)).all()
    baseline_by_user = {}
    for baseline in baselines:
        existing = baseline_by_user.get(baseline.user_id)
        if not existing or baseline.created_at > existing.created_at:
            baseline_by_user[baseline.user_id] = baseline

    session_scores_by_user = {}
    for training_session in completed_training_sessions:
        session_scores_by_user.setdefault(training_session.user_id, []).append(training_session.score)

    improvements = []
    for user_id, scores in session_scores_by_user.items():
        baseline = baseline_by_user.get(user_id)
        if not baseline:
            continue
        average_score = sum(scores) / len(scores)
        improvements.append(average_score - baseline.overall_score)

    average_improvement_score = round(sum(improvements) / len(improvements), 1) if improvements else 0.0

    risk_monitoring = _build_risk_monitoring(
        session,
        today_start,
        completed_training_sessions,
        all_training_sessions,
        session_contexts,
    )

    return {
        "total_patients": total_patients,
        "active_patients": active_patients,
        "active_patients_today": active_patients_today,
        "total_doctors": total_doctors,
        "pending_doctors": pending_doctors,
        "active_doctors": active_doctors,
        "completed_sessions": completed_sessions,
        "total_departments": total_departments,
        "average_improvement_score": average_improvement_score,
        "high_risk_patients": len(risk_monitoring["high_risk_patients"]),
        "high_risk_list": risk_monitoring["high_risk_patients"][:5],
        "risk_distribution": {
            "labels": ["High", "Moderate", "Stable"],
            "counts": [
                risk_monitoring["risk_breakdown"]["high"],
                risk_monitoring["risk_breakdown"]["moderate"],
                risk_monitoring["risk_breakdown"]["stable"],
            ],
        },
        "most_used_tasks": most_used_tasks,
        "patient_activity": {
            "labels": activity_labels,
            "sessions": activity_sessions,
            "patients": activity_patients,
        },
        "fatigue_trend": {
            "labels": fatigue_labels,
            "fatigue_levels": fatigue_levels,
            "scores": fatigue_scores,
        },
        "completion_trend": {
            "labels": completion_labels,
            "rates": completion_rates,
            "completed_sessions": completion_completed,
        },
        "performance_trend": {
            "labels": performance_labels,
            "scores": performance_scores,
        },
    }


@router.get("/risk-alerts")
def list_risk_alerts(admin_id: int, session: Session = Depends(get_session)):
    _require_admin(admin_id, session)

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    completed_training_sessions = list(session.exec(
        select(TrainingSession).where(TrainingSession.completed == True)
    ).all())
    all_training_sessions = list(session.exec(select(TrainingSession)).all())
    completed_session_ids = {
        training_session.id for training_session in completed_training_sessions if training_session.id is not None
    }
    session_contexts = [
        context
        for context in session.exec(select(SessionContext)).all()
        if context.training_session_id in completed_session_ids
    ] if completed_session_ids else []

    risk_monitoring = _build_risk_monitoring(
        session,
        today_start,
        completed_training_sessions,
        all_training_sessions,
        session_contexts,
    )

    return {
        "alerts": risk_monitoring["high_risk_patients"],
        "total": len(risk_monitoring["high_risk_patients"]),
    }


@router.post("/risk-alerts/{patient_id}/notify-doctor")
def notify_risk_alert_doctor(patient_id: int, admin_id: int, session: Session = Depends(get_session)):
    admin = _require_admin(admin_id, session)
    alert, risk_patient = _get_current_risk_alert(session, patient_id)

    if not alert.assigned_doctor_id:
        raise HTTPException(status_code=400, detail="No assigned doctor found for this patient")

    doctor = session.get(Doctor, alert.assigned_doctor_id)
    if not doctor or doctor.id is None:
        raise HTTPException(status_code=404, detail="Assigned doctor not found")

    now = datetime.utcnow()
    intervention = DoctorIntervention(
        doctor_id=doctor.id,
        patient_id=patient_id,
        intervention_type="admin_risk_alert",
        description=f"Admin risk alert from {admin.full_name}: {risk_patient['alert_summary']}. Indicators: {', '.join(risk_patient['reasons'])}.",
        intervention_data=json.dumps({
            "source": "admin_risk_dashboard",
            "risk_score": risk_patient["risk_score"],
            "alert_status": alert.status,
        }),
    )

    alert.doctor_notified_at = now
    alert.updated_at = now
    session.add(intervention)
    session.add(alert)
    session.commit()

    return {"message": f"Dr. {doctor.full_name or doctor.email} has been notified", "patient_id": patient_id}


@router.post("/risk-alerts/{patient_id}/escalate")
def escalate_risk_alert(patient_id: int, admin_id: int, session: Session = Depends(get_session)):
    admin = _require_admin(admin_id, session)
    alert, risk_patient = _get_current_risk_alert(session, patient_id)

    now = datetime.utcnow()
    alert.status = "escalated"
    alert.escalated_at = now
    alert.updated_at = now
    if alert.doctor_notified_at is None:
        alert.doctor_notified_at = now

    if alert.assigned_doctor_id:
        doctor = session.get(Doctor, alert.assigned_doctor_id)
        if doctor and doctor.id is not None:
            intervention = DoctorIntervention(
                doctor_id=doctor.id,
                patient_id=patient_id,
                intervention_type="admin_escalation",
                description=f"Escalated risk case from {admin.full_name}: {risk_patient['alert_summary']}. Please review urgently.",
                intervention_data=json.dumps({
                    "source": "admin_risk_dashboard",
                    "risk_score": risk_patient["risk_score"],
                    "reasons": risk_patient["reasons"],
                }),
            )
            session.add(intervention)

    session.add(alert)
    session.commit()

    return {"message": "Risk case escalated", "patient_id": patient_id}


@router.post("/risk-alerts/{patient_id}/mark-reviewed")
def mark_risk_alert_reviewed(patient_id: int, admin_id: int, session: Session = Depends(get_session)):
    _require_admin(admin_id, session)
    alert, _ = _get_current_risk_alert(session, patient_id)

    now = datetime.utcnow()
    alert.status = "reviewed"
    alert.reviewed_at = now
    alert.reviewed_by_admin_id = admin_id
    alert.updated_at = now
    session.add(alert)
    session.commit()

    return {"message": "Risk alert marked as reviewed", "patient_id": patient_id}


# ─────────────────────────────────────────────
# DOCTOR MANAGEMENT
# ─────────────────────────────────────────────

@router.get("/doctors")
def list_doctors(admin_id: int, session: Session = Depends(get_session)):
    """List all doctors with their current status."""
    _require_admin(admin_id, session)
    doctors = session.exec(select(Doctor)).all()
    return {
        "doctors": [
            {
                "id": d.id,
                "email": d.email,
                "full_name": d.full_name,
                "license_number": d.license_number,
                "specialization": d.specialization,
                "institution": d.institution,
                "department_id": d.department_id,
                "department_name": d.department.name if d.department else None,
                "is_active": d.is_active,
                "is_verified": d.is_verified,
                "created_at": d.created_at,
                "last_login": d.last_login,
            }
            for d in doctors
        ],
        "total": len(doctors),
    }


# ─────────────────────────────────────────────
# DEPARTMENT MANAGEMENT
# ─────────────────────────────────────────────

@router.get("/departments")
def list_departments(admin_id: int, session: Session = Depends(get_session)):
    """List departments with doctor and patient counts."""
    _require_admin(admin_id, session)
    departments = session.exec(select(Department)).all()

    department_rows = []
    for department in departments:
        doctors = session.exec(select(Doctor).where(Doctor.department_id == department.id)).all()
        doctor_ids = [doctor.id for doctor in doctors]
        patient_count = 0
        if doctor_ids:
            assignments = session.exec(select(PatientAssignment).where(PatientAssignment.is_active == True)).all()
            patient_ids = {assignment.patient_id for assignment in assignments if assignment.doctor_id in doctor_ids}
            patient_count = len(patient_ids)

        department_rows.append({
            "id": department.id,
            "name": department.name,
            "description": department.description,
            "doctor_count": len(doctors),
            "patient_count": patient_count,
        })

    return {"departments": department_rows, "total": len(department_rows)}


@router.post("/departments")
def create_department(body: CreateDepartmentBody, admin_id: int, session: Session = Depends(get_session)):
    """Create a new hospital department."""
    _require_admin(admin_id, session)

    department_name = body.name.strip()
    if not department_name:
        raise HTTPException(status_code=400, detail="Department name is required")

    existing = session.exec(select(Department).where(Department.name == department_name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department already exists")

    department = Department(name=department_name, description=(body.description or '').strip() or None)
    session.add(department)
    session.commit()
    session.refresh(department)

    return {
        "message": f"Department {department.name} created successfully",
        "department": {
            "id": department.id,
            "name": department.name,
            "description": department.description,
            "doctor_count": 0,
            "patient_count": 0,
        },
    }


@router.patch("/doctors/{doctor_id}/department")
def assign_doctor_department(doctor_id: int, body: AssignDoctorDepartmentBody, admin_id: int, session: Session = Depends(get_session)):
    """Assign or clear a doctor's department."""
    _require_admin(admin_id, session)

    doctor = session.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    department = None
    if body.department_id is not None:
        department = session.get(Department, body.department_id)
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")

    doctor.department_id = body.department_id
    session.add(doctor)
    admin = session.get(Admin, admin_id)
    _create_audit_log(
        session,
        actor_type="admin",
        actor_id=admin_id,
        actor_name=admin.full_name if admin else f"Admin #{admin_id}",
        action_type="doctor_department_updated",
        category="admin",
        summary=f"Admin updated department for Dr. {doctor.full_name}",
        target_type="doctor",
        target_id=doctor.id,
        target_name=doctor.full_name,
        detail=f"Department set to {department.name}" if department else "Department cleared",
    )
    session.commit()

    return {
        "message": f"Dr. {doctor.full_name} assigned to {department.name}" if department else f"Department cleared for Dr. {doctor.full_name}",
        "doctor_id": doctor.id,
        "department_id": body.department_id,
    }


@router.patch("/doctors/{doctor_id}/approve")
def approve_doctor(doctor_id: int, admin_id: int, session: Session = Depends(get_session)):
    """Approve a doctor's registration so they can log in."""
    _require_admin(admin_id, session)
    doctor = session.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor.is_verified = True
    doctor.is_active = True
    session.add(doctor)
    admin = session.get(Admin, admin_id)
    _create_audit_log(session, "admin", admin_id, admin.full_name if admin else f"Admin #{admin_id}", "doctor_approved", "admin", f"Admin approved Dr. {doctor.full_name}", "doctor", doctor.id, doctor.full_name)
    session.commit()
    return {"message": f"Doctor {doctor.full_name} has been approved", "doctor_id": doctor_id}


@router.patch("/doctors/{doctor_id}/suspend")
def suspend_doctor(doctor_id: int, admin_id: int, session: Session = Depends(get_session)):
    """Suspend a doctor account (sets is_active=False)."""
    _require_admin(admin_id, session)
    doctor = session.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor.is_active = False
    session.add(doctor)
    admin = session.get(Admin, admin_id)
    _create_audit_log(session, "admin", admin_id, admin.full_name if admin else f"Admin #{admin_id}", "doctor_suspended", "admin", f"Admin suspended Dr. {doctor.full_name}", "doctor", doctor.id, doctor.full_name)
    session.commit()
    return {"message": f"Doctor {doctor.full_name} has been suspended", "doctor_id": doctor_id}


@router.patch("/doctors/{doctor_id}/activate")
def activate_doctor(doctor_id: int, admin_id: int, session: Session = Depends(get_session)):
    """Re-activate a previously suspended doctor."""
    _require_admin(admin_id, session)
    doctor = session.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor.is_active = True
    session.add(doctor)
    admin = session.get(Admin, admin_id)
    _create_audit_log(session, "admin", admin_id, admin.full_name if admin else f"Admin #{admin_id}", "doctor_activated", "admin", f"Admin reactivated Dr. {doctor.full_name}", "doctor", doctor.id, doctor.full_name)
    session.commit()
    return {"message": f"Doctor {doctor.full_name} has been activated", "doctor_id": doctor_id}


# ─────────────────────────────────────────────
# PATIENT MANAGEMENT
# ─────────────────────────────────────────────

@router.get("/patients")
def list_patients(admin_id: int, session: Session = Depends(get_session)):
    """List all patient accounts."""
    _require_admin(admin_id, session)
    patients = session.exec(select(User)).all()
    return {
        "patients": [
            {
                "id": p.id,
                "email": p.email,
                "full_name": p.full_name,
                "date_of_birth": p.date_of_birth,
                "diagnosis": p.diagnosis,
                "is_active": p.is_active,
                "consent_to_share": p.consent_to_share,
            }
            for p in patients
        ],
        "total": len(patients),
    }


@router.patch("/patients/{patient_id}/deactivate")
def deactivate_patient(patient_id: int, admin_id: int, session: Session = Depends(get_session)):
    """Deactivate a patient account."""
    _require_admin(admin_id, session)
    patient = session.get(User, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient.is_active = False
    session.add(patient)
    admin = session.get(Admin, admin_id)
    _create_audit_log(session, "admin", admin_id, admin.full_name if admin else f"Admin #{admin_id}", "patient_deactivated", "admin", f"Admin deactivated patient {patient.full_name or patient.email}", "patient", patient.id, patient.full_name or patient.email)
    session.commit()
    return {"message": f"Patient account deactivated", "patient_id": patient_id}


@router.patch("/patients/{patient_id}/activate")
def activate_patient(patient_id: int, admin_id: int, session: Session = Depends(get_session)):
    """Re-activate a patient account."""
    _require_admin(admin_id, session)
    patient = session.get(User, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient.is_active = True
    session.add(patient)
    admin = session.get(Admin, admin_id)
    _create_audit_log(session, "admin", admin_id, admin.full_name if admin else f"Admin #{admin_id}", "patient_activated", "admin", f"Admin activated patient {patient.full_name or patient.email}", "patient", patient.id, patient.full_name or patient.email)
    session.commit()
    return {"message": f"Patient account activated", "patient_id": patient_id}


# ─────────────────────────────────────────────
# RESET PASSWORDS
# ─────────────────────────────────────────────

@router.post("/doctors/{doctor_id}/reset-password")
def reset_doctor_password(doctor_id: int, admin_id: int, body: ResetPasswordBody, session: Session = Depends(get_session)):
    """Reset a doctor's password."""
    _require_admin(admin_id, session)
    if not body.new_password or len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    doctor = session.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctor.password_hash = hash_password(body.new_password)
    session.add(doctor)
    admin = session.get(Admin, admin_id)
    _create_audit_log(session, "admin", admin_id, admin.full_name if admin else f"Admin #{admin_id}", "doctor_password_reset", "admin", f"Admin reset password for Dr. {doctor.full_name}", "doctor", doctor.id, doctor.full_name)
    session.commit()
    return {"message": f"Password reset for Dr. {doctor.full_name}", "doctor_id": doctor_id}


@router.post("/patients/{patient_id}/reset-password")
def reset_patient_password(patient_id: int, admin_id: int, body: ResetPasswordBody, session: Session = Depends(get_session)):
    """Reset a patient's password."""
    _require_admin(admin_id, session)
    if not body.new_password or len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    patient = session.get(User, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient.password_hash = hash_password(body.new_password)
    session.add(patient)
    admin = session.get(Admin, admin_id)
    _create_audit_log(session, "admin", admin_id, admin.full_name if admin else f"Admin #{admin_id}", "patient_password_reset", "admin", f"Admin reset password for patient {patient.full_name or patient.email}", "patient", patient.id, patient.full_name or patient.email)
    session.commit()
    return {"message": "Patient password reset successfully", "patient_id": patient_id}


# ─────────────────────────────────────────────
# TRANSFER PATIENT TO ANOTHER DOCTOR
# ─────────────────────────────────────────────

@router.post("/patients/{patient_id}/transfer")
def transfer_patient(patient_id: int, admin_id: int, body: TransferPatientBody, session: Session = Depends(get_session)):
    """Transfer a patient's active assignment to a different doctor."""
    _require_admin(admin_id, session)

    patient = session.get(User, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    new_doctor = session.get(Doctor, body.new_doctor_id)
    if not new_doctor or not new_doctor.is_active or not new_doctor.is_verified:
        raise HTTPException(status_code=400, detail="Target doctor not found or not active/verified")

    # Find current active assignment
    assignment = session.exec(
        select(PatientAssignment)
        .where(PatientAssignment.patient_id == patient_id)
        .where(PatientAssignment.is_active == True)
    ).first()

    if not assignment:
        raise HTTPException(status_code=404, detail="No active assignment found for this patient")

    if assignment.doctor_id == body.new_doctor_id:
        raise HTTPException(status_code=400, detail="Patient is already assigned to this doctor")

    old_doctor = session.get(Doctor, assignment.doctor_id)
    old_name = old_doctor.full_name if old_doctor else f"Doctor #{assignment.doctor_id}"

    assignment.doctor_id = body.new_doctor_id
    assignment.assigned_at = datetime.utcnow()
    assignment.assigned_by = admin_id
    session.add(assignment)
    admin = session.get(Admin, admin_id)
    _create_audit_log(
        session,
        "admin",
        admin_id,
        admin.full_name if admin else f"Admin #{admin_id}",
        "patient_transferred",
        "admin",
        f"Admin transferred {patient.full_name or patient.email} to Dr. {new_doctor.full_name}",
        "patient",
        patient.id,
        patient.full_name or patient.email,
        f"Transferred from {old_name} to Dr. {new_doctor.full_name}",
        {"old_doctor": old_name, "new_doctor": new_doctor.full_name},
    )
    session.commit()

    return {
        "message": f"Patient transferred from {old_name} to Dr. {new_doctor.full_name}",
        "patient_id": patient_id,
        "new_doctor_id": body.new_doctor_id,
    }


# ─────────────────────────────────────────────
# PATIENT OVERSIGHT (READ-ONLY PROFILE)
# ─────────────────────────────────────────────

@router.get("/patients/{patient_id}/overview")
def get_patient_overview_admin(patient_id: int, admin_id: int, session: Session = Depends(get_session)):
    """
    Read-only patient overview for admin oversight.
    Returns profile, assigned doctor, training summary, risk level,
    recent sessions, and progress reports. No medical data is modified.
    """
    _require_admin(admin_id, session)

    patient = session.get(User, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Active doctor assignment
    assignment = session.exec(
        select(PatientAssignment)
        .where(PatientAssignment.patient_id == patient_id)
        .where(PatientAssignment.is_active == True)
    ).first()

    doctor = session.get(Doctor, assignment.doctor_id) if assignment else None

    # Training sessions (sorted newest-first)
    all_sessions = list(session.exec(
        select(TrainingSession)
        .where(TrainingSession.user_id == patient_id)
        .order_by(col(TrainingSession.created_at).desc())
    ).all())

    total_sessions = len(all_sessions)
    last_activity = all_sessions[0].created_at if all_sessions else None
    days_since: int | None = (datetime.utcnow() - last_activity).days if last_activity else None

    # Risk level: re-use persisted RiskAlert if present, otherwise compute inline
    risk_alert = session.exec(
        select(RiskAlert).where(RiskAlert.patient_id == patient_id)
    ).first()

    if risk_alert:
        risk_level = risk_alert.risk_level
        risk_score = risk_alert.risk_score
    else:
        recent_cutoff = datetime.utcnow() - timedelta(days=14)
        recent = [s for s in all_sessions if s.completed and s.created_at >= recent_cutoff]
        scores = [s.score for s in recent]
        avg_score = round(sum(scores) / len(scores), 1) if scores else None

        baseline = session.exec(
            select(BaselineAssessment).where(BaselineAssessment.user_id == patient_id)
        ).first()

        r = 0
        if baseline and baseline.overall_score < 45:
            r += 2
        if baseline and avg_score is not None:
            delta = avg_score - baseline.overall_score
            if delta <= -12:
                r += 2
            elif delta <= -6:
                r += 1
        if avg_score is not None and avg_score < 50:
            r += 1

        risk_score = r
        risk_level = "high" if r >= 4 else "moderate" if r >= 2 else "stable"

    # Domain-level breakdown from all sessions
    domain_counts: dict[str, int] = {}
    domain_scores: dict[str, list[float]] = {}
    for s in all_sessions:
        domain_counts[s.domain] = domain_counts.get(s.domain, 0) + 1
        domain_scores.setdefault(s.domain, []).append(s.score)
    domain_summary = [
        {
            "domain": domain,
            "sessions": domain_counts[domain],
            "avg_score": round(sum(domain_scores[domain]) / len(domain_scores[domain]), 1),
        }
        for domain in domain_counts
    ]

    # Last 10 training sessions
    recent_sessions_data = [
        {
            "id": s.id,
            "domain": s.domain,
            "task": s.task_code or s.task_type,
            "score": round(s.score, 1),
            "accuracy": round(s.accuracy, 1),
            "duration_s": s.duration,
            "difficulty": s.difficulty_level,
            "completed": s.completed,
            "date": s.created_at.isoformat(),
        }
        for s in all_sessions[:10]
    ]

    # Up to 5 most recent progress reports
    reports = list(session.exec(
        select(ProgressReport)
        .where(ProgressReport.patient_id == patient_id)
        .order_by(col(ProgressReport.generated_at).desc())
    ).all())[:5]

    reports_data = [
        {
            "id": r.id,
            "period_type": r.period_type,
            "period_start": r.period_start.isoformat() if r.period_start else None,
            "period_end": r.period_end.isoformat() if r.period_end else None,
            "generated_at": r.generated_at.isoformat() if r.generated_at else None,
            "doctor_commentary": r.doctor_commentary,
        }
        for r in reports
    ]

    return {
        "profile": {
            "id": patient.id,
            "full_name": patient.full_name or "(no name)",
            "email": patient.email,
            "date_of_birth": patient.date_of_birth,
            "diagnosis": patient.diagnosis,
            "is_active": patient.is_active,
            "consent_to_share": patient.consent_to_share,
        },
        "doctor": {
            "id": doctor.id,
            "full_name": doctor.full_name,
            "specialization": doctor.specialization,
            "institution": doctor.institution,
        } if doctor else None,
        "assignment": {
            "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None,
            "treatment_goal": assignment.treatment_goal,
            "diagnosis": assignment.diagnosis,
        } if assignment else None,
        "training_summary": {
            "total_sessions": total_sessions,
            "last_activity": last_activity.isoformat() if last_activity else None,
            "days_since_last_activity": days_since,
            "domain_summary": domain_summary,
        },
        "risk": {
            "level": risk_level,
            "score": risk_score,
        },
        "recent_sessions": recent_sessions_data,
        "reports": reports_data,
    }


# ─────────────────────────────────────────────
# INTERVENTION MONITORING
# ─────────────────────────────────────────────

@router.get("/interventions")
def list_interventions(admin_id: int, days: int = 0, session: Session = Depends(get_session)):
    """
    List all doctor interventions for admin clinical quality oversight.
    days=0 returns all-time records. Includes enriched doctor and patient names.
    """
    _require_admin(admin_id, session)

    query = select(DoctorIntervention).order_by(col(DoctorIntervention.created_at).desc())
    if days > 0:
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = query.where(DoctorIntervention.created_at >= cutoff)

    interventions = list(session.exec(query).all())

    all_doctors = {d.id: d for d in session.exec(select(Doctor)).all() if d.id is not None}
    all_patients = {p.id: p for p in session.exec(select(User)).all() if p.id is not None}

    items = []
    for i in interventions:
        doc = all_doctors.get(i.doctor_id)
        pat = all_patients.get(i.patient_id)
        items.append({
            "id": i.id,
            "doctor_id": i.doctor_id,
            "doctor_name": doc.full_name if doc else f"Doctor #{i.doctor_id}",
            "doctor_specialization": doc.specialization if doc else None,
            "patient_id": i.patient_id,
            "patient_name": (pat.full_name or pat.email) if pat else f"Patient #{i.patient_id}",
            "intervention_type": i.intervention_type,
            "description": i.description,
            "created_at": i.created_at.isoformat(),
        })

    by_type: dict[str, int] = {}
    by_doctor: dict[int, dict] = {}
    for item in items:
        t = item["intervention_type"]
        by_type[t] = by_type.get(t, 0) + 1
        did = item["doctor_id"]
        if did not in by_doctor:
            by_doctor[did] = {"doctor_id": did, "doctor_name": item["doctor_name"], "count": 0}
        by_doctor[did]["count"] += 1

    top_doctors = sorted(by_doctor.values(), key=lambda x: -x["count"])
    doctor_generated = sum(1 for item in items if not item["intervention_type"].startswith("admin_"))

    return {
        "summary": {
            "total": len(items),
            "doctor_generated": doctor_generated,
            "by_type": by_type,
            "top_doctors": top_doctors[:5],
        },
        "interventions": items,
    }


def _audit_message_content(subject: str | None, body: str):
    combined = f"{subject or ''} {body}".strip()
    lowered = combined.lower()
    abuse_terms = [
        term
        for term in ["idiot", "stupid", "useless", "worthless", "shut up", "hate you", "lazy"]
        if term in lowered
    ]

    letters = [char for char in combined if char.isalpha()]
    uppercase_ratio = (
        sum(1 for char in letters if char.isupper()) / len(letters)
        if len(letters) >= 12
        else 0
    )
    repeated_punctuation = any(token in combined for token in ("!!!", "???", "?!?!", "!!?"))

    reasons: list[str] = []
    if abuse_terms:
        reasons.append("abusive language detected")
    if uppercase_ratio >= 0.65:
        reasons.append("excessive capitalization")
    if repeated_punctuation:
        reasons.append("aggressive punctuation")

    score = len(abuse_terms) * 2
    if uppercase_ratio >= 0.65:
        score += 1
    if repeated_punctuation:
        score += 1

    severity = "none"
    if score >= 4:
        severity = "high"
    elif score >= 2:
        severity = "medium"
    elif score >= 1:
        severity = "low"

    return {
        "flagged": bool(reasons),
        "severity": severity,
        "reasons": reasons,
        "abuse_terms": abuse_terms,
    }


@router.get("/messages/audit")
def audit_messages(
    admin_id: int,
    days: int = 0,
    limit: int = 300,
    session: Session = Depends(get_session),
):
    """Read-only communication audit view for admins."""
    _require_admin(admin_id, session)

    query = select(Message).order_by(col(Message.created_at).desc()).limit(limit)
    if days > 0:
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = query.where(Message.created_at >= cutoff)

    messages = list(session.exec(query).all())
    doctors_by_id = {doctor.id: doctor for doctor in session.exec(select(Doctor)).all() if doctor.id is not None}
    patients_by_id = {patient.id: patient for patient in session.exec(select(User)).all() if patient.id is not None}

    items = []
    flagged_count = 0
    patient_to_doctor = 0
    doctor_to_patient = 0
    unread_count = 0

    for message in messages:
        if message.sender_type == "doctor":
            sender = doctors_by_id.get(message.sender_id)
            sender_name = sender.full_name if sender else f"Doctor #{message.sender_id}"
        else:
            sender = patients_by_id.get(message.sender_id)
            sender_name = (sender.full_name or sender.email) if sender else f"Patient #{message.sender_id}"

        if message.recipient_type == "doctor":
            recipient = doctors_by_id.get(message.recipient_id)
            recipient_name = recipient.full_name if recipient else f"Doctor #{message.recipient_id}"
        else:
            recipient = patients_by_id.get(message.recipient_id)
            recipient_name = (recipient.full_name or recipient.email) if recipient else f"Patient #{message.recipient_id}"

        direction = f"{message.sender_type}_to_{message.recipient_type}"
        if direction == "patient_to_doctor":
            patient_to_doctor += 1
        elif direction == "doctor_to_patient":
            doctor_to_patient += 1

        if not message.is_read:
            unread_count += 1

        audit = _audit_message_content(message.subject, message.message)
        if audit["flagged"]:
            flagged_count += 1

        preview = message.message.strip()
        if len(preview) > 180:
            preview = f"{preview[:177]}..."

        items.append({
            "id": message.id,
            "sender_id": message.sender_id,
            "sender_type": message.sender_type,
            "sender_name": sender_name,
            "recipient_id": message.recipient_id,
            "recipient_type": message.recipient_type,
            "recipient_name": recipient_name,
            "direction": direction,
            "subject": message.subject,
            "message": message.message,
            "preview": preview,
            "is_read": message.is_read,
            "created_at": message.created_at.isoformat(),
            "audit": audit,
        })

    return {
        "summary": {
            "total": len(items),
            "flagged": flagged_count,
            "unread": unread_count,
            "patient_to_doctor": patient_to_doctor,
            "doctor_to_patient": doctor_to_patient,
        },
        "messages": items,
    }


@router.get("/audit-logs")
def get_audit_logs(
    admin_id: int,
    days: int = 30,
    limit: int = 400,
    session: Session = Depends(get_session),
):
    """Unified system activity feed for admin traceability."""
    _require_admin(admin_id, session)

    cutoff = datetime.utcnow() - timedelta(days=days) if days > 0 else None
    doctors_by_id = {doctor.id: doctor for doctor in session.exec(select(Doctor)).all() if doctor.id is not None}
    patients_by_id = {patient.id: patient for patient in session.exec(select(User)).all() if patient.id is not None}

    events = []

    audit_query = select(AuditLog).order_by(col(AuditLog.created_at).desc())
    if cutoff:
        audit_query = audit_query.where(AuditLog.created_at >= cutoff)
    for entry in list(session.exec(audit_query).all()):
        events.append({
            "id": f"audit-{entry.id}",
            "created_at": entry.created_at.isoformat(),
            "category": entry.category,
            "action_type": entry.action_type,
            "actor_type": entry.actor_type,
            "actor_name": entry.actor_name,
            "target_name": entry.target_name,
            "summary": entry.summary,
            "detail": entry.detail,
            "badge": "Admin Action",
        })

    training_query = select(TrainingSession).where(TrainingSession.completed == True).order_by(col(TrainingSession.created_at).desc())
    if cutoff:
        training_query = training_query.where(TrainingSession.created_at >= cutoff)
    for training_session in list(session.exec(training_query).all()):
        patient = patients_by_id.get(training_session.user_id)
        patient_name = (patient.full_name or patient.email) if patient else f"Patient #{training_session.user_id}"
        events.append({
            "id": f"session-{training_session.id}",
            "created_at": training_session.created_at.isoformat(),
            "category": "training",
            "action_type": "session_submitted",
            "actor_type": "patient",
            "actor_name": patient_name,
            "target_name": _format_task_name(training_session),
            "summary": f"{patient_name} submitted a training session",
            "detail": f"{_format_task_name(training_session)} in {training_session.domain.replace('_', ' ').title()} with score {round(training_session.score, 1)}",
            "badge": "Training",
        })

    intervention_query = select(DoctorIntervention).order_by(col(DoctorIntervention.created_at).desc())
    if cutoff:
        intervention_query = intervention_query.where(DoctorIntervention.created_at >= cutoff)
    for intervention in list(session.exec(intervention_query).all()):
        doctor = doctors_by_id.get(intervention.doctor_id)
        patient = patients_by_id.get(intervention.patient_id)
        doctor_name = doctor.full_name if doctor else f"Doctor #{intervention.doctor_id}"
        patient_name = (patient.full_name or patient.email) if patient else f"Patient #{intervention.patient_id}"
        events.append({
            "id": f"intervention-{intervention.id}",
            "created_at": intervention.created_at.isoformat(),
            "category": "clinical",
            "action_type": intervention.intervention_type,
            "actor_type": "doctor",
            "actor_name": doctor_name,
            "target_name": patient_name,
            "summary": f"Dr. {doctor_name} sent intervention for {patient_name}",
            "detail": intervention.description,
            "badge": "Clinical",
        })

    assignment_query = select(PatientAssignment).order_by(col(PatientAssignment.assigned_at).desc())
    if cutoff:
        assignment_query = assignment_query.where(PatientAssignment.assigned_at >= cutoff)
    for assignment in list(session.exec(assignment_query).all()):
        doctor = doctors_by_id.get(assignment.doctor_id)
        patient = patients_by_id.get(assignment.patient_id)
        doctor_name = doctor.full_name if doctor else f"Doctor #{assignment.doctor_id}"
        patient_name = (patient.full_name or patient.email) if patient else f"Patient #{assignment.patient_id}"
        actor_name = doctor_name
        actor_type = "doctor"
        summary = f"Dr. {doctor_name} assigned patient {patient_name}"
        if assignment.assigned_by:
            summary = f"Admin updated assignment for {patient_name}"
            actor_name = "Hospital Administrator"
            actor_type = "admin"
        events.append({
            "id": f"assignment-{assignment.id}",
            "created_at": assignment.assigned_at.isoformat(),
            "category": "system",
            "action_type": "patient_assignment",
            "actor_type": actor_type,
            "actor_name": actor_name,
            "target_name": patient_name,
            "summary": summary,
            "detail": f"Assigned to Dr. {doctor_name}",
            "badge": "Assignment",
        })

    message_query = select(Message).order_by(col(Message.created_at).desc())
    if cutoff:
        message_query = message_query.where(Message.created_at >= cutoff)
    for message in list(session.exec(message_query).all()):
        if message.sender_type == "doctor":
            sender = doctors_by_id.get(message.sender_id)
            sender_name = sender.full_name if sender else f"Doctor #{message.sender_id}"
        else:
            sender = patients_by_id.get(message.sender_id)
            sender_name = (sender.full_name or sender.email) if sender else f"Patient #{message.sender_id}"

        if message.recipient_type == "doctor":
            recipient = doctors_by_id.get(message.recipient_id)
            recipient_name = recipient.full_name if recipient else f"Doctor #{message.recipient_id}"
        else:
            recipient = patients_by_id.get(message.recipient_id)
            recipient_name = (recipient.full_name or recipient.email) if recipient else f"Patient #{message.recipient_id}"

        direction_label = "Doctor → Patient" if message.sender_type == "doctor" else "Patient → Doctor"
        events.append({
            "id": f"message-{message.id}",
            "created_at": message.created_at.isoformat(),
            "category": "communication",
            "action_type": "message_sent",
            "actor_type": message.sender_type,
            "actor_name": sender_name,
            "target_name": recipient_name,
            "summary": f"{direction_label}: {sender_name} to {recipient_name}",
            "detail": message.subject or message.message[:140],
            "badge": "Message",
        })

    events.sort(key=lambda event: event["created_at"], reverse=True)
    limited_events = events[:limit]
    by_category = {
        "admin": sum(1 for event in limited_events if event["category"] == "admin"),
        "clinical": sum(1 for event in limited_events if event["category"] == "clinical"),
        "training": sum(1 for event in limited_events if event["category"] == "training"),
        "communication": sum(1 for event in limited_events if event["category"] == "communication"),
        "system": sum(1 for event in limited_events if event["category"] == "system"),
    }

    return {
        "summary": {
            "total": len(limited_events),
            "by_category": by_category,
            "admin_actions": by_category["admin"],
            "clinical_actions": by_category["clinical"],
            "training_events": by_category["training"],
            "communication_events": by_category["communication"],
        },
        "logs": limited_events,
    }


@router.get("/system-health")
def get_system_health(admin_id: int, session: Session = Depends(get_session)):
    """Enterprise-style health snapshot for admin monitoring."""
    _require_admin(admin_id, session)

    api_now = datetime.utcnow()
    uptime_delta = api_now - PROCESS_STARTED_AT
    uptime_seconds = max(int(uptime_delta.total_seconds()), 0)

    db_latency_started = perf_counter()
    database_status = "operational"
    database_latency_ms = 0.0
    database_error = None
    try:
        session.exec(select(Admin.id).limit(1)).first()
        database_latency_ms = round((perf_counter() - db_latency_started) * 1000, 1)
    except Exception as exc:
        database_status = "degraded"
        database_latency_ms = round((perf_counter() - db_latency_started) * 1000, 1)
        database_error = str(exc)

    active_cutoff = api_now - timedelta(minutes=15)
    recent_contexts = list(session.exec(
        select(SessionContext).where(SessionContext.created_at >= active_cutoff)
    ).all())
    recent_training = list(session.exec(
        select(TrainingSession).where(TrainingSession.created_at >= active_cutoff)
    ).all())

    active_user_ids = {
        context.user_id for context in recent_contexts if context.user_id is not None
    } | {
        training.user_id for training in recent_training if training.user_id is not None
    }

    total_patients = len(list(session.exec(select(User.id)).all()))
    total_doctors = len(list(session.exec(select(Doctor.id)).all()))

    return {
        "api": {
            "status": "operational",
            "checked_at": api_now.isoformat(),
            "version": "v1",
        },
        "database": {
            "status": database_status,
            "latency_ms": database_latency_ms,
            "error": database_error,
        },
        "sessions": {
            "active_count": len(active_user_ids),
            "window_minutes": 15,
            "recent_contexts": len(recent_contexts),
            "recent_training_events": len(recent_training),
        },
        "server": {
            "started_at": PROCESS_STARTED_AT.isoformat(),
            "uptime_seconds": uptime_seconds,
            "uptime_minutes": round(uptime_seconds / 60, 1),
        },
        "capacity": {
            "patients": total_patients,
            "doctors": total_doctors,
        },
    }


@router.get("/notifications")
def list_notifications(admin_id: int, session: Session = Depends(get_session)):
    """List admin notifications and summary metrics."""
    _require_admin(admin_id, session)

    admins_by_id = {admin.id: admin for admin in session.exec(select(Admin)).all() if admin.id is not None}
    notifications = list(session.exec(
        select(Notification).order_by(col(Notification.created_at).desc())
    ).all())

    items = []
    for notification in notifications:
        creator = admins_by_id.get(notification.created_by_admin_id)
        items.append({
            "id": notification.id,
            "notification_type": notification.notification_type,
            "audience": notification.audience,
            "title": notification.title,
            "message": notification.message,
            "is_active": notification.is_active,
            "created_at": notification.created_at.isoformat(),
            "created_by": creator.full_name if creator else f"Admin #{notification.created_by_admin_id}",
        })

    return {
        "summary": {
            "total": len(items),
            "active": sum(1 for item in items if item["is_active"]),
            "research": sum(1 for item in items if item["notification_type"] == "research_invitation"),
            "feature_updates": sum(1 for item in items if item["notification_type"] == "feature_update"),
        },
        "notifications": items,
    }


@router.post("/notifications")
def create_notification(admin_id: int, body: NotificationCreateBody, session: Session = Depends(get_session)):
    """Publish a new admin notification."""
    admin = _require_admin(admin_id, session)
    allowed_types = {"announcement", "feature_update", "research_invitation"}
    allowed_audiences = {"all", "patient", "doctor"}

    if body.notification_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid notification type")
    if body.audience not in allowed_audiences:
        raise HTTPException(status_code=400, detail="Invalid audience")
    if not body.title.strip() or not body.message.strip():
        raise HTTPException(status_code=400, detail="Title and message are required")

    notification = Notification(
        notification_type=body.notification_type,
        audience=body.audience,
        title=body.title.strip(),
        message=body.message.strip(),
        created_by_admin_id=admin_id,
    )
    session.add(notification)
    _create_audit_log(
        session,
        "admin",
        admin_id,
        admin.full_name,
        "notification_published",
        "admin",
        f"Admin published notification: {notification.title}",
        "notification",
        None,
        notification.title,
        f"Audience: {notification.audience}",
        {"type": notification.notification_type, "audience": notification.audience},
    )
    session.commit()
    session.refresh(notification)

    return {
        "message": "Notification published successfully",
        "notification_id": notification.id,
    }


@router.get("/research-exports/summary")
def get_research_export_summary(admin_id: int, session: Session = Depends(get_session)):
    _require_admin(admin_id, session)

    dataset_catalog = [
        ("cognitive_performance", "Cognitive Performance Dataset", "Training-session level scores, accuracy, difficulty shifts, and linked context."),
        ("fatigue", "Fatigue Dataset", "Fatigue and contextual variables correlated with task performance."),
        ("reaction_time", "Reaction Time Dataset", "Reaction-time focused export across tasks and domains for research analysis."),
        ("anonymized_patients", "Anonymized Patient Data", "Patient-level anonymized demographics and aggregated outcomes."),
    ]

    datasets = []
    for dataset_key, label, description in dataset_catalog:
        rows, summary = _build_research_dataset(session, dataset_key)
        datasets.append({
            "key": dataset_key,
            "label": label,
            "description": description,
            "record_count": summary["record_count"],
            "unique_patients": summary["unique_patients"],
            "date_range": summary["date_range"],
            "formats": ["csv", "json", "pdf"],
            "preview_fields": list(rows[0].keys())[:6] if rows else [],
        })

    return {
        "datasets": datasets,
        "summary": {
            "total_datasets": len(datasets),
            "total_records": sum(dataset["record_count"] for dataset in datasets),
            "generated_at": datetime.utcnow().isoformat(),
        },
    }


@router.get("/research-exports/download")
def download_research_export(
    admin_id: int,
    dataset: Literal["cognitive_performance", "fatigue", "reaction_time", "anonymized_patients"],
    file_format: Literal["csv", "json", "pdf"],
    session: Session = Depends(get_session),
):
    admin = _require_admin(admin_id, session)
    rows, summary = _build_research_dataset(session, dataset)

    dataset_title_map = {
        "cognitive_performance": "Cognitive Performance Dataset",
        "fatigue": "Fatigue Dataset",
        "reaction_time": "Reaction Time Dataset",
        "anonymized_patients": "Anonymized Patient Dataset",
    }
    dataset_title = dataset_title_map[dataset]
    date_stamp = datetime.utcnow().strftime("%Y-%m-%d")
    filename_base = f"neurobloom-{dataset.replace('_', '-')}-{date_stamp}"

    if file_format == "csv":
        payload = _serialize_csv(rows)
        media_type = "text/csv"
        file_extension = "csv"
    elif file_format == "json":
        payload = _serialize_json(summary, rows)
        media_type = "application/json"
        file_extension = "json"
    else:
        payload = _serialize_pdf(dataset_title, summary, rows)
        media_type = "application/pdf"
        file_extension = "pdf"

    _create_audit_log(
        session,
        "admin",
        admin_id,
        admin.full_name,
        "research_export_downloaded",
        "admin",
        f"Admin exported {dataset_title}",
        "research_export",
        None,
        dataset_title,
        f"Format: {file_format.upper()}",
        {"dataset": dataset, "format": file_format, "records": summary["record_count"]},
    )
    session.commit()

    return StreamingResponse(
        io.BytesIO(payload),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename_base}.{file_extension}"'
        },
    )
