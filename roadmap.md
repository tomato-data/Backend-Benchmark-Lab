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

### Ruby ⏳ 예정

| 프레임워크 | 아키텍처 | 상태    | 벤치마크 |
| ---------- | -------- | ------- | -------- |
| Rails      | -        | ⏳ 예정 | -        |

> **벤치마크 가치**:
> - **4번째 언어** 추가 (Python, TypeScript, Go, Ruby)
> - **Convention over Configuration** 패러다임 — 현재 프로젝트의 명시적 설정 프레임워크들과 대비
> - **ActiveRecord** vs SQLAlchemy vs Prisma — 완전히 다른 ORM 패턴 비교
> - **Puma 멀티스레드** — Ruby는 GIL이 없으므로 Python과 동시성 특성이 다름
>
> **검증 과제**: Auth 시나리오(17-a,b,c)에서 JWT vs Session 비교
> - Python에서는 Session이 14% 빠름 (GIL로 인한 CPU 바운드 병목)
> - Ruby는 GIL이 없으므로 **JWT가 Python보다 상대적으로 유리할 것으로 예상**
> - Go와 함께 "CPU 효율적 환경에서 JWT 유리" 가설 검증 가능

### Go ⏳ 예정

| 프레임워크 | 상태    |
| ---------- | ------- |
| Fiber      | ⏳ 예정 |
| Gin        | ⏳ 예정 |

> **검증 과제**: Go Fiber에서 Auth 시나리오(17-a,b,c) 구현 후 JWT vs Session 성능 비교
> - Python에서는 Session이 14% 빠름 (GIL로 인한 CPU 바운드 병목)
> - Go에서는 Goroutine 병렬 처리로 **JWT가 더 빠를 것으로 예상**
> - 이를 통해 "CPU 효율적 환경에서 JWT 유리" 가설 검증

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
| 12  | db-bulk-operations | 대량 INSERT/UPDATE (1000건+)          | ✅ 완료 |
| 13  | db-transactions    | 복합 트랜잭션 (락 경합)               | ✅ 완료 |

### 프레임워크별 적용 현황

| 시나리오              | fastapi-pragmatic | fastapi-strict | django  |
| --------------------- | ----------------- | -------------- | ------- |
| 09-db-pagination      | ✅                | ⏳ 예정        | ⏳ 예정 |
| 10-db-column-overhead | ✅                | ⏳ 예정        | ⏳ 예정 |
| 11-db-n-plus-one      | ✅                | ⏳ 예정        | ⏳ 예정 |
| 12-db-bulk-operations | ✅                | ⏳ 예정        | ⏳ 예정 |
| 13-db-transactions    | ✅                | ⏳ 예정        | ⏳ 예정 |

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

| 테이블                    | 컬럼 수     | 예상 성능     |
| ------------------------- | ----------- | ------------- |
| `users_narrow`            | 5개         | 가장 빠름     |
| `users_wide`              | 20개        | 1.5~2x 느림   |
| `users_extra_wide`        | 50개        | 2~3x 느림     |
| `users_wide` (5개 SELECT) | 20개 중 5개 | Narrow와 유사 |

#### B. 데이터 타입별 비교 (각 5개 컬럼)

| 테이블                 | 타입      | 예상 순위       |
| ---------------------- | --------- | --------------- |
| `users_type_int`       | INTEGER   | 1위 (가장 빠름) |
| `users_type_timestamp` | TIMESTAMP | 2위             |
| `users_type_uuid`      | UUID      | 3위             |
| `users_type_varchar`   | VARCHAR   | 4위             |
| `users_type_text`      | TEXT      | 5위             |
| `users_type_jsonb`     | JSONB     | 6위 (가장 느림) |

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

| 로딩 전략     | 쿼리 수     | p(95)    | Lazy 대비     |
| ------------- | ----------- | -------- | ------------- |
| Lazy (N+1)    | 1 + 20 = 21 | 102.71ms | 1.0x (기준)   |
| Eager (JOIN)  | 1           | 24.86ms  | **4.1x 빠름** |
| Subquery (IN) | 2           | 27.99ms  | **3.7x 빠름** |

| 작업                                | 상태    |
| ----------------------------------- | ------- |
| DB 스키마 (authors, posts)          | ✅ 완료 |
| SQLAlchemy 모델 (relationship)      | ✅ 완료 |
| Pydantic 스키마                     | ✅ 완료 |
| 라우터 구현 (lazy, eager, subquery) | ✅ 완료 |
| k6 시나리오 (랜덤 offset)           | ✅ 완료 |
| 문서화 (`docs/17`)                  | ✅ 완료 |

**핵심 인사이트**:

