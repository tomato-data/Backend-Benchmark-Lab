from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.database.models import UserModel


class UserRepositoryImpl(UserRepository):
    """
    UserRepository의 실제 구현체

    핵심 포인트:
    - Domain의 ABC를 상속
    - SQLALchemy를 사용하여 실제 DB 작업
    - Entity ↔ ORM Model 변환 담당
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_entity(self, model: UserModel) -> User:
        """ORM Model → Domain Entity 변환"""
        return User(id=model.id, name=model.name, email=model.email)

    def _to_model(self, entity: User) -> UserModel:
        """Domain Entity → ORM Model 변환"""
        return UserModel(id=entity.id, name=entity.name, email=entity.email)

    async def find_all(self) -> list[User]:
        result = await self._session.execute(select(UserModel))
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def find_by_id(self, user_id: int) -> Optional[User]:
        model = await self._session.get(UserModel, user_id)
        return self._to_entity(model) if model else None

    async def save(self, user: User) -> User:
        if user.id is None:
            # 새 사용자 생성
            model = UserModel(name=user.name, email=user.email)
            self._session.add(model)
            await self._session.commit()
            await self._session.refresh(model)
            return self._to_entity(model)
        else:
            # 기존 사용자 수정
            model = await self._session.get(UserModel, user.id)
            if model:
                model.name = user.name
                model.email = user.email
                await self._session.commit()
                await self._session.refresh(model)
                return self._to_entity(model)
            raise ValueError(f"User {user.id} not found")

    async def delete(self, user_id: int) -> bool:
        model = await self._session.get(UserModel, user_id)
        if model:
            await self._session.delete(model)
            await self._session.commit()
            return True
        return False
