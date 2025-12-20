from fastapi import APIRouter, Depends

from src.presentation.middleware.auth import verify_token
from src.presentation.schemas.common import ProtectedResponse

router = APIRouter(tags=["protected"])


@router.get("/protected", response_model=ProtectedResponse)
async def protected_endpoint(
    token: str = Depends(verify_token),  # 미들웨어 체인
):
    """Protected endpoint - middleware chain performance"""
    return ProtectedResponse(
        message="Access granted",
        user=f"user_from_token_{token[:8]}",
    )
