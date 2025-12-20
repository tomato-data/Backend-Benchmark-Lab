from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """
    Domain Entity - 순수 비즈니스 객체

    외부 의존성 없음:
    - SQLAlchemy 없음 (ORM은 Infrastructure)
    - Pydantic 없음 (직렬화는 Presentation)
    """

    id: Optional[int]  # 생성 전에는 None
    name: str
    email: str

    def __post_init__(self):
        """간단한 비즈니스 규칙 검증"""
        if not self.name or len(self.name) > 100:
            raise ValueError("Name must be 1-100 characters")
        if not self.email or "@" not in self.email:
            raise ValueError("Invalid email format")
