# FastAPI Strict Clean Architecture 구현

> **목표**: Pragmatic 아키텍처와 Strict Clean Architecture를 비교하여 "아키텍처 오버헤드가 실제 성능에 얼마나 영향을 주는가?"를 검증

---

## 1. 아키텍처 비교

### Pragmatic (기존)

```
src/
├── presentation/          # API 레이어
│   └── api/v1/users.py   # 라우터에서 직접 DB 접근
└── infrastructure/
    └── database/
        └── models.py     # SQLAlchemy ORM
```

**특징**: 라우터(Presentation)에서 **직접** SQLAlchemy 모델 사용 → 레이어 경계가 모호

### Strict Clean Architecture (신규)

```
src/
├── domain/                    # 핵심 비즈니스 로직 (의존성 없음)
│   ├── entities/             # 순수 Python 클래스
│   ├── repositories/         # ABC (추상 인터페이스)
│   └── use_cases/            # 비즈니스 로직
├── application/               # 유스케이스 조율
│   └── services/
├── infrastructure/            # 외부 의존성 구현
│   └── database/
│       ├── models.py         # SQLAlchemy ORM
│       └── repositories/     # ABC 구현체
└── presentation/              # HTTP 인터페이스
    ├── api/v1/
    └── schemas/              # Pydantic (API 전용)
```

**특징**: 레이어 간 명확한 경계, 의존성 역전 원칙(DIP) 적용

---

## 2. 핵심 차이점

| 관점 | Pragmatic | Strict Clean |
|------|-----------|--------------|
| **의존성 방향** | Presentation → Infrastructure | Presentation → Application → Domain ← Infrastructure |
| **DB 접근** | 라우터에서 직접 | Repository 패턴으로 추상화 |
| **비즈니스 로직** | 라우터에 혼재 | Use Case에 분리 |
| **테스트 용이성** | DB 모킹 필요 | Repository 모킹으로 단위 테스트 |
| **코드량** | 적음 | 많음 (2~3배) |
| **런타임 오버헤드** | 적음 | 추가 레이어로 인한 오버헤드 |

---

## 3. 구현 단계

### Step 1: Domain 레이어 (완료)

프로젝트 초기화:
```bash
cd implementations
mkdir python-fastapi-strict && cd python-fastapi-strict
uv init --name fastapi-strict
uv add fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" asyncpg pydantic python-multipart
```

#### 3.1 Entity 정의 (`src/domain/entities/user.py`)

```python
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
    id: Optional[int]
    name: str
    email: str

    def __post_init__(self):
        if not self.name or len(self.name) > 100:
            raise ValueError("Name must be 1-100 characters")
        if not self.email or "@" not in self.email:
            raise ValueError("Invalid email format")
```

**왜 dataclass인가?**
- Python 표준 라이브러리 (외부 의존성 없음)
- `__eq__`, `__repr__` 자동 생성
- 불변성 필요시 `frozen=True` 옵션 가능

#### 3.2 Repository 인터페이스 (`src/domain/repositories/user_repository.py`)

```python
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
        pass

    @abstractmethod
    async def find_by_id(self, user_id: int) -> Optional[User]:
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        pass
```

#### 3.3 Use Case 정의 (`src/domain/use_cases/user_use_cases.py`)

```python
from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository


class GetAllUsersUseCase:
    def __init__(self, repository: UserRepository):
        self._repository = repository

    async def execute(self) -> list[User]:
        return await self._repository.find_all()


class CreateUserUseCase:
    def __init__(self, repository: UserRepository):
        self._repository = repository

    async def execute(self, name: str, email: str) -> User:
        user = User(id=None, name=name, email=email)
        return await self._repository.save(user)
```

---

### Step 2: Infrastructure 레이어 (완료)

#### 3.4 Database Connection (`src/infrastructure/database/connection.py`)

```python
import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 환경변수에서 DB URL 읽기 (Docker 환경 대응)
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/benchmark"
)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
```

> **주의**: 환경변수명 오타 주의! `DATABASE_URL`을 `DATABSE_URL`로 잘못 쓰면 connection refused 에러 발생

#### 3.5 ORM Model (`src/infrastructure/database/models.py`)

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

#### 3.6 Repository 구현체 (`src/infrastructure/database/repositories/user_repository_impl.py`)

