# Backend-Benchmark-Lab Roadmap

> 프로젝트 진행 상황 추적 및 향후 계획

---

## Phase 1: 기본 인프라 ✅ 완료

- [x] 프로젝트 구조 설계
- [x] Docker Compose 환경 구성
- [x] PostgreSQL + 초기 스키마
- [x] k6 벤치마크 기본 설정
- [x] 모니터링 스택 (Prometheus + Grafana + cAdvisor)

---

## Phase 2: Basic 시나리오 (01-08) ✅ 완료

프레임워크 간 성능 비교를 위한 기본 시나리오

| #   | 시나리오         | 설명                               | 상태 |
| --- | ---------------- | ---------------------------------- | ---- |
| 01  | lightweight      | Health check (프레임워크 오버헤드) | ✅   |
| 02  | json-payload     | JSON 직렬화/역직렬화               | ✅   |
| 03  | db-read          | 사용자 목록 조회 (SELECT)          | ✅   |
| 04  | db-write         | 사용자 생성 (INSERT)               | ✅   |
| 05  | external-api     | 외부 API 호출 시뮬레이션           | ✅   |
| 06  | middleware-chain | 인증 + 로깅 미들웨어               | ✅   |
| 07  | file-upload      | 파일 업로드                        | ✅   |
| 08  | concurrent-mixed | 혼합 워크로드                      | ✅   |

---

## Phase 3: 프레임워크 구현

### Python ✅ 완료

| 프레임워크 | 아키텍처                    | 상태    | 벤치마크 |
| ---------- | --------------------------- | ------- | -------- |
| FastAPI    | Pragmatic                   | ✅ 완료 | ✅ 완료  |
| FastAPI    | Strict (Clean Architecture) | ✅ 완료 | ✅ 완료  |
| Django     | DRF ViewSet                 | ✅ 완료 | ✅ 완료  |
| Flask      | -                           | ⏳ 예정 | -        |

### TypeScript (Node.js) 🔄 진행 중

| 프레임워크 | 아키텍처  | 상태    | 벤치마크 |
| ---------- | --------- | ------- | -------- |
| Express    | Pragmatic | ✅ 완료 | ⏳ 예정  |
| Fastify    | -         | ⏳ 예정 | -        |
| NestJS     | -         | ⏳ 예정 | -        |

### Go ⏳ 예정

| 프레임워크 | 상태    |
| ---------- | ------- |
| Fiber      | ⏳ 예정 |
| Gin        | ⏳ 예정 |

---

## Phase 4: 시나리오 디렉토리 재구성 ✅ 완료

```
scenarios/
├── basic/           # 기존 01-08 이동 ✅
├── db-advanced/     # DB 최적화 시나리오
├── caching/         # 캐싱 시나리오
├── real-world/      # 실제 서비스 패턴
└── stress/          # 스트레스 테스트
```

- [x] 기존 01-08 시나리오를 `basic/`으로 이동
- [x] runner 스크립트 경로 수정 (`run-benchmark.sh`)
- [ ] 카테고리별 runner 스크립트 추가 (향후)

---

## Phase 5: DB 심화 시나리오 (db-advanced) 🔄 진행 중

> 대상: 모든 프레임워크 (pragmatic, strict, django, ...)
>
> **참고**: 랜덤 접근 패턴으로 PostgreSQL Buffer Cache 영향 최소화. 캐싱 효과 비교는 마지막 복합 시나리오에서 cold/warm 2버전으로 측정 예정.

| #   | 시나리오           | 설명                                  | 상태    |
| --- | ------------------ | ------------------------------------- | ------- |
| 09  | db-pagination      | OFFSET vs Cursor 페이지네이션         | ✅ 완료 |
| 10  | db-column-overhead | 컬럼 수 + 데이터 타입별 조회 오버헤드 | ✅ 완료 |
| 11  | db-n-plus-one      | N+1 문제 (lazy vs eager loading)      | ✅ 완료 |
| 12  | db-bulk-operations | 대량 INSERT/UPDATE (1000건+)          | ⏳ 예정    |
| 13  | db-transactions    | 복합 트랜잭션 (락 경합)               | ⏳ 예정    |

### 프레임워크별 적용 현황

| 시나리오 | fastapi-pragmatic | fastapi-strict | django |
| -------- | ----------------- | -------------- | ------ |
| 09-db-pagination | ✅ | ⏳ 예정 | ⏳ 예정 |
| 10-db-column-overhead | ✅ | ⏳ 예정 | ⏳ 예정 |
| 11-db-n-plus-one | ✅ | ⏳ 예정 | ⏳ 예정 |

### 09-db-pagination 상세 ✅ 완료

