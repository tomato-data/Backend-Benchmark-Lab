import time

from fastapi import APIRouter, Header, HTTPException

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = "benchmark-secret-key-12345"
ALGORITHM = "HS256"
SESSION_TTL = 1800


async def get_authorization_token(authorization: str = Header(...)) -> str:
    """Authorization 헤더에서 Bearer 토큰 추출"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    return authorization[7:]  # "Bearer " 제거


# ===========================================
# 17-a: No Auth (기준선)
# ===========================================
@router.get("/public")
async def public_endpoint():
    """인증 없음 - 기준선 측정용"""
    return {
        "message": "public endpoint",
        "authenticated": False,
    }
