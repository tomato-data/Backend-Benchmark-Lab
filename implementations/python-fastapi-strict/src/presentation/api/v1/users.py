from fastapi import APIRouter, Depends, HTTPException

from src.application.services.user_service import UserService
from src.presentation.api.dependencies import get_user_service
from src.presentation.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
async def get_users(
    service: UserService = Depends(get_user_service),
):
    """Get all users - DB read performance"""
    users = await service.get_all_users()
    return [UserResponse.model_validate(u.__dict__) for u in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    """Get user by ID - DB read performance"""
    user = await service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user.__dict__)


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service),
):
    user = await service.create_user(user_data.name, user_data.email)
    return UserResponse.model_validate(user.__dict__)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    """Delete user - DB write performance"""
    deleted = await service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
