from pydantic import BaseModel, ConfigDict
from datetime import datetime


class PostResponse(BaseModel):
    """Post 응답 스키마 (Author 없이)"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str | None
    view_count: int
    created_at: datetime


class AuthorResponse(BaseModel):
    """Author 응답 스키마 (Posts 없이)"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    bio: str | None
    created_at: datetime


class AuthorWithPostsResponse(BaseModel):
    """Author + Posts 응답 스키마 (N+1 테스트용)"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    bio: str | None
    created_at: datetime
    posts: list[PostResponse]  # 핵심: posts 포함
