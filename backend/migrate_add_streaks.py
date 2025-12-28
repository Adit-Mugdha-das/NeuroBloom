"""
Migration script to add streak tracking columns to training_plans table.
Run this once to update your existing database.
"""
from sqlalchemy import create_engine, text

# Database connection
DATABASE_URL = "postgresql://postgres:2107118@localhost:5432/neurobloom_db"
engine = create_engine(DATABASE_URL)

def migrate():
    """Add streak columns to training_plans table"""
    
    with engine.connect() as conn:
        try:
            # Add new columns with ALTER TABLE
            print("Adding streak tracking columns...")
            
            conn.execute(text("""
                ALTER TABLE training_plans 
                ADD COLUMN IF NOT EXISTS current_streak INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS longest_streak INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS total_training_days INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS streak_freeze_available BOOLEAN DEFAULT TRUE,
                ADD COLUMN IF NOT EXISTS last_streak_reset TIMESTAMP
            """))
            
            conn.commit()
            print("✅ Successfully added streak tracking columns!")
            
            # Verify columns were added
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'training_plans' 
                AND column_name IN ('current_streak', 'longest_streak', 'total_training_days', 
                                   'streak_freeze_available', 'last_streak_reset')
            """))
            
            print("\nNew columns:")
            for row in result:
                print(f"  - {row[0]}: {row[1]}")
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    print("Starting migration: Add streak tracking to training_plans")
    print("-" * 60)
    migrate()
    print("-" * 60)
    print("Migration complete! You can now use streak tracking features.")
