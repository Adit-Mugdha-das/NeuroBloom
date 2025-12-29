from app.models.cognitive_task import CognitiveTask
from app.core.config import engine
from sqlmodel import Session, select

with Session(engine) as session:
    # Check if operation_span already exists
    existing = session.exec(
        select(CognitiveTask).where(CognitiveTask.task_code == 'operation_span')
    ).first()
    
    if existing:
        print('✓ Operation Span task already exists')
    else:
        # Add new task
        operation_span = CognitiveTask(
            task_code='operation_span',
            task_name='Operation Span',
            domain='working_memory',
            description='Remember letters while verifying math equations (dual-task)',
            instructions='Verify if each equation is correct, then remember the letter shown. At the end, recall all letters in order.',
            difficulty_min=1,
            difficulty_max=10,
            estimated_duration_seconds=180,
            cognitive_load='high'
        )
        
        session.add(operation_span)
        session.commit()
        session.refresh(operation_span)
        
        print(f'✓ Added Operation Span task (ID: {operation_span.id})')
        print(f'  Domain: {operation_span.domain}')
        print(f'  Difficulty: {operation_span.difficulty_min}-{operation_span.difficulty_max}')
        print(f'  Duration: {operation_span.estimated_duration_seconds}s')
