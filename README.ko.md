# Backend Benchmark Lab

[![English](https://img.shields.io/badge/lang-English-blue)](README.md)

> **"동일 로직, 다른 구현"** — 백엔드 프레임워크 성능을 실증적으로 검증하는 벤치마크 실험실

## 하이라이트

- **4개 언어, 5개 프레임워크**를 동일 API 스펙 위에서 공정 비교
- **26개 실전 시나리오** ("Hello World"가 아닌): N+1, 캐싱, 인증, 트랜잭션, 서버 구성
- **105회 서버 구성 테스트**로 배포 튜닝이 프레임워크 선택보다 중요함을 입증
- 모든 수치는 리소스 제한된 Docker 컨테이너에서 **k6 10회 반복 평균**

![Framework RPS Comparison](assets/charts/01-framework-rps.png)

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
| 호스트 | Apple M5 Pro, 18 cores, 48 GB |
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
| Rails 8 | API-only MVC | ✅ | ✅ |
| Go Fiber | — | — | — |

---

## 벤치마크 결과 (2026-03-27)

### 전체 비교: 5개 프레임워크 (RPS)

| 시나리오 | Express | FastAPI-P | FastAPI-S | Rails | Django |
|----------|---------|-----------|-----------|-------|--------|
| 01-lightweight | **20,492** | 14,225 | 13,928 | 3,632 | 2,899 |
| 02-json-payload | **17,403** | 11,790 | 11,635 | 4,200 | 2,621 |
| 03-db-read | 498 | 147 | 170 | **1,524** | 288 |
| 04-db-write | **5,875** | 1,280 | 1,528 | 1,719 | 411 |
| 05-external-api | 92 | **94** | 93 | 90 | 19 |
| 06-middleware | **18,771** | 9,799 | 10,455 | 3,519 | 2,560 |
| 07-file-upload | **10,063** | 6,029 | 6,084 | 3,150 | 2,622 |
| 08-mixed | 244 | 122 | 133 | **557** | 93 |

> Express가 경량 처리량에서 선두이지만, **Rails가 DB 읽기(Express 대비 3배)와 혼합 워크로드(Express 대비 2.3배)에서 1위**. I/O 경계(05)에서는 모든 비동기 프레임워크가 수렴. Django의 동기 처리가 외부 API 호출에서 병목.

![Framework RPS Comparison](assets/charts/01-framework-rps.png)

### Rails: 예상을 뒤엎은 강자

- **DB 읽기 1위** — ActiveRecord의 효율적 SELECT가 Prisma조차 앞섬 (1,524 vs 498 RPS)
- **혼합 워크로드 1위** — Puma의 멀티스레드 아키텍처가 동시성 처리에서 압도적 (557 vs 244 RPS)
- **최고 안정성** — 혼합 워크로드 변동계수 CV 5.8% (타 프레임워크 45% 이상)
- 경량 시나리오에서는 Ruby 인터프리터 오버헤드로 약세

### Clean Architecture: 성능 패널티 제로

FastAPI Strict (Clean Architecture) vs Pragmatic: **DB 쓰기 +19.4% 향상**, 표준편차 대폭 감소 (lightweight: 37 vs 265). 레이어 분리가 속도와 안정성 모두를 개선.

![Clean Architecture vs Pragmatic](assets/charts/02-clean-architecture.png)

### DB, 캐싱, 인증 핵심 결과

- **Cursor 페이지네이션**: 깊은 페이지에서 OFFSET 대비 1.7x 빠름 (인덱스 탐색 vs 전체 스캔)
- **Eager Loading (JOIN)**: N+1 문제 해결, 4.1x 향상 (쿼리 21개 -> 1개)
- **대량 INSERT (Raw VALUES)**: 개별 INSERT 대비 187x 빠름 (commit 횟수가 전부)
- **비관적 잠금**: 높은 동시성 환경에서 유일한 안전한 선택 (Serializable 성공률: 0.6%)
- **Redis 캐시 히트**: 10x 처리량 + tail latency 스파이크 제거
- **Session 인증이 JWT보다 14% 빠름** (Python) — GIL로 인해 CPU 바운드 JWT 검증이 비동기 Redis 조회보다 느림

![Caching Impact](assets/charts/03-caching-impact.png)

### 서버 구성: Uvicorn vs Gunicorn (2026-03-02)

> 동일 FastAPI 앱, 3가지 서버 구성 (Uvicorn / Gunicorn+Uvicorn 2w / 4w), 5 Round × 35조합 × 3회 = **총 105 runs**

**가설 검증 결과**

| 가설 | 내용 | 결과 | 핵심 데이터 |
|------|------|------|------------|
| H1 | I/O-bound에서 비동기 단일 프로세스 우세 | **기각** | gunicorn-4w가 3~6% 우세, P99에서 13% 격차 |
| H2 | CPU-bound에서 멀티프로세스 우세 | **채택** | gunicorn-2w가 **1.86배** (GIL 우회) |
| H3 | 저사양에서 멀티프로세스 역효과 | **조건부 채택** | I/O → 역효과 없음, CPU → **98% 성능 하락** |

**Round별 핵심 결과**

| Round | 워크로드 | CPU | 승자 | 핵심 데이터 |
|-------|---------|-----|------|------------|
| R1 | I/O (sleep) | 1 vCPU | gunicorn-4w | +6% RPS, VU=200에서 P99 126→145ms 격차 |
| R2 | CPU (fibonacci) | 2 vCPU | gunicorn-2w | **1.86배** RPS, uvicorn P99=60초 타임아웃 |
| R3 | I/O (sleep) | 0.25 vCPU | ~동등 | 3가지 구성 모두 안정, 5% 이내 차이 |
| R4 | CPU (fibonacci) | 0.25 vCPU | uvicorn | **3.4배** — gunicorn-4w는 0.27 RPS |
| R5 | Mixed (DB+연산) | 1/2 vCPU | 상황별 | 1 vCPU: uvicorn, 2 vCPU: gunicorn-2w (1.7배) |

**배포 가이드**

| 워크로드 유형 | 1 vCPU 이하 | 2+ vCPU |
|--------------|-------------|---------|
| **I/O-bound** (API 호출, DB 쿼리) | Uvicorn 단독 | Gunicorn + N워커 (약간 이득) |
| **CPU-bound** (연산, 해싱) | Uvicorn 단독 | **Gunicorn + N워커 필수** (N = vCPU 수) |
| **Mixed** (현실적 서비스) | Uvicorn 단독 | **Gunicorn + N워커 필수** (N = vCPU 수) |

**교훈**: (1) workers > vCPU = CPU-bound에서 서비스 장애 수준, (2) 단일 프로세스는 추가 CPU를 활용 불가 — Uvicorn@1vCPU ≈ Uvicorn@2vCPU, (3) I/O-bound에서 CPU는 거의 무관 — 0.25 vCPU ≈ 1 vCPU 처리량.

![Server Config Benchmark](assets/charts/04-server-config.png)

---

## 핵심 인사이트

1. **"N배 빠르다"는 반쪽짜리 진실** — Express가 lightweight에서 Django보다 7배 빠르지만, DB 읽기와 혼합 워크로드에서는 Rails가 전체 1위.
2. **병목은 프레임워크가 아니다** — 최적화 우선순위: DB 쿼리 > 캐싱 > 인프라 설정 > 프레임워크 선택.
3. **Rails의 DB 성능은 예상 외로 강력하다** — ActiveRecord + Puma가 Express(Prisma) 대비 DB 읽기 3배, 혼합 워크로드 2.3배.
4. **Clean Architecture는 성능 패널티가 없다** — 오히려 DB 작업에서 15-19% 빠르고 분산이 훨씬 낮음.
5. **서버 구성이 프레임워크 선택보다 중요하다** — 적절한 worker 설정만으로 1.86x 성능 향상.
6. **Python GIL이 JWT vs Session 성능을 역전시킨다** — Session이 14% 빠름. CPU 바운드 JWT 검증이 GIL 하에서 비효율적.
7. **"쿼리 1개 = 더 빠르다"는 거짓** — ORM 3개 분리 쿼리가 Raw SQL 1개 합침보다 1.4x 빠름 (옵티마이저가 쿼리별 최적 계획 선택).
8. **commit 횟수가 대량 처리 성능의 99%를 결정** — Individual INSERT (2.98s) vs Raw VALUES (15.91ms) = 187배 차이.
9. **혼합 워크로드 = 실제 트래픽의 프록시** — 시나리오 08 결과 (Rails 1위)가 실제 프로덕션 트래픽 패턴을 가장 잘 대변.

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
docker compose --profile rails up -d
```

### 벤치마크 실행

```bash
cd runner
./run-benchmark.sh python-fastapi-pragmatic    # FastAPI 전체 시나리오
./run-benchmark.sh typescript-express 05        # 단일 시나리오
./run-benchmark.sh ruby-rails 03+              # 03번부터 끝까지
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
- [x] Basic 시나리오 01-08 (5개 프레임워크)
- [x] FastAPI Pragmatic vs Strict 아키텍처 비교
- [x] DB 심화 09-13 (Pagination, Column, N+1, Bulk, Transactions)
- [x] 캐싱 14-16 (Redis Hit/Miss)
- [x] 인증 17 (JWT vs Session)
- [x] 집계 18 (ORM vs Raw SQL)
- [x] 서버 구성 실험 (Uvicorn vs Gunicorn, 105회)
- [x] Ruby Rails 8 구현 + 벤치마크

### 예정

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
