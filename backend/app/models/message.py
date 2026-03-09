from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

class Message(SQLModel, table=True):
    """Secure messages between doctors and patients"""
    __tablename__ = "messages"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Participants
    sender_id: int  # References User.id or Doctor.id depending on sender_type
    sender_type: str  # "doctor" or "patient"
    recipient_id: int  # References User.id or Doctor.id depending on recipient_type
    recipient_type: str  # "doctor" or "patient"
    
    # Message content
    subject: Optional[str] = Field(default=None, max_length=200)
    message: str  # Message content
    
    # Threading (optional - for future enhancement)
    parent_message_id: Optional[int] = Field(default=None, foreign_key="messages.id")
    
    # Status tracking
    is_read: bool = Field(default=False)
    read_at: Optional[datetime] = Field(default=None)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
