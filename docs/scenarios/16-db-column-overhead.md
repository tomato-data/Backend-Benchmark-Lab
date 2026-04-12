# 10-db-column-overhead 시나리오

## 개요

컬럼 수와 데이터 타입에 따른 DB 조회 오버헤드를 측정한다. 100,000건 데이터에서 각 테이블 구조별 성능 차이를 비교한다.

---

## 측정 목표

- 컬럼 수 증가에 따른 조회 성능 저하 확인
- 데이터 타입별 직렬화/역직렬화 오버헤드 비교
- `SELECT *` 사용 시 숨겨진 비용 가시화

---

## 테이블 구조

### A. 컬럼 수 비교

| 테이블 | 컬럼 수 | 구성 |
|--------|---------|------|
| `users_narrow` | 5개 | id, name, email, status, created_at |
| `users_wide` | 20개 | 기본 5개 + phone, address, bio 등 15개 |
| `users_extra_wide` | 50개 | 기본 3개 + field_01~45 + created_at |

### B. 데이터 타입별 비교 (각 8개 컬럼)

| 테이블 | 타입 | 구성 |
|--------|------|------|
| `users_type_int` | INTEGER | id, name, email + int_col_01~05 |
| `users_type_varchar` | VARCHAR | id, name, email + varchar_col_01~05 |
| `users_type_text` | TEXT | id, name, email + text_col_01~05 |
| `users_type_jsonb` | JSONB | id, name, email + json_col_01~05 |
| `users_type_timestamp` | TIMESTAMP | id, name, email + ts_col_01~05 |
| `users_type_uuid` | UUID | id, name, email + uuid_col_01~05 |

---

## 엔드포인트 스펙

### A. 컬럼 수 비교

```
GET /column-overhead/narrow?limit=100
GET /column-overhead/wide?limit=100
GET /column-overhead/extra-wide?limit=100
```

### B. 데이터 타입별 비교

```
GET /column-overhead/type/int?limit=100
GET /column-overhead/type/varchar?limit=100
GET /column-overhead/type/text?limit=100
GET /column-overhead/type/jsonb?limit=100
GET /column-overhead/type/timestamp?limit=100
GET /column-overhead/type/uuid?limit=100
```

---

## 구현 코드

### SQLAlchemy 모델 (예시: UserWideModel)

```python
class UserWideModel(Base):
    __tablename__ = "users_wide"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    phone: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(String(500))
    # ... 15개 추가 컬럼
    preferences: Mapped[dict | None] = mapped_column(JSONB, default={})
```

### 라우터 (예시)

```python
@router.get("/narrow", response_model=list[UserNarrowResponse])
async def get_users_narrow(
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """5개 컬럼 테이블 조회"""
    query = select(UserNarrowModel).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
```

---

## k6 스크립트

```javascript
// scenarios/db-advanced/10-db-column-overhead.js
import http from "k6/http";
import { check, group } from "k6";
import { BASE_URL, defaultOptions } from "../config.js";

const LIMIT = 100;

export const options = {
  ...defaultOptions,
  thresholds: {
    "group_duration{group:::A. Column Count - Narrow (5)}": ["p(95)<100"],
    "group_duration{group:::A. Column Count - Wide (20)}": ["p(95)<200"],
    "group_duration{group:::A. Column Count - Extra Wide (50)}": ["p(95)<300"],
  },
};

export default function () {
  // A. 컬럼 수 비교
  group("A. Column Count - Narrow (5)", function () {
    const res = http.get(`${BASE_URL}/column-overhead/narrow?limit=${LIMIT}`);
    check(res, {
      "narrow status 200": (r) => r.status === 200,
      "narrow has items": (r) => r.json().length > 0,
    });
  });

  group("A. Column Count - Wide (20)", function () {
    const res = http.get(`${BASE_URL}/column-overhead/wide?limit=${LIMIT}`);
    check(res, { "wide status 200": (r) => r.status === 200 });
  });

  group("A. Column Count - Extra Wide (50)", function () {
    const res = http.get(`${BASE_URL}/column-overhead/extra-wide?limit=${LIMIT}`);
    check(res, { "extra-wide status 200": (r) => r.status === 200 });
  });

  // B. 데이터 타입별 비교
  group("B. Data Type - INT", function () { /* ... */ });
  group("B. Data Type - VARCHAR", function () { /* ... */ });
  group("B. Data Type - TEXT", function () { /* ... */ });
  group("B. Data Type - JSONB", function () { /* ... */ });
  group("B. Data Type - TIMESTAMP", function () { /* ... */ });
  group("B. Data Type - UUID", function () { /* ... */ });
}
```

---

## 실행 방법

