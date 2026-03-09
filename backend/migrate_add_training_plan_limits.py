"""
Database migration to add default training pacing limits to training plans.
"""

from sqlmodel import Session, create_engine, text

from app.core.config import settings


engine = create_engine(str(settings.DATABASE_URL))


def add_training_plan_limit_columns():
    with Session(engine) as session:
        session.execute(text("""
            ALTER TABLE training_plans
            ADD COLUMN IF NOT EXISTS max_sessions_per_day INTEGER DEFAULT 3
        """))
        session.execute(text("""
            ALTER TABLE training_plans
            ADD COLUMN IF NOT EXISTS recommended_sessions_per_week INTEGER DEFAULT 7
        """))
        session.execute(text("""
            ALTER TABLE training_plans
            ADD COLUMN IF NOT EXISTS tasks_per_session INTEGER DEFAULT 4
        """))
        session.execute(text("""
            ALTER TABLE training_plans
            ADD COLUMN IF NOT EXISTS recommended_session_length_min_minutes INTEGER DEFAULT 5
        """))
        session.execute(text("""
            ALTER TABLE training_plans
            ADD COLUMN IF NOT EXISTS recommended_session_length_max_minutes INTEGER DEFAULT 10
        """))
        session.execute(text("""
            ALTER TABLE training_plans
            ADD COLUMN IF NOT EXISTS cooldown_between_sessions_minutes INTEGER DEFAULT 30
        """))

        session.execute(text("""
            UPDATE training_plans
            SET
                max_sessions_per_day = COALESCE(max_sessions_per_day, 3),
                recommended_sessions_per_week = COALESCE(recommended_sessions_per_week, 7),
                tasks_per_session = COALESCE(tasks_per_session, 4),
                recommended_session_length_min_minutes = COALESCE(recommended_session_length_min_minutes, 5),
                recommended_session_length_max_minutes = COALESCE(recommended_session_length_max_minutes, 10),
                cooldown_between_sessions_minutes = COALESCE(cooldown_between_sessions_minutes, 30)
        """))
        session.commit()

    print("✓ Training plan pacing limit columns added")


if __name__ == "__main__":
    add_training_plan_limit_columns()