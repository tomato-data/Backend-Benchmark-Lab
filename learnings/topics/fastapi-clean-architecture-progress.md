# FastAPI 벤치마크 앱 구현 진행 기록

## 개요

- **목표**: FastAPI 벤치마크 앱 구현
- **패키지 매니저**: uv
- **최종 아키텍처**: 간소화된 실용적 구조 (Pragmatic Architecture)

---

## 아키텍처 여정: Clean Architecture → Pragmatic Architecture

### Phase 1: Strict Clean Architecture 학습 (완료)

처음에는 **Strict Clean Architecture**를 적용하여 개념을 학습했습니다.

```
┌─────────────────────────────────────────────────────────┐
│              Presentation (가장 바깥)                    │
│        FastAPI, Pydantic Schemas, Middleware            │
├─────────────────────────────────────────────────────────┤
│                    Application                           │
│              Use Cases, DTOs, 비즈니스 로직              │
├─────────────────────────────────────────────────────────┤
│                    Infrastructure                        │
│     SQLAlchemy, External APIs, Repository 구현체         │
├─────────────────────────────────────────────────────────┤
│                 Domain (가장 안쪽)                       │
│         Entities, Repository Interfaces                  │
└─────────────────────────────────────────────────────────┘
            ↑ 의존성 방향: 바깥 → 안쪽으로만
```

**학습한 핵심 개념들:**

1. **의존성 규칙**: 안쪽 레이어는 바깥 레이어를 절대 알지 못함
2. **의존성 역전(DIP)**: 추상(인터페이스)에 의존, 구현에 의존하지 않음
3. **단일 책임**: 각 레이어는 하나의 책임만 가짐

---

### Phase 2: 방향 전환 결정

#### 문제 인식

Strict Clean Architecture 구현 중 다음 문제들이 발견됨:

**1. 과도한 변환 오버헤드**
```
요청
  ↓
Router (Pydantic Schema)
  ↓ 변환
UseCase (DTO)
  ↓ 변환
Repository (Domain Entity)
  ↓ 변환
SQLAlchemy Model
  ↓
DB 저장
  ↓ 역변환 3회
응답
```

**총 6번의 객체 변환** - 벤치마크 앱에서 불필요한 오버헤드

**2. 벤치마크 목적과의 충돌**

| 관점 | Strict Clean Architecture | 벤치마크 목적 |
|------|---------------------------|---------------|
| 목표 | 유지보수성, 테스트 용이성 | **프레임워크 순수 성능 측정** |
| 복잡도 | 높음 (4개 레이어) | 낮을수록 좋음 |
| 공정성 | - | 다른 프레임워크와 **동일 조건** 필요 |

**3. 순수성 vs 실용성 논쟁**

구현 중 타입 에러 발생:
```
"CoroutineType[Any, Any, list[User]]"은 "list[User]"에 할당할 수 없습니다.
```

- Domain의 추상 메서드는 동기(`def`)
- Infrastructure의 구현은 비동기(`async def`)
- 해결: Domain도 `async`로 수정 → **순수성 타협**

**결론:**
- 이미 순수성을 타협했고
- 벤치마크 목적에 맞지 않으며
- 다른 프레임워크와 공정한 비교가 어려움

→ **Pragmatic Architecture로 간소화 결정**

---

### Phase 3: Pragmatic Architecture (현재)

#### 간소화된 구조

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation                          │
│     FastAPI Router + Pydantic Schema (입출력 통일)       │
├─────────────────────────────────────────────────────────┤
│                    Infrastructure                        │
│         SQLAlchemy Model (DB 직접 매핑)                  │
└─────────────────────────────────────────────────────────┘
```

**제거된 것들:**
- ❌ Domain 레이어 (Entity, Repository Interface)
- ❌ Application 레이어 (UseCase, DTO)

**유지된 것들:**
- ✅ Presentation 레이어 (Router, Pydantic Schema)
- ✅ Infrastructure 레이어 (SQLAlchemy Model, DB Connection)

---

## 전체 플로우 상세 설명

### 간소화된 요청-응답 플로우

```
┌─────────────────────────────────────────────────────────────────────┐
│                         HTTP 요청                                    │
│                   POST /users {"name": "토마토", "email": "..."}     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Router                                  │
│  @router.post("/users")                                             │
│  async def create_user(user: UserCreate, db: AsyncSession):         │
│      ↓                                                              │
│      Pydantic이 자동으로 JSON → UserCreate 변환                      │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     SQLAlchemy 작업                                  │
│  model = UserModel(**user.model_dump())                             │
│  db.add(model)                                                      │
│  await db.commit()                                                  │
│  await db.refresh(model)                                            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      응답 반환                                       │
│  return UserResponse.model_validate(model)                          │
│      ↓                                                              │
│      Pydantic이 자동으로 SQLAlchemy Model → JSON 변환                │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         HTTP 응답                                    │
│                   {"id": 1, "name": "토마토", "email": "..."}        │
└─────────────────────────────────────────────────────────────────────┘
```

### 변환 횟수 비교

| 구조 | 변환 횟수 | 설명 |
|------|----------|------|
| Strict Clean Architecture | 6회 | JSON→Schema→DTO→Entity→Model→DB→... |
| **Pragmatic Architecture** | **2회** | JSON→Schema→Model→DB→Model→Schema→JSON |

---

## 파일 구조 (간소화 후)

```
src/
├── main.py                           # FastAPI 앱 진입점
│
├── infrastructure/
│   └── database/
│       ├── connection.py             # DB 연결 설정
│       └── models.py                 # SQLAlchemy 모델
│
└── presentation/
    ├── schemas/
    │   ├── user.py                   # Pydantic 스키마
    │   └── common.py                 # 공통 스키마
    └── api/
        └── v1/
            ├── router.py             # 라우터 통합
            ├── health.py             # /health
            ├── echo.py               # /echo
            ├── users.py              # /users
            ├── external.py           # /external
            ├── protected.py          # /protected
            └── upload.py             # /upload
