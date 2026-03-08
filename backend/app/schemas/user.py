from pydantic import BaseModel, ConfigDict
from typing import Optional

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str
    
