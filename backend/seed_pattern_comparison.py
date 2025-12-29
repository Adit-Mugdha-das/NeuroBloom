"""
Seed script to add Pattern Comparison task to the cognitive_tasks table
"""

import sys
sys.path.append('.')

from sqlmodel import Session, select
from app.core.config import engine
from app.models.cognitive_task import CognitiveTask

def seed_pattern_comparison():
    """Add Pattern Comparison (Visual Matching) to the database"""
    
    with Session(engine) as session:
        # Check if task already exists
        existing = session.exec(
            select(CognitiveTask).where(CognitiveTask.task_code == "pattern_comparison")
        ).first()
        
        if existing:
            print("Pattern Comparison already exists in database")
            return
        
        # Create new task
        pattern_comparison_task = CognitiveTask(
            task_code="pattern_comparison",
            domain="processing_speed",
            task_name="Pattern Comparison (Visual Matching)",
            description="Decide if two patterns are SAME or DIFFERENT as quickly as possible. From the Woodcock-Johnson Tests of Cognitive Abilities. Measures pure processing speed with minimal motor requirements - ideal for MS assessment.",
            clinical_validation="Woodcock-Johnson Tests of Cognitive Abilities - Validated measure of processing speed. Pure cognitive assessment with minimal physical demands. Performance norms: 35+ correct/min = Excellent, 25-34 = Good, 15-24 = Average, <15 = Practice needed (Salthouse, 1996).",
            instructions="You will see two patterns side by side. Your task is to decide as quickly and accurately as possible if they are SAME or DIFFERENT. Click the appropriate button. Speed and accuracy both count - try to be fast AND correct!",
            is_baseline_task=False,
            difficulty_min=1,
            difficulty_max=10,
            estimated_duration_seconds=120,
            requires_audio=False,
            requires_keyboard=False,
            cognitive_load="medium"
        )
        
        session.add(pattern_comparison_task)
        session.commit()
        session.refresh(pattern_comparison_task)
        
        print(f"✅ Successfully added Pattern Comparison (ID: {pattern_comparison_task.id})")
        print(f"   Domain: {pattern_comparison_task.domain}")
        print(f"   Task Code: {pattern_comparison_task.task_code}")
        print(f"   Task Name: {pattern_comparison_task.task_name}")
        print(f"   Difficulty Range: {pattern_comparison_task.difficulty_min}-{pattern_comparison_task.difficulty_max}")

if __name__ == "__main__":
    print("Seeding Pattern Comparison task...")
    seed_pattern_comparison()
    print("Done!")
