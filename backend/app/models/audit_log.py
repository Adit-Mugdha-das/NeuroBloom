from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class AuditLog(SQLModel, table=True):
    """Persistent system audit records for traceability and compliance."""
    __tablename__ = "audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    actor_type: str = Field(index=True)
    actor_id: Optional[int] = Field(default=None, index=True)
    actor_name: str
    action_type: str = Field(index=True)
    category: str = Field(index=True)
    target_type: Optional[str] = Field(default=None, index=True)
    target_id: Optional[int] = Field(default=None, index=True)
    target_name: Optional[str] = Field(default=None)
    summary: str
    detail: Optional[str] = Field(default=None)
    metadata_json: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)