from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_db
from src.infrastructure.database.models import (
    UserNarrowModel,
    UserWideModel,
    UserExtraWideModel,
    UserTypeIntModel,
    UserTypeVarcharModel,
    UserTypeTextModel,
    UserTypeJsonbModel,
    UserTypeTimestampModel,
    UserTypeUuidModel,
)
from src.presentation.schemas.column_overhead import (
    UserNarrowResponse,
    UserWideResponse,
    UserExtraWideResponse,
    UserTypeIntResponse,
    UserTypeVarcharResponse,
    UserTypeTextResponse,
    UserTypeJsonbResponse,
    UserTypeTimestampResponse,
    UserTypeUuidResponse,
)

router = APIRouter(prefix="/column-overhead", tags=["column-overhead"])

# ============================================
# A. 컬럼 수 비교
# ============================================


@router.get("/narrow", response_model=list[UserNarrowResponse])
async def get_users_narrow(
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """5개 컬럼 테이블 조회"""
    query = select(UserNarrowModel).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/wide", response_model=list[UserWideResponse])
async def get_users_wide(
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """20개 컬럼 테이블 조회"""
    query = select(UserWideModel).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/extra-wide", response_model=list[UserExtraWideResponse])
async def get_users_extra_wide(
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """50개 컬럼 테이블 조회"""
    query = select(UserExtraWideModel).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


# ============================================
# B. 데이터 타입별 비교
# ============================================


@router.get("/type/int", response_model=list[UserTypeIntResponse])
async def get_users_type_int(
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """INTEGER 타입 테이블 조회"""
    query = select(UserTypeIntModel).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/type/varchar", response_model=list[UserTypeVarcharResponse])
async def get_users_type_varchar(
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """VARCHAR 타입 테이블 조회"""
    query = select(UserTypeVarcharModel).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/type/text", response_model=list[UserTypeTextResponse])
async def get_users_type_text(
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """TEXT 타입 테이블 조회"""
    query = select(UserTypeTextModel).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/type/jsonb", response_model=list[UserTypeJsonbResponse])
async def get_users_type_jsonb(
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """JSONB 타입 테이블 조회"""
    query = select(UserTypeJsonbModel).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/type/timestamp", response_model=list[UserTypeTimestampResponse])
async def get_users_type_timestamp(
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """TIMESTAMP 타입 테이블 조회"""
    query = select(UserTypeTimestampModel).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/type/uuid", response_model=list[UserTypeUuidResponse])
async def get_users_type_uuid(
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """UUID 타입 테이블 조회"""
    query = select(UserTypeUuidModel).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
