from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.user_service import UserService
from src.infrastructure.database.connection import get_db
from src.infrastructure.database.repositories.user_repository_impl import (
    UserRepositoryImpl,
)


async def get_user_service(
    session: AsyncSession = Depends(get_db),
) -> UserService:
    """
    의존성 주입 체인:
    DB Session → Repository → Service

    이것이 Clean Architecture의 "조립" 지점입니다.
    """
    repository = UserRepositoryImpl(session)
    return UserService(repository)
