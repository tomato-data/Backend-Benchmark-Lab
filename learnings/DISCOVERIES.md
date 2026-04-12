# Discoveries

개발 중 발견한 교훈과 주의사항을 기록한다.

---

## 2024-12-07

### SQLAlchemy Dialect 이름

**문제**: `postgres+asyncpg://` 사용 시 에러 발생

```
sqlalchemy.exc.NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:postgres.asyncpg
```

**해결**: `postgresql+asyncpg://` 사용 (postgresql, 'ql' 포함)

---

### Docker Named Volume Scope

**질문**: 서로 다른 프로젝트에서 같은 볼륨명 사용 시 충돌?

**답변**: 충돌 없음. Docker Compose는 자동으로 프로젝트명(디렉토리명)을 prefix로 붙임.

```
project_a/docker-compose.yml → project_a_postgres_data
project_b/docker-compose.yml → project_b_postgres_data
```

---

## 2025-12-07

### FastAPI vs Django 벤치마크 인사이트

#### 1. "N배 빠르다"는 반쪽짜리 진실

| 시나리오 유형 | FastAPI 우위 |
|-------------|-------------|
| 순수 처리량 (lightweight, middleware) | 7~9배 |
| 실제 혼합 워크로드 | **1.4배** |
| DB 읽기 | Django가 **1.6배 빠름** |

**교훈**: 마이크로벤치마크 숫자에 현혹되지 말 것. 실제 서비스는 혼합 워크로드에 가깝다.

#### 2. 병목은 프레임워크가 아니다

```
05-external-api: FastAPI 94 RPS, Django 19 RPS
```

둘 다 100ms I/O에 묶여있음. FastAPI가 5배 빠르지만, **둘 다 "느림"**.
진짜 병목은 외부 의존성 (DB, 외부 API, 네트워크).

**교훈**: 프레임워크 최적화보다 DB 쿼리 최적화, 캐싱, 인프라 스케일링이 더 큰 영향.

#### 3. 안정성(CV) 역전 현상

| 부하 수준 | 더 안정적 | 이유 추측 |
|----------|----------|----------|
| 고부하 (06, 07) | FastAPI | async 이벤트 루프가 효율적으로 관리 |
| 저부하 (01, 03, 04, 05) | Django | 동기 모델의 예측 가능성 |

Django 06번 CV 12.7%는 Gunicorn worker 간 경쟁 때문으로 추측.

#### 4. 현실적인 프레임워크 선택 기준

| 상황 | 추천 |
|------|------|
| 높은 동시성, WebSocket, 실시간 | FastAPI |
| 전통적인 CRUD, Admin 필요 | Django (생산성 + 충분한 성능) |
| DB 집약적 워크로드 | 둘 다 비슷 (DB가 병목) |

> **핵심**: "어떤 프레임워크가 더 좋냐"보다 "내 서비스의 병목이 어디냐"가 더 중요한 질문

---

### 향후 실험 스코프 추가

벤치마크 결과를 바탕으로 추가 실험이 필요한 영역:

1. **Gunicorn + Uvicorn 조합 테스트**
   - 현재: Uvicorn 단독 (FastAPI), Gunicorn sync workers (Django)
   - 실험: `gunicorn -k uvicorn.workers.UvicornWorker` 프로덕션 권장 구성
   - 목표: 워커 관리 + 비동기 처리의 최적 조합 확인

2. **DB 쿼리 최적화 영향 측정**
   - 현재: 단순 SELECT * (페이지네이션 없음)
   - 실험: 인덱스, 페이지네이션, N+1 해결, 커넥션 풀 튜닝
   - 목표: "프레임워크 차이 vs DB 최적화 차이" 정량 비교

3. **워커 수 실험**
   - 현재: 고정 (Uvicorn 1, Gunicorn 2)
   - 실험: 1, 2, 4, 8, 2*CPU+1 워커
   - 목표: 리소스 제한 환경에서 최적 워커 수 도출

---

## 2026-01-01

### 10-db-column-overhead 인사이트

#### 1. 컬럼 수 증가의 실제 영향

| 컬럼 수 변화 | 성능 저하 |
|-------------|----------|
| 5개 → 20개 (4배) | **1.23배** 느림 |
| 5개 → 50개 (10배) | **1.45배** 느림 |

**교훈**: 컬럼 수 증가가 성능에 미치는 영향은 예상보다 비선형적. 네트워크/직렬화 오버헤드가 더 큰 비중을 차지함.