```bash
# 서버 실행
docker compose --profile fastapi-pragmatic up -d

# DB 시드 데이터 확인 (각 테이블 100,000건)
cat scripts/init_db.sql | docker compose exec -T postgres psql -U benchmark -d benchmark

# k6 테스트 실행
k6 run scenarios/db-advanced/10-db-column-overhead.js
```

---

## 벤치마크 결과 (2026-01-01)

### 환경

- 데이터: 각 테이블 100,000건
- VUs: 10
- Duration: 30s
- Limit: 100건/요청

### A. 컬럼 수 비교 결과

| 테이블 | 컬럼 수 | p(95) | Narrow 대비 |
|--------|---------|-------|-------------|
| Narrow | 5개 | 36.33ms | 1.0x (기준) |
| Wide | 20개 | 44.73ms | **1.23x 느림** |
| Extra Wide | 50개 | 52.76ms | **1.45x 느림** |

### B. 데이터 타입별 비교 결과

| 타입 | p(95) | 비고 |
|------|-------|------|
| INT | 36.84ms | |
| TEXT | 36.76ms | |
| UUID | 38.57ms | |
| TIMESTAMP | 38.60ms | |
| JSONB | 41.15ms | 파싱 오버헤드 |

> **Cold Start 발견**: 최초 테스트에서 INT가 48.57ms로 가장 느렸으나, 이는 **B 그룹 첫 번째 호출**이었기 때문. 순서를 변경하여 VARCHAR를 첫 번째로 테스트하자 VARCHAR가 48.53ms로 느려지고 INT는 36.84ms로 정상화됨. **첫 번째 호출 시 약 +10ms cold start 오버헤드** 발생.

**결론: 데이터 타입 간 성능 차이는 미미함 (36~41ms, ±7%)**

### 전체 HTTP 메트릭

| 메트릭 | 값 |
|--------|-----|
| http_req_duration (avg) | 19.97ms |
| http_req_duration (p95) | 39.96ms |
| http_reqs | 14,760 (491/s) |
| 성공률 | 100% |
| data_received | 617 MB (21 MB/s) |

### 모든 체크 통과

```
✓ narrow status 200
✓ narrow has items
✓ wide status 200
✓ wide has items
✓ extra-wide status 200
✓ extra-wide has items
✓ int status 200
✓ varchar status 200
✓ text status 200
✓ jsonb status 200
✓ timestamp status 200
✓ uuid status 200
```

---

## 핵심 포인트

### 1. 컬럼 수와 성능

- 컬럼 수가 **4배** 증가해도 (5개 → 20개) 성능은 **1.23배**만 저하
- 컬럼 수가 **10배** 증가해도 (5개 → 50개) 성능은 **1.45배**만 저하
- 예상보다 선형적이지 않음 → 네트워크/직렬화 오버헤드가 더 큰 영향

### 2. 데이터 타입과 성능

- 모든 타입이 **36~41ms** 범위로 차이가 미미함 (±7%)
- **Cold Start 효과 발견**: 첫 번째 호출되는 그룹이 항상 +10ms 느림
- **JSONB만 약간 느림** (41ms): 바이너리 JSON 파싱 오버헤드
- 결론: **데이터 타입 선택은 성능에 거의 영향 없음**

### 3. 데이터 전송량

- 617 MB / 30초 = **21 MB/s**
- 컬럼이 많을수록 JSON 페이로드 크기 증가
- 네트워크 대역폭이 병목이 될 수 있음

### 4. 실무 적용 가이드

| 상황 | 권장 |
|------|------|
| 목록 조회 (리스트 페이지) | 필요한 컬럼만 SELECT (Projection) |
| 상세 조회 (단건) | 전체 컬럼 OK |
| API 응답 | DTO로 필요한 필드만 반환 |
| ORM 사용 시 | `load_only()` 또는 별도 경량 모델 |

### 5. SELECT * 의 숨겨진 비용

```python
# 안티패턴: 전체 컬럼 로드
query = select(UserWideModel)

# 권장: 필요한 컬럼만 로드
from sqlalchemy.orm import load_only
query = select(UserWideModel).options(
    load_only(UserWideModel.id, UserWideModel.name, UserWideModel.email)
)
```

---

## 향후 실험 (B-2)

> 기존 `users` 테이블에 각 타입별 1개 컬럼만 추가한 테이블 비교
> 실무 질문: "컬럼 하나 추가하면 얼마나 느려질까?"
> 예상: 차이 미미 (1-5% 미만), 하지만 검증 필요

---

## 다음 단계

- 11-db-n-plus-one: N+1 문제 (lazy vs eager loading)
- 캐싱 시나리오 (14-15)와 비교

---

_Last updated: 2026-01-01_
