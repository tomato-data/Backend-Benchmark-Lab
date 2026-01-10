import json
import time

from fastapi import APIRouter, Depends, HTTPException, Query
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.cache.connection import get_redis
from src.infrastructure.database.connection import get_db
from src.infrastructure.database.models import UserModel
from src.presentation.schemas.caching import (
    CacheResult,
    CacheWarmupResult,
)


router = APIRouter(prefix="/cache", tags=["caching"])

CACHE_TTL = 300  # 5분


@router.get("/users/{user_id}/no-cache", response_model=CacheResult)
async def get_user_no_cache(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """항상 DB에서 조회 (캐시 미사용)"""
    start = time.perf_counter()

    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    elapsed = (time.perf_counter() - start) * 1000

    return CacheResult(
        source="database",
        user_id=user.id,
        name=user.name,
        email=user.email,
        elapsed_ms=round(elapsed, 2),
    )


@router.get("/users/{user_id}/cached", response_model=CacheResult)
async def get_user_cached(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """캐시 우선 조회 (미스 시 DB -> 캐시 저장)"""
    start = time.perf_counter()
    cache_key = f"user:{user_id}"

    # 1. 캐시 조회
    cached = await redis.get(cache_key)
    if cached:
        data = json.loads(cached)
        elapsed = (time.perf_counter() - start) * 1000
        return CacheResult(
            source="cache",
            user_id=data["id"],
            name=data["name"],
            email=data["email"],
            elapsed_ms=round(elapsed, 2),
        )

    # 2. 캐시 미스 -> DB 조회
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 3. 캐시 저장
    user_data = {"id": user.id, "name": user.name, "email": user.email}
    await redis.setex(cache_key, CACHE_TTL, json.dumps(user_data))

    elapsed = (time.perf_counter() - start) * 1000

    return CacheResult(
        source="database",
        user_id=user.id,
        name=user.name,
        email=user.email,
        elapsed_ms=round(elapsed, 2),
    )


@router.post("/warmup", response_model=CacheWarmupResult)
async def warmup_cache(
    count: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """캐시 워밍업 (N명 미리 로드)"""
    start = time.perf_counter()

    result = await db.execute(select(UserModel).limit(count))
    users = result.scalars().all()

    for user in users:
        cache_key = f"user:{user.id}"
        user_data = {"id": user.id, "name": user.name, "email": user.email}
        await redis.setex(cache_key, CACHE_TTL, json.dumps(user_data))

    elapsed = (time.perf_counter() - start) * 1000

    return CacheWarmupResult(
        warmed_count=len(users),
        elapsed_ms=round(elapsed, 2),
    )


@router.delete("/flush")
async def flush_cache(redis: Redis = Depends(get_redis)):
    """캐시 전체 삭제"""
    await redis.flushdb()
    return {"message": "Cache flushed"}
