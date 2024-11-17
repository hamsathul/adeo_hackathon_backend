# app/schemas/chat.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ChatMessageBase(BaseModel):
    content: str

class ChatMessageCreate(ChatMessageBase):
    user_id: int  # Changed from str to int
    is_bot: bool = False

class ChatMessage(ChatMessageBase):
    id: str
    timestamp: datetime
    user_id: int  # Changed from str to int
    is_bot: bool
    read: bool

    class Config:
        from_attributes = True