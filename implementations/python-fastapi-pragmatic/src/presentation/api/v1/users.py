from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_db
from src.infrastructure.database.models import UserModel, UserPaginationModel
from src.presentation.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    PaginatedOffsetResponse,
    PaginatedCursorResponse,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db)):
    """Get all users - DB read performance"""
    result = await db.execute(select(UserModel))
    models = result.scalars().all()
    return [UserResponse.model_validate(m) for m in models]


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create user - DB write performance"""
    model = UserModel(**user.model_dump())
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return UserResponse.model_validate(model)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, user: UserUpdate, db: AsyncSession = Depends(get_db)
):
    """Update user - DB write performance"""
    model = await db.get(UserModel, user_id)
    if model is None:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)

    await db.commit()
    await db.refresh(model)
    return UserResponse.model_validate(model)


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Delete user - DB write performance"""
    model = await db.get(UserModel, user_id)
    if model is None:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(model)
    await db.commit()


# OFFSET 페이지네이션 (09 시나리오용 - users_pagination 테이블 사용)
@router.get("/offset", response_model=PaginatedOffsetResponse)
async def get_users_offset(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """OFFSET 페이지네이션 - 뒤쪽 페이지일수록 느림"""
    offset = (page - 1) * size

    # 전체 개수
    total = (
        await db.execute(select(func.count()).select_from(UserPaginationModel))
    ).scalar() or 0

    # 데이터 조회
    query = (
        select(UserPaginationModel)
        .offset(offset)
        .limit(size)
        .order_by(UserPaginationModel.id)
    )
    result = await db.execute(query)
    items = result.scalars().all()

    return PaginatedOffsetResponse(
        items=[UserResponse.model_validate(m) for m in items],
        total=total,
        page=page,
        size=size,
        total_pages=(total + size - 1) // size,
    )


# Cursor 페이지네이션 (09 시나리오용 - users_pagination 테이블 사용)
@router.get("/cursor", response_model=PaginatedCursorResponse)
async def get_users_cursor(
    cursor: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Cursor 페이지네이션 - 일정한 성능 O(limit)"""
    # Where id > cursor (인덱스 활용)
    query = (
        select(UserPaginationModel)
        .where(UserPaginationModel.id > cursor)
        .order_by(UserPaginationModel.id)
        .limit(size + 1)  # 다음 페이지 존재 여부 확인용 +1
    )
    result = await db.execute(query)
    items = list(result.scalars().all())

    # 다음 페이지 존재 여부
    has_next = len(items) > size
    if has_next:
        items = items[:size]  # +1 제거

    next_cursor = items[-1].id if has_next and items else None

    return PaginatedCursorResponse(
        items=[UserResponse.model_validate(m) for m in items],
        next_cursor=next_cursor,
        size=size,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get user by ID - DB read performance"""
    model = await db.get(UserModel, user_id)
    if model is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(model)
