from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc
from typing import List
import random
import json
from datetime import datetime

from app.models.test_result import TestResult
from app.schemas.test_result import TestResultCreate, TestResultRead
from app.core.config import engine

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
        "tasks_by_type": tasks_by_type,
        "recent_scores": recent_scores
    }
