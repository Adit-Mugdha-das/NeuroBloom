"""
Add new columns to User table for doctor portal feature
"""

from sqlmodel import Session, text
from app.core.config import engine

def add_user_columns():
    """Add new columns to existing User table"""
    print("\n" + "="*60)
    print("Adding new columns to User table...")
    print("="*60 + "\n")
    
    with Session(engine) as session:
        try:
            # Add full_name column
            session.exec(text("""
                ALTER TABLE "user" 
                ADD COLUMN IF NOT EXISTS full_name VARCHAR;
            """))
            print("✅ Added full_name column")
            
            # Add date_of_birth column
            session.exec(text("""
                ALTER TABLE "user" 
                ADD COLUMN IF NOT EXISTS date_of_birth VARCHAR;
            """))
            print("✅ Added date_of_birth column")
            
            # Add diagnosis column
            session.exec(text("""
                ALTER TABLE "user" 
                ADD COLUMN IF NOT EXISTS diagnosis VARCHAR;
            """))
            print("✅ Added diagnosis column")
            
            # Add consent_to_share column with default FALSE
            session.exec(text("""
                ALTER TABLE "user" 
                ADD COLUMN IF NOT EXISTS consent_to_share BOOLEAN DEFAULT FALSE;
            """))
            print("✅ Added consent_to_share column")
            
            session.commit()
            print("\n✨ User table migration completed successfully!\n")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            session.rollback()

if __name__ == "__main__":
    add_user_columns()
