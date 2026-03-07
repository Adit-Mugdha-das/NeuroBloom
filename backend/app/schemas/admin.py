from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class AdminRead(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
