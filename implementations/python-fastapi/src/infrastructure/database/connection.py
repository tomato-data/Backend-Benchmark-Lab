from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

import os

# 1. 환경변수에서 DB URL 읽기
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/benchmark"
)

# 2. 엔진 생성 (연결 풀 관리)
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # SQL 쿼리 로그 출력 (개발 시 유용)
)

# 3. 세션 팩토리 생성
async_session = async_sessionmaker(
    bind=engine,  # 어떤 엔진 (DB)에 연결할지
    expire_on_commit=False,  # 커밋 후에도 객체 속성 접근 가능
)


# 4. FastAPI 의존성 주입용 함수
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