```python
from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.database.models import UserModel


class UserRepositoryImpl(UserRepository):
    """
    UserRepository의 실제 구현체
    - Domain의 ABC를 상속
    - SQLAlchemy를 사용하여 실제 DB 작업
    - Entity ↔ ORM Model 변환 담당
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    def _to_entity(self, model: UserModel) -> User:
        return User(id=model.id, name=model.name, email=model.email)

    async def find_all(self) -> list[User]:
        result = await self._session.execute(select(UserModel))
        return [self._to_entity(m) for m in result.scalars().all()]

    async def save(self, user: User) -> User:
        model = UserModel(name=user.name, email=user.email)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._to_entity(model)
```

---

## 4. Q&A: ABC 패턴과 의존성 역전

### Q: UserRepository(ABC)가 UserRepositoryImpl로 "넘겨주는" 역할인가요?

**A**: "넘겨준다"보다는 **"대체된다"**가 더 정확합니다.

#### 코드 작성 시 (컴파일 타임)
```python
class GetAllUsersUseCase:
    def __init__(self, repository: UserRepository):  # ← 추상 타입만 알고 있음
        self._repository = repository
```

#### 실제 실행 시 (런타임)
```python
repo = UserRepositoryImpl(session)       # ← 구현체 인스턴스 생성
use_case = GetAllUsersUseCase(repo)      # ← 구현체를 주입!
await use_case.execute()                  # ← UserRepositoryImpl.find_all() 호출됨
```

#### 그림으로 이해

```
┌─────────────────────────────────────────────────┐
│  UseCase (코드 작성 시)                          │
│  "나는 UserRepository 타입만 알아"               │
│  repository: UserRepository  ← 추상 타입         │
└─────────────────────────────────────────────────┘
                    ↓ 런타임에 주입
┌─────────────────────────────────────────────────┐
│  UseCase (실제 실행 시)                          │
│  repository: UserRepositoryImpl ← 실제 객체      │
│              ↓                                  │
│         find_all() 호출 → SQLAlchemy 쿼리 실행  │
└─────────────────────────────────────────────────┘
```

#### 왜 이렇게 하나요?

1. **교체 가능성**: 테스트 시 DB 없이 Fake 구현체 사용 가능
2. **Domain 순수성**: Domain 레이어에 `sqlalchemy` import 없음
3. **의존성 역전**: 상위 레이어(Domain)가 하위 레이어(Infrastructure)를 모름

```python
# 테스트할 때 - DB 없이!
class FakeUserRepository(UserRepository):
    async def find_all(self):
        return [User(id=1, name="Test", email="test@test.com")]

use_case = GetAllUsersUseCase(FakeUserRepository())  # ← 가짜 주입
```

---

### Step 3: Application 레이어 (완료)

#### 3.7 User Service (`src/application/services/user_service.py`)

```python
from typing import Optional

from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository
from src.domain.use_cases.user_use_cases import (
    CreateUserUseCase,
    DeleteUserUseCase,
    GetAllUsersUseCase,
    GetUserByIdUseCase,
)


class UserService:
    """
    Application Service - Use Case 조율자

    역할:
    - 여러 Use Case를 조합하여 복잡한 비즈니스 흐름 처리
    - 트랜잭션 경계 관리 (필요시)
    - 현재는 단순 위임이지만, 확장 가능
    """

    def __init__(self, repository: UserRepository):
        self._repository = repository

    async def get_all_users(self) -> list[User]:
        use_case = GetAllUsersUseCase(self._repository)
        return await use_case.execute()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        use_case = GetUserByIdUseCase(self._repository)
        return await use_case.execute(user_id)

    async def create_user(self, name: str, email: str) -> User:
        use_case = CreateUserUseCase(self._repository)
        return await use_case.execute(name, email)

    async def delete_user(self, user_id: int) -> bool:
        use_case = DeleteUserUseCase(self._repository)
        return await use_case.execute(user_id)
```

---

### Step 4: Presentation 레이어 (완료)

#### 3.8 의존성 주입 (`src/presentation/api/dependencies.py`)

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.user_service import UserService
from src.infrastructure.database.connection import get_db
from src.infrastructure.database.repositories.user_repository_impl import UserRepositoryImpl


async def get_user_service(
    session: AsyncSession = Depends(get_db),
) -> UserService:
    """
    의존성 주입 체인: DB Session → Repository → Service
    이것이 Clean Architecture의 "조립" 지점입니다.
    """
    repository = UserRepositoryImpl(session)
    return UserService(repository)
