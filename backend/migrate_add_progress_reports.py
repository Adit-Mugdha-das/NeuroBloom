"""
Migration script to add progress_reports table
Run this to create the progress reports feature in the database
"""

from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings
from app.models.progress_report import ProgressReport

def main():
    print("Creating progress_reports table...")
    
    engine = create_engine(settings.DATABASE_URL, echo=True)
    
    # Create the table
    SQLModel.metadata.create_all(engine, tables=[ProgressReport.__table__])
    
    print("✅ Progress reports table created successfully!")
    print("\nYou can now use the progress reports feature:")
    print("- Generate weekly/monthly reports")
    print("- View auto-generated analytics")
    print("- Add doctor commentary")
    print("- Export to PDF/CSV")

if __name__ == "__main__":
    main()
