from app.models.cognitive_task import CognitiveTask
from app.core.config import engine
from sqlmodel import Session, select

with Session(engine) as session:
    # Check if sdmt already exists
    existing = session.exec(
        select(CognitiveTask).where(CognitiveTask.task_code == 'sdmt')
    ).first()
    
    if existing:
        print('✓ SDMT task already exists')
    else:
        # Add new task
        sdmt = CognitiveTask(
            task_code='sdmt',
            task_name='Symbol Digit Modalities Test',
            domain='processing_speed',
            description='⭐ GOLD STANDARD: Match symbols to digits using reference key - most sensitive MS cognitive test',
            instructions='Study the symbol-digit key, then type the matching number for each symbol as quickly as possible. 90 seconds.',
            clinical_validation='Most widely used in MS clinical trials. Predicts employment and daily functioning. Reference: Benedict et al., 2017',
            difficulty_min=1,
            difficulty_max=10,
            estimated_duration_seconds=90,
            cognitive_load='medium',
            requires_keyboard=True
        )
        
        session.add(sdmt)
        session.commit()
        session.refresh(sdmt)
        
        print(f'✓ Added SDMT task (ID: {sdmt.id})')
        print(f'  Domain: {sdmt.domain}')
        print(f'  Difficulty: {sdmt.difficulty_min}-{sdmt.difficulty_max}')
        print(f'  Duration: {sdmt.estimated_duration_seconds}s')
        print(f'  ⭐ GOLD STANDARD for MS cognitive assessment')
