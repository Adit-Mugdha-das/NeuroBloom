from sqlmodel import SQLModel

from app.core.config import engine
from app.models.notification import Notification  # noqa: F401


def main():
    SQLModel.metadata.create_all(engine, checkfirst=True)
    print("notifications table verified")


if __name__ == "__main__":
    main()