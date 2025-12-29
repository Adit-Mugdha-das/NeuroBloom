"""Seed Inspection Time task to database."""

from sqlmodel import Session, select
from app.core.config import engine
from app.models.cognitive_task import CognitiveTask

with Session(engine) as session:
    # Check if inspection time task already exists
    existing = session.exec(
        select(CognitiveTask).where(CognitiveTask.task_code == 'IT')
    ).first()
    
    if not existing:
        task = CognitiveTask(
            task_code='IT',
            task_name='Inspection Time',
            domain='processing_speed',
            description='Measures pure perceptual processing speed through brief visual presentations',
            clinical_validation='Vickers & Smith, 1986 - Cognitive aging research, perceptual speed assessment',
            is_baseline_task=False,
            difficulty_min=1,
            difficulty_max=10,
            estimated_duration_seconds=480,  # 8 minutes
            requires_audio=False,
            requires_keyboard=True,
            cognitive_load='low',
            instructions='View two lines briefly, then indicate which was longer'
        )
        session.add(task)
        session.commit()
        print('✅ Inspection Time task added successfully!')
        print(f'Task ID: {task.id}')
    else:
        print('ℹ️ Inspection Time task already exists')
        print(f'Task ID: {existing.id}')