OFFSET vs Cursor 페이지네이션 성능 비교

- **테이블**: `users` (100,000건) - 기존 테이블 통합
- **Cursor 기준**: `id` (PK) - 실무에서는 `created_at + id` Base64 인코딩 사용
- **핵심**: OFFSET은 뒤쪽 페이지일수록 느림 (O(offset+limit)) vs Cursor는 일정 (O(limit))
- **결과**: Cursor가 OFFSET 대비 **1.7배 빠름** (p95 기준: 34ms vs 60ms)

| 작업                         | 상태    |
| ---------------------------- | ------- |
| DB 스키마 (100,000건 시드)   | ✅ 완료 |
| Pydantic 스키마              | ✅ 완료 |
| 라우터 구현 (offset, cursor) | ✅ 완료 |
| k6 시나리오                  | ✅ 완료 |
| 문서화 (`docs/15`)           | ✅ 완료 |

### 10-db-column-overhead 상세 ✅ 완료

컬럼 수 및 데이터 타입에 따른 조회 오버헤드 측정

- **결과**: 컬럼 5개 → 50개 (10배) 증가 시 성능 **1.45배** 저하
- **인사이트**: 예상보다 선형적이지 않음 → 네트워크/직렬화가 더 큰 영향
- **데이터 타입**: 모든 타입 36~41ms로 차이 미미 (±7%), JSONB만 약간 느림
- **Cold Start 발견**: k6 그룹 첫 번째 호출 시 +10ms 오버헤드 발생

#### A. 컬럼 수 비교

| 테이블             | 컬럼 수 | 예상 성능       |
| ------------------ | ------- | --------------- |
| `users_narrow`     | 5개     | 가장 빠름       |
| `users_wide`       | 20개    | 1.5~2x 느림     |
| `users_extra_wide` | 50개    | 2~3x 느림       |
| `users_wide` (5개 SELECT) | 20개 중 5개 | Narrow와 유사 |

#### B. 데이터 타입별 비교 (각 5개 컬럼)

| 테이블                 | 타입      | 예상 순위         |
| ---------------------- | --------- | ----------------- |
| `users_type_int`       | INTEGER   | 1위 (가장 빠름)   |
| `users_type_timestamp` | TIMESTAMP | 2위               |
| `users_type_uuid`      | UUID      | 3위               |
| `users_type_varchar`   | VARCHAR   | 4위               |
| `users_type_text`      | TEXT      | 5위               |
| `users_type_jsonb`     | JSONB     | 6위 (가장 느림)   |

#### B-2. 단일 컬럼 추가 비교 (향후 실험)

> 기존 `users` 테이블에 각 타입별 1개 컬럼만 추가한 테이블 비교
> 실무 질문: "컬럼 하나 추가하면 얼마나 느려질까?"
> 예상: 차이 미미 (1-5% 미만), 하지만 검증 필요

**학습 포인트**:
- `SELECT *` 피하기
- ORM 기본 동작 (전체 컬럼 로드) 주의
- **Projection**의 중요성
- **JSONB는 편리하지만 비용이 큼**

### 11-db-n-plus-one 상세 ✅ 완료

N+1 문제와 로딩 전략별 성능 비교

- **테이블**: `authors` (1,000건) + `posts` (8,000건, author당 8개)
- **로딩 전략**: Lazy (N+1) vs Eager (joinedload) vs Subquery (selectinload)
- **결과**: Eager가 Lazy 대비 **4.1배 빠름** (p95 기준: 24.86ms vs 102.71ms)

| 로딩 전략 | 쿼리 수 | p(95) | Lazy 대비 |
|-----------|---------|-------|-----------|
| Lazy (N+1) | 1 + 20 = 21 | 102.71ms | 1.0x (기준) |
| Eager (JOIN) | 1 | 24.86ms | **4.1x 빠름** |
| Subquery (IN) | 2 | 27.99ms | **3.7x 빠름** |

| 작업                         | 상태    |
| ---------------------------- | ------- |
| DB 스키마 (authors, posts)   | ✅ 완료 |
| SQLAlchemy 모델 (relationship) | ✅ 완료 |
| Pydantic 스키마              | ✅ 완료 |
| 라우터 구현 (lazy, eager, subquery) | ✅ 완료 |
| k6 시나리오 (랜덤 offset)    | ✅ 완료 |
| 문서화 (`docs/17`)           | ✅ 완료 |

**핵심 인사이트**:
- Async SQLAlchemy는 의도적으로 lazy loading을 차단 (MissingGreenlet)
- 1:Many 관계에는 `selectinload`가 적합 (중복 데이터 없음)
- 1:1, 1:Few 관계에는 `joinedload`가 적합 (최소 쿼리)

