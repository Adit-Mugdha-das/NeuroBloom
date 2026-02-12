"""
Migration: Add Session Context Table

Adds pre-task questionnaire data storage for MS research.

Run this script to add the session_contexts table.

Usage:
    python migrate_add_session_context.py
"""

from sqlmodel import SQLModel, Session, create_engine, select
from app.core.config import settings
from app.models.session_context import SessionContext
from app.models.user import User
from app.models.training_session import TrainingSession


def create_session_context_table():
    """Create session_contexts table"""
    print("\n" + "="*70)
    print("  SESSION CONTEXT TABLE MIGRATION - MS Research Enhancement")
    print("="*70)
    
    print("\n📋 This migration adds:")
    print("  ✅ session_contexts table - Pre-task questionnaire data")
    print("  ✅ Fatigue level tracking (1-10 scale)")
    print("  ✅ Sleep quality tracking")
    print("  ✅ Medication timing tracking")
    print("  ✅ Pain, stress, and readiness levels")
    print("  ✅ Contextual factors for research analysis")
    
    print("\n" + "="*70)
    
    # Ask for confirmation
    response = input("\n🔹 Proceed with migration? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("\n❌ Migration cancelled.")
        return
    
    print("\n[1/3] Creating database engine...")
    engine = create_engine(settings.DATABASE_URL, echo=False)
    
    print("[2/3] Creating session_contexts table...")
    
    try:
        # Create table
        SQLModel.metadata.create_all(engine, tables=[SessionContext.__table__])  # type: ignore
        print("✅ session_contexts table created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return
    
    print("\n[3/3] Verifying table structure...")
    
    try:
        with Session(engine) as session:
            # Test query
            session.exec(select(SessionContext)).all()
            print("✅ session_contexts table verified")
            
    except Exception as e:
        print(f"❌ Error verifying table: {e}")
        return
    
    print("\n[✓] Migration Summary:")
    print("="*70)
    print("✅ session_contexts table - CREATED")
    print("\n📊 Table Structure:")
    print("  - id (Primary Key)")
    print("  - user_id (Foreign Key → user.id)")
    print("  - training_session_id (Foreign Key → training_sessions.id)")
    print("  - created_at (Timestamp)")
    print("\n  Pre-Task Questionnaire Fields:")
    print("  - fatigue_level (1-10)")
    print("  - sleep_quality (1-10)")
    print("  - sleep_hours (float)")
    print("  - medication_taken_today (boolean)")
    print("  - hours_since_medication (float)")
    print("  - pain_level (1-10)")
    print("  - stress_level (1-10)")
    print("  - time_of_day (string)")
    print("  - readiness_level (1-10)")
    print("  - notes (text)")
    print("  - distractions_present (boolean)")
    print("  - location (string)")
    print("="*70)
    
    print("\n✨ Migration completed successfully!")
    print("\n📌 Next steps:")
    print("1. Restart your backend server")
    print("2. Test pre-task questionnaire endpoint:")
    print("   POST /api/training/session-context")
    print("3. Update frontend to show questionnaire before tasks")
    print("4. Start collecting contextual data!")
    
    print("\n📊 Research Benefits:")
    print("  • Correlate fatigue with performance")
    print("  • Analyze medication timing effects")
    print("  • Detect circadian performance patterns")
    print("  • Identify environmental factors")
    print("  • Enable personalized interventions")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    create_session_context_table()
