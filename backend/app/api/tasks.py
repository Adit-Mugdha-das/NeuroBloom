from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc
from typing import List
import random
import json
from datetime import datetime

from app.models.test_result import TestResult
from app.schemas.test_result import TestResultCreate, TestResultRead
from app.core.config import engine
from app.services.dccs_task import dccs_task_service
from app.services.plus_minus_task import plus_minus_task_service
from app.services.tol_task import tol_task_service
from app.services.soc_task import soc_task_service

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

# Word lists for memory test
WORD_LISTS = {
    "easy": ["apple", "chair", "ocean", "light", "music"],
    "medium": ["elephant", "mountain", "library", "garden", "window", "coffee", "sunset"],
    "hard": ["symphony", "telescope", "hurricane", "cathedral", "butterfly", "chemistry", "peninsula", "atmosphere", "democracy"]
}

@router.get("/memory/start")
def start_memory_test(difficulty: str = "medium"):
    """Generate a random word list for memory test"""
    if difficulty not in WORD_LISTS:
        difficulty = "medium"
    
    words = random.sample(WORD_LISTS[difficulty], min(5, len(WORD_LISTS[difficulty])))
    
    return {
        "words": words,
        "difficulty": difficulty,
        "count": len(words),
        "time_limit": 10  # seconds to memorize
    }

@router.post("/results", response_model=TestResultRead)
def submit_result(
    result: TestResultCreate, 
    user_id: int,
    session: Session = Depends(get_session)
):
    """Submit a test result"""
    test_result = TestResult(
        user_id=user_id,
        task_type=result.task_type,
        score=result.score,
        details=result.details
    )
    
    session.add(test_result)
    session.commit()
    session.refresh(test_result)
    
    return test_result

@router.get("/results/{user_id}", response_model=List[TestResultRead])
def get_user_results(user_id: int, session: Session = Depends(get_session)):
    """Get all test results for a user"""
    results = session.exec(
        select(TestResult)
        .where(TestResult.user_id == user_id)
        .order_by(desc(TestResult.created_at))
    ).all()
    
    return results

@router.get("/results/{user_id}/stats")
def get_user_stats(user_id: int, session: Session = Depends(get_session)):
    """Get user statistics"""
    results = session.exec(
        select(TestResult).where(TestResult.user_id == user_id)
    ).all()
    
    if not results:
        return {
            "total_sessions": 0,
            "average_score": 0,
            "tasks_by_type": {},
            "recent_scores": []
        }
    
    total = len(results)
    avg_score = sum(r.score for r in results) / total
    best_score = max(r.score for r in results)
    
    tasks_by_type = {}
    for result in results:
        if result.task_type not in tasks_by_type:
            tasks_by_type[result.task_type] = 0
        tasks_by_type[result.task_type] += 1
    
    recent = sorted(results, key=lambda x: x.created_at, reverse=True)[:10]
    recent_scores = [
        {
            "task_type": r.task_type,
            "score": r.score,
            "date": r.created_at.strftime("%Y-%m-%d %H:%M")
        }
        for r in recent
    ]
    
    return {
        "total_sessions": total,
        "average_score": round(avg_score, 2),
        "best_score": round(best_score, 2),
        "tasks_by_type": tasks_by_type,
        "recent_scores": recent_scores
    }

@router.get("/results/{user_id}/baseline-status")
def get_baseline_status(user_id: int, session: Session = Depends(get_session)):
    """Get baseline task completion status for a user"""
    # Define the 6 baseline tasks
    baseline_tasks = [
        "working_memory",
        "attention", 
        "flexibility",
        "planning",
        "processing_speed",
        "visual_scanning"
    ]
    
    # Get all results for this user
    results = session.exec(
        select(TestResult).where(TestResult.user_id == user_id)
    ).all()
    
    # Check which tasks have been completed
    completed_tasks = set(r.task_type for r in results)
    
    status = {}
    for task in baseline_tasks:
        status[task] = task in completed_tasks
    
    # Calculate overall completion
    completed_count = sum(1 for task in baseline_tasks if status[task])
    
    return {
        "tasks": status,
        "completed_count": completed_count,
        "total_tasks": len(baseline_tasks),
        "all_completed": completed_count == len(baseline_tasks)
    }


# DCCS Task endpoints
@router.post("/dccs/generate")
def generate_dccs_session(difficulty: int = 1):
    """
    Generate a new DCCS session
    
    Args:
        difficulty: Difficulty level 1-10
        
    Returns:
        Complete session configuration with all three phases
    """
    try:
        session_data = dccs_task_service.generate_session(difficulty)
        return session_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dccs/score")
def score_dccs_session(
    session_data: dict,
    user_responses: List[dict]
):
    """
    Score a completed DCCS session
    
    Args:
        session_data: Original session configuration
        user_responses: List of user responses with timing
        
    Returns:
        Detailed scoring including switch costs and perseverative errors
    """
    try:
        results = dccs_task_service.score_session(session_data, user_responses)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Plus-Minus Task endpoints
@router.post("/plus-minus/generate")
def generate_plus_minus_session(difficulty: int = 1):
    """
    Generate a new Plus-Minus session
    
    Args:
        difficulty: Difficulty level 1-10
        
    Returns:
        Complete session configuration with all three blocks
    """
    try:
        session_data = plus_minus_task_service.generate_session(difficulty)
        return session_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plus-minus/score")
def score_plus_minus_session(
    session_data: dict,
    user_responses: List[dict]
):
    """
    Score a completed Plus-Minus session
    
    Args:
        session_data: Original session configuration
        user_responses: List of user responses with timing
        
    Returns:
        Detailed scoring including switching cost
    """
    try:
        results = plus_minus_task_service.score_session(session_data, user_responses)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tol/generate")
def generate_tol_session(difficulty: int = 1):
    """
    Generate a Tower of London session
    
    Args:
        difficulty: Difficulty level 1-10
        
    Returns:
        Complete session with planning problems
    """
    try:
        session_data = tol_task_service.generate_session(difficulty)
        return session_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tol/score")
def score_tol_session(
    session_data: dict,
    user_solutions: List[dict]
):
    """
    Score a completed Tower of London session
    
    Args:
        session_data: Original session configuration
        user_solutions: List of user solutions with moves and timing
        
    Returns:
        Detailed scoring including planning efficiency
    """
    try:
        results = tol_task_service.score_session(session_data, user_solutions)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/soc/generate")
def generate_soc_session(difficulty: int = 1):
    """
    Generate a Stockings of Cambridge session
    
    Args:
        difficulty: Difficulty level 1-10
        
    Returns:
        Complete session with planning problems (balls in stockings)
    """
    try:
        session_data = soc_task_service.generate_session(difficulty)
        return session_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/soc/score")
def score_soc_session(
    session_data: dict,
    user_solutions: List[dict]
):
    """
    Score a completed Stockings of Cambridge session
    
    Args:
        session_data: Original session configuration
        user_solutions: List of user solutions with moves and timing
        
    Returns:
        Detailed scoring including planning efficiency
    """
    try:
        results = soc_task_service.score_session(session_data, user_solutions)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
