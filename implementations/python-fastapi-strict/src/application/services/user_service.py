from typing import Optional

from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository
from src.domain.use_cases.user_use_cases import (
    CreateUserUseCase,
    DeleteUserUseCase,
    GetAllUsersUseCase,
    GetUserByIdUseCase,
)


class UserService:
    """
    Application Service - Use Case 조율자

    역할:
    - 여러 Use Case를 조합하여 복잡한 비즈니스 흐름 처리
    - 트랜잭션 경계 관리 (필요시)
    - 현재는 단순 위임이지만, 확장 가능
    """

    def __init__(self, repository: UserRepository):
        self._repository = repository

    async def get_all_users(self) -> list[User]:
        use_case = GetAllUsersUseCase(self._repository)
        return await use_case.execute()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        use_case = GetUserByIdUseCase(self._repository)
        return await use_case.execute(user_id)

    async def create_user(self, name: str, email: str) -> User:
        use_case = CreateUserUseCase(self._repository)
        return await use_case.execute(name, email)

    async def delete_user(self, user_id: int) -> bool:
        use_case = DeleteUserUseCase(self._repository)
        return await use_case.execute(user_id)
