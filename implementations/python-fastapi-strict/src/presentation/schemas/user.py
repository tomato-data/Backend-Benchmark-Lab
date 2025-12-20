from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """사용자 생성 요청"""

    name: str
    email: EmailStr


class UserUpdate(BaseModel):
    """사용자 수정 요청"""

    name: str | None = None
    email: EmailStr | None = None


class UserResponse(BaseModel):
    """사용자 응답"""

    id: int
    name: str
    email: str

    model_config = {"from_attributes": True}
