"""
Migration script to add messages table for secure doctor-patient communication
"""
from sqlmodel import SQLModel, create_engine
from app.core.config import settings
from app.models.message import Message

def migrate():
    """Add messages table to database"""
    engine = create_engine(settings.DATABASE_URL)
    
    print("Creating messages table...")
    SQLModel.metadata.create_all(engine, tables=[Message.__table__])
    print("✓ Messages table created successfully!")
    print("\nSecure messaging features are now available:")
    print("- Doctor can send messages to patients")
    print("- Patients can send messages to their assigned doctor")
    print("- Message threading support")
    print("- Read receipts")

if __name__ == "__main__":
    migrate()
