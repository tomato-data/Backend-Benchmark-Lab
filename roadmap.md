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

### TypeScript (Node.js) ⏳ 예정

| 프레임워크 | 상태    |
| ---------- | ------- |
| Express    | ⏳ 예정 |
| Fastify    | ⏳ 예정 |
| NestJS     | ⏳ 예정 |

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

## Phase 5: DB 심화 시나리오 (db-advanced) ⏳ 예정

> 대상: 모든 프레임워크 (pragmatic, strict, django, ...)

| #   | 시나리오           | 설명                             | Before | After |
| --- | ------------------ | -------------------------------- | ------ | ----- |
| 09  | db-pagination      | OFFSET vs Cursor 페이지네이션    | ⏳     | ⏳    |
| 10  | db-n-plus-one      | N+1 문제 (lazy vs eager loading) | ⏳     | ⏳    |
| 11  | db-bulk-operations | 대량 INSERT/UPDATE (1000건+)     | ⏳     | ⏳    |
| 12  | db-transactions    | 복합 트랜잭션 (락 경합)          | ⏳     | ⏳    |

### 구현 작업

- [ ] 테스트 데이터 생성 스크립트 (충분한 양의 데이터)
- [ ] 각 프레임워크에 엔드포인트 추가
- [ ] k6 시나리오 작성
- [ ] Before/After 비교용 runner 스크립트

---

## Phase 6: 캐싱 시나리오 (caching) ⏳ 예정

| #   | 시나리오      | 설명                       | 상태 |
| --- | ------------- | -------------------------- | ---- |
| 13  | cache-hit     | Redis 캐시 히트            | ⏳   |
| 14  | cache-miss-db | 캐시 미스 → DB → 캐시 저장 | ⏳   |

---

## Phase 7: 실제 서비스 패턴 (real-world) ⏳ 예정

> 대상: 모든 프레임워크 (아키텍처 차이가 드러나는 시나리오)

| #   | 시나리오        | 설명                             | 상태 |
| --- | --------------- | -------------------------------- | ---- |
| 15  | auth-jwt        | JWT 생성/검증 오버헤드           | ⏳   |
| 16  | aggregation     | 집계 쿼리 (COUNT, SUM, GROUP BY) | ⏳   |
| 17  | search          | 텍스트 검색 (LIKE vs Full-text)  | ⏳   |
| 18  | real-world-flow | 인증→조회→수정→응답 E2E          | ⏳   |

---

## Phase 8: 스트레스 테스트 (stress) ⏳ 예정

| #   | 시나리오      | 설명                                 | 상태 |
| --- | ------------- | ------------------------------------ | ---- |
| 19  | spike-traffic | 트래픽 급증 (10→100→10 VUs)          | ⏳   |
| 20  | long-running  | 장시간 부하 (5분+), 메모리 누수 탐지 | ⏳   |

---

## Phase 9: Variant 실험 ⏳ 예정

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
| `docs/99`             | 벤치마크 결과 비교표              |
| `docs/DISCOVERIES.md` | 교훈 및 인사이트                  |

---

_Last updated: 2026-01-01_
