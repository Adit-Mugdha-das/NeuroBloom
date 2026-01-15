from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone

class ProgressReport(SQLModel, table=True):
    """
    Auto-generated progress reports for patients.
    Stores weekly/monthly aggregated performance data.
    """
    __tablename__ = "progress_reports"  # type: ignore
    
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="user.id", index=True)
    doctor_id: int = Field(foreign_key="doctors.id", index=True)
    
    # Report period
    period_type: str = Field(index=True)  # "weekly" or "monthly"
    period_start: datetime = Field(index=True)
    period_end: datetime = Field(index=True)
    
    # Aggregated data (stored as JSON)
    report_data: str = Field(default="{}")  # JSON with performance metrics, trends, etc.
    
    # Doctor notes
    doctor_commentary: Optional[str] = None
    
    # Timestamps
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
