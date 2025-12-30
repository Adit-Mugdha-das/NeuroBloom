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
    try:
        # Debug: Check all users in database
        all_users = session.exec(select(User)).all()
        print(f"DEBUG: Total users in DB: {len(all_users)}")
        print(f"DEBUG: Login attempt for: {user.email}")
        
        user_db = session.exec(select(User).where(User.email == user.email)).first()
        
        if not user_db:
            print(f"DEBUG: User not found: {user.email}")
            print(f"DEBUG: Available emails: {[u.email for u in all_users]}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        print(f"DEBUG: User found: {user_db.email}, ID: {user_db.id}")
        
        if not verify_password(user.password, user_db.password_hash):
            print(f"DEBUG: Password verification failed for {user.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        print(f"DEBUG: Login successful for {user.email}")
        return {
            "message": "Login successful",
            "email": user_db.email,
            "id": user_db.id
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in login: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
