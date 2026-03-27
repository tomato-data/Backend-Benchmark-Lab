# Backend Benchmark Lab

> **"동일 로직, 다른 구현"** — 백엔드 프레임워크의 성능을 실증적으로 검증하는 벤치마크 실험실

4개 언어, 6개 프레임워크 구현체를 동일한 API 스펙 위에 올리고, 26개 시나리오로 성능을 비교합니다.
마이크로벤치마크 숫자가 아닌 **실제 서비스에 가까운 워크로드**에서 얻은 인사이트를 기록합니다.

---

## 목차

- [프로젝트 구조](#프로젝트-구조)
- [기술 스택](#기술-스택)
- [실험 환경](#실험-환경)
- [프레임워크 구현 현황](#프레임워크-구현-현황)
- [벤치마크 결과](#벤치마크-결과)
  - [Basic 시나리오 (01-08)](#basic-시나리오-01-08)
  - [아키텍처 비교: Pragmatic vs Clean Architecture](#아키텍처-비교-pragmatic-vs-clean-architecture)
  - [DB 심화 시나리오 (09-13)](#db-심화-시나리오-09-13)
  - [캐싱 시나리오 (14-16)](#캐싱-시나리오-14-16)
  - [인증 시나리오 (17)](#인증-시나리오-17)
  - [집계 쿼리 시나리오 (18)](#집계-쿼리-시나리오-18)
  - [서버 구성 실험](#서버-구성-실험-uvicorn-vs-gunicorn)
- [핵심 인사이트](#핵심-인사이트)
- [실행 방법](#실행-방법)
- [로드맵](#로드맵)

---

## 프로젝트 구조

```
Backend-Benchmark-Lab/
├── implementations/          # 프레임워크별 구현체 (동일 API)
│   ├── python-fastapi-pragmatic/    # FastAPI — 실용적 아키텍처
│   ├── python-fastapi-strict/       # FastAPI — Clean Architecture
│   ├── python-django/               # Django — DRF ViewSet
│   ├── python-server-config/        # 서버 구성 실험 (Uvicorn vs Gunicorn)
│   ├── typescript-express/          # Express.js + Prisma
│   └── ruby-rails/                  # Rails 8 API-only + ActiveRecord
│
├── scenarios/                # k6 벤치마크 시나리오 (26개)
│   ├── basic/                #   01-08: 프레임워크 비교
│   ├── db-advanced/          #   09-13: DB 최적화
│   ├── caching/              #   14-16: Redis 캐싱
│   ├── auth/                 #   17: JWT vs Session
│   ├── real-world/           #   18+: 집계, 검색 등
│   ├── server-config/        #   서버 구성 실험
│   └── stress/               #   스트레스 테스트
│
├── results/                  # JSON 형식 벤치마크 결과
├── docs/                     # 상세 문서 (27개+)
├── runner/                   # 자동화 스크립트
└── monitoring/               # Prometheus + Grafana
```

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| **벤치마크** | k6 (Grafana), 10 VUs, 30s, 10회 반복 평균 |
| **컨테이너** | Docker Compose (프로필 기반 전환) |
| **데이터베이스** | PostgreSQL 16 |
| **캐시** | Redis |
| **모니터링** | Prometheus + cAdvisor + Grafana |
| **API 스펙** | OpenAPI (Single Source of Truth) |

### 프레임워크별 기술 스택

| 구현체 | 언어 | 프레임워크 | 서버 | ORM | 검증 |
|--------|------|-----------|------|-----|------|
| python-fastapi | Python 3.12 | FastAPI | Uvicorn | SQLAlchemy (async) | Pydantic |
| python-django | Python 3.12 | Django 5 | Gunicorn | Django ORM | DRF Serializer |
| typescript-express | TypeScript | Express | Node.js 22 | Prisma | Zod (선택적) |
| ruby-rails | Ruby 3.3+ | Rails 8 | Puma | ActiveRecord | — |

---

## 실험 환경

| 항목 | 값 |
|------|-----|
| 호스트 | MacBook Apple Silicon |
| 컨테이너 CPU | 2 cores (서버), 2 cores (DB) |
| 컨테이너 메모리 | 2 GB (서버), 1 GB (DB) |
| k6 VUs | 10 |
| k6 Duration | 30초 |
| 반복 횟수 | 10회 (평균 계산) |

> 모든 프레임워크에 동일한 리소스 제한을 적용하여 공정한 비교를 보장합니다.

---

## 프레임워크 구현 현황

| 프레임워크 | 아키텍처 | 구현 | 벤치마크 |
|-----------|----------|------|---------|
| FastAPI | Pragmatic | ✅ | ✅ |
| FastAPI | Strict (Clean Architecture) | ✅ | ✅ |
| Django | DRF ViewSet | ✅ | ✅ |
| Express | Pragmatic + Prisma | ✅ | ✅ |
| Rails 8 | API-only MVC | ✅ | - |
| Go Fiber | — | - | - |
| Flask | — | - | - |
| Fastify | — | - | - |
| NestJS | — | - | - |

---

## 벤치마크 결과

### Basic 시나리오 (01-08)

> 프레임워크 간 핵심 성능을 비교하는 8개 기본 시나리오

#### Express vs FastAPI vs Django — 전체 비교

| 시나리오 | Express | FastAPI (Pragmatic) | Django | 최고 성능 |
|---------|---------|-------------------|--------|----------|
| **01-lightweight** | **17,005** RPS | 11,616 RPS | 1,655 RPS | Express |
| **02-json-payload** | **14,112** RPS | 9,555 RPS | 1,652 RPS | Express |
| **03-db-read** | **413** RPS | 146 RPS | 252 RPS | Express |
| **04-db-write** | **5,022** RPS | 1,091 RPS | 373 RPS | Express |
| **05-external-api** | 93 RPS | 92 RPS | 19 RPS | 동등 (I/O 병목) |
| **06-middleware** | **14,309** RPS | 8,697 RPS | 1,339 RPS | Express |
| **07-file-upload** | **9,436** RPS | 5,313 RPS | 1,417 RPS | Express |
| **08-mixed** | **551** RPS | 125 RPS | 92 RPS | Express |

#### Express vs FastAPI 상세

| 시나리오 | Express RPS | FastAPI RPS | 배율 | 핵심 원인 |
|---------|-------------|-------------|------|----------|
| 01-lightweight | 17,005 | 11,616 | **1.5x** | V8 JIT 컴파일 우위 |
| 02-json-payload | 14,112 | 9,555 | **1.5x** | Pydantic 검증 오버헤드 |
| 03-db-read | 413 | 146 | **2.8x** | Prisma 직접 JSON 반환 vs Pydantic model_validate 1000건 |
| 04-db-write | 5,022 | 1,091 | **4.6x** | Prisma 쿼리 생성 효율 |
| 05-external-api | 93 | 92 | **1.0x** | 100ms I/O 지연이 지배적 |
| 08-mixed | 551 | 125 | **4.4x** | Node.js 이벤트 루프 리소스 관리 |

#### FastAPI vs Django 상세

| 시나리오 | FastAPI RPS | Django RPS | 배율 | 핵심 원인 |
|---------|-------------|------------|------|----------|
| 01-lightweight | 13,999 | 1,655 | **8.5x** | async 이벤트 루프 우위 |
| 03-db-read | 158 | **252** | **0.6x** | Django ORM 단순 SELECT 최적화 |
| 05-external-api | 94 | 19 | **5.0x** | Django 동기 I/O 블로킹 (2 workers) |
| 08-mixed | 131 | 92 | **1.4x** | 혼합 워크로드에서 격차 축소 |

#### Latency 상세 (p95)

| 시나리오 | Express p95 | FastAPI p95 | Django p95 |
|---------|-------------|-------------|------------|
| 01-lightweight | 1.106ms | 1.093ms | 2.408ms |
| 03-db-read | 31.58ms | 119.57ms | 47.03ms |
| 04-db-write | 3.02ms | 17.89ms | 32.59ms |
| 08-mixed | 101.69ms | 229.99ms | 231.46ms |

---

### 아키텍처 비교: Pragmatic vs Clean Architecture

> FastAPI 두 아키텍처의 성능 차이를 검증합니다.

| 시나리오 | Pragmatic RPS | Strict RPS | 차이 |
|---------|---------------|------------|------|
| 01-lightweight | 11,616 | 11,983 | **+3.2%** (Strict 우위) |
| 02-json-payload | 9,555 | 9,922 | **+3.8%** |
| 03-db-read | 146 | 153 | **+5.0%** |
| 04-db-write | 1,091 | 1,305 | **+19.6%** |
| 06-middleware | 8,697 | 9,205 | **+5.8%** |
| 08-mixed | 125 | 123 | -1.5% (동등) |

**안정성 비교 (표준편차)**

| 시나리오 | Pragmatic std | Strict std |
|---------|---------------|------------|
| 01-lightweight | **2,469** | **367** |
| 04-db-write | 210 | 127 |

> **결론**: Clean Architecture는 성능 저하가 **전혀 없으며**, 오히려 3-6% 빠르고 표준편차가 크게 낮아 **안정성이 우수**합니다. 특히 DB 쓰기에서 +20% 향상은 명확한 트랜잭션 경계 분리 덕분으로 추정됩니다.

---

### DB 심화 시나리오 (09-13)

> FastAPI Pragmatic + PostgreSQL 환경에서 DB 최적화 기법을 비교합니다.

#### 09 — OFFSET vs Cursor 페이지네이션

| 방식 | 쿼리 | 시간복잡도 | p95 |
|------|------|----------|-----|
| OFFSET | `OFFSET 99980 LIMIT 20` | O(offset + limit) | 60ms |
| **Cursor** | `WHERE id > 99980 LIMIT 20` | O(limit) | **34ms** |

> Cursor가 **1.7배 빠름**. OFFSET은 99,980행을 스캔한 뒤 버리는 반면, Cursor는 인덱스를 타고 직접 접근합니다.

#### 10 — 컬럼 수 & 데이터 타입 오버헤드

**A. 컬럼 수 영향**

| 테이블 | 컬럼 수 | p95 | 기준 대비 |
|--------|---------|-----|----------|
| Narrow | 5개 | 36.33ms | 1.0x |
| Wide | 20개 | 44.73ms | 1.23x |
| Extra Wide | 50개 | 52.76ms | **1.45x** |

**B. 데이터 타입 영향**

| 타입 | p95 | 비고 |
|------|-----|------|
| INT | 36ms | |
| VARCHAR | 37ms | |
| TIMESTAMP | 38ms | |
| UUID | 38ms | |
| TEXT | 39ms | |
| JSONB | **41ms** | 파싱 오버헤드 |

> 모든 타입이 **±7%** 범위 내. 데이터 타입은 성능이 아닌 **데이터 모델링 관점**으로 선택해도 무방합니다.

#### 11 — N+1 문제 (Lazy vs Eager vs Subquery)

| 로딩 전략 | 쿼리 수 | p95 | 기준 대비 |
|----------|---------|-----|----------|
| Lazy (N+1) | 21 | 102.71ms | 1.0x |
| **Eager (JOIN)** | 1 | **24.86ms** | **4.1x 빠름** |
| Subquery (IN) | 2 | 27.99ms | **3.7x 빠름** |

> Async SQLAlchemy는 의도적으로 lazy loading을 차단(MissingGreenlet)하여 N+1 문제를 컴파일 타임에 방지합니다.

#### 12 — 대량 INSERT/UPDATE (1,000건)

| 방식 | p95 | 기준 대비 |
|------|-----|----------|
| Individual INSERT | 2.98s | 1.0x |
| Batch (add_all) | 38.86ms | **77x 빠름** |
| **Raw VALUES** | **15.91ms** | **187x 빠름** |
| Individual UPDATE | 2.96s | 1.0x |
| **Bulk CASE WHEN** | **23.86ms** | **124x 빠름** |

> commit 횟수가 성능의 99%를 결정합니다 (1,000회 vs 1회).

#### 13 — 트랜잭션 락 경합 (10 VUs 동시 접근)

| 방식 | 성공률 | p95 | 데이터 정합성 |
|------|--------|-----|-------------|
| No Lock | 100% | 15ms | ❌ Lost Update |
| **Pessimistic** | **100%** | **13ms** | **✅ 안전** |
| Optimistic | 59% | 48ms | ✅ (성공 시) |
| Serializable | 0.6% | 8ms | ✅ (성공 시) |

> 높은 동시성 환경에서는 **Pessimistic Lock**이 최적. Serializable은 동시성이 높으면 사실상 사용 불가합니다 (성공률 0.6%).

---

### 캐싱 시나리오 (14-16)

> FastAPI + PostgreSQL + Redis 환경

| 시나리오 | RPS | p95 | 기준 대비 |
|---------|-----|-----|----------|
| 14-no-cache (DB Only) | 1,238 | 23.27ms | 기준선 |
| 15-with-cache (Hit/Miss 혼합) | 5,532 | 2.26ms | **10.3x 빠름** |
| 16-a-pure-hit (100% Hit) | **5,605** | **2.24ms** | **10.4x 빠름** |
| 16-b-pure-miss (100% Miss) | 534 | 31.06ms | 1.3x 느림 |

**응답 분포 개선 효과**

| 환경 | p95/avg 비율 | 의미 |
|------|-------------|------|
| DB Only | 2.9x | 변동 큼 (간헐적 지연) |
| Redis Hit | **1.3x** | 변동 거의 없음 |

> 캐시 히트 시 **10배 성능 + tail latency 대폭 감소**. 캐시 미스 시 16% 오버헤드(Redis 확인 + 저장). **히트율 설계가 성공의 핵심**입니다.

---

### 인증 시나리오 (17)

> FastAPI + PostgreSQL + Redis 환경

| 시나리오 | Median | P95 | Throughput | 기준 대비 |
|---------|--------|-----|------------|----------|
| 17-a: No Auth | 0.92ms | 1.48ms | 9,532 req/s | 기준선 |
| 17-b: JWT | 4.98ms | 22.35ms | 1,283 req/s | **7.4x 느림** |
| **17-c: Session** | **4.75ms** | **17.39ms** | **1,464 req/s** | **6.5x 느림** |

**JWT vs Session 직접 비교**

| 메트릭 | JWT | Session | 승자 |
|--------|-----|---------|------|
| Median | 4.98ms | **4.75ms** | Session (+4.8%) |
| P95 | 22.35ms | **17.39ms** | Session (+28.5%) |
| Throughput | 1,283/s | **1,464/s** | **Session (+14.1%)** |

> **예상과 반대의 결과**: Session이 JWT보다 **14% 빠름**. JWT 서명 검증(CPU 바운드)이 Python GIL 하에서 Redis I/O 조회(비동기)보다 비효율적입니다. GIL이 없는 Go/Ruby에서는 역전 가능성이 있어 추가 검증 예정입니다.

---

### 집계 쿼리 시나리오 (18)

> FastAPI + PostgreSQL, `users_wide` 100,000건, 인덱스 추가 후 측정

| 쿼리 유형 | ORM (분리) | Raw SQL (합침) | 승자 |
|----------|-----------|---------------|------|
| Count (3종) | **199.86ms** | 289.58ms | **ORM 1.4x 빠름** |
| Country GROUP BY | 204.32ms | 209.61ms | 동등 |
| Author JOIN | 117.24ms | **109.73ms** | Raw (미미) |

**EXPLAIN ANALYZE로 밝혀진 원인**

| 쿼리 | 실행 계획 | 실행 시간 |
|------|----------|----------|
| Raw (1개 합침) | Seq Scan + **Disk Sort** (2,160kB) | **56ms** |
| ORM (3개 분리) | Index Only Scan × 3 | **28ms** (9+10+9) |

> **"쿼리 1개 = 더 빠르다"는 거짓**. 합친 쿼리는 `COUNT(DISTINCT)` 때문에 전체가 Seq Scan + Disk Sort로 강제됩니다. 분리된 쿼리는 각각 독립적으로 Index Only Scan을 활용합니다.

**인덱스 효과**

| 대상 | Before | After | 개선 |
|------|--------|-------|------|
| Count ORM | 373.87ms | 199.86ms | **-47%** |
| Count Raw | 299.72ms | 289.58ms | -3% (인덱스 무시됨) |

---

### 서버 구성 실험 (Uvicorn vs Gunicorn)

> 3개 가설을 5개 라운드, 105회 테스트로 검증

#### 가설 검증 결과

| 가설 | 예상 | 결과 |
|------|------|------|
| H1: I/O-bound에서 비동기 단일 프로세스 우위 | Uvicorn 우위 | **기각** — Gunicorn-4w가 3-6% 우세 |
| H2: CPU-bound에서 멀티프로세스 우위 | Gunicorn 우위 | **채택** — Gunicorn-2w가 **1.86x** 우세 |
| H3: 저사양에서 멀티프로세스 역효과 | 역효과 | **조건부 채택** — CPU-bound에서만 극심 |

#### 주요 수치

| 환경 | Uvicorn | Gunicorn | 배율 |
|------|---------|----------|------|
| I/O-bound, 1 vCPU | 1.0x | **1.06x** | Gunicorn 소폭 우위 |
| CPU-bound, 2 vCPU | 1.0x | **1.86x** | Gunicorn 압도적 |
| CPU-bound, 0.25 vCPU | **3.4x** | 1.0x | Uvicorn 압도적 |

> **Uvicorn CPU-bound VU=100**: P99가 **60초**(= 테스트 시간 전체)로 이벤트 루프 완전 블로킹.
> **Gunicorn-4w 0.25 vCPU**: RPS가 0.27로 **98% 붕괴**. 프로세스 스케줄링 오버헤드가 가용 CPU를 초과.

#### 배포 권장 사항

| vCPU | 권장 구성 |
|------|----------|
| 0.25 ~ 0.5 | Uvicorn 단독 |
| 1 | Uvicorn 또는 Gunicorn 1 worker |
| 2+ | Gunicorn (workers = vCPU 수) |

> **핵심 원칙**: workers > vCPU는 절대 금지 (특히 CPU-bound)

---

## 핵심 인사이트

### 1. "N배 빠르다"는 반쪽짜리 진실

| 시나리오 유형 | FastAPI vs Django |
|-------------|-----------------|
| 순수 처리량 (lightweight) | 7-9x |
| **실제 혼합 워크로드** | **1.4x** |
| DB 읽기 | Django가 **1.6x 빠름** |

마이크로벤치마크 숫자에 현혹되지 마세요. 실제 서비스는 혼합 워크로드에 가깝습니다.

### 2. 병목은 프레임워크가 아니다

```
최적화 우선순위:
DB 쿼리 > 캐싱 > 인프라 설정 > 프레임워크 선택
```

05-external-api에서 FastAPI(94 RPS)와 Django(19 RPS) 모두 "느림". 진짜 병목은 외부 의존성입니다.

### 3. Clean Architecture는 성능 패널티가 없다

레이어 분리가 오히려 **3-6% 빠르고**, 표준편차가 크게 낮아 **안정성이 우수**합니다. DB 쓰기에서 +20% 향상은 명확한 트랜잭션 경계 덕분으로 추정됩니다.

### 4. 서버 구성이 프레임워크 선택보다 중요하다

- Uvicorn + CPU-bound = **98% 성능 붕괴**
- workers > vCPU = 재앙
- 적절한 서버 구성으로 동일 프레임워크에서 **1.86배** 성능 차이

### 5. Python GIL이 인증 성능을 역전시킨다

JWT(CPU 바운드)가 Session(I/O 바운드)보다 **14% 느린** 예상 밖의 결과. GIL 하에서 CPU 작업이 비동기 I/O보다 비효율적입니다.

### 6. "쿼리 1개 = 더 빠르다"는 거짓

ORM(3개 분리)이 Raw SQL(1개 합침)보다 **1.4배 빠름**. PostgreSQL 옵티마이저는 하나의 SELECT에 하나의 실행 계획만 선택하므로, 분리된 쿼리가 각각 최적의 인덱스를 활용할 수 있습니다.

### 7. 데이터 타입 선택은 성능에 거의 영향 없다

INT, VARCHAR, UUID, TIMESTAMP 모두 **±7%** 범위. JSONB만 파싱 오버헤드로 약간 느림. **데이터 모델링 관점**에서 선택하세요.

### 8. commit 횟수가 대량 처리 성능의 99%를 결정한다

Individual INSERT(2.98s) vs Raw VALUES(15.91ms) — **187배** 차이. ORM 오버헤드(2.4x)보다 commit 횟수(1000x)가 압도적입니다.

### 9. 벤치마크에는 Cold Start 효과가 있다

k6 첫 번째 호출에서 **+10ms 오버헤드** 발생. 실행 순서를 바꿔 재현하거나 워밍업을 추가해야 정확한 비교가 가능합니다.

---

## 실행 방법

### 벤치마크 대상 시작

```bash
cd implementations

# 프레임워크 선택 (택 1)
docker compose --profile fastapi-pragmatic up -d
docker compose --profile fastapi-strict up -d
docker compose --profile django up -d
docker compose --profile express up -d
```

### 벤치마크 실행

```bash
cd runner
./run-benchmark.sh          # 전체 시나리오
./run-benchmark.sh 05       # 05번부터 실행
```

### 모니터링 (선택)

```bash
cd monitoring
docker compose up -d
# Grafana: http://localhost:3000 (admin/admin)
```

---

## 로드맵

### 완료

- [x] 인프라 (Docker, k6, Prometheus + Grafana)
- [x] Basic 시나리오 01-08 (4개 프레임워크)
- [x] FastAPI Pragmatic vs Strict 아키텍처 비교
- [x] DB 심화 09-13 (Pagination, Column, N+1, Bulk, Transactions)
- [x] 캐싱 14-16 (Redis Hit/Miss)
- [x] 인증 17 (JWT vs Session)
- [x] 집계 18 (ORM vs Raw SQL)
- [x] 서버 구성 실험 (Uvicorn vs Gunicorn, 105회)
- [x] Ruby Rails 8 구현

### 예정

- [ ] Ruby Rails 벤치마크 실행
- [ ] Go Fiber 구현 + JWT vs Session 검증
- [ ] Flask, Fastify, NestJS 구현
- [ ] 텍스트 검색 (LIKE vs Full-text)
- [ ] E2E 플로우 (인증 → 조회 → 수정 → 응답)
- [ ] Rails Solid Cache vs Redis 비교
- [ ] 스트레스 테스트 (스파이크, 장시간 부하)
- [ ] Pydantic vs msgspec, SQLAlchemy vs Raw asyncpg

---

## 문서

| 문서 | 내용 |
|------|------|
| [`docs/99-benchmark-results.md`](docs/99-benchmark-results.md) | 전체 벤치마크 결과표 |
| [`docs/DISCOVERIES.md`](docs/DISCOVERIES.md) | 교훈 및 인사이트 |
| [`docs/archive/`](docs/archive/) | 시나리오별 상세 분석 (27개+) |
| [`roadmap.md`](roadmap.md) | 프로젝트 로드맵 |

---

---

# English

> **"Same Logic, Different Implementations"** — An empirical benchmark laboratory for backend frameworks

This project implements identical API endpoints across 4 languages and 6 frameworks, then compares their performance across 26 scenarios. The focus is on **real-world insights** rather than synthetic microbenchmark numbers.

---

## Table of Contents

- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Test Environment](#test-environment)
- [Framework Status](#framework-status)
- [Benchmark Results](#benchmark-results)
  - [Basic Scenarios (01-08)](#basic-scenarios-01-08)
  - [Architecture: Pragmatic vs Clean Architecture](#architecture-pragmatic-vs-clean-architecture)
  - [DB Advanced (09-13)](#db-advanced-scenarios-09-13)
  - [Caching (14-16)](#caching-scenarios-14-16)
  - [Authentication (17)](#authentication-scenario-17)
  - [Aggregation (18)](#aggregation-scenario-18)
  - [Server Configuration](#server-configuration-uvicorn-vs-gunicorn)
- [Key Insights](#key-insights)
- [Getting Started](#getting-started)
- [Roadmap](#roadmap-1)

---

## Project Structure

```
Backend-Benchmark-Lab/
├── implementations/          # Framework implementations (identical APIs)
│   ├── python-fastapi-pragmatic/    # FastAPI — Pragmatic architecture
│   ├── python-fastapi-strict/       # FastAPI — Clean Architecture
│   ├── python-django/               # Django — DRF ViewSet
│   ├── python-server-config/        # Server config experiments
│   ├── typescript-express/          # Express.js + Prisma
│   └── ruby-rails/                  # Rails 8 API-only + ActiveRecord
│
├── scenarios/                # k6 benchmark scripts (26 scenarios)
│   ├── basic/                #   01-08: Framework comparison
│   ├── db-advanced/          #   09-13: DB optimization
│   ├── caching/              #   14-16: Redis caching
│   ├── auth/                 #   17: JWT vs Session
│   ├── real-world/           #   18+: Aggregation, search
│   ├── server-config/        #   Server configuration
│   └── stress/               #   Stress testing
│
├── results/                  # Benchmark results (JSON)
├── docs/                     # Detailed documentation (27+ files)
├── runner/                   # Automation scripts
└── monitoring/               # Prometheus + Grafana
```

---

## Tech Stack

| Area | Technology |
|------|-----------|
| **Benchmarking** | k6 (Grafana), 10 VUs, 30s, averaged over 10 runs |
| **Containers** | Docker Compose (profile-based switching) |
| **Database** | PostgreSQL 16 |
| **Cache** | Redis |
| **Monitoring** | Prometheus + cAdvisor + Grafana |
| **API Spec** | OpenAPI (Single Source of Truth) |

### Framework Tech Stacks

| Implementation | Language | Framework | Server | ORM | Validation |
|---------------|----------|-----------|--------|-----|-----------|
| python-fastapi | Python 3.12 | FastAPI | Uvicorn | SQLAlchemy (async) | Pydantic |
| python-django | Python 3.12 | Django 5 | Gunicorn | Django ORM | DRF Serializer |
| typescript-express | TypeScript | Express | Node.js 22 | Prisma | Zod (optional) |
| ruby-rails | Ruby 3.3+ | Rails 8 | Puma | ActiveRecord | — |

---

## Test Environment

| Item | Value |
|------|-------|
| Host | MacBook Apple Silicon |
| Container CPU | 2 cores (server), 2 cores (DB) |
| Container Memory | 2 GB (server), 1 GB (DB) |
| k6 VUs | 10 |
| k6 Duration | 30 seconds |
| Iterations | 10 runs (averaged) |

> Identical resource constraints applied across all frameworks to ensure fair comparison.

---

## Framework Status

| Framework | Architecture | Implemented | Benchmarked |
|-----------|-------------|-------------|-------------|
| FastAPI | Pragmatic | ✅ | ✅ |
| FastAPI | Strict (Clean Architecture) | ✅ | ✅ |
| Django | DRF ViewSet | ✅ | ✅ |
| Express | Pragmatic + Prisma | ✅ | ✅ |
| Rails 8 | API-only MVC | ✅ | — |
| Go Fiber | — | — | — |

---

## Benchmark Results

### Basic Scenarios (01-08)

#### Express vs FastAPI vs Django — Full Comparison

| Scenario | Express | FastAPI (Pragmatic) | Django | Winner |
|---------|---------|-------------------|--------|--------|
| **01-lightweight** | **17,005** RPS | 11,616 RPS | 1,655 RPS | Express |
| **02-json-payload** | **14,112** RPS | 9,555 RPS | 1,652 RPS | Express |
| **03-db-read** | **413** RPS | 146 RPS | 252 RPS | Express |
| **04-db-write** | **5,022** RPS | 1,091 RPS | 373 RPS | Express |
| **05-external-api** | 93 RPS | 92 RPS | 19 RPS | Tie (I/O bound) |
| **06-middleware** | **14,309** RPS | 8,697 RPS | 1,339 RPS | Express |
| **07-file-upload** | **9,436** RPS | 5,313 RPS | 1,417 RPS | Express |
| **08-mixed** | **551** RPS | 125 RPS | 92 RPS | Express |

#### Express vs FastAPI Detail

| Scenario | Express | FastAPI | Ratio | Root Cause |
|---------|---------|---------|-------|-----------|
| 01-lightweight | 17,005 | 11,616 | **1.5x** | V8 JIT compilation advantage |
| 03-db-read | 413 | 146 | **2.8x** | Prisma direct JSON vs Pydantic model_validate on 1000 objects |
| 04-db-write | 5,022 | 1,091 | **4.6x** | Prisma query generation efficiency |
| 05-external-api | 93 | 92 | **1.0x** | 100ms I/O latency dominates |
| 08-mixed | 551 | 125 | **4.4x** | Node.js event loop resource management |

#### FastAPI vs Django Detail

| Scenario | FastAPI | Django | Ratio | Root Cause |
|---------|---------|--------|-------|-----------|
| 01-lightweight | 13,999 | 1,655 | **8.5x** | Async event loop advantage |
| 03-db-read | 158 | **252** | **0.6x** | Django ORM optimized for simple SELECT |
| 05-external-api | 94 | 19 | **5.0x** | Django sync I/O blocks workers |
| 08-mixed | 131 | 92 | **1.4x** | Gap narrows under mixed workload |

---

### Architecture: Pragmatic vs Clean Architecture

| Scenario | Pragmatic RPS | Strict RPS | Difference |
|---------|---------------|------------|------------|
| 01-lightweight | 11,616 | 11,983 | **+3.2%** (Strict wins) |
| 02-json-payload | 9,555 | 9,922 | **+3.8%** |
| 03-db-read | 146 | 153 | **+5.0%** |
| 04-db-write | 1,091 | 1,305 | **+19.6%** |
| 06-middleware | 8,697 | 9,205 | **+5.8%** |

**Stability (Standard Deviation)**

| Scenario | Pragmatic std | Strict std |
|---------|---------------|------------|
| 01-lightweight | **2,469** | **367** |
| 04-db-write | 210 | 127 |

> **Conclusion**: Clean Architecture has **zero performance penalty** — it's actually 3-6% faster with significantly lower variance. The +20% improvement in DB writes is attributed to cleaner transaction boundaries.

---

### DB Advanced Scenarios (09-13)

#### 09 — OFFSET vs Cursor Pagination

| Method | Complexity | p95 | Speedup |
|--------|-----------|-----|---------|
| OFFSET | O(offset + limit) | 60ms | baseline |
| **Cursor** | O(limit) | **34ms** | **1.7x faster** |

#### 10 — Column Count & Data Type Overhead

| Columns | p95 | vs Baseline |
|---------|-----|------------|
| 5 (narrow) | 36.33ms | 1.0x |
| 20 (wide) | 44.73ms | 1.23x |
| 50 (extra wide) | 52.76ms | **1.45x** |

> All data types (INT, VARCHAR, UUID, TIMESTAMP, TEXT, JSONB) within **±7%**. Choose based on data modeling, not performance.

#### 11 — N+1 Problem

| Strategy | Queries | p95 | Speedup |
|----------|---------|-----|---------|
| Lazy (N+1) | 21 | 102.71ms | baseline |
| **Eager (JOIN)** | 1 | **24.86ms** | **4.1x faster** |
| Subquery (IN) | 2 | 27.99ms | **3.7x faster** |

#### 12 — Bulk Operations (1,000 records)

| Method | p95 | Speedup |
|--------|-----|---------|
| Individual INSERT | 2.98s | baseline |
| Batch (add_all) | 38.86ms | **77x faster** |
| **Raw VALUES** | **15.91ms** | **187x faster** |
| Individual UPDATE | 2.96s | baseline |
| **Bulk CASE WHEN** | **23.86ms** | **124x faster** |

> Commit count determines 99% of bulk performance (1,000 commits vs 1).

#### 13 — Transaction Lock Contention (10 concurrent VUs)

| Strategy | Success Rate | p95 | Data Integrity |
|----------|-------------|-----|---------------|
| No Lock | 100% | 15ms | ❌ Lost Update |
| **Pessimistic** | **100%** | **13ms** | **✅ Safe** |
| Optimistic | 59% | 48ms | ✅ (when succeeds) |
| Serializable | 0.6% | 8ms | ✅ (when succeeds) |

---

### Caching Scenarios (14-16)

| Scenario | RPS | p95 | vs Baseline |
|---------|-----|-----|------------|
| 14-no-cache (DB only) | 1,238 | 23.27ms | baseline |
| 15-with-cache (mixed) | 5,532 | 2.26ms | **10.3x faster** |
| 16-a-pure-hit (100%) | **5,605** | **2.24ms** | **10.4x faster** |
| 16-b-pure-miss (100%) | 534 | 31.06ms | 1.3x slower |

> Cache hits deliver **10x speedup** with dramatically reduced tail latency (p95/avg ratio: 2.9x → 1.3x). Cache misses incur 16% overhead.

---

### Authentication Scenario (17)

| Method | Median | P95 | Throughput | vs No Auth |
|--------|--------|-----|------------|-----------|
| No Auth | 0.92ms | 1.48ms | 9,532/s | baseline |
| JWT | 4.98ms | 22.35ms | 1,283/s | **7.4x slower** |
| **Session** | **4.75ms** | **17.39ms** | **1,464/s** | **6.5x slower** |

> **Surprising result**: Session auth is **14% faster than JWT** in Python. JWT signature verification (CPU-bound) is less efficient under the GIL than Redis lookup (async I/O). This may reverse in languages without a GIL (Go, Ruby).

---

### Aggregation Scenario (18)

| Query Type | ORM (separate) | Raw SQL (combined) | Winner |
|-----------|----------------|-------------------|--------|
| Count (3 types) | **199.86ms** | 289.58ms | **ORM 1.4x faster** |
| Country GROUP BY | 204.32ms | 209.61ms | Tie |
| Author JOIN | 117.24ms | **109.73ms** | Raw (marginal) |

**Root Cause (EXPLAIN ANALYZE)**

| Query | Execution Plan | Time |
|-------|---------------|------|
| Raw (1 combined) | Seq Scan + **Disk Sort** (2,160kB) | **56ms** |
| ORM (3 separate) | Index Only Scan × 3 | **28ms** |

> **"Fewer queries = faster" is FALSE**. The combined query forces Seq Scan + Disk Sort due to `COUNT(DISTINCT)`. Separate queries each leverage Index Only Scan independently.

---

### Server Configuration (Uvicorn vs Gunicorn)

> 3 hypotheses validated across 5 rounds, 105 total test runs

| Hypothesis | Result | Key Finding |
|-----------|--------|-------------|
| H1: Async wins for I/O-bound | **Rejected** | Gunicorn-4w 3-6% faster (coroutine scheduling distribution) |
| H2: Multiprocess wins for CPU-bound | **Accepted** | Gunicorn-2w **1.86x** faster |
| H3: Multiprocess hurts on low resources | **Conditionally accepted** | CPU-bound only: 98% degradation |

| Environment | Uvicorn | Gunicorn | Ratio |
|------------|---------|----------|-------|
| I/O-bound, 1 vCPU | 1.0x | **1.06x** | Gunicorn slight edge |
| CPU-bound, 2 vCPU | 1.0x | **1.86x** | Gunicorn dominant |
| CPU-bound, 0.25 vCPU | **3.4x** | 1.0x | Uvicorn dominant |

**Deployment Recommendation**

| vCPU | Configuration |
|------|--------------|
| 0.25 - 0.5 | Uvicorn standalone |
| 1 | Uvicorn or Gunicorn 1 worker |
| 2+ | Gunicorn (workers = vCPU count) |

> **Golden rule**: Never set workers > vCPU count, especially for CPU-bound workloads.

---

## Key Insights

### 1. "N times faster" is a half-truth

FastAPI is 7-9x faster than Django in lightweight APIs, but only **1.4x** in mixed workloads. Django is actually **1.6x faster** for DB reads. Don't be misled by microbenchmarks.

### 2. The bottleneck is rarely the framework

```
Optimization priority:
DB queries > Caching > Infrastructure config > Framework choice
```

### 3. Clean Architecture has zero performance penalty

Layer separation is actually **3-6% faster** with much lower variance. The +20% DB write improvement comes from cleaner transaction boundaries.

### 4. Server configuration matters more than framework choice

Uvicorn + CPU-bound = **98% performance collapse**. Proper server configuration yields **1.86x** improvement on the same framework.

### 5. Python's GIL reverses JWT vs Session performance

Session auth is **14% faster than JWT** in Python — the opposite of conventional wisdom. CPU-bound JWT verification suffers under the GIL.

### 6. "Fewer queries = faster" is false

ORM (3 separate queries) beats Raw SQL (1 combined query) by **1.4x** because PostgreSQL's optimizer picks one execution plan per SELECT.

### 7. Data type selection barely affects performance

All types within **±7%**. Only JSONB shows noticeable overhead from parsing. Choose based on data modeling needs.

### 8. Commit count determines 99% of bulk performance

Individual INSERT (2.98s) vs Raw VALUES (15.91ms) — **187x** difference. ORM overhead (2.4x) is negligible compared to commit count (1000x).

### 9. Benchmarks have cold start effects

First k6 call adds **+10ms** overhead. Always randomize execution order or add warmup rounds for accurate comparison.

---

## Getting Started

### Start a benchmark target

```bash
cd implementations

# Choose a framework (pick one)
docker compose --profile fastapi-pragmatic up -d
docker compose --profile fastapi-strict up -d
docker compose --profile django up -d
docker compose --profile express up -d
```

### Run benchmarks

```bash
cd runner
./run-benchmark.sh          # All scenarios
./run-benchmark.sh 05       # Start from scenario 05
```

### Monitoring (optional)

```bash
cd monitoring
docker compose up -d
# Grafana: http://localhost:3000 (admin/admin)
```

---

## Roadmap

### Completed

- [x] Infrastructure (Docker, k6, Prometheus + Grafana)
- [x] Basic scenarios 01-08 (4 frameworks)
- [x] FastAPI Pragmatic vs Strict architecture comparison
- [x] DB Advanced 09-13 (Pagination, Column, N+1, Bulk, Transactions)
- [x] Caching 14-16 (Redis hit/miss)
- [x] Authentication 17 (JWT vs Session)
- [x] Aggregation 18 (ORM vs Raw SQL)
- [x] Server configuration experiment (Uvicorn vs Gunicorn, 105 runs)
- [x] Ruby Rails 8 implementation

### Planned

- [ ] Ruby Rails benchmarks
- [ ] Go Fiber implementation + JWT vs Session validation
- [ ] Flask, Fastify, NestJS implementations
- [ ] Text search (LIKE vs Full-text)
- [ ] E2E flow (Auth → Read → Write → Response)
- [ ] Rails Solid Cache vs Redis
- [ ] Stress testing (spike traffic, long-running)
- [ ] Pydantic vs msgspec, SQLAlchemy vs Raw asyncpg

---

## Documentation

| Document | Content |
|----------|---------|
| [`docs/99-benchmark-results.md`](docs/99-benchmark-results.md) | Complete benchmark result tables |
| [`docs/DISCOVERIES.md`](docs/DISCOVERIES.md) | Lessons learned and insights |
| [`docs/archive/`](docs/archive/) | Per-scenario detailed analysis (27+ files) |
| [`roadmap.md`](roadmap.md) | Project roadmap |