---

## Phase 6: 캐싱 시나리오 (caching) ⏳ 예정

> DB Buffer Cache (Phase 5)와의 비교 포인트:
> - Phase 5: DB 레벨 캐싱 (PostgreSQL Buffer Cache)
> - Phase 6: 애플리케이션 레벨 캐싱 (Redis)

| #   | 시나리오      | 설명                       | 상태 |
| --- | ------------- | -------------------------- | ---- |
| 14  | cache-hit     | Redis 캐시 히트            | ⏳   |
| 15  | cache-miss-db | 캐시 미스 → DB → 캐시 저장 | ⏳   |

---

## Phase 7: 실제 서비스 패턴 (real-world) ⏳ 예정

> 대상: 모든 프레임워크 (아키텍처 차이가 드러나는 시나리오)

| #   | 시나리오        | 설명                             | 상태 |
| --- | --------------- | -------------------------------- | ---- |
| 16  | auth-jwt        | JWT 생성/검증 오버헤드           | ⏳   |
| 17  | aggregation     | 집계 쿼리 (COUNT, SUM, GROUP BY) | ⏳   |
| 18  | search          | 텍스트 검색 (LIKE vs Full-text)  | ⏳   |
| 19  | real-world-flow | 인증→조회→수정→응답 E2E          | ⏳   |

---

## Phase 8: 스트레스 테스트 (stress) ⏳ 예정

| #   | 시나리오      | 설명                                 | 상태 |
| --- | ------------- | ------------------------------------ | ---- |
| 20  | spike-traffic | 트래픽 급증 (10→100→10 VUs)          | ⏳   |
| 21  | long-running  | 장시간 부하 (5분+), 메모리 누수 탐지 | ⏳   |

---

## Phase 9: 복합 시나리오 (cold/warm 비교) ⏳ 예정

> DB Buffer Cache + Redis Cache 효과를 극적으로 비교

| 시나리오            | 설명                         |
| ------------------- | ---------------------------- |
| 22-mixed-cold       | 서버 재시작 후 첫 실행       |
| 22-mixed-warm       | 동일 요청 반복 후 실행       |

**측정 포인트**:
- PostgreSQL Buffer Cache 워밍업 효과
- Redis 캐시 히트율 변화
- 전체 응답 시간 차이

---

## Phase 10: Variant 실험 ⏳ 예정

### FastAPI

- [ ] SQLAlchemy vs Raw asyncpg
- [ ] Pydantic vs msgspec
- [ ] Uvicorn vs Gunicorn+Uvicorn

### Django

- [ ] sync vs async
- [ ] ViewSet vs APIView
- [ ] ORM vs Raw SQL

### 공통

- [ ] 워커 수 실험: 1, 2, 4, 8, (2\*CPU+1)
- [ ] 커넥션 풀 크기: 5, 10, 20, 50
- [ ] **암호 해시 알고리즘**: Argon2 (cffi) vs bcrypt 성능 비교
  - 동일 비밀번호로 해시 생성/검증 속도 측정
  - 메모리 사용량 비교
  - 보안 권장 설정에서의 실제 오버헤드

---

## 완료된 주요 성과

### 벤치마크 결과 (2024-12)

| 비교                         | 결과                             |
| ---------------------------- | -------------------------------- |
| FastAPI vs Django (경량 API) | FastAPI **7~9배** 빠름           |
| FastAPI vs Django (DB 읽기)  | Django **1.6배** 빠름            |
| FastAPI vs Django (혼합)     | FastAPI **1.4배** 빠름           |
| Pragmatic vs Strict          | 경량 API에서 **10~17%** 오버헤드 |

상세: `docs/99-benchmark-results.md`, `docs/DISCOVERIES.md`

---

## 문서화

| 문서                  | 내용                              |
| --------------------- | --------------------------------- |
| `docs/01-05`          | 인프라 + 초기 설정                |
| `docs/06-10`          | 시나리오 상세                     |
| `docs/11`             | 벤치마크 자동화                   |
| `docs/12`             | Django 구현 가이드                |
| `docs/13`             | 모니터링                          |
| `docs/14`             | FastAPI Strict Clean Architecture |
| `docs/15`             | DB Pagination (OFFSET vs Cursor)  |
| `docs/16`             | DB Column Overhead (컬럼 수/타입) |
| `docs/17`             | DB N+1 문제 (Lazy vs Eager)       |
| `docs/18`             | TypeScript Express 구현           |
| `docs/99`             | 벤치마크 결과 비교표              |
| `docs/DISCOVERIES.md` | 교훈 및 인사이트                  |

---

_Last updated: 2026-01-03_
