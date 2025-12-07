from fastapi import APIRouter, Header, HTTPException

from src.presentation.schemas.common import ProtectedResponse

router = APIRouter(tags=["protected"])


@router.get("/protected", response_model=ProtectedResponse)
async def protected_endpoint(
    authorization: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
):
    """Protected endpoint - middleware chain performance (auth, logging, validation)"""
    # Simulate authentication
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header required")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    token = authorization.replace("Bearer ", "")

    # Simulate token validation (in real app, would verify JWT)
    if len(token) < 10:
        raise HTTPException(status_code=401, detail="Invalid token")

    return ProtectedResponse(
        message="Access granted",
        user=f"user_from_token_{token[:8]}",
    )