```

#### 3.9 Pydantic Schema (`src/presentation/schemas/user.py`)

```python
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr  # Strict: 이메일 검증 추가 (email-validator 필요)


class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    model_config = {"from_attributes": True}
```

> **Strict vs Pragmatic 차이점**: Strict 버전은 `EmailStr`로 이메일 형식을 검증합니다. 이를 위해 `uv add email-validator` 필요.

---

### Step 5: Docker 설정 (완료)

#### 3.10 Dockerfile

Pragmatic 버전과 동일한 멀티스테이지 빌드 사용.

#### 3.11 docker-compose.yml 서비스 추가

```yaml
python-fastapi-strict:
  build: ./python-fastapi-strict
  profiles: ["fastapi-strict"]
  ports:
    - "8000:8000"
  environment:
    DATABASE_URL: postgresql+asyncpg://benchmark:benchmark@postgres:5432/benchmark
  depends_on:
    postgres:
      condition: service_healthy
  deploy:
    resources:
      limits:
        cpus: "2"
        memory: 2G
```

#### 3.12 실행 및 테스트

```bash
cd implementations
docker compose --profile fastapi-strict up --build -d

# 테스트
curl http://localhost:8000/api/v1/health
# {"status":"ok","server":"python-fastapi-strict"}
```

---

## 5. 트러블슈팅

### 에러 1: `email-validator is not installed`

**원인**: `EmailStr` 사용 시 `email-validator` 패키지 필요

**해결**:
```bash
uv add email-validator
```

### 에러 2: `Connection refused`

**원인**: `DATABASE_URL` 환경변수명 오타 (예: `DATABSE_URL`)

**해결**: 환경변수명 정확히 확인

### 에러 3: `Name or service not known`

**원인**: 하드코딩된 DB 호스트명 (Docker 환경에서 `db` vs `postgres`)

**해결**: 환경변수로 DB URL 주입

---

## 6. 벤치마크 측정 대상

| 항목 | 측정 방법 |
|------|----------|
| 함수 호출 오버헤드 | 레이어 수 증가에 따른 지연 |
| 객체 변환 비용 | Entity ↔ ORM Model ↔ Pydantic Schema |
| 메모리 사용량 | 추가 객체 생성으로 인한 메모리 증가 |
| 실제 차이 의미 | I/O 대비 아키텍처 오버헤드 비율 |

---

## 7. 진행 상황

- [x] Step 1: Domain 레이어 (Entity, Repository ABC, Use Cases)
- [x] Step 2: Infrastructure 레이어 (DB Connection, ORM, Repository Impl)
- [x] Step 3: Application 레이어 (Service)
- [x] Step 4: Presentation 레이어 (Router, Schema, DI)
- [x] Step 5: Docker 설정 및 테스트

---

## 8. 다음 단계

### 옵션 A: 벤치마크 실행 및 비교
Pragmatic vs Strict 성능 비교:
```bash
# Strict 벤치마크
docker compose --profile fastapi-strict up -d
./runner/run-benchmark.sh

# Pragmatic 벤치마크
docker compose --profile fastapi-pragmatic up -d
./runner/run-benchmark.sh
```

### 옵션 B: 누락된 엔드포인트 추가 (완료)
모든 엔드포인트 구현 완료:
- [x] `/health` - Health check
- [x] `/echo` - JSON echo
- [x] `/users` - CRUD
- [x] `/external` - External API simulation
- [x] `/protected` - 인증 미들웨어 (Depends 패턴)
- [x] `/upload` - 파일 업로드

#### Strict vs Pragmatic 차이점: 인증 처리

**Pragmatic**: 엔드포인트 내에서 직접 인증 로직 처리
```python
@router.get("/protected")
async def protected_endpoint(authorization: str | None = Header(...)):
    if authorization is None:
        raise HTTPException(...)
    # ... 인증 로직
```

**Strict**: 의존성 주입으로 분리 (Clean Architecture)
```python
# middleware/auth.py
async def verify_token(authorization: str | None = Header(...)) -> str:
    # 인증 로직 분리
    return token

# api/v1/protected.py
@router.get("/protected")
async def protected_endpoint(token: str = Depends(verify_token)):
    # 인증은 미들웨어가 처리, 엔드포인트는 비즈니스 로직만
    return ProtectedResponse(...)
```

### 옵션 C: 코드 품질 개선
- 타입 힌트 완성도 검증
- 에러 핸들링 통일
- 로깅 추가
