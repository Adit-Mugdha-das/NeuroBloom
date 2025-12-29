"""Seed PASAT task to database."""

from sqlmodel import Session, select
from app.core.config import engine
from app.models.cognitive_task import CognitiveTask

with Session(engine) as session:
    # Check if PASAT task already exists
    existing = session.exec(
        select(CognitiveTask).where(CognitiveTask.task_code == 'PASAT')
    ).first()
    
    if not existing:
        task = CognitiveTask(
            task_code='PASAT',
            task_name='Paced Auditory Serial Addition Test',
            domain='attention',
            description='Add each new digit to the previous digit - MS gold standard attention test',
            clinical_validation='Gronwall, 1977 - Most widely used MS cognitive test, measures sustained attention + working memory',
            is_baseline_task=False,
            difficulty_min=1,
            difficulty_max=10,
            estimated_duration_seconds=240,  # 4 minutes average
            requires_audio=False,  # Visual mode available
            requires_keyboard=True,
            cognitive_load='high',
            instructions='Add each new digit to the previous digit, ignore running total'
        )
        session.add(task)
        session.commit()
        print('✅ PASAT task added successfully!')
        print(f'Task ID: {task.id}')
    else:
        print('ℹ️ PASAT task already exists')
        print(f'Task ID: {existing.id}')
