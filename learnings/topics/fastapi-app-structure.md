# FastAPI 벤치마크 앱 구조 상세 문서

## 개요

이 문서는 Backend Benchmark Lab의 FastAPI 구현체 전체 구조를 상세히 설명합니다.
벤치마크 목적에 맞게 **Pragmatic Architecture** (실용적 아키텍처)를 채택했습니다.

---

## 목차

1. [프로젝트 구조](#1-프로젝트-구조)
2. [아키텍처 설계](#2-아키텍처-설계)
3. [레이어별 상세 설명](#3-레이어별-상세-설명)
4. [API 엔드포인트](#4-api-엔드포인트)
5. [설정 파일](#5-설정-파일)
6. [실행 방법](#6-실행-방법)
7. [데이터 흐름](#7-데이터-흐름)

---

## 1. 프로젝트 구조

```
implementations/python-fastapi/
├── pyproject.toml          # 의존성 관리 (uv)
├── uv.lock                  # 의존성 잠금 파일
├── Dockerfile               # 컨테이너 이미지 빌드
├── docker-compose.yml       # 로컬 개발 환경 (앱 + PostgreSQL)
├── .env.example             # 환경 변수 템플릿
├── .python-version          # Python 버전 명시 (3.12)
├── README.md
│
├── src/                     # 소스 코드 루트
│   ├── __init__.py
│   ├── main.py              # FastAPI 앱 진입점 ⭐
│   │
│   ├── infrastructure/      # 인프라스트럭처 레이어
│   │   ├── __init__.py
│   │   └── database/
│   │       ├── __init__.py
│   │       ├── connection.py   # DB 연결 설정
│   │       └── models.py       # SQLAlchemy ORM 모델
│   │
│   └── presentation/        # 프레젠테이션 레이어
│       ├── __init__.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── dependencies.py  # FastAPI 의존성 (예약)
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── router.py    # 라우터 통합
│       │       ├── health.py    # 헬스체크 엔드포인트
│       │       ├── echo.py      # 에코 엔드포인트
│       │       ├── users.py     # 사용자 CRUD 엔드포인트
│       │       ├── external.py  # 외부 API 시뮬레이션
│       │       ├── protected.py # 인증 필요 엔드포인트
│       │       └── upload.py    # 파일 업로드 엔드포인트
│       ├── middleware/
│       │   ├── __init__.py
│       │   ├── auth.py          # 인증 미들웨어 (예약)
│       │   └── logging.py       # 로깅 미들웨어 (예약)
│       └── schemas/
│           ├── __init__.py
│           ├── common.py        # 공통 Pydantic 스키마
│           └── user.py          # 사용자 Pydantic 스키마
│
└── tests/                   # 테스트 (예약)
    ├── __init__.py
    ├── unit/
    │   └── __init__.py
    └── integration/
        └── __init__.py
```

---

## 2. 아키텍처 설계

### 2.1 채택한 아키텍처: Pragmatic (실용적) 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                   Presentation Layer                     │
│         (FastAPI Routers, Pydantic Schemas)             │
├─────────────────────────────────────────────────────────┤
│                  Infrastructure Layer                    │
│         (SQLAlchemy Models, DB Connection)              │
└─────────────────────────────────────────────────────────┘
                          ↓
                    [PostgreSQL]
```

### 2.2 왜 Pragmatic Architecture인가?

이 프로젝트는 **벤치마크 Lab**입니다. 목적이 다릅니다:

| 관점 | Clean Architecture | Pragmatic Architecture |
|------|-------------------|------------------------|
| **목적** | 유지보수성, 테스트 용이성 | 성능 측정, 프레임워크 비교 |
| **레이어** | 4개 (Domain, Application, Infrastructure, Presentation) | 2개 (Presentation, Infrastructure) |
| **객체 변환** | 6번 (Entity ↔ Model ↔ DTO ↔ Schema) | 2번 (Model ↔ Schema) |
| **복잡도** | 높음 | 낮음 |
| **성능 오버헤드** | 있음 | 최소화 |

벤치마크에서는 **프레임워크 자체의 성능**을 측정해야 하므로, 불필요한 추상화 레이어를 제거했습니다.

### 2.3 레이어 간 의존성

```
Presentation (FastAPI Routers)
      │
      │ imports
      ▼
Infrastructure (SQLAlchemy)
      │
      │ connects to
      ▼
   Database
```

- **Presentation**: HTTP 요청/응답 처리, 유효성 검증
- **Infrastructure**: 데이터 영속화, 외부 서비스 연동

---

## 3. 레이어별 상세 설명

### 3.1 진입점: `src/main.py`

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.infrastructure.database.connection import engine
from src.infrastructure.database.models import Base
from src.presentation.api.v1.router import router as v1_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup: 테이블 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: 연결 정리
    await engine.dispose()


app = FastAPI(
    title="FastAPI Benchmark",
    description="Backend Benchmark Lab - FastAPI Implementation",
    version="1.0.0",
    lifespan=lifespan,
)

# API 라우터 등록
app.include_router(v1_router)


@app.get("/")
async def root():
    return {"message": "FastAPI Benchmark API", "docs": "/docs"}
```

#### 핵심 개념

**Lifespan Context Manager (수명 주기 관리)**

FastAPI 0.100+에서 도입된 새로운 패턴입니다. 기존 `@app.on_event("startup")`을 대체합니다.

```python
@asynccontextmanager
async def lifespan(_app: FastAPI):
    # === STARTUP ===
    # yield 이전: 앱 시작 시 실행
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # 앱 실행 중

    # === SHUTDOWN ===
    # yield 이후: 앱 종료 시 실행
    await engine.dispose()
```

- `yield` 이전: 앱 시작 시 한 번 실행 (DB 테이블 생성)
- `yield` 이후: 앱 종료 시 한 번 실행 (연결 풀 정리)

---

### 3.2 Infrastructure Layer

#### 3.2.1 데이터베이스 연결: `connection.py`

```python
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import os

# 1. 환경변수에서 DB URL 읽기
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/benchmark"
)

# 2. 엔진 생성 (연결 풀 관리)
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # SQL 쿼리 로그 출력 (개발 시 유용)
)

# 3. 세션 팩토리 생성
async_session = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

# 4. FastAPI 의존성 주입용 함수
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
```

#### 핵심 개념

**SQLAlchemy 2.0 Async 컴포넌트**

| 컴포넌트 | 역할 | 비유 |
|----------|------|------|
| `create_async_engine` | 연결 풀 관리자 | 수영장 관리인 (수영장 = 연결 풀) |
| `async_sessionmaker` | 세션 공장 | 수영복 대여소 (세션 = 수영복) |
| `AsyncSession` | 개별 DB 세션 | 수영복 한 벌 (작업 단위) |

**연결 URL 형식**

```
postgresql+asyncpg://postgres:postgres@localhost:5432/benchmark
└──────┬─────┘ └──┬──┘ └──┬──┘ └──┬──┘ └───┬───┘ └──┬──┘
    dialect   driver   user    pass    host:port   db
```

- `postgresql`: 데이터베이스 종류
- `asyncpg`: 비동기 PostgreSQL 드라이버
- 나머지: 인증 정보 및 연결 대상

**`expire_on_commit=False` 옵션**

```python
async_session = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,  # 중요!
)
```

이 옵션이 없으면:
```python
await db.commit()
print(model.name)  # LazyLoad 에러! (세션이 만료됨)
```

이 옵션이 있으면:
```python
await db.commit()
print(model.name)  # OK! (메모리에 캐시된 값 사용)
```

---

#### 3.2.2 ORM 모델: `models.py`

```python
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
```

#### 핵심 개념

**SQLAlchemy 2.0 스타일 (Type-Annotated Mapping)**

이전 방식 (1.x):
```python
class User(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
```

새 방식 (2.0):
```python
class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
```

**장점**:
- 타입 힌트 지원 (IDE 자동완성, 타입 체크)
- 더 명확한 문법
- Pydantic과 일관성

**`Mapped[T]`의 의미**

| 타입 | 의미 | DB 컬럼 |
|------|------|---------|
| `Mapped[int]` | 필수, 정수 | `NOT NULL INTEGER` |
| `Mapped[str]` | 필수, 문자열 | `NOT NULL VARCHAR` |
| `Mapped[int \| None]` | 선택적, 정수 | `INTEGER` (nullable) |

---

### 3.3 Presentation Layer

#### 3.3.1 Pydantic 스키마: `schemas/user.py`

```python
from pydantic import BaseModel, ConfigDict


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
```

#### 핵심 개념

**스키마 분리 패턴**

| 스키마 | 용도 | 필드 |
|--------|------|------|
| `UserCreate` | 생성 요청 | name, email (필수) |
| `UserUpdate` | 수정 요청 | name, email (선택적) |
| `UserResponse` | 응답 | id, name, email |

왜 분리하나요?
- **생성**: `id`가 없음 (서버가 생성)
- **수정**: 일부 필드만 변경 가능 (Partial Update)
- **응답**: 모든 필드 포함

**`ConfigDict(from_attributes=True)`**

SQLAlchemy 모델을 Pydantic 모델로 변환 가능하게 합니다:

```python
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    # ...

# SQLAlchemy 모델 → Pydantic 모델 변환
sqlalchemy_model = UserModel(id=1, name="Kim", email="kim@test.com")
pydantic_model = UserResponse.model_validate(sqlalchemy_model)  # OK!
```

이 설정이 없으면:
```python
UserResponse.model_validate(sqlalchemy_model)
# Error: Input should be a valid dictionary
```

---

#### 3.3.2 공통 스키마: `schemas/common.py`

```python
from typing import Any
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class EchoRequest(BaseModel):
    message: str
    data: dict[str, Any] | None = None


class EchoResponse(BaseModel):
    message: str
    data: dict[str, Any] | None = None


class ExternalResponse(BaseModel):
    source: str
    latency_ms: float
    data: dict[str, Any] | None = None


class ProtectedResponse(BaseModel):
    message: str
    user: str | None = None


class UploadResponse(BaseModel):
    filename: str
    size: int
    content_type: str | None = None
```

각 벤치마크 시나리오에 맞는 응답 스키마입니다.

---

#### 3.3.3 API 라우터

##### 라우터 통합: `v1/router.py`

```python
from fastapi import APIRouter

from src.presentation.api.v1 import health, echo, users, external, protected, upload

router = APIRouter()

# 모든 라우터 포함
router.include_router(health.router)
router.include_router(echo.router)
router.include_router(users.router)
router.include_router(external.router)
router.include_router(protected.router)
router.include_router(upload.router)
```

**장점**:
- 각 엔드포인트를 독립 모듈로 분리
- `main.py`는 단일 라우터만 등록
- API 버전 관리 용이 (`/v1`, `/v2`)

---

##### 헬스체크: `v1/health.py`

```python
from fastapi import APIRouter
from src.presentation.schemas.common import HealthResponse

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint - minimal overhead"""
    return HealthResponse(status="ok")
```

**벤치마크 목적**: 프레임워크의 최소 오버헤드 측정

---

##### 에코: `v1/echo.py`

```python
from fastapi import APIRouter
from src.presentation.schemas.common import EchoRequest, EchoResponse

router = APIRouter(tags=["echo"])

@router.post("/echo", response_model=EchoResponse)
async def echo(request: EchoRequest):
    """Echo endpoint - JSON serialization/deserialization performance"""
    return EchoResponse(message=request.message, data=request.data)
```

**벤치마크 목적**: JSON 직렬화/역직렬화 성능 측정

---

##### 사용자 CRUD: `v1/users.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_db
from src.infrastructure.database.models import UserModel
from src.presentation.schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db)):
    """Get all users - DB read performance"""
    result = await db.execute(select(UserModel))
    models = result.scalars().all()
    return [UserResponse.model_validate(m) for m in models]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get user by ID - DB read performance"""
    model = await db.get(UserModel, user_id)
    if model is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(model)


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create user - DB write performance"""
    model = UserModel(**user.model_dump())
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return UserResponse.model_validate(model)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, user: UserUpdate, db: AsyncSession = Depends(get_db)
):
    """Update user - DB write performance"""
    model = await db.get(UserModel, user_id)
    if model is None:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)

    await db.commit()
    await db.refresh(model)
    return UserResponse.model_validate(model)


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Delete user - DB write performance"""
    model = await db.get(UserModel, user_id)
    if model is None:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(model)
    await db.commit()
```

**벤치마크 목적**: 데이터베이스 CRUD 성능 측정

**핵심 패턴**:

1. **의존성 주입 (`Depends`)**
   ```python
   async def get_users(db: AsyncSession = Depends(get_db)):
   ```
   - FastAPI가 자동으로 `get_db()` 호출
   - 세션 생성 → 함수 실행 → 세션 정리

2. **SQLAlchemy 2.0 쿼리 스타일**
   ```python
   # SELECT
   result = await db.execute(select(UserModel))
   models = result.scalars().all()

   # GET BY ID
   model = await db.get(UserModel, user_id)

   # INSERT
   db.add(model)
   await db.commit()

   # DELETE
   await db.delete(model)
   await db.commit()
   ```

3. **Partial Update**
   ```python
   update_data = user.model_dump(exclude_unset=True)
   for field, value in update_data.items():
       setattr(model, field, value)
   ```
   - `exclude_unset=True`: 명시적으로 설정된 필드만 포함
   - 클라이언트가 보내지 않은 필드는 변경하지 않음

---

##### 외부 API 시뮬레이션: `v1/external.py`

```python
import asyncio
import time
from fastapi import APIRouter
from src.presentation.schemas.common import ExternalResponse

router = APIRouter(tags=["external"])

@router.get("/external", response_model=ExternalResponse)
async def call_external_api():
    """External API call simulation - async I/O performance"""
    start = time.perf_counter()

    # 외부 API 지연 시뮬레이션 (100ms)
    await asyncio.sleep(0.1)

    latency = (time.perf_counter() - start) * 1000

    return ExternalResponse(
        source="simulated_external_api",
        latency_ms=round(latency, 2),
        data={"message": "External API response"},
    )
```

**벤치마크 목적**: 비동기 I/O 성능 측정 (동시 요청 처리 능력)

---

##### 인증 필요 엔드포인트: `v1/protected.py`

```python
from fastapi import APIRouter, Header, HTTPException
from src.presentation.schemas.common import ProtectedResponse

router = APIRouter(tags=["protected"])

@router.get("/protected", response_model=ProtectedResponse)
async def protected_endpoint(
    authorization: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
):
    """Protected endpoint - middleware chain performance"""
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header required")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    token = authorization.replace("Bearer ", "")

    if len(token) < 10:
        raise HTTPException(status_code=401, detail="Invalid token")

    return ProtectedResponse(
        message="Access granted",
        user=f"user_from_token_{token[:8]}",
    )
```

**벤치마크 목적**: 헤더 파싱, 인증 로직 오버헤드 측정

---

##### 파일 업로드: `v1/upload.py`

```python
from fastapi import APIRouter, UploadFile, File
from src.presentation.schemas.common import UploadResponse

router = APIRouter(tags=["upload"])

@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """File upload endpoint - streaming performance"""
    content = await file.read()
    size = len(content)

    return UploadResponse(
        filename=file.filename or "unknown",
        size=size,
        content_type=file.content_type,
    )
```

**벤치마크 목적**: 파일 업로드 처리, 스트리밍 성능 측정

---

## 4. API 엔드포인트

| 메서드 | 경로 | 설명 | 벤치마크 목적 |
|--------|------|------|---------------|
| GET | `/` | 루트 | - |
| GET | `/health` | 헬스체크 | 최소 오버헤드 |
| POST | `/echo` | 에코 | JSON 직렬화 |
| GET | `/users` | 전체 사용자 조회 | DB 읽기 |
| GET | `/users/{id}` | 특정 사용자 조회 | DB 읽기 |
| POST | `/users` | 사용자 생성 | DB 쓰기 |
| PUT | `/users/{id}` | 사용자 수정 | DB 쓰기 |
| DELETE | `/users/{id}` | 사용자 삭제 | DB 쓰기 |
| GET | `/external` | 외부 API 시뮬레이션 | 비동기 I/O |
| GET | `/protected` | 인증 필요 | 미들웨어 체인 |
| POST | `/upload` | 파일 업로드 | 스트리밍 |

---

## 5. 설정 파일

### 5.1 `pyproject.toml`

```toml
[project]
name = "python-fastapi"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "asyncpg>=0.31.0",           # PostgreSQL 비동기 드라이버
    "fastapi>=0.123.10",         # 웹 프레임워크
    "httpx>=0.28.1",             # 비동기 HTTP 클라이언트
    "pydantic>=2.12.5",          # 데이터 검증
    "pydantic-settings>=2.12.0", # 설정 관리
    "python-multipart>=0.0.20",  # 파일 업로드 지원
    "sqlalchemy[asyncio]>=2.0.44", # ORM
    "uvicorn[standard]>=0.38.0", # ASGI 서버
]

[dependency-groups]
dev = [
    "pytest>=9.0.1",
    "pytest-asyncio>=1.3.0",
]
```

### 5.2 `Dockerfile`

```dockerfile
# syntax=docker/dockerfile:1

# ============================================
# Stage 1: Builder - Install dependencies with uv
# ============================================
FROM python:3.12-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY src/ ./src/

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.12-slim AS runtime

RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src ./src

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

EXPOSE 8000

USER appuser

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**핵심 포인트**:
- **Multi-stage build**: 빌드 도구 없이 최소 런타임 이미지
- **uv**: 빠른 의존성 설치 (Rust 기반)
- **non-root user**: 보안 강화
- **캐시 마운트**: 재빌드 시 의존성 캐시 활용

### 5.3 `docker-compose.yml`

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/benchmark
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: benchmark
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

**핵심 포인트**:
- **healthcheck**: DB가 준비된 후에만 앱 시작
- **volume**: 데이터 영속화
- **네트워크**: Docker 내부 DNS (`db` 호스트명)

### 5.4 `.env.example`

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/benchmark

# Application
APP_ENV=development
DEBUG=true
```

---

## 6. 실행 방법

### 6.1 Docker Compose (권장)

```bash
cd implementations/python-fastapi

# 빌드 및 실행
docker compose up --build

# 백그라운드 실행
docker compose up -d --build

# 로그 확인
docker compose logs -f app

# 종료
docker compose down
```

### 6.2 로컬 실행 (개발용)

```bash
cd implementations/python-fastapi

# 의존성 설치
uv sync

# PostgreSQL이 실행 중이어야 함
# .env 파일 생성 (필요 시)
cp .env.example .env

# 앱 실행
uv run uvicorn src.main:app --reload

# 또는
uv run python -m uvicorn src.main:app --reload
```

### 6.3 API 문서 확인

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 7. 데이터 흐름

### 7.1 사용자 생성 요청 흐름

```
Client                    FastAPI                 SQLAlchemy              PostgreSQL
  │                          │                        │                       │
  │  POST /users             │                        │                       │
  │  {"name":"Kim",          │                        │                       │
  │   "email":"kim@test.com"}│                        │                       │
  │ ─────────────────────────>                        │                       │
  │                          │                        │                       │
  │                    ┌─────┴─────┐                  │                       │
  │                    │ Pydantic  │                  │                       │
  │                    │ Validate  │                  │                       │
  │                    │ (UserCreate)                 │                       │
  │                    └─────┬─────┘                  │                       │
  │                          │                        │                       │
  │                    ┌─────┴─────┐                  │                       │
  │                    │ get_db()  │                  │                       │
  │                    │ Depends   │                  │                       │
  │                    └─────┬─────┘                  │                       │
  │                          │                        │                       │
  │                          │  UserModel(**data)     │                       │
  │                          │ ───────────────────────>                       │
  │                          │                        │                       │
  │                          │                        │  INSERT INTO users    │
  │                          │                        │ ──────────────────────>
  │                          │                        │                       │
  │                          │                        │       RETURNING *     │
  │                          │                        │ <──────────────────────
  │                          │                        │                       │
  │                          │    model (with id)     │                       │
  │                          │ <───────────────────────                       │
  │                          │                        │                       │
  │                    ┌─────┴─────┐                  │                       │
  │                    │ Pydantic  │                  │                       │
  │                    │ Serialize │                  │                       │
  │                    │ (UserResponse)               │                       │
  │                    └─────┬─────┘                  │                       │
  │                          │                        │                       │
  │  201 Created             │                        │                       │
  │  {"id":1,"name":"Kim",   │                        │                       │
  │   "email":"kim@test.com"}│                        │                       │
  │ <─────────────────────────                        │                       │
```

### 7.2 객체 변환 흐름 (Pragmatic)

```
HTTP Request (JSON)
       │
       ▼
┌──────────────────┐
│ Pydantic Schema  │  UserCreate
│ (Validation)     │
└────────┬─────────┘
         │ .model_dump()
         ▼
┌──────────────────┐
│ SQLAlchemy Model │  UserModel
│ (ORM)            │
└────────┬─────────┘
         │ DB operation
         ▼
    [PostgreSQL]
         │
         ▼
┌──────────────────┐
│ SQLAlchemy Model │  UserModel (with id)
└────────┬─────────┘
         │ .model_validate()
         ▼
┌──────────────────┐
│ Pydantic Schema  │  UserResponse
│ (Serialization)  │
└────────┬─────────┘
         │
         ▼
HTTP Response (JSON)
```

**총 변환**: 2번 (Schema → Model → Schema)

---

## 마무리

이 문서는 FastAPI 벤치마크 앱의 전체 구조를 설명합니다.
Pragmatic Architecture를 채택하여 프레임워크 자체의 성능을 정확히 측정할 수 있도록 설계했습니다.

다음 단계:
1. Docker 빌드 테스트
2. 앱 실행 확인
3. k6 벤치마크 스크립트 작성
4. 다른 프레임워크 구현 (Django, Flask, Express 등)
