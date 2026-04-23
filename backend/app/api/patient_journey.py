from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.config import engine
from app.services.patient_journey import build_patient_journey

router = APIRouter()


def get_session():
    with Session(engine) as session:
        yield session


@router.get("/{user_id}")
def get_patient_journey(user_id: int, session: Session = Depends(get_session)):
    journey = build_patient_journey(session, user_id)
    if not journey.get("user_exists"):
        raise HTTPException(status_code=404, detail=journey.get("blocking_reason", "User not found"))
    return journey
