from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_db
from src.infrastructure.database.models import UserModel
from src.presentation.schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db)):
    """Get all users - DB read performance"""
    result = await db.execute(select(UserModel))
    models = result.scalars().all()
    return [UserResponse.model_validate(m) for m in models]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get user by ID - DB read performance"""
    model = await db.get(UserModel, user_id)
    if model is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(model)


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
