"""
Migration: add departments table and doctor.department_id column.
Run once: python migrate_add_departments.py
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from sqlmodel import SQLModel
from app.core.config import engine
from app.models.department import Department


def migrate():
	with engine.connect() as conn:
		SQLModel.metadata.create_all(engine, tables=[Department.__table__], checkfirst=True)
		print("departments table created (or already existed)")

		try:
			conn.execute(text('ALTER TABLE doctors ADD COLUMN IF NOT EXISTS department_id INTEGER'))
			conn.commit()
			print("department_id column added to doctors table")
		except Exception as exc:
			conn.rollback()
			print(f"department_id migration skipped: {exc}")


if __name__ == "__main__":
	migrate()