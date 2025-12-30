"""
Seed Stroop Color-Word Test task to database
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sqlmodel import Session, create_engine, select
from app.models.cognitive_task import CognitiveTask
from app.core.config import settings
from datetime import datetime

# Create database engine
engine = create_engine(str(settings.DATABASE_URL), echo=True)

def seed_stroop_task():
    with Session(engine) as session:
        # Check if task already exists
        existing = session.exec(
            select(CognitiveTask).where(CognitiveTask.task_code == "STROOP")
        ).first()
        
        if existing:
            print("⚠️  Stroop task already exists in database")
            return
        
        # Create new task
        stroop_task = CognitiveTask(
            task_code="STROOP",
            domain="attention",
            task_name="Stroop Color-Word Test",
            description="Name ink color while ignoring word meaning - classic inhibitory control test",
            clinical_validation="Stroop, 1935; Parmenter et al., 2007 - Classic attention and executive function assessment",
            is_baseline_task=False,
            difficulty_min=1,
            difficulty_max=10,
            estimated_duration_seconds=180,  # ~3 minutes
            requires_audio=False,
            requires_keyboard=False,  # Click-based
            cognitive_load="high",
            instructions="Click the button matching the INK COLOR, ignore what the word says",
            created_at=datetime.utcnow()
        )
        
        session.add(stroop_task)
        session.commit()
        session.refresh(stroop_task)
        
        print("✅ Stroop Color-Word Test task added successfully!")
        print(f"Task ID: {stroop_task.id}")

if __name__ == "__main__":
    seed_stroop_task()
