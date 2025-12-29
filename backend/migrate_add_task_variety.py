"""
Database migration to add task variety system
Adds cognitive_tasks table and task rotation tracking
"""

from sqlmodel import Session, select, create_engine, text
from app.core.config import settings
from app.models.user import User
from app.models.training_plan import TrainingPlan
import json

# Database connection
engine = create_engine(str(settings.DATABASE_URL))

def add_task_variety_columns():
    """Add task_code column to existing tables and create new tables"""
    from sqlmodel import SQLModel
    
    # Create ALL tables defined in models (including TrainingSession with task_code)
    SQLModel.metadata.create_all(engine)
    
    print("✓ All database tables created/updated")

def seed_task_definitions():
    """Create task definitions in database"""
    
    from app.models.cognitive_task import CognitiveTask
    
    with Session(engine) as session:
        
        # Insert baseline tasks (original 6)
        baseline_tasks = [
            {
                'task_code': 'n_back',
                'domain': 'working_memory',
                'task_name': 'N-Back Test',
                'description': 'Remember if current item matches item N steps back',
                'clinical_validation': 'Widely used working memory test (Kirchner, 1958)',
                'is_baseline_task': True,
                'difficulty_min': 1,
                'difficulty_max': 10,
                'estimated_duration_seconds': 120,
                'requires_audio': False,
                'requires_keyboard': True,
                'cognitive_load': 'high',
                'instructions': 'Numbers will appear one at a time. Press the button if the current number matches the one shown N positions ago.'
            },
            {
                'task_code': 'simple_reaction',
                'domain': 'processing_speed',
                'task_name': 'Simple Reaction Time',
                'description': 'Press button as fast as possible when stimulus appears',
                'clinical_validation': 'Basic processing speed measure',
                'is_baseline_task': True,
                'difficulty_min': 1,
                'difficulty_max': 10,
                'estimated_duration_seconds': 60,
                'requires_audio': False,
                'requires_keyboard': True,
                'cognitive_load': 'low',
                'instructions': 'Click or press the button as quickly as possible when the target appears.'
            },
            {
                'task_code': 'cpt',
                'domain': 'attention',
                'task_name': 'Continuous Performance Test',
                'description': 'Respond to target stimuli, ignore non-targets',
                'clinical_validation': 'Sustained attention standard (Rosvold et al., 1956)',
                'is_baseline_task': True,
                'difficulty_min': 1,
                'difficulty_max': 10,
                'estimated_duration_seconds': 180,
                'requires_audio': False,
                'requires_keyboard': True,
                'cognitive_load': 'medium',
                'instructions': 'Press the button when you see the target letter. Do not press for other letters.'
            },
            {
                'task_code': 'task_switching',
                'domain': 'flexibility',
                'task_name': 'Task Switching',
                'description': 'Switch between different task rules',
                'clinical_validation': 'Cognitive flexibility measure (Monsell, 2003)',
                'is_baseline_task': True,
                'difficulty_min': 1,
                'difficulty_max': 10,
                'estimated_duration_seconds': 150,
                'requires_audio': False,
                'requires_keyboard': True,
                'cognitive_load': 'high',
                'instructions': 'Follow the rule shown at the top. The rule will change during the task.'
            },
            {
                'task_code': 'tower_of_london',
                'domain': 'planning',
                'task_name': 'Tower of London',
                'description': 'Move disks to match target in minimum moves',
                'clinical_validation': 'Executive planning gold standard (Shallice, 1982)',
                'is_baseline_task': True,
                'difficulty_min': 1,
                'difficulty_max': 10,
                'estimated_duration_seconds': 180,
                'requires_audio': False,
                'requires_keyboard': True,
                'cognitive_load': 'high',
                'instructions': 'Move the colored disks to match the target configuration in as few moves as possible.'
            },
            {
                'task_code': 'visual_search',
                'domain': 'visual_scanning',
                'task_name': 'Visual Search',
                'description': 'Find target among distractors',
                'clinical_validation': 'Visual attention measure (Treisman & Gelade, 1980)',
                'is_baseline_task': True,
                'difficulty_min': 1,
                'difficulty_max': 10,
                'estimated_duration_seconds': 120,
                'requires_audio': False,
                'requires_keyboard': True,
                'cognitive_load': 'medium',
                'instructions': 'Find the target item among the distractors as quickly as possible.'
            }
        ]
        
        for task_data in baseline_tasks:
            # Check if task already exists
            existing = session.exec(
                select(CognitiveTask).where(CognitiveTask.task_code == task_data['task_code'])
            ).first()
            
            if not existing:
                task = CognitiveTask(**task_data)
                session.add(task)
        
        # Add Digit Span (our first new task!)
        digit_span_exists = session.exec(
            select(CognitiveTask).where(CognitiveTask.task_code == 'digit_span')
        ).first()
        
        if not digit_span_exists:
            digit_span = CognitiveTask(
                task_code='digit_span',
                domain='working_memory',
                task_name='Digit Span Test',
                description='Remember and repeat sequences of digits in forward or backward order',
                clinical_validation='WAIS-IV subtest, gold standard (Wechsler, 2008). Used in MACFIMS for MS patients',
                is_baseline_task=False,
                difficulty_min=1,
                difficulty_max=10,
                estimated_duration_seconds=90,
                requires_audio=True,
                requires_keyboard=True,
                cognitive_load='medium',
                instructions='Listen to or watch the sequence of digits. When prompted, type the digits in the correct order. Forward trials: type in same order. Backward trials: type in reverse order.'
            )
            session.add(digit_span)
        
        session.commit()
        print("✓ Task definitions seeded successfully")

