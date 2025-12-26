from pydantic import BaseModel
from datetime import datetime

class TestResultCreate(BaseModel):
    task_type: str
    score: float
    details: str = None

class TestResultRead(BaseModel):
    id: int
    user_id: int
    task_type: str
    score: float
    details: str = None
    created_at: datetime
    
    class Config:
        from_attributes = True
