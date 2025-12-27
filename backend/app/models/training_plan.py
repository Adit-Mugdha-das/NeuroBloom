from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional, ClassVar
import json

class TrainingPlan(SQLModel, table=True):
    """
    Stores personalized training plan generated from baseline assessment.
    Identifies focus areas and recommended tasks per domain.
    """
    __tablename__: ClassVar[str] = "training_plans"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    baseline_assessment_id: int = Field(foreign_key="baseline_assessments.id")
    
    # Focus areas (JSON array of domain names)
    primary_focus: str = Field(default="[]")  # 2 weakest domains
    secondary_focus: str = Field(default="[]")  # 2 middle domains
    maintenance: str = Field(default="[]")  # 2 strongest domains
    
    # Recommended tasks per domain (JSON mapping)
    recommended_tasks: str = Field(default="{}")
    
    # Initial difficulty levels per domain (JSON mapping)
    initial_difficulty: str = Field(default="{}")
    
    # Current difficulty levels (updated as user trains)
    current_difficulty: str = Field(default="{}")
    
    # Plan metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    
    # Progress tracking
    total_sessions_completed: int = Field(default=0)
    last_session_date: Optional[datetime] = Field(default=None)
    
    # Current session tracking
    current_session_number: int = Field(default=1)
    current_session_tasks_completed: str = Field(default="[]")  # JSON array of completed task domains
    
    def get_primary_focus(self):
        """Parse primary focus domains from JSON"""
        return json.loads(self.primary_focus)
    
    def get_secondary_focus(self):
        """Parse secondary focus domains from JSON"""
        return json.loads(self.secondary_focus)
    
    def get_maintenance(self):
        """Parse maintenance domains from JSON"""
        return json.loads(self.maintenance)
    
    def get_recommended_tasks(self):
        """Parse recommended tasks from JSON"""
        return json.loads(self.recommended_tasks)
    
    def get_initial_difficulty(self):
        """Parse initial difficulty from JSON"""
        return json.loads(self.initial_difficulty)
    
    def get_current_difficulty(self):
        """Parse current difficulty from JSON"""
        return json.loads(self.current_difficulty)
    
    def get_current_session_tasks_completed(self):
        """Parse current session completed tasks from JSON"""
        return json.loads(self.current_session_tasks_completed)
