from fastapi import Header, HTTPException


async def verify_token(
    authorization: str | None = Header(default=None),
) -> str:
    """
    인증 미들웨어 (의존성 주입 방식)

    Clean Architecture:
    - Presentation 레이어에서 인증 처리
    - 엔드포인트에 명시적으로 주입
    """
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header required")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    token = authorization.replace("Bearer ", "")

    if len(token) < 10:
        raise HTTPException(status_code=401, detail="Invalid token")

    return token