- Async SQLAlchemy는 의도적으로 lazy loading을 차단 (MissingGreenlet)
- 1:Many 관계에는 `selectinload`가 적합 (중복 데이터 없음)
- 1:1, 1:Few 관계에는 `joinedload`가 적합 (최소 쿼리)

### 12-db-bulk-operations 상세 ✅ 완료

대량 INSERT/UPDATE 시 다양한 방식의 성능 비교

- **테이블**: `bulk_items` (동적 생성, 매 테스트 TRUNCATE)
- **건수**: 1,000건/요청
- **결과**: Raw INSERT가 Individual 대비 **187배 빠름**

| 방식                    | p(95)   | Individual 대비 |
| ----------------------- | ------- | --------------- |
| Individual INSERT       | 2.98s   | 1.0x (기준)     |
| Batch INSERT (add_all)  | 38.86ms | **77x 빠름**    |
| Raw INSERT (VALUES)     | 15.91ms | **187x 빠름**   |
| Individual UPDATE       | 2.96s   | 1.0x (기준)     |
| Bulk UPDATE (CASE WHEN) | 23.86ms | **124x 빠름**   |

| 작업                     | 상태    |
| ------------------------ | ------- |
| DB 스키마 (bulk_items)   | ✅ 완료 |
| SQLAlchemy 모델          | ✅ 완료 |
| Pydantic 스키마          | ✅ 완료 |
| 라우터 구현 (5가지 방식) | ✅ 완료 |
| k6 시나리오              | ✅ 완료 |
| 문서화 (`docs/19`)       | ✅ 완료 |

**핵심 인사이트**:

- commit 횟수가 성능의 99%를 결정 (1000회 vs 1회)
- ORM 오버헤드는 약 2.4배 (Batch vs Raw)
- 대량 처리 시 반드시 배치/벌크 방식 사용

### 13-db-transactions 상세 ✅ 완료

트랜잭션 락 경합(Lock Contention) 성능 및 데이터 정합성 비교

- **테이블**: `products` (10개 상품, 각 재고 1000개)
- **시나리오**: 10 VUs가 같은 상품에 동시 재고 차감
- **결과**: Pessimistic Lock이 **100% 성공 + 13ms**로 최적

| 방식            | 성공률   | p(95)    | 데이터 정합성  |
| --------------- | -------- | -------- | -------------- |
| No Lock         | 100%     | 15ms     | ❌ Lost Update |
| **Pessimistic** | **100%** | **13ms** | ✅ 안전        |
| Optimistic      | 59%      | 48ms     | ✅ (성공 시)   |
| Serializable    | 0.6%     | 8ms      | ✅ (성공 시)   |

| 작업                     | 상태    |
| ------------------------ | ------- |
| DB 스키마 (products)     | ✅ 완료 |
| SQLAlchemy 모델          | ✅ 완료 |
| Pydantic 스키마          | ✅ 완료 |
| 라우터 구현 (4가지 방식) | ✅ 완료 |
| k6 시나리오              | ✅ 완료 |
| 문서화 (`docs/20`)       | ✅ 완료 |

**핵심 인사이트**:

- No Lock은 **절대 사용 금지** (Lost Update 발생)
- Pessimistic Lock이 동시성 높은 환경에서 최적
- Optimistic Lock은 충돌 적은 환경에서만 유효
- Serializable은 동시성 높으면 사실상 사용 불가

---

## Phase 6: 캐싱 시나리오 (caching) ✅ 완료

> DB Buffer Cache (Phase 5)와의 비교 포인트:
>
> - Phase 5: DB 레벨 캐싱 (PostgreSQL Buffer Cache)
> - Phase 6: 애플리케이션 레벨 캐싱 (Redis)

| #   | 시나리오   | 설명                                | 상태    |
| --- | ---------- | ----------------------------------- | ------- |
| 14  | no-cache   | 캐시 없는 환경 (순수 DB) - 기준선   | ✅ 완료 |
| 15  | with-cache | 캐시 있는 환경 (Redis Hit/Miss 혼합) | ✅ 완료 |
| 16-a | pure-hit  | 100% 캐시 히트 (최대 이득)          | ✅ 완료 |
| 16-b | pure-miss | 100% 캐시 미스 (오버헤드 측정)      | ✅ 완료 |

### 14-no-cache 상세 ✅ 완료

캐시 없는 환경에서 순수 DB 성능 측정 (기준선)

- **Redis**: 불필요
- **엔드포인트**: `GET /cache/users/{id}/no-cache`
- **목적**: 캐시 도입 전 성능 기준선

### 15-with-cache 상세 ✅ 완료

캐시 있는 환경에서 Hit/Miss 혼합 성능 측정

- **Redis**: 필수
- **엔드포인트**: `GET /cache/users/{id}/cached`
- **워밍업**: 1~100 사용자 (10% 히트율 보장)
- **목적**: 캐시 도입 후 성능 비교

