"""
Migration to add assignment_requests table
"""
from sqlmodel import Session, SQLModel
from app.core.config import engine
from app.models.assignment_request import AssignmentRequest

def migrate():
    print("Creating assignment_requests table...")
    SQLModel.metadata.create_all(engine, tables=[AssignmentRequest.__table__])
    print("✅ Migration complete!")

if __name__ == "__main__":
    migrate()
