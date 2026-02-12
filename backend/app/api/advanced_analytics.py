"""
Advanced Analytics API Endpoints
Phase 1: MS Research Enhancement

Provides endpoints for:
1. Pre-task questionnaires (session context)
2. Advanced analytics (fatigue, IIV, trends)
3. Digital biomarkers extraction
4. Longitudinal analysis with contextual correlations

Add these to your training router by importing this module.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, col
from typing import Optional
import json
from datetime import datetime, timedelta

from app.models.training_session import TrainingSession
from app.models.session_context import SessionContext
from app.core.config import engine
from app.core.advanced_analytics import (
    analyze_session_advanced,
    generate_longitudinal_report
)


router = APIRouter(prefix="/api/training", tags=["advanced-analytics"])


def get_session():
    with Session(engine) as session:
        yield session


# ==================== SESSION CONTEXT ENDPOINTS ====================

@router.post("/session-context")
def create_session_context(
    user_id: int,
    fatigue_level: Optional[int] = None,
    sleep_quality: Optional[int] = None,
    sleep_hours: Optional[float] = None,
    medication_taken_today: Optional[bool] = None,
    hours_since_medication: Optional[float] = None,
    pain_level: Optional[int] = None,
    stress_level: Optional[int] = None,
    time_of_day: Optional[str] = None,
    readiness_level: Optional[int] = None,
    notes: Optional[str] = None,
    distractions_present: Optional[bool] = None,
    location: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Store pre-task questionnaire data for MS research.
    
    Called BEFORE starting a cognitive task to capture contextual factors.
    Enables correlation analysis: performance vs fatigue, sleep, medication timing, etc.
    
    Returns the context_id to link with subsequent training session.
    """
    # Determine time_of_day if not provided
    if not time_of_day:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            time_of_day = 'morning'
        elif 12 <= hour < 17:
            time_of_day = 'afternoon'
        elif 17 <= hour < 21:
            time_of_day = 'evening'
        else:
            time_of_day = 'night'
    
    context = SessionContext(
        user_id=user_id,
        fatigue_level=fatigue_level,
        sleep_quality=sleep_quality,
        sleep_hours=sleep_hours,
        medication_taken_today=medication_taken_today,
        hours_since_medication=hours_since_medication,
        pain_level=pain_level,
        stress_level=stress_level,
        time_of_day=time_of_day,
        readiness_level=readiness_level,
        notes=notes,
        distractions_present=distractions_present,
        location=location
    )
    
    session.add(context)
    session.commit()
    session.refresh(context)
    
    return {
        "context_id": context.id,
        "message": "Pre-task context recorded successfully",
        "time_of_day": time_of_day
    }


@router.get("/session-context/{user_id}/recent")
def get_recent_context(
    user_id: int,
    limit: int = 10,
    session: Session = Depends(get_session)
):
    """Get recent pre-task questionnaire responses for a user"""
    contexts = session.exec(
        select(SessionContext)
        .where(SessionContext.user_id == user_id)
        .order_by(col(SessionContext.created_at).desc())
        .limit(limit)
    ).all()
    
    return {
        "contexts": [
            {
                "id": c.id,
                "created_at": c.created_at,
                "fatigue_level": c.fatigue_level,
                "sleep_quality": c.sleep_quality,
                "sleep_hours": c.sleep_hours,
                "medication_taken_today": c.medication_taken_today,
                "hours_since_medication": c.hours_since_medication,
                "pain_level": c.pain_level,
                "stress_level": c.stress_level,
                "time_of_day": c.time_of_day,
                "readiness_level": c.readiness_level,
                "notes": c.notes,
                "distractions_present": c.distractions_present,
                "location": c.location
            }
            for c in contexts
        ]
    }


@router.patch("/training-session/{session_id}/link-context")
def link_context_to_session(
    session_id: int,
    context_id: int,
    session: Session = Depends(get_session)
):
    """Link a session context to a completed training session"""
    training_session = session.get(TrainingSession, session_id)
    if not training_session:
        raise HTTPException(status_code=404, detail="Training session not found")
    
    context = session.get(SessionContext, context_id)
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    # Link them
    context.training_session_id = session_id
    session.add(context)
    session.commit()
    
    return {"message": "Context linked to session successfully"}


# ==================== ADVANCED ANALYTICS ENDPOINTS ====================

@router.get("/advanced-analytics/{user_id}/session/{session_id}")
def get_session_advanced_analytics(
    user_id: int,
    session_id: int,
    session: Session = Depends(get_session)
):
    """
    Get advanced analytics for a single session including:
    - Fatigue signature
    - IIV metrics (RT variability, CV)
    - Contextual factors
    
    For MS research and doctor portal.
    """
    # Get training session
    training_session = session.get(TrainingSession, session_id)
    if not training_session or training_session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get context if available
    context = session.exec(
        select(SessionContext)
        .where(SessionContext.training_session_id == session_id)
    ).first()
    
    # Parse raw data
    raw_data = json.loads(training_session.raw_data) if training_session.raw_data else {}
    
    # Build session data for analysis
    session_data = {
        'trials': raw_data.get('trials', []),
        'score': training_session.score,
        'mean_rt': training_session.average_reaction_time,
        'accuracy': training_session.accuracy,
        'context': {
            'fatigue_level': context.fatigue_level if context else None,
            'sleep_quality': context.sleep_quality if context else None,
            'medication_taken': context.medication_taken_today if context else None,
            'hours_since_medication': context.hours_since_medication if context else None,
            'time_of_day': context.time_of_day if context else None
        } if context else {}
    }
    
    # Run advanced analysis
    analytics = analyze_session_advanced(session_data)
    
    return {
        "session_id": session_id,
        "user_id": user_id,
        "domain": training_session.domain,
        "task_type": training_session.task_type,
        "date": training_session.created_at,
        "analytics": analytics
    }


