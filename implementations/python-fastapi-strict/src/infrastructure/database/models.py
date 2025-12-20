from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    """
    SQLAlchemy ORM Model - Infrastructure 전용

    Domain Entity(User)와 분리됨:
    - Domain은 DB를 모름
    - 이 모델은 DB 테이블과 1:1 매핑
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
