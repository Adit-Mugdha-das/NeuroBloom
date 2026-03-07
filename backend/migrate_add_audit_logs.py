from sqlmodel import SQLModel

from app.core.config import engine
from app.models.audit_log import AuditLog  # noqa: F401


def main():
    SQLModel.metadata.create_all(engine, checkfirst=True)
    print("audit_logs table verified")


if __name__ == "__main__":
    main()