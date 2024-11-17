# app/models/chat.py
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import datetime

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    is_bot = Column(Boolean, default=False)
    read = Column(Boolean, default=False)

    # Add this relationship
    user = relationship("User", back_populates="chat_messages")