# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator
from app.core.config import get_settings
from urllib.parse import urlparse, urlunparse

settings = get_settings()

def get_db_urls():
    url = settings.DATABASE_URL
    if url:
        parsed = urlparse(url)
        async_url = urlunparse(parsed._replace(scheme='postgresql+psycopg'))
        sync_url = url  # Keep original URL for sync connection
        return async_url, sync_url
    return None, None

async_url, sync_url = get_db_urls()

# Keep existing sync engine (maintain original naming)
engine = create_engine(
    sync_url,
    pool_pre_ping=True,
    echo=True  # Set to False in production
)

# Create async engine with different name
async_engine = create_async_engine(
    async_url,
    pool_pre_ping=True,
    echo=True,  # Set to False in production
    pool_size=5,
    max_overflow=10
)

# Keep existing sync SessionLocal (maintain original naming)
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# Create async session maker with different name
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Keep existing get_db (maintain original naming)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
# Add async get_db with different name
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
