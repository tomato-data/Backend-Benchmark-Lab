from typing import Optional

from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository


class GetAllUsersUseCase:
    """모든 사용자 조회 유스케이스"""

    def __init__(self, repository: UserRepository):
        self._repository = repository

    async def execute(self) -> list[User]:
        return await self._repository.find_all()


class GetUserByIdUseCase:
    """ID로 사용자 조회 유스케이스"""

    def __init__(self, repository: UserRepository):
        self._repository = repository

    async def execute(self, user_id: int) -> Optional[User]:
        return await self._repository.find_by_id(user_id)


class CreateUserUseCase:
    """사용자 생성 유스케이스"""

    def __init__(self, repository: UserRepository):
        self._repository = repository

    async def execute(self, name: str, email: str) -> User:
        user = User(id=None, name=name, email=email)
        return await self._repository.save(user)


class DeleteUserUseCase:
    """사용자 삭제 유스케이스"""

    def __init__(self, repository: UserRepository):
        self._repository = repository

    async def execute(self, user_id: int) -> bool:
        return await self._repository.delete(user_id)