@router.get("/advanced-analytics/{user_id}/longitudinal")
def get_longitudinal_analytics(
    user_id: int,
    days: int = 30,
    domain: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Get comprehensive longitudinal analysis including:
    - EWMA trends
    - Within-person variability
    - Contextual correlations
    - Digital biomarkers (fatigue index, CV)
    
    Perfect for doctor portal and research analysis.
    """
    # Get sessions from last N days
    since_date = datetime.utcnow() - timedelta(days=days)
    
    query = select(TrainingSession).where(
        TrainingSession.user_id == user_id,
        TrainingSession.created_at >= since_date
    )
    
    if domain:
        query = query.where(TrainingSession.domain == domain)
    
    training_sessions = session.exec(
        query.order_by(col(TrainingSession.created_at).asc())
    ).all()
    
    if not training_sessions:
        return {
            "error": "No sessions found",
            "user_id": user_id,
            "days": days,
            "domain": domain
        }
    
    # Get contexts for these sessions
    session_ids = [ts.id for ts in training_sessions]
    contexts = session.exec(
        select(SessionContext)
        .where(col(SessionContext.training_session_id).in_(session_ids))
    ).all()
    
    # Create context lookup
    context_map = {c.training_session_id: c for c in contexts}
    
    # Build session data with advanced metrics
    sessions_data = []
    
    for ts in training_sessions:
        context = context_map.get(ts.id)
        raw_data = json.loads(ts.raw_data) if ts.raw_data else {}
        
        # Analyze this session
        session_analysis = analyze_session_advanced({
            'trials': raw_data.get('trials', []),
            'score': ts.score,
            'mean_rt': ts.average_reaction_time,
            'accuracy': ts.accuracy
        })
        
        sessions_data.append({
            'session_id': ts.id,
            'date': ts.created_at.isoformat(),
            'score': ts.score,
            'mean_rt': ts.average_reaction_time,
            'accuracy': ts.accuracy,
            'domain': ts.domain,
            'task_type': ts.task_type,
            'fatigue_metrics': session_analysis['fatigue_metrics'],
            'iiv_metrics': session_analysis['iiv_metrics'],
            # Contextual factors
            'fatigue_level': context.fatigue_level if context else None,
            'sleep_quality': context.sleep_quality if context else None,
            'hours_since_medication': context.hours_since_medication if context else None,
            'pain_level': context.pain_level if context else None,
            'stress_level': context.stress_level if context else None,
            'time_of_day': context.time_of_day if context else None
        })
    
    # Generate comprehensive report
    report = generate_longitudinal_report(sessions_data, include_context_correlation=True)
    
    return {
        "user_id": user_id,
        "analysis_period": {
            "days": days,
            "start_date": since_date.isoformat(),
            "end_date": datetime.utcnow().isoformat()
        },
        "domain_filter": domain,
        "report": report
    }


@router.get("/advanced-analytics/{user_id}/biomarkers")
def get_digital_biomarkers(
    user_id: int,
    days: int = 30,
    session: Session = Depends(get_session)
):
    """
    Extract digital biomarkers for MS research.
    
    Returns key metrics:
    - Average fatigue index
    - Average CV (coefficient of variation)
    - Trend direction (improving/declining/stable)
    - RCI (reliable change index)
    - Contextual correlations
    
    For clinical research and publications.
    """
    # Get longitudinal data
    longitudinal_data = get_longitudinal_analytics(
        user_id=user_id,
        days=days,
        session=session
    )
    
    if 'error' in longitudinal_data:
        return longitudinal_data
    
    report = longitudinal_data['report']
    
    # Extract key biomarkers
    biomarkers = {
        "user_id": user_id,
        "assessment_period_days": days,
        "total_sessions": report['summary']['total_sessions'],
        
        # Primary biomarkers
        "fatigue_index": {
            "mean": report['biomarkers']['average_fatigue_index'],
            "interpretation": "High" if report['biomarkers']['average_fatigue_index'] > 0.5 else 
                            "Moderate" if report['biomarkers']['average_fatigue_index'] > 0.3 else "Low"
        },
        
        "rt_coefficient_of_variation": {
            "mean": report['biomarkers']['average_cv'],
            "interpretation": "High variability" if report['biomarkers']['average_cv'] > 0.35 else
                            "Moderate variability" if report['biomarkers']['average_cv'] > 0.25 else "Normal"
        },
        
        "reliable_change_index": {
            "value": report['biomarkers']['rci'],
            "interpretation": "Significant improvement" if report['biomarkers']['rci'] > 1.96 else
                            "Significant decline" if report['biomarkers']['rci'] < -1.96 else "Stable"
        },
        
        # Trends
        "performance_trend": {
            "direction": report['trends']['score_trend']['trend_direction'],
            "strength": report['trends']['score_trend']['trend_strength'],
            "current_ewma": report['trends']['score_trend']['current_ewma']
        },
        
        "rt_trend": {
            "direction": report['trends']['rt_trend']['trend_direction'],
            "strength": report['trends']['rt_trend']['trend_strength'],
            "current_ewma": report['trends']['rt_trend']['current_ewma']
        },
        
        # Contextual correlations
        "fatigue_correlation": report.get('contextual_analysis', {}).get('fatigue_level', {}),
        "sleep_correlation": report.get('contextual_analysis', {}).get('sleep_quality', {}),
        "medication_timing_correlation": report.get('contextual_analysis', {}).get('hours_since_medication', {})
    }
    
    return biomarkers
