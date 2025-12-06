from fastapi import APIRouter

from src.presentation.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint - minimal overhead"""
    return HealthResponse(status="ok")
