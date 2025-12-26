from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.core.config import engine
from app.core.security import hash_password, verify_password
import traceback

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

@router.post("/register", response_model=UserRead)
def register(user: UserCreate, session: Session = Depends(get_session)):
    try:
        existing = session.exec(select(User).where(User.email == user.email)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        user_db = User(email=user.email, password_hash=hash_password(user.password))
        session.add(user_db)
        session.commit()
        session.refresh(user_db)
        return user_db
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in register: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
def login(user: UserLogin, session: Session = Depends(get_session)):
    user_db = session.exec(select(User).where(User.email == user.email)).first()
    if not user_db or not verify_password(user.password, user_db.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "message": "Login successful",
        "email": user_db.email,
        "id": user_db.id
    }