#### 2. 데이터 타입은 성능에 거의 영향 없음

- 모든 타입 (INT, VARCHAR, TEXT, JSONB, TIMESTAMP, UUID)이 36~41ms 범위
- 차이는 ±7%로 미미함
- JSONB만 약간 느림 (41ms) - 바이너리 JSON 파싱 오버헤드

**교훈**: 데이터 타입 선택은 성능보다 **데이터 모델링 관점**에서 결정해도 됨.

#### 3. k6 벤치마크 Cold Start 효과 발견

**현상**: 첫 번째 테스트에서 INT가 48.57ms로 가장 느렸음 (예상: 가장 빠름)

**원인 추적**:
1. k6 스크립트에서 INT가 B 그룹 첫 번째였음
2. 순서를 변경하여 VARCHAR를 첫 번째로 테스트
3. 결과: VARCHAR가 48.53ms로 느려지고, INT는 36.84ms로 정상화

**결론**: **첫 번째 호출 시 약 +10ms cold start 오버헤드** 발생

**교훈**: 벤치마크 결과 해석 시 **실행 순서**를 반드시 고려할 것. 순서를 바꿔 재현하거나, 워밍업 라운드를 추가하는 것이 정확한 비교에 필수적.

---

## 2026-02-07

### Ruby on Rails 구현 인사이트

#### 1. Rails의 Convention은 양날의 검

`rails new`가 생성하는 파일 중 **실제로 필요한 것은 절반 이하**였다.

| 생성된 것 | 실제 사용 | 삭제/주석 처리 |
|----------|----------|--------------|
| ActionMailer | 미사용 | railtie 주석 처리 + 파일 삭제 |
| ActionView | 미사용 (API-only) | railtie 주석 처리 |
| Solid Cache/Queue | 미사용 | production.rb 설정 주석 처리 + 스키마 삭제 |
| Kamal 배포 | 미사용 | 디렉토리 삭제 |
| GitHub CI | 미사용 | 디렉토리 삭제 |

**교훈**: `--skip-*` 플래그를 최대한 활용해도 불필요한 파일이 남는다. API-only 벤치마크에서는 생성 후 정리 작업이 필수.

#### 2. Docker 빌드 시 네이티브 gem 의존성

`psych` gem(YAML 파서)이 `libyaml` C 라이브러리를 필요로 함. Dockerfile 빌드 스테이지에 `libyaml-dev`, 런타임 스테이지에 `libyaml-0-2`를 명시적으로 추가해야 함.

**교훈**: Ruby gem은 Python pip과 마찬가지로 네이티브 확장이 있는 경우가 많다. Docker slim 이미지 사용 시 빌드/런타임 의존성을 분리하여 관리해야 함.

#### 3. 모노레포에서 .gitignore 충돌

루트 `.gitignore`에 `lib/`, `*.log` 같은 범용 패턴이 있으면 새 언어(Ruby) 추가 시 파일이 무시될 수 있음.

**해결**: 범용 패턴을 특정 디렉토리로 스코핑 (`lib/` → `**/python-*/lib/`)

**교훈**: 모노레포에서 새 언어/프레임워크 추가 시 `.gitignore` 충돌을 반드시 점검할 것.

#### 4. Puma의 on_worker_boot deprecation

Puma 7.x에서 `on_worker_boot`가 deprecated. `before_worker_boot`로 변경 필요.

**교훈**: Rails 8 + Puma 7 조합에서 공식 가이드의 코드 스니펫이 이미 deprecated일 수 있다. 실제 실행 후 경고 로그를 반드시 확인할 것.

#### 5. MVC는 프론트엔드와 무관한 설계 원칙

MVC의 View = "사용자에게 보여주는 응답"이다. API 서버에서는 JSON 응답이 곧 View.

| 프레임워크 | 아키텍처 | 자유도 |
|-----------|---------|--------|
| Rails | MVC 강제 | Convention으로 고정 |
| Django | MTV (이름만 다른 MVC) | 느슨한 관례 |
| FastAPI | 자유 | 개발자가 직접 설계 |
| Express | 자유 | 개발자가 직접 설계 |

**교훈**: 아키텍처 강제(Rails)와 아키텍처 자유(FastAPI) 각각의 트레이드오프가 있다. 벤치마크에서는 "Convention의 오버헤드"를 측정하는 것도 의미 있는 비교 포인트.
