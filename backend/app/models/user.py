from sqlmodel import SQLModel, Field
from typing import Optional

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    password_hash: str
    
    # Patient-specific fields for doctor portal
    full_name: Optional[str] = Field(default=None)
    date_of_birth: Optional[str] = Field(default=None)
    diagnosis: Optional[str] = Field(default=None)
    consent_to_share: bool = Field(default=False)  # Patient consent for doctor access
