from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.session import get_db, engine
from app.db.utils import check_database_connection
from app.db.base_class import Base
from typing import ForwardRef
Role = ForwardRef('RoleSchema')
from app.api.v1.endpoints import auth, roles, permissions, departments, analysis, crewai, googlecrew, search, documentprocessor
from app.db.session import SessionLocal
from datetime import datetime
import uvicorn
from fastapi_socketio import SocketManager
from app.api.v1.endpoints.chat import register_socket_events, get_chat_router
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

settings = get_settings()

# Create the FastAPI app first
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for streamlining Abu Dhabi government services",
    version=settings.VERSION,
)

# Configure CORS before SocketManager
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)



# Add routers before SocketManager
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(roles.router, prefix="/api/v1/auth", tags=["roles"]) 
app.include_router(permissions.router, prefix="/api/v1/auth", tags=["permissions"])
app.include_router(departments.router, prefix="/api/v1/auth", tags=["departments"])
app.include_router(analysis.router, prefix="/api/v1", tags=["Deprartment Document Processor"])
app.include_router(crewai.router, prefix="/api/v1/crewai", tags=["research"])
app.include_router(googlecrew.router, prefix="/api/v1/google", tags=["googlesearch"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(get_chat_router(), prefix="/api/v1/chat", tags=["chat"])
app.include_router(documentprocessor.router, prefix="/api/v1/documentprocessor", tags=["Document Processor"])


# Initialize SocketManager after routes are set up
sio = SocketManager(
    app=app,
    mount_location='',
    socketio_path='socket.io',
    cors_allowed_origins=["http://localhost:3000"],
    async_mode='asgi',
    logger=True,
    engineio_logger=True
)

@sio.on('connect')
async def handle_connect(sid, environ):
    logger.info(f"Client connected: {sid}")
    return True

@sio.on('disconnect')
async def handle_disconnect(sid):
    logger.info(f"Client disconnected: {sid}")

@sio.on('message')
async def handle_message(sid, data):
    try:
        logger.info(f"Received message from {sid}: {data}")
        await sio.emit('response', {"status": "Message received", "data": data}, to=sid)
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await sio.emit('error', {"error": str(e)}, to=sid)
        
register_socket_events(sio)

# Create database tables
Base.metadata.create_all(bind=engine)

# Your existing endpoints
@app.get("/test-db")
async def test_db(db: Session = Depends(get_db)):
    return check_database_connection(db)

@app.get(f"{settings.API_V1_STR}/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "status": "active",
        "version": settings.VERSION
    }

@app.get(f"{settings.API_V1_STR}/hello/{{name}}")
async def say_hello(name: str):
    return {"message": f"Hello, {name}!"}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1")).scalar()
        return {
            "status": "healthy",
            "database": "connected",
            "api_version": settings.VERSION
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": str(e),
            "api_version": settings.VERSION
        }

@app.get("/diagnostics")
async def database_diagnostics(db: Session = Depends(get_db)):
    try:
        diagnostics = {
            "connection": db.execute(text("SELECT 1")).scalar() == 1,
            "version": db.execute(text("SELECT version()")).scalar(),
            "database": db.execute(text("SELECT current_database()")).scalar(),
            "user": db.execute(text("SELECT current_user")).scalar(),
            "timestamp": datetime.utcnow()
        }
        return {
            "status": "success",
            "diagnostics": diagnostics
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow()
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True, log_level="INFO")