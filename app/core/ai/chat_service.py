# app/core/ai/chat_service.py
from app.models.chat import ChatMessage
from app.models.auth import User
from app.schemas.chat import ChatMessageCreate
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

class ChatService:
    def __init__(self, db: Session):
        self.db = db

    def create_message(self, message: ChatMessageCreate) -> ChatMessage:
        """Create a new chat message"""
        try:
            # Get or create user
            user = self.db.query(User).filter(User.id == message.user_id).first()
            if not user:
                # Handle case where user doesn't exist
                raise ValueError(f"User {message.user_id} not found")

            # Create message
            db_message = ChatMessage(
                id=str(uuid.uuid4()),
                content=message.content,
                user_id=user.id,
                is_bot=message.is_bot,
                timestamp=datetime.utcnow(),
                read=False
            )
            
            self.db.add(db_message)
            self.db.commit()
            self.db.refresh(db_message)
            return db_message
            
        except Exception as e:
            self.db.rollback()
            raise

    def mark_as_read(self, message_id: str) -> None:
        """Mark a message as read"""
        message = self.db.query(ChatMessage).filter(
            ChatMessage.id == message_id
        ).first()
        if message:
            message.read = True
            self.db.commit()

    def get_chat_history(self, user_id: int, limit: int = 50):
        """Get chat history for a user"""
        return self.db.query(ChatMessage).filter(
            ChatMessage.user_id == user_id
        ).order_by(ChatMessage.timestamp.desc()).limit(limit).all()