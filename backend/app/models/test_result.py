from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class TestResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    task_type: str  # "memory", "attention", "speed", "executive"
    score: float  # percentage or points
    details: Optional[str] = None  # JSON string with additional data
    created_at: datetime = Field(default_factory=datetime.utcnow)
