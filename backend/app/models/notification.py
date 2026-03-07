from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Notification(SQLModel, table=True):
    """Platform-wide admin notifications for doctors and patients."""
    __tablename__ = "notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    notification_type: str = Field(index=True)  # announcement | feature_update | research_invitation
    audience: str = Field(index=True)  # all | patient | doctor
    title: str = Field(max_length=160)
    message: str = Field(max_length=1000)
    created_by_admin_id: int = Field(foreign_key="admins.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    is_active: bool = Field(default=True, index=True)