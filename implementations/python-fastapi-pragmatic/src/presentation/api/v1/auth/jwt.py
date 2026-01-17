import time

from fastapi import APIRouter, Depends, HTTPException
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_db
from src.infrastructure.database.models import UserModel
from .common import SECRET_KEY, ALGORITHM, SESSION_TTL, get_authorization_token

router = APIRouter(prefix="/auth", tags=["auth-jwt"])


def create_jwt_token(user_id: int, email: str) -> str:
    """JWT 토큰 생성"""
    payload = {"sub": str(user_id), "email": email, "exp": time.time() + SESSION_TTL}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_jwt_token(token: str) -> dict:
    """JWT 토큰 검증"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid JWT token")


@router.post("/login/jwt")
async def login_jwt(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """JWT 로그인 - DB 조회 후 토큰 발급"""
    start = time.perf_counter()

    # DB에서 사용자 조회
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # JWT 토큰 생성
    token = create_jwt_token(user.id, user.email)

    elapsed = (time.perf_counter() - start) * 1000

    return {
        "access_token": token,
        "token_type": "bearer",
        "elapsed_ms": round(elapsed, 2),
    }


@router.get("/protected/jwt")
async def protected_jwt(
    token: str = Depends(get_authorization_token),
    db: AsyncSession = Depends(get_db),
):
    """JWT 보호된 리소스 - 토큰 검증 후 DB 조회"""
    start = time.perf_counter()

    # JWT 검증
    payload = verify_jwt_token(token)
    user_id = int(payload["sub"])

    # DB에서 사용자 조회 (실제 존재 확인)
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    elapsed = (time.perf_counter() - start) * 1000

    return {
        "message": "protected resources",
        "auth_type": "jwt",
        "user_id": user.id,
        "email": user.email,
        "elapsed_ms": round(elapsed, 2),
    }
