# app/core/config.py
from pydantic import BaseModel
from typing import List, ClassVar
from functools import lru_cache
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    
	
    # API Settings
    PROJECT_NAME: str = "Abu Dhabi Government Services API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    
    # Security Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
	# AI Settings
    GOOGLE_API_KEY: str = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    AI71_BASE_URL: ClassVar[str] = "https://api.ai71.ai/v1/"
    AI71_API_KEY: str = os.getenv("AI71_API_KEY")
    SERPER_API_KEY: str = os.getenv("SERPER_API_KEY")
    
        # Database Settings - Using Docker service name 'db'
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/adeo_services"

@lru_cache()
def get_settings() -> Settings:
    return Settings()