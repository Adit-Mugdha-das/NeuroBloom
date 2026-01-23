from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
import json

from app.models.baseline_assessment import BaselineAssessment
from app.models.test_result import TestResult
from app.schemas.baseline_assessment import BaselineAssessmentCreate, BaselineAssessmentRead
from app.core.config import engine
from app.core.scoring import (
    calculate_working_memory_score,
    calculate_attention_score,
    calculate_flexibility_score,
    calculate_planning_score,
    calculate_processing_speed_score,
    calculate_visual_scanning_score,
    calculate_overall_score
)

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session


@router.post("/calculate", response_model=BaselineAssessmentRead)
def calculate_baseline(user_id: int, session: Session = Depends(get_session)):
    """
    Calculate baseline assessment from test results
    Aggregates all 6 domain tests and creates baseline profile
    """
    # Get all test results for user
    results = session.exec(
        select(TestResult).where(TestResult.user_id == user_id)
    ).all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No test results found")
    
    # Organize by task type
    domain_data = {}
    for result in results:
        task_type = result.task_type
        if task_type not in domain_data:
            domain_data[task_type] = []
        
        # Parse details if JSON string
        details = result.details
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except:
                details = {}
        
        domain_data[task_type].append({
            'score': result.score,
            'details': details,
            'created_at': result.created_at.isoformat() if result.created_at else None
        })
    
    # Calculate domain scores
    domain_scores = {}
    
    # Working Memory
    if 'working_memory' in domain_data:
        latest = domain_data['working_memory'][-1]
        metrics = latest['details']
        domain_scores['working_memory'] = calculate_working_memory_score(metrics)
    
    # Attention
    if 'attention' in domain_data:
        latest = domain_data['attention'][-1]
        metrics = latest['details']
        domain_scores['attention'] = calculate_attention_score(metrics)
    
    # Flexibility
    if 'flexibility' in domain_data:
        latest = domain_data['flexibility'][-1]
        metrics = latest['details']
        domain_scores['flexibility'] = calculate_flexibility_score(metrics)
    
    # Planning
    if 'planning' in domain_data:
        latest = domain_data['planning'][-1]
        metrics = latest['details']
        domain_scores['planning'] = calculate_planning_score(metrics)
    
    # Processing Speed
    if 'processing_speed' in domain_data:
        latest = domain_data['processing_speed'][-1]
        metrics = latest['details']
        domain_scores['processing_speed'] = calculate_processing_speed_score(metrics)
    
    # Visual Scanning
    if 'visual_scanning' in domain_data:
        latest = domain_data['visual_scanning'][-1]
        metrics = latest['details']
        domain_scores['visual_scanning'] = calculate_visual_scanning_score(metrics)
    
    # Calculate overall score
    overall = calculate_overall_score(domain_scores)
    
    # Check if baseline already exists
    existing = session.exec(
        select(BaselineAssessment)
        .where(BaselineAssessment.user_id == user_id)
        .where(BaselineAssessment.is_baseline == True)
    ).first()
    
    if existing:
        # Update existing baseline
        from datetime import datetime
        existing.working_memory_score = domain_scores.get('working_memory', 0)
        existing.attention_score = domain_scores.get('attention', 0)
        existing.flexibility_score = domain_scores.get('flexibility', 0)
        existing.planning_score = domain_scores.get('planning', 0)
        existing.processing_speed_score = domain_scores.get('processing_speed', 0)
        existing.visual_scanning_score = domain_scores.get('visual_scanning', 0)
        existing.overall_score = overall
        existing.raw_metrics = json.dumps(domain_data)
        existing.assessment_date = datetime.now()  # Update assessment date
        
        session.add(existing)
        session.commit()
        session.refresh(existing)
        
        # AUTO-GENERATE TRAINING PLAN after baseline update
        try:
            from app.api.training import generate_training_plan
            generate_training_plan(user_id, session)
        except Exception as e:
            # Log but don't fail baseline update if training plan fails
            print(f"Warning: Could not auto-generate training plan: {e}")
        
        return existing
    else:
        # Create new baseline
        baseline = BaselineAssessment(
            user_id=user_id,
            working_memory_score=domain_scores.get('working_memory', 0),
            attention_score=domain_scores.get('attention', 0),
            flexibility_score=domain_scores.get('flexibility', 0),
            planning_score=domain_scores.get('planning', 0),
            processing_speed_score=domain_scores.get('processing_speed', 0),
            visual_scanning_score=domain_scores.get('visual_scanning', 0),
            overall_score=overall,
            raw_metrics=json.dumps(domain_data),
            is_baseline=True
        )
        
        session.add(baseline)
        session.commit()
        session.refresh(baseline)
        
        # AUTO-GENERATE TRAINING PLAN after baseline creation
        try:
            from app.api.training import generate_training_plan
            generate_training_plan(user_id, session)
        except Exception as e:
            # Log but don't fail baseline creation if training plan fails
            print(f"Warning: Could not auto-generate training plan: {e}")
        
        return baseline


@router.get("/{user_id}", response_model=BaselineAssessmentRead)
def get_baseline(user_id: int, session: Session = Depends(get_session)):
    """Get user's baseline assessment"""
    baseline = session.exec(
        select(BaselineAssessment)
        .where(BaselineAssessment.user_id == user_id)
        .where(BaselineAssessment.is_baseline == True)
    ).first()
    
    if not baseline:
        raise HTTPException(status_code=404, detail="No baseline assessment found")
    
    return baseline