```

**삭제된 디렉토리:**
- `src/domain/` (entities, repositories)
- `src/application/` (use_cases, dto)

---

## 구현 상세

### 1. Infrastructure - Database Connection

**파일**: `src/infrastructure/database/connection.py`

```python
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/benchmark"
)

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
```

**핵심 개념:**
- `create_async_engine`: 비동기 DB 엔진 (연결 풀 관리)
- `async_sessionmaker`: 세션 팩토리
- `get_db`: FastAPI Depends용 의존성 주입 함수
- `expire_on_commit=False`: 커밋 후에도 객체 속성 접근 가능

---

### 2. Infrastructure - SQLAlchemy Model

**파일**: `src/infrastructure/database/models.py`

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

**SQLAlchemy 2.0 스타일:**
- `Mapped[타입]`: 타입 힌트 + ORM 매핑 동시 제공
- `mapped_column()`: 컬럼 속성 정의

---

### 3. Presentation - Pydantic Schema

**파일**: `src/presentation/schemas/user.py`

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

**핵심:**
- `ConfigDict(from_attributes=True)`: SQLAlchemy Model → Pydantic 자동 변환 허용
- `model_validate(orm_model)`: ORM 객체를 Pydantic 모델로 변환

---

### 4. Presentation - Router

**파일**: `src/presentation/api/v1/users.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_db
from src.infrastructure.database.models import UserModel
from src.presentation.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserModel))
    models = result.scalars().all()
    return [UserResponse.model_validate(m) for m in models]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    model = await db.get(UserModel, user_id)
    if model is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(model)


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    model = UserModel(**user.model_dump())
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return UserResponse.model_validate(model)
```

---

## 학습 내용 정리

### Clean Architecture에서 배운 것들

1. **의존성 역전 원칙(DIP)**
   - 고수준 모듈이 저수준 모듈에 의존하지 않음
   - 추상(인터페이스)에 의존

2. **레이어 분리의 장점**
   - 테스트 용이성
   - 기술 변경 시 영향 범위 최소화

3. **순수성 vs 실용성 트레이드오프**
   - 완벽한 분리는 비용이 높음
   - 프로젝트 목적에 맞는 수준 선택 필요

### 벤치마크 프로젝트에서의 교훈

1. **목적에 맞는 아키텍처 선택**
   - 엔터프라이즈 앱 → Clean Architecture 적합
   - 벤치마크 앱 → 간소화된 구조 적합

2. **공정한 비교를 위한 동일 조건**
   - 모든 프레임워크가 비슷한 복잡도를 가져야 함

3. **과도한 추상화의 비용**
   - 객체 변환 오버헤드
   - 코드 복잡도 증가

---

## API 엔드포인트 구현 현황

| 엔드포인트 | 메서드 | 시나리오 | 상태 |
|-----------|--------|---------|------|
| `/health` | GET | 경량 API | 구현 예정 |
| `/echo` | POST | JSON 직렬화 | 구현 예정 |
| `/users` | GET | DB 읽기 | 구현 예정 |
| `/users` | POST | DB 쓰기 | 구현 예정 |
| `/users/{id}` | GET | DB 읽기 | 구현 예정 |
| `/external` | GET | 외부 API | 구현 예정 |
| `/protected` | GET | 미들웨어 | 구현 예정 |
| `/upload` | POST | 파일 업로드 | 구현 예정 |

---

## 다음 단계

1. [x] 아키텍처 간소화
2. [ ] Pydantic Schema 작성
3. [ ] FastAPI Router 작성
4. [ ] main.py 통합
5. [ ] Dockerfile 작성
6. [ ] 테스트 실행
