from sqlmodel import SQLModel, create_engine
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:2107118@localhost:5432/neurobloom_db"

settings = Settings()

engine = create_engine(settings.DATABASE_URL, echo=True)

def init_db():
    # Import all models here so SQLModel knows about them
    from app.models.user import User
    from app.models.test_result import TestResult
    
    SQLModel.metadata.create_all(engine)
