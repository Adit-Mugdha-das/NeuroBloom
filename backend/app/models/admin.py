from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Admin(SQLModel, table=True):
    """Hospital Administrator model"""
    __tablename__ = "admins"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    full_name: str = Field(default="Hospital Administrator")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None)
