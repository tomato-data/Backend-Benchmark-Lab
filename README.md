# Backend-Benchmark-Lab

Backend 프레임워크 벤치마크 비교 프로젝트.

## 구조

```
implementations/     # 각 프레임워크 구현체
  ├── python-fastapi-pragmatic/
  ├── python-django/
  └── docker-compose.yml

scenarios/           # k6 벤치마크 시나리오 (01~08)
monitoring/          # Prometheus + cAdvisor + Grafana
runner/              # 벤치마크 자동화 스크립트
```

## 현재 완료

| 프레임워크 | 상태 |
|-----------|------|
| FastAPI (async, Uvicorn) | ✅ 완료 |
| Django (sync, Gunicorn) | ✅ 완료 |

## 핵심 결과

- FastAPI가 경량 API에서 **7~9배** 빠름
- 혼합 워크로드에서는 **1.4배** 차이로 줄어듦
- DB 읽기에서 Django가 **1.6배** 빠름
- 상세: `docs/99-benchmark-results.md`

## 실행 방법

```bash
# 벤치마크 대상 시작
cd implementations
docker compose --profile fastapi-pragmatic up -d

# 벤치마크 실행
cd runner
./run-benchmark.sh        # 전체
./run-benchmark.sh 05     # 05번부터

# 모니터링 (선택)
cd monitoring
docker compose up -d
# Grafana: http://localhost:3000 (admin/admin)
```

## 향후 계획

- [ ] Gunicorn + Uvicorn 조합 테스트
- [ ] DB 쿼리 최적화 영향 측정
- [ ] 워커 수 실험 (1, 2, 4, 8)
- [ ] Flask, Express, Fastify, NestJS, Go Fiber 추가

---

## 프레임워크별 분기 실험 계획

각 프레임워크의 특성에 맞는 변형(variant)을 구현하여 비교 실험 진행 예정.
상세 내용은 각 프레임워크 구현 시 `docs/`에 문서화.

### Python

- [ ] **FastAPI**: pragmatic vs strict, SQLAlchemy vs Raw asyncpg, Pydantic vs msgspec, Uvicorn vs Gunicorn+Uvicorn
- [ ] **Django**: sync vs async, ViewSet vs APIView, ORM vs Raw SQL, 워커 수 실험
- [ ] **Flask**: sync vs async (Quart)

### TypeScript (Node.js)

- [ ] **Express**: callback vs async/await
- [ ] **Fastify**: schema vs no-schema (검증 오버헤드)
- [ ] **NestJS**: Express 어댑터 vs Fastify 어댑터

### Go

- [ ] **Fiber**: default vs prefork (멀티 프로세스)
- [ ] **Gin**: Fiber와 비교

### 공통 실험

- [ ] 워커/인스턴스 수: 1, 2, 4, (2*CPU+1)
- [ ] 커넥션 풀 크기: 5, 10, 20, 50
- [ ] JSON 라이브러리: 기본 vs 대안 (orjson, simdjson 등)

---

## 시나리오 확장 계획

현재 basic 시나리오(01-08)에 추가로 심화 시나리오 구성 예정.

### 시나리오 구조

```
scenarios/
├── basic/           # 기존 01-08 (프레임워크 비교용)
├── db-advanced/     # DB 심화 (최적화 기법 비교용)
├── caching/         # 캐싱
├── real-world/      # 실제 서비스 패턴
└── stress/          # 스트레스 테스트
```

### 추가 시나리오 목록

#### DB 심화 (09-12)

- [ ] **09-db-pagination**: OFFSET vs Cursor 페이지네이션
- [ ] **10-db-n-plus-one**: N+1 문제 (lazy vs eager loading)
- [ ] **11-db-bulk-operations**: 대량 INSERT/UPDATE (1000건+)
- [ ] **12-db-transactions**: 복합 트랜잭션 (락 경합)

#### 캐싱 (13-14)

- [ ] **13-cache-hit**: Redis/메모리 캐시 히트율
- [ ] **14-cache-miss-db**: 캐시 미스 → DB → 캐시 저장 플로우

#### 실제 서비스 패턴 (15-18)

- [ ] **15-auth-jwt**: JWT 생성/검증 오버헤드
- [ ] **16-aggregation**: 집계 쿼리 (COUNT, SUM, GROUP BY)
- [ ] **17-search**: 텍스트 검색 (LIKE vs Full-text)
- [ ] **18-real-world-flow**: 인증→조회→수정→응답 E2E

#### 스트레스 테스트 (19-20)

- [ ] **19-spike-traffic**: 트래픽 급증 (10→100→10 VUs)
- [ ] **20-long-running**: 장시간 부하 (5분+), 메모리 누수 탐지

### 최적화 실험 전략

**기본 원칙**: 최적화 실험은 `python-fastapi-pragmatic` 단일 프레임워크에서 Before/After 비교

| 이유 | 설명 |
|-----|------|
| 변수 통제 | 프레임워크 차이 vs 최적화 효과 구분 명확 |
| 중복 방지 | 쿼리 최적화는 ORM 레벨 문제, 프레임워크마다 반복 불필요 |
| 이미 비교 완료 | 프레임워크 성능 차이는 basic 시나리오(01-08)에서 측정됨 |

**예외 (프레임워크별 비교 가치 있는 경우)**:

| 시나리오 | 이유 |
|---------|------|
| 13-cache-hit | Redis 클라이언트가 다름 (aioredis vs django-redis) |
| 15-auth-jwt | JWT 라이브러리가 다름 (python-jose vs PyJWT vs jsonwebtoken) |

**결과 구조**:

```
results/
├── python-fastapi-pragmatic/
│   ├── 2024-12-07/              # basic 시나리오
│   └── optimization/
│       ├── 09-pagination/
│       │   ├── before/          # OFFSET
│       │   └── after/           # Cursor
│       └── 10-n-plus-one/
│           ├── before/          # lazy loading
│           └── after/           # joinedload
```
