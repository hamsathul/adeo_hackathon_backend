# app/api/v1/endpoints/chat.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.ai.chat_handler import ChatHandler
from app.core.ai.chat_service import ChatService
from app.schemas.chat import ChatMessageCreate
from app.models.chat import ChatMessage
from app.models.auth import User
from datetime import datetime
import logging
import json
from typing import Dict, Optional
import uuid

router = APIRouter()
logger = logging.getLogger("chatbot.socket")

# Store active sessions
class SessionManager:
    def __init__(self):
        self.active_sessions: Dict[str, dict] = {}
        logger.info("Session Manager initialized")

    def create_session(self, sid: str, user_id: Optional[int] = None):
        """Create a new session"""
        self.active_sessions[sid] = {
            'user_id': user_id,
            'connected_at': datetime.utcnow(),
            'last_activity': datetime.utcnow()
        }
        logger.info(f"New session created for SID: {sid}, User ID: {user_id}")

    def update_session(self, sid: str):
        """Update session last activity"""
        if sid in self.active_sessions:
            self.active_sessions[sid]['last_activity'] = datetime.utcnow()

    def remove_session(self, sid: str):
        """Remove a session"""
        if sid in self.active_sessions:
            del self.active_sessions[sid]
            logger.info(f"Session removed for SID: {sid}")

    def get_user_id(self, sid: str) -> Optional[int]:
        """Get user ID for a session"""
        return self.active_sessions.get(sid, {}).get('user_id')

session_manager = SessionManager()

async def handle_chat_message(sid: str, data: dict, db: Session, sio):
    """Handle incoming chat messages"""
    try:
        chat_handler = ChatHandler(db)
        chat_service = ChatService(db)
        
        # Get user ID from session or data
        user_id = data.get('user_id') or session_manager.get_user_id(sid)
        
        # Validate user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise ValueError(f"User {user_id} not found")

        # Parse message content
        content = data.get('content', '').strip()
        if not content:
            raise ValueError("Message content cannot be empty")

        logger.info(f"Processing message from user {user_id}: {content[:50]}...")
        
        # Create and save user message
        user_message = ChatMessageCreate(
            content=content,
            user_id=user.id,
            is_bot=False
        )
        user_db_message = chat_service.create_message(user_message)
        logger.debug(f"User message saved with ID: {user_db_message.id}")
        
        # Initialize streaming response
        ai_message_id = str(uuid.uuid4())
        accumulated_content = []
        
        # Stream AI response
        async for chunk in chat_handler.handle_message_stream(content, str(user.id)):
            if not chunk["is_complete"]:
                accumulated_content.append(chunk["content"])
                # Emit streaming chunk
                await sio.emit('message_received', {
                    "type": "ai_message_chunk",
                    "message": {
                        "id": ai_message_id,
                        "content": chunk["content"],
                        "timestamp": chunk["timestamp"].isoformat(),
                        "is_bot": True,
                        "is_streaming": True
                    }
                }, to=sid)
            
        # Combine all chunks
        complete_content = "".join(accumulated_content)
        
        # Create and save complete AI message
        ai_message = ChatMessageCreate(
            content=complete_content,
            user_id=user.id,
            is_bot=True
        )
        ai_db_message = chat_service.create_message(ai_message)
        logger.debug(f"AI message saved with ID: {ai_db_message.id}")
        
        # Emit completion message
        await sio.emit('message_received', {
            "type": "ai_message_complete",
            "message": {
                "id": str(ai_db_message.id),
                "content": complete_content,
                "timestamp": ai_db_message.timestamp.isoformat(),
                "is_bot": True,
                "is_streaming": False
            }
        }, to=sid)
        
        # Update session activity
        session_manager.update_session(sid)
        
        return {
            "user_message": user_db_message,
            "ai_message": ai_db_message
        }
        
    except ValueError as e:
        logger.warning(f"Validation error in chat message: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error handling chat message: {str(e)}", exc_info=True)
        raise