### 16-a-pure-hit 상세 ✅ 완료

100% 캐시 히트 환경 (최대 이득 측정)

- **Redis**: 필수
- **워밍업**: 1~1000 사용자 (100% 히트율)
- **목적**: 캐시 히트 시 최대 성능 이득

### 16-b-pure-miss 상세 ✅ 완료

100% 캐시 미스 환경 (오버헤드 측정)

- **Redis**: 필수
- **방식**: 매 요청마다 캐시 삭제 후 조회
- **목적**: 캐시 미스 시 오버헤드 측정 (Redis GET + DB + Redis SET)

| 작업                       | 상태    |
| -------------------------- | ------- |
| Redis 연결 설정            | ✅ 완료 |
| 캐싱 엔드포인트 구현       | ✅ 완료 |
| k6 시나리오 (14, 15, 16)   | ✅ 완료 |
| 문서화 (`docs/21`)         | ✅ 완료 |
| 벤치마크 실행 및 결과 기록 | ✅ 완료 |

### 벤치마크 결과 요약 (2026-01-17)

| 시나리오 | RPS | p(95) | vs 14번 |
| -------- | --- | ----- | ------- |
| 14-no-cache | 1,238 | 23.27ms | 기준선 |
| 15-with-cache | 5,532 | 2.26ms | **10.3배 빠름** |
| 16-a-pure-hit | 5,605 | 2.24ms | **10.4배 빠름** |
| 16-b-pure-miss | 534 | 31.06ms | **1.3배 느림** |

**핵심 인사이트**: 캐시 미스 시 16% 오버헤드 발생 (Redis 확인 + 저장)

---

## Phase 7: 실제 서비스 패턴 (real-world) 🔄 진행 중

> 대상: 모든 프레임워크 (아키텍처 차이가 드러나는 시나리오)

| #    | 시나리오        | 설명                             | 상태       |
| ---- | --------------- | -------------------------------- | ---------- |
| 17-a | auth-none       | 인증 없음 (기준선)               | ✅ 완료    |
| 17-b | auth-jwt        | JWT Stateless 인증               | ✅ 완료    |
| 17-c | auth-session    | Session Store Stateful 인증      | ✅ 완료    |
| 18   | aggregation     | 집계 쿼리 (COUNT, SUM, GROUP BY) | 🔄 진행 중 |
| 19   | search          | 텍스트 검색 (LIKE vs Full-text)  | ⏳         |
| 20   | real-world-flow | 인증→조회→수정→응답 E2E          | ⏳         |

### 17. 인증 방식 비교 (Auth Benchmark) ✅ 완료

인증 오버헤드 및 방식별 특성 비교

#### 벤치마크 결과 (2026-01-17)

| 시나리오 | Median | P95 | Throughput | vs No Auth |
|----------|--------|-----|------------|------------|
| **17-a: No Auth** | 0.92ms | 1.48ms | 9,532 req/s | 기준선 |
| **17-b: JWT** | 4.98ms | 22.35ms | 1,283 req/s | **7.4배 느림** |
| **17-c: Session** | 4.75ms | 17.39ms | 1,464 req/s | **6.5배 느림** |

#### 핵심 인사이트

- **Session이 JWT보다 14% 빠름** (예상과 반대)
- JWT 서명 검증(CPU 바운드)이 Redis 조회(I/O 바운드)보다 Python에서 비효율적
- 인증 추가 시 처리량 **6.5~7.4배 감소**
- 보안 요구사항에 따라 선택, 성능은 Session이 우위

#### 인증 방식 개요

| 방식 | 이름 | 토큰 저장 | 검증 방식 | 특징 |
|------|------|----------|----------|------|
| **No Auth** | 인증 없음 | - | - | 기준선 측정용 |
| **JWT (Stateless)** | 클라이언트 토큰 | 클라이언트 | 서명 검증 | 서버 부하 낮음, 즉시 무효화 불가 |
| **Session Store (Stateful)** | 서버 세션 | Redis | DB/Redis 조회 | 즉시 무효화 가능, 이상탐지 가능 |

#### Stateless vs Stateful 비교

| 관점 | JWT (Stateless) | Session Store (Stateful) |
|------|-----------------|--------------------------|
| **확장성** | ✅ 서버 간 공유 불필요 | ⚠️ Redis 등 공유 저장소 필요 |
| **즉시 로그아웃** | ❌ 토큰 만료까지 유효 | ✅ 즉시 세션 삭제 가능 |
| **다중 로그인 제어** | ❌ 불가 | ✅ 세션 수 제한 가능 |
| **이상 탐지** | ❌ 서버에 기록 없음 | ✅ 접속 기록으로 탐지 가능 |
| **서버 부하** | ⚠️ CPU (서명 검증) | ✅ 낮음 (Redis 조회) |

