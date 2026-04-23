"""
Migration script to add missing columns to baseline_assessments table
"""
from sqlalchemy import text

from app.core.config import engine

def add_missing_columns():
    """Add is_baseline and assessment_duration_minutes columns if they don't exist"""
    
    with engine.connect() as conn:
        # Check if is_baseline column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'baseline_assessments'
        """))
        
        existing_columns = [row[0] for row in result]
        print(f"Existing columns: {existing_columns}")
        
        # Add is_baseline if missing
        if 'is_baseline' not in existing_columns:
            print("Adding is_baseline column...")
            conn.execute(text("""
                ALTER TABLE baseline_assessments 
                ADD COLUMN is_baseline BOOLEAN DEFAULT true
            """))
            conn.commit()
            print("✅ Added is_baseline column")
        else:
            print("✅ is_baseline column already exists")
        
        # Add assessment_duration_minutes if missing
        if 'assessment_duration_minutes' not in existing_columns:
            print("Adding assessment_duration_minutes column...")
            conn.execute(text("""
                ALTER TABLE baseline_assessments 
                ADD COLUMN assessment_duration_minutes INTEGER DEFAULT 0
            """))
            conn.commit()
            print("✅ Added assessment_duration_minutes column")
        else:
            print("✅ assessment_duration_minutes column already exists")
        
        # Add created_at if missing
        if 'created_at' not in existing_columns:
            print("Adding created_at column...")
            conn.execute(text("""
                ALTER TABLE baseline_assessments 
                ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """))
            conn.commit()
            print("✅ Added created_at column")
        else:
            print("✅ created_at column already exists")

def add_training_plan_session_tracking():
    """Add session tracking columns to training_plans table"""
    
    with engine.connect() as conn:
        # Check existing columns in training_plans
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'training_plans'
        """))
        
        existing_columns = [row[0] for row in result]
        print(f"Training plans columns: {existing_columns}")
        
        # Add current_session_number if missing
        if 'current_session_number' not in existing_columns:
            print("Adding current_session_number column...")
            conn.execute(text("""
                ALTER TABLE training_plans 
                ADD COLUMN current_session_number INTEGER DEFAULT 1
            """))
            conn.commit()
            print("✅ Added current_session_number column")
        else:
            print("✅ current_session_number column already exists")
        
        # Add current_session_tasks_completed if missing
        if 'current_session_tasks_completed' not in existing_columns:
            print("Adding current_session_tasks_completed column...")
            conn.execute(text("""
                ALTER TABLE training_plans 
                ADD COLUMN current_session_tasks_completed TEXT DEFAULT '[]'
            """))
            conn.commit()
            print("✅ Added current_session_tasks_completed column")
        else:
            print("✅ current_session_tasks_completed column already exists")

if __name__ == "__main__":
    print("🔧 Checking baseline_assessments table schema...")
    add_missing_columns()
    print("\n🔧 Checking training_plans table schema...")
    add_training_plan_session_tracking()
    print("\n✨ Migration complete!")
