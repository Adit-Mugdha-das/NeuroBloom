"""
Migration script to add missing columns to baseline_assessments table
"""
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:2107118@localhost:5432/neurobloom_db"
engine = create_engine(DATABASE_URL)

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

if __name__ == "__main__":
    print("🔧 Checking baseline_assessments table schema...")
    add_missing_columns()
    print("✨ Migration complete!")
