from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class RiskAlert(SQLModel, table=True):
	__tablename__ = "risk_alerts"  # type: ignore[assignment]

	id: Optional[int] = Field(default=None, primary_key=True)
	patient_id: int = Field(foreign_key="user.id", index=True, unique=True)
	assigned_doctor_id: Optional[int] = Field(default=None, foreign_key="doctors.id", index=True)
	risk_score: int = Field(default=0)
	risk_level: str = Field(default="high", max_length=20)
	alert_summary: str = Field(default="High risk patient")
	risk_reasons_json: str = Field(default="[]")
	status: str = Field(default="open", max_length=20)
	doctor_notified_at: Optional[datetime] = Field(default=None)
	escalated_at: Optional[datetime] = Field(default=None)
	reviewed_at: Optional[datetime] = Field(default=None)
	reviewed_by_admin_id: Optional[int] = Field(default=None, foreign_key="admins.id")
	created_at: datetime = Field(default_factory=datetime.utcnow)
	updated_at: datetime = Field(default_factory=datetime.utcnow)