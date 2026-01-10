"""
Add unassigned_at column to patient_assignments table
"""
from sqlmodel import Session, text
from app.core.config import engine

def migrate():
    with Session(engine) as session:
        try:
            # Check if column already exists
            result = session.exec(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='patient_assignments' 
                AND column_name='unassigned_at'
            """))
            
            if result.first():
                print("✅ Column 'unassigned_at' already exists")
                return
            
            # Add unassigned_at column
            session.exec(text("""
                ALTER TABLE patient_assignments 
                ADD COLUMN unassigned_at TIMESTAMP NULL
            """))
            session.commit()
            
            print("✅ Successfully added 'unassigned_at' column to patient_assignments table")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    print("Running migration: Add unassigned_at to patient_assignments...")
    migrate()
    print("Migration complete!")
