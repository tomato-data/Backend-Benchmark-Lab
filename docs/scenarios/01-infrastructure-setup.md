# Infrastructure Setup

## 개요

벤치마크 테스트를 위한 인프라 구성 문서. 모든 백엔드 구현체가 동일한 환경에서 테스트될 수 있도록 Docker Compose 기반 통합 환경을 구축한다.

---

## Docker Compose 아키텍처

### 설계 원칙

1. **단일 포트 정책**: 모든 백엔드는 `8000`번 포트 사용
2. **Profile 기반 선택**: 한 번에 하나의 백엔드만 실행
3. **공유 DB**: PostgreSQL을 공통 데이터베이스로 사용

### 왜 이 구조인가?

- k6 스크립트에서 `BASE_URL`을 고정할 수 있음
- 백엔드 교체 시 스크립트 수정 불필요
- 동일 DB 환경에서 공정한 비교 가능

### 파일 위치

```
implementations/
├── docker-compose.yml    # 통합 Compose 파일
├── python-fastapi/
├── python-django/
└── ...
```

### 사용법

```bash
cd implementations

# PostgreSQL만 실행
docker compose up postgres -d

# 특정 백엔드 실행 (profile 사용)
docker compose --profile fastapi up

# 종료
docker compose down
```

### 주의사항: DATABASE_URL

SQLAlchemy는 `postgresql` dialect를 사용한다 (`postgres`가 아님):

```
# 올바른 형식
postgresql+asyncpg://user:pass@host:5432/db

# 잘못된 형식 (에러 발생)
postgres+asyncpg://user:pass@host:5432/db
```

---

## Docker Named Volume

각 프로젝트의 볼륨은 자동으로 분리된다:

```
# docker-compose.yml의 볼륨명이 같아도
implementations/  → implementations_postgres_data
other_project/    → other_project_postgres_data
```

데이터 충돌 걱정 없음.

---

## 다음 단계

→ [02-k6-benchmark-setup.md](./02-k6-benchmark-setup.md)