def update_existing_sessions():
    """Update existing training sessions with task_code from task_type"""
    
    with Session(engine) as session:
        # First, add task_code column if it doesn't exist
        try:
            session.execute(text("""
                ALTER TABLE training_sessions 
                ADD COLUMN IF NOT EXISTS task_code VARCHAR(50)
            """))
            session.commit()
            print("✓ Added task_code column to training_sessions")
        except Exception as e:
            print(f"Note: task_code column may already exist: {e}")
        
        # Map old task_type to new task_code  
        task_mapping = {
            'n_back': 'n_back',
            'reaction_time': 'simple_reaction',
            'continuous_performance': 'cpt',
            'task_switching': 'task_switching',
            'tower_hanoi': 'tower_of_london',
            'visual_search': 'visual_search'
        }
        
        for old_type, new_code in task_mapping.items():
            session.execute(text("""
                UPDATE training_sessions 
                SET task_code = :new_code 
                WHERE task_type = :old_type AND (task_code IS NULL OR task_code = '')
            """), {'new_code': new_code, 'old_type': old_type})
        
        session.commit()
        print("✓ Existing sessions updated with task codes")

def verify_migration():
    """Verify migration was successful"""
    
    from app.models.cognitive_task import CognitiveTask
    
    with Session(engine) as session:
        # Check task count
        total_count = session.exec(select(CognitiveTask)).all()
        print(f"✓ Total tasks in database: {len(total_count)}")
        
        # Check baseline tasks
        baseline_count = session.exec(
            select(CognitiveTask).where(CognitiveTask.is_baseline_task == True)
        ).all()
        print(f"✓ Baseline tasks: {len(baseline_count)}")
        
        # Check new tasks
        variety_count = session.exec(
            select(CognitiveTask).where(CognitiveTask.is_baseline_task == False)
        ).all()
        print(f"✓ Training variety tasks: {len(variety_count)}")
        
        # List all tasks
        all_tasks = session.exec(
            select(CognitiveTask).order_by(CognitiveTask.domain, CognitiveTask.task_code)
        ).all()
        print("\n📋 All available tasks:")
        current_domain = None
        for task in all_tasks:
            if task.domain != current_domain:
                print(f"\n  {task.domain.upper().replace('_', ' ')}:")
                current_domain = task.domain
            baseline_marker = " [BASELINE]" if task.is_baseline_task else ""
            print(f"    • {task.task_code}: {task.task_name}{baseline_marker}")

if __name__ == "__main__":
    print("🔧 Starting task variety migration...\n")
    
    try:
        add_task_variety_columns()
        seed_task_definitions()
        update_existing_sessions()
        verify_migration()
        
        print("\n✅ Migration completed successfully!")
        print("\n📝 Next steps:")
        print("  1. Restart backend server")
        print("  2. Implement Digit Span frontend component")
        print("  3. Test task rotation system")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
