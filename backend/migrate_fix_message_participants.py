"""Fix the messages table so doctor participants are not constrained to user.id."""

from sqlalchemy import create_engine, inspect, text
from sqlmodel import SQLModel

from app.core.config import settings
from app.models.message import Message


def migrate() -> None:
    engine = create_engine(settings.DATABASE_URL)

    SQLModel.metadata.create_all(engine, tables=[Message.__table__])

    inspector = inspect(engine)
    foreign_keys = inspector.get_foreign_keys("messages")
    constraint_names = [
        fk.get("name")
        for fk in foreign_keys
        if set(fk.get("constrained_columns", [])) & {"sender_id", "recipient_id"}
    ]

    if not constraint_names:
        print("No sender/recipient foreign keys found on messages table.")
        return

    with engine.begin() as connection:
        for constraint_name in constraint_names:
            if not constraint_name:
                continue
            connection.execute(text(f'ALTER TABLE messages DROP CONSTRAINT IF EXISTS "{constraint_name}"'))
            print(f"Dropped constraint: {constraint_name}")

    print("✓ Messages table now supports doctor and patient participant IDs safely.")


if __name__ == "__main__":
    migrate()