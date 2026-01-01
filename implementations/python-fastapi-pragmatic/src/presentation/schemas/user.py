from pydantic import BaseModel, ConfigDict
from datetime import datetime


class UserCreate(BaseModel):
    name: str
    email: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    created_at: datetime


# Pagination 응답 스키마
class PaginatedOffsetResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    size: int
    total_pages: int


class PaginatedCursorResponse(BaseModel):
    items: list[UserResponse]
    next_cursor: int | None
    size: int
