import secrets
import time

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.cache.connection import get_redis
from src.infrastructure.database.connection import get_db
from src.infrastructure.database.models import UserModel
from .common import SESSION_TTL, get_authorization_token

router = APIRouter(prefix="/auth", tags=["auth-session"])


@router.post("/login/session")
async def login_session(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """세션 로그인 - DB 조회 후 Redis에 세션 저장"""
    start = time.perf_counter()

    # DB에서 사용자 조회
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # 랜덤 세션 토큰 생성
    session_token = secrets.token_urlsafe(32)

    # Redis에 세션 저장
    await redis.setex(f"session:{session_token}", SESSION_TTL, str(user.id))

    elapsed = (time.perf_counter() - start) * 1000

    return {
        "session_token": session_token,
        "token_type": "session",
        "elapsed_ms": round(elapsed, 2),
    }


@router.get("/protected/session")
async def protected_session(
    token: str = Depends(get_authorization_token),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """세션 보호된 리소스 - Redis 조회 후 DB 조회"""
    start = time.perf_counter()

    # Redis에서 세션 조회
    user_id_str = await redis.get(f"session:{token}")

    if not user_id_str:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    user_id = int(user_id_str)

    # DB에서 사용자 조회
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    elapsed = (time.perf_counter() - start) * 1000

    return {
        "message": "protected resource",
        "auth_type": "session",
        "user_id": user.id,
        "email": user.email,
        "elapsed_ms": round(elapsed, 2),
    }
