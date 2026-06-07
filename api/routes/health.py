"""Health check endpoints."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from config.settings import settings
from datetime import datetime

router = APIRouter()

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: str
    provider: str

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        timestamp=datetime.utcnow().isoformat(),
        provider=settings.LLM_PROVIDER
    )

@router.get("/ready")
async def readiness_check():
    """Readiness check for container orchestration."""
    return {"status": "ready"}

@router.get("/live")
async def liveness_check():
    """Liveness check for container orchestration."""
    return {"status": "alive"}