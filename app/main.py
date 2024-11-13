from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
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

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "api_version": settings.VERSION,
        "service": settings.PROJECT_NAME
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)