### 18. 집계 쿼리 (Aggregation) 🔄 진행 중

ORM vs Raw SQL 집계 쿼리 성능 비교

#### 구현 완료 (2026-01-25)

| 작업 | 상태 |
| --- | --- |
| Pydantic 스키마 (`aggregation.py`) | ✅ 완료 |
| 라우터 구현 (6개 엔드포인트) | ✅ 완료 |
| k6 시나리오 (`18-aggregation.js`) | ✅ 완료 |

#### 엔드포인트

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /aggregation/count/orm` | COUNT 3종 비교 (ORM) |
| `GET /aggregation/count/raw` | COUNT 3종 비교 (Raw SQL) |
| `GET /aggregation/stats/country/orm` | 국가별 통계 GROUP BY (ORM) |
| `GET /aggregation/stats/country/raw` | 국가별 통계 GROUP BY (Raw SQL) |
| `GET /aggregation/stats/author/orm` | 작가별 통계 JOIN + GROUP BY (ORM) |
| `GET /aggregation/stats/author/raw` | 작가별 통계 JOIN + GROUP BY (Raw SQL) |

#### 첫 벤치마크 결과 (2026-01-25)

| 시나리오 | p(95) | Threshold | 결과 |
|---------|-------|-----------|------|
| Count ORM | 373.87ms | <100ms | ❌ |
| Count Raw | 299.72ms | <50ms | ❌ |
| Country ORM | 205.27ms | <200ms | ❌ |
| Country Raw | 203.06ms | <100ms | ❌ |
| Author ORM | 109.4ms | <200ms | ✅ |
| Author Raw | 100.75ms | <100ms | ❌ |

#### 핵심 발견

1. **ORM vs Raw SQL 차이 미미** (1~9%)
   - 병목은 ORM이 아니라 **DB 쿼리 자체**
2. **100,000건 COUNT가 JOIN보다 느림** (이상 현상)
   - `users_wide` 테이블에 **인덱스 없음** 추정
3. **인덱스 추가 필요**
   - `country`, `status` 컬럼에 인덱스 추가 후 재벤치마크 필요

#### TODO (다음 작업)

- [ ] `users_wide` 테이블에 인덱스 추가
  ```sql
  CREATE INDEX idx_users_wide_country ON users_wide(country);
  CREATE INDEX idx_users_wide_status ON users_wide(status);
  ```
- [ ] 인덱스 추가 후 재벤치마크 (Before/After 비교)
- [ ] Threshold 현실적으로 조정
- [ ] 문서화 (`docs/23-aggregation.md`)
- [ ] 결과 분석 및 인사이트 정리

---

## Phase 8: 스트레스 테스트 (stress) ⏳ 예정

| #   | 시나리오      | 설명                                 | 상태 |
| --- | ------------- | ------------------------------------ | ---- |
| 21  | spike-traffic | 트래픽 급증 (10→100→10 VUs)          | ⏳   |
| 22  | long-running  | 장시간 부하 (5분+), 메모리 누수 탐지 | ⏳   |

---

## Phase 9: 복합 시나리오 (cold/warm 비교) ⏳ 예정

> DB Buffer Cache + Redis Cache 효과를 극적으로 비교

| 시나리오      | 설명                   |
| ------------- | ---------------------- |
| 23-mixed-cold | 서버 재시작 후 첫 실행 |
| 23-mixed-warm | 동일 요청 반복 후 실행 |

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

| 문서                  | 내용                               |
| --------------------- | ---------------------------------- |
| `docs/01-05`          | 인프라 + 초기 설정                 |
| `docs/06-10`          | 시나리오 상세                      |
| `docs/11`             | 벤치마크 자동화                    |
| `docs/12`             | Django 구현 가이드                 |
| `docs/13`             | 모니터링                           |
| `docs/14`             | FastAPI Strict Clean Architecture  |
| `docs/15`             | DB Pagination (OFFSET vs Cursor)   |
| `docs/16`             | DB Column Overhead (컬럼 수/타입)  |
| `docs/17`             | DB N+1 문제 (Lazy vs Eager)        |
| `docs/18`             | TypeScript Express 구현            |
| `docs/19`             | DB Bulk Operations (INSERT/UPDATE) |
| `docs/20`             | DB Transactions (락 경합)          |
| `docs/21`             | Caching (Redis Hit/Miss)           |
| `docs/22`             | Auth (JWT vs Session)              |
| `docs/23`             | Aggregation (집계 쿼리) - 작성 예정 |
| `docs/99`             | 벤치마크 결과 비교표               |
| `docs/DISCOVERIES.md` | 교훈 및 인사이트                   |

---

_Last updated: 2026-02-07_
