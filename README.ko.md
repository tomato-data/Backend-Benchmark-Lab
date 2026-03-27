# Backend Benchmark Lab

[![English](https://img.shields.io/badge/lang-English-blue)](README.md)

> **"동일 로직, 다른 구현"** — 백엔드 프레임워크 성능을 실증적으로 검증하는 벤치마크 실험실

## 하이라이트

- **4개 언어, 6개 프레임워크**를 동일 API 스펙 위에서 공정 비교
- **26개 실전 시나리오** ("Hello World"가 아닌): N+1, 캐싱, 인증, 트랜잭션, 서버 구성
- **105회 서버 구성 테스트**로 배포 튜닝이 프레임워크 선택보다 중요함을 입증
- 모든 수치는 리소스 제한된 Docker 컨테이너에서 **k6 10회 반복 평균**

<!-- TODO: Add hero benchmark chart image -->

---

## 왜 만들었나

회사에서 FastAPI를 쓰고 있었지만, **왜 이 프레임워크를 쓰는지** 명확히 설명할 수 없었습니다. "빠르다"는 말은 많은데, 어떤 상황에서 얼마나 빠른지, 다른 프레임워크와 구조적으로 어떻게 다른지 직접 검증하고 싶었습니다.

단순한 합성 벤치마크 대신 실전 시나리오를 구축해 **데이터 기반으로 기술 선택의 근거를 확보**하는 것이 목표입니다.

---

## 프로젝트 구조

```
Backend-Benchmark-Lab/
├── implementations/          # 프레임워크별 구현체 (동일 API)
│   ├── python-fastapi-pragmatic/    # FastAPI — 실용적 아키텍처
│   ├── python-fastapi-strict/       # FastAPI — Clean Architecture
│   ├── python-django/               # Django — DRF ViewSet
│   ├── python-server-config/        # 서버 구성 실험
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
| Rails 8 | API-only MVC | ✅ | — |
| Go Fiber | — | — | — |

---

## 벤치마크 결과

### 기본 비교: Express vs FastAPI vs Django

| 시나리오 | Express | FastAPI | Django | 최고 성능 |
|---------|---------|---------|--------|----------|
| 01-lightweight | **17,005** | 11,616 | 1,655 | Express |
| 03-db-read | **413** | 146 | 252 | Express |
| 04-db-write | **5,022** | 1,091 | 373 | Express |
| 05-external-api | 93 | 92 | 19 | 동등 (I/O 병목) |
| 08-mixed | **551** | 125 | 92 | Express |

> Express가 순수 처리량에서 압도적 (FastAPI 대비 1.5-4.6x). 하지만 I/O 경계에서는 모든 프레임워크가 수렴합니다. 실제 워크로드에서 격차는 크게 줄어듭니다.

<!-- TODO: Add benchmark chart images -->

### Clean Architecture: 성능 패널티 제로

FastAPI Strict (Clean Architecture) vs Pragmatic: 전 시나리오에서 **3-6% 더 빠르고**, DB 쓰기에서 **+19.6%** 향상, 표준편차 대폭 감소 (lightweight: 2,469 vs 367). 레이어 분리가 속도와 안정성 모두를 개선합니다.

### DB, 캐싱, 인증 핵심 결과

- **Cursor 페이지네이션**: 깊은 페이지에서 OFFSET 대비 1.7x 빠름 (인덱스 탐색 vs 전체 스캔)
- **Eager Loading (JOIN)**: N+1 문제 해결, 4.1x 향상 (쿼리 21개 -> 1개)
- **대량 INSERT (Raw VALUES)**: 개별 INSERT 대비 187x 빠름 (commit 횟수가 전부)
- **비관적 잠금**: 높은 동시성 환경에서 유일한 안전한 선택 (Serializable 성공률: 0.6%)
- **Redis 캐시 히트**: 10x 처리량 + tail latency 스파이크 제거
- **Session 인증이 JWT보다 14% 빠름** (Python) — GIL로 인해 CPU 바운드 JWT 검증이 비동기 Redis 조회보다 느림

<!-- TODO: Add benchmark chart images -->

### 서버 구성: 배포 권장 사항

> 3개 가설, 5라운드, 105회 테스트 (Uvicorn vs Gunicorn)

| vCPU | 권장 구성 |
|------|----------|
| 0.25 ~ 0.5 | Uvicorn 단독 |
| 1 | Uvicorn 또는 Gunicorn 1 worker |
| 2+ | Gunicorn (workers = vCPU 수) |

> **핵심 원칙**: workers > vCPU는 절대 금지. Uvicorn + CPU-bound = 98% 붕괴. 적절한 서버 구성으로 동일 프레임워크에서 1.86배 성능 차이.

---

## 핵심 인사이트

1. **"N배 빠르다"는 반쪽짜리 진실** — FastAPI는 lightweight에서 Django보다 7-9x 빠르지만, 혼합 워크로드에서는 1.4x. DB 읽기에서는 Django가 1.6x 빠름.
2. **병목은 프레임워크가 아니다** — 최적화 우선순위: DB 쿼리 > 캐싱 > 인프라 설정 > 프레임워크 선택.
3. **Clean Architecture는 성능 패널티가 없다** — 오히려 3-6% 빠르고 분산이 훨씬 낮음.
4. **서버 구성이 프레임워크 선택보다 중요하다** — 적절한 worker 설정만으로 1.86x 성능 향상.
5. **Python GIL이 JWT vs Session 성능을 역전시킨다** — Session이 14% 빠름. CPU 바운드 JWT 검증이 GIL 하에서 비효율적.
6. **"쿼리 1개 = 더 빠르다"는 거짓** — ORM 3개 분리 쿼리가 Raw SQL 1개 합침보다 1.4x 빠름 (옵티마이저가 쿼리별 최적 계획 선택).
7. **데이터 타입 선택은 성능에 거의 영향 없다** — 모든 타입이 +-7% 범위. JSONB만 파싱 오버헤드. 데이터 모델링 관점에서 선택.
8. **commit 횟수가 대량 처리 성능의 99%를 결정** — Individual INSERT (2.98s) vs Raw VALUES (15.91ms) = 187배 차이.
9. **벤치마크에는 Cold Start 효과가 있다** — k6 첫 호출에서 +10ms 오버헤드. 실행 순서 랜덤화 또는 워밍업 추가 필요.

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
- [ ] E2E 플로우 (인증 -> 조회 -> 수정 -> 응답)
- [ ] Rails Solid Cache vs Redis 비교
- [ ] 스트레스 테스트 (스파이크, 장시간 부하)
- [ ] Pydantic vs msgspec, SQLAlchemy vs Raw asyncpg

---

## 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE)로 제공됩니다.
