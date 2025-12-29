"""
Seed script to add Trail Making Test Part A to the cognitive_tasks table
"""

import sys
sys.path.append('.')

from sqlmodel import Session, select
from app.core.config import engine
from app.models.cognitive_task import CognitiveTask

def seed_trail_making_a():
    """Add Trail Making Test Part A to the database"""
    
    with Session(engine) as session:
        # Check if task already exists
        existing = session.exec(
            select(CognitiveTask).where(CognitiveTask.task_code == "trail_making_a")
        ).first()
        
        if existing:
            print("Trail Making Test Part A already exists in database")
            return
        
        # Create new task
        trail_making_a_task = CognitiveTask(
            task_code="trail_making_a",
            domain="processing_speed",
            task_name="Trail Making Test - Part A",
            description="Connect numbered circles in sequence (1→2→3...→25) as fast as possible. Classic neuropsychological test from the Halstead-Reitan Battery measuring psychomotor speed, visual scanning, and motor coordination. Highly sensitive to MS progression.",
            clinical_validation="Halstead-Reitan Battery - Gold standard neuropsychological test. Highly sensitive to MS progression and psychomotor speed deficits. Performance based on completion time normalized to 25 circles: <29s=Excellent, 29-39s=Good, 40-78s=Average, >78s=Needs Practice.",
            instructions="You will see circles with numbers scattered across the screen. Click them in numerical order (1→2→3...→25) as quickly and accurately as possible. The test tracks your time, errors, and path efficiency. Try to move smoothly between circles and scan ahead to plan your path.",
            is_baseline_task=False,
            difficulty_min=1,
            difficulty_max=10,
            estimated_duration_seconds=90,
            requires_audio=False,
            requires_keyboard=False,
            cognitive_load="medium"
        )
        
        session.add(trail_making_a_task)
        session.commit()
        session.refresh(trail_making_a_task)
        
        print(f"✅ Successfully added Trail Making Test Part A (ID: {trail_making_a_task.id})")
        print(f"   Domain: {trail_making_a_task.domain}")
        print(f"   Task Code: {trail_making_a_task.task_code}")
        print(f"   Task Name: {trail_making_a_task.task_name}")
        print(f"   Difficulty Range: {trail_making_a_task.difficulty_min}-{trail_making_a_task.difficulty_max}")

if __name__ == "__main__":
    print("Seeding Trail Making Test Part A...")
    seed_trail_making_a()
    print("Done!")
