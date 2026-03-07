"""
Migration: Add admins table and is_active column to users table
Run once: python migrate_add_admin.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.config import engine
from app.models.admin import Admin
from sqlmodel import SQLModel


def migrate():
    with engine.connect() as conn:
        # 1. Create admins table if not exists
        SQLModel.metadata.create_all(engine, tables=[Admin.__table__], checkfirst=True)
        print("✓ admins table created (or already existed)")

        # 2. Add is_active column to users if missing
        try:
            conn.execute(text(
                'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE NOT NULL'
            ))
            conn.commit()
            print("✓ is_active column added to user table")
        except Exception as e:
            conn.rollback()
            print(f"  (is_active column may already exist: {e})")

    print("\nMigration complete.")


if __name__ == "__main__":
    migrate()