def register_socket_events(sio):
    """Register Socket.IO event handlers"""
    
    @sio.on('connect')
    async def handle_connect(sid, environ):
        """Handle client connection"""
        try:
            logger.info(f"Client connecting: {sid}")
            session_manager.create_session(sid)
            await sio.emit('connect_response', {
                "status": "connected",
                "sid": sid,
                "timestamp": datetime.utcnow().isoformat()
            }, to=sid)
        except Exception as e:
            logger.error(f"Error in connect handler: {str(e)}", exc_info=True)
            await sio.emit('error', {
                "message": "Connection error occurred",
                "timestamp": datetime.utcnow().isoformat()
            }, to=sid)

    @sio.on('disconnect')
    def handle_disconnect(sid):
        """Handle client disconnect"""
        try:
            logger.info(f"Client disconnected: {sid}")
            session_manager.remove_session(sid)
        except Exception as e:
            logger.error(f"Error in disconnect handler: {str(e)}", exc_info=True)

    @sio.on('authenticate')
    async def handle_authenticate(sid, data):
        """Handle user authentication"""
        try:
            user_id = data.get('user_id')
            if user_id:
                session_manager.create_session(sid, user_id)
                await sio.emit('auth_response', {
                    "status": "authenticated",
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }, to=sid)
        except Exception as e:
            logger.error(f"Error in authentication handler: {str(e)}", exc_info=True)
            await sio.emit('error', {
                "message": "Authentication error occurred",
                "timestamp": datetime.utcnow().isoformat()
            }, to=sid)

    @sio.on('chat_message')
    async def handle_chat_socket_message(sid, data):
        """Handle chat messages via Socket.IO"""
        try:
            db = next(get_db())
            
            # Pass sio instance to handle_chat_message
            result = await handle_chat_message(sid, data, db, sio)
            
            # Emit user message acknowledgment
            await sio.emit('message_received', {
                "type": "user_message",
                "message": {
                    "id": str(result["user_message"].id),
                    "content": result["user_message"].content,
                    "timestamp": result["user_message"].timestamp.isoformat(),
                    "is_bot": False
                }
            }, to=sid)
            
        except ValueError as e:
            logger.warning(f"Validation error: {str(e)}")
            await sio.emit('error', {
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }, to=sid)
        except Exception as e:
            logger.error(f"Error in chat message handler: {str(e)}", exc_info=True)
            await sio.emit('error', {
                "message": "An error occurred processing your message",
                "timestamp": datetime.utcnow().isoformat()
            }, to=sid)

# REST endpoints remain unchanged

# REST endpoints
@router.get("/history/{user_id}")
def get_chat_history(
    user_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get chat history for a user"""
    try:
        chat_service = ChatService(db)
        messages = chat_service.get_chat_history(user_id, limit)
        
        return {
            "status": "success",
            "messages": [
                {
                    "id": str(msg.id),
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "is_bot": msg.is_bot,
                    "read": msg.read
                }
                for msg in messages
            ]
        }
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving chat history: {str(e)}"
        )

@router.post("/mark-read/{message_id}")
def mark_message_as_read(
    message_id: str,
    db: Session = Depends(get_db)
):
    """Mark a message as read"""
    try:
        chat_service = ChatService(db)
        chat_service.mark_as_read(message_id)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error marking message as read: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error marking message as read: {str(e)}"
        )

@router.get("/active-sessions")
def get_active_sessions():
    """Get information about active sessions"""
    try:
        return {
            "status": "success",
            "active_sessions": len(session_manager.active_sessions),
            "sessions": [
                {
                    "sid": sid,
                    "user_id": session["user_id"],
                    "connected_at": session["connected_at"].isoformat(),
                    "last_activity": session["last_activity"].isoformat()
                }
                for sid, session in session_manager.active_sessions.items()
            ]
        }
    except Exception as e:
        logger.error(f"Error getting active sessions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving active sessions: {str(e)}"
        )

def get_chat_router():
    """Get the chat router"""
    return router