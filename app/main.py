from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.session import get_db, engine
from app.db.utils import check_database_connection
from app.db.base_class import Base
from typing import ForwardRef
Role = ForwardRef('RoleSchema')
from app.api.v1.endpoints import auth, roles, permissions, departments, analysis, crewai, googlecrew, search
from app.db.session import SessionLocal
from datetime import datetime
import uvicorn

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for streamlining Abu Dhabi government services",
    version=settings.VERSION,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(roles.router, prefix="/api/v1/auth", tags=["roles"]) 
app.include_router(permissions.router, prefix="/api/v1/auth", tags=["permissions"])
app.include_router(departments.router, prefix="/api/v1/auth", tags=["departments"])
app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])
app.include_router(crewai.router, prefix="/api/v1/crewai", tags=["research"])
app.include_router(googlecrew.router, prefix="/api/v1/google", tags=["googlesearch"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])





# Create database tables
Base.metadata.create_all(bind=engine)

# Test database connection
@app.get("/test-db")
async def test_db(db: Session = Depends(get_db)):
    return check_database_connection(db)

# API routes will be prefixed with /api/v1
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
    
# Basic database diagnostics
@app.get("/diagnostics")
async def database_diagnostics(db: Session = Depends(get_db)):
    try:
        diagnostics = {
            # Test basic connection
            "connection": db.execute(text("SELECT 1")).scalar() == 1,
            
            # Get database version
            "version": db.execute(text("SELECT version()")).scalar(),
            
            # Get current database name
            "database": db.execute(text("SELECT current_database()")).scalar(),
            
            # Get current user
            "user": db.execute(text("SELECT current_user")).scalar(),
            
            # Timestamp
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
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)