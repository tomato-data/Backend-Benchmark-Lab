from abc import ABC, abstractmethod
from typing import Optional

from src.domain.entities.user import User


class UserRepository(ABC):
    """
    Repository 추상 인터페이스 (DIP - 의존성 역전 원칙)
    Domain에 위치하지만, 구현은 Infrastructure에서 합니다.
    """

    @abstractmethod
    async def find_all(self) -> list[User]:
        """모든 사용자 조회"""
        pass

    @abstractmethod
    async def find_by_id(self, user_id: int) -> Optional[User]:
        """ID로 사용자 조회"""
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        """사용자 저장 (생성/수정)"""
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        """사용자 삭제"""
        pass
