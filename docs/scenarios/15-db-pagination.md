# 09-db-pagination 시나리오

## 개요

OFFSET vs Cursor 페이지네이션 성능을 비교한다. 100,000건 데이터에서 랜덤 페이지 접근 시 각 방식의 성능 차이를 측정한다.

---

## 측정 목표

- OFFSET 방식의 뒤쪽 페이지 성능 저하 확인
- Cursor 방식의 일정한 성능 확인
- 인덱스 활용 여부에 따른 쿼리 효율성

---

## 페이지네이션 방식 비교

| 방식 | 쿼리 | 시간복잡도 | 특징 |
|------|------|-----------|------|
| OFFSET | `SELECT * FROM users OFFSET 99980 LIMIT 20` | O(offset + limit) | 뒤쪽 페이지일수록 느림 |
| Cursor | `SELECT * FROM users WHERE id > 99980 LIMIT 20` | O(limit) | 항상 일정한 성능 |

### OFFSET이 느린 이유

```sql
-- page 5000 요청 시 (뒤쪽 페이지)
SELECT * FROM users OFFSET 99980 LIMIT 20;
```

DB는 99,980개 행을 **스캔한 후 버리고** 그 다음 20개만 반환한다.

### Cursor가 빠른 이유

```sql
-- cursor=99980 이후 요청 시
SELECT * FROM users WHERE id > 99980 ORDER BY id LIMIT 20;
```

`id`는 Primary Key (인덱스)이므로 바로 해당 위치로 점프하여 20개만 읽는다.

---

## 엔드포인트 스펙

### OFFSET 페이지네이션

```
GET /users/offset?page=1&size=20

Response:
{
  "items": [{ "id": 1, "name": "User1", "email": "...", "created_at": "..." }, ...],
  "total": 100000,
  "page": 1,
  "size": 20,
  "total_pages": 5000
}
```

### Cursor 페이지네이션

```
GET /users/cursor?cursor=0&size=20

Response:
{
  "items": [{ "id": 1, "name": "User1", "email": "...", "created_at": "..." }, ...],
  "next_cursor": 20,  // 다음 페이지 없으면 null
  "size": 20
}
```

---

## 구현 코드

### SQLAlchemy 모델

```python
class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```

### OFFSET 엔드포인트

```python
@router.get("/offset", response_model=PaginatedOffsetResponse)
async def get_users_offset(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * size

    # 전체 개수
    total = (
        await db.execute(select(func.count()).select_from(UserModel))
    ).scalar() or 0

    # 데이터 조회
    query = select(UserModel).offset(offset).limit(size).order_by(UserModel.id)
    result = await db.execute(query)
    items = result.scalars().all()

    return PaginatedOffsetResponse(
        items=[UserResponse.model_validate(m) for m in items],
        total=total,
        page=page,
        size=size,
        total_pages=(total + size - 1) // size,
    )
```

### Cursor 엔드포인트

```python
@router.get("/cursor", response_model=PaginatedCursorResponse)
async def get_users_cursor(
    cursor: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    # WHERE id > cursor (인덱스 활용)
    query = (
        select(UserModel)
        .where(UserModel.id > cursor)
        .order_by(UserModel.id)
        .limit(size + 1)  # 다음 페이지 존재 여부 확인용 +1
    )
    result = await db.execute(query)
    items = list(result.scalars().all())

    # 다음 페이지 존재 여부
    has_next = len(items) > size
    if has_next:
        items = items[:size]

    next_cursor = items[-1].id if has_next and items else None

    return PaginatedCursorResponse(
        items=[UserResponse.model_validate(m) for m in items],
        next_cursor=next_cursor,
        size=size,
    )
```

---

## k6 스크립트

```javascript
// scenarios/db-advanced/09-db-pagination.js
import http from "k6/http";
import { check, group } from "k6";
import { randomIntBetween } from "https://jslib.k6.io/k6-utils/1.2.0/index.js";
import { BASE_URL, defaultOptions } from "../config.js";

const TOTAL_RECORDS = 100000;
const PAGE_SIZE = 20;
const TOTAL_PAGES = Math.floor(TOTAL_RECORDS / PAGE_SIZE);

export const options = {
  ...defaultOptions,
  thresholds: {
    "group_duration{group:::OFFSET pagination}": ["p(95)<500"],
    "group_duration{group:::Cursor pagination}": ["p(95)<200"],
  },
};

export default function () {
  // 랜덤 페이지/커서로 DB 캐싱 효과 최소화
  const randomPage = randomIntBetween(1, TOTAL_PAGES);
  const randomCursor = randomIntBetween(0, TOTAL_RECORDS - PAGE_SIZE);

  group("OFFSET pagination", function () {
    const res = http.get(
      `${BASE_URL}/users/offset?page=${randomPage}&size=${PAGE_SIZE}`
    );
    check(res, {
      "offset status 200": (r) => r.status === 200,
      "offset has items": (r) => r.json().items && r.json().items.length > 0,
      "offset has total": (r) => r.json().total === TOTAL_RECORDS,
    });
  });

  group("Cursor pagination", function () {
    const res = http.get(
      `${BASE_URL}/users/cursor?cursor=${randomCursor}&size=${PAGE_SIZE}`
    );
    check(res, {
      "cursor status 200": (r) => r.status === 200,
      "cursor has items": (r) => r.json().items && r.json().items.length > 0,
    });
  });
}
```

---

## 실행 방법

```bash
# 서버 실행
docker compose --profile fastapi-pragmatic up -d

# DB 시드 데이터 확인 (100,000건)
cat scripts/init_db.sql | docker compose exec -T postgres psql -U benchmark -d benchmark

# k6 테스트 실행
k6 run scenarios/db-advanced/09-db-pagination.js
```

---

## 벤치마크 결과 (2026-01-01)

### 환경
- 데이터: 100,000건
- VUs: 10
- Duration: 30s
- 랜덤 페이지 접근 (DB 캐싱 효과 최소화)

### 결과

| 메트릭 | OFFSET | Cursor | 비교 |
|--------|--------|--------|------|
| p(95) | 60.02ms | 34.42ms | **Cursor 1.7배 빠름** |
| Threshold | < 500ms ✓ | < 200ms ✓ | 모두 통과 |

### 전체 HTTP 메트릭

| 메트릭 | 값 |
|--------|-----|
| http_req_duration (avg) | 16.64ms |
| http_req_duration (p95) | 52.56ms |
| http_reqs | 17,894 (596/s) |
| 성공률 | 100% |

---

## 핵심 포인트

### 1. OFFSET의 한계

- 뒤쪽 페이지일수록 느려짐 (O(offset + limit))
- 페이지 5000 요청 시 99,980개 행을 스캔 후 버림
- 데이터가 많아질수록 성능 저하 심화

### 2. Cursor의 장점

- 항상 일정한 성능 (O(limit))
- Primary Key 인덱스 활용으로 바로 해당 위치 접근
- 데이터 양에 무관하게 일정한 응답 시간

### 3. 실무 적용 가이드

| 상황 | 권장 방식 |
|------|----------|
| 관리자 페이지 (임의 페이지 접근) | OFFSET (UX 우선) |
| 무한 스크롤 (순차 접근) | Cursor |
| 대용량 데이터 (10만건+) | Cursor |
| API 페이지네이션 | Cursor |

#### 관리자 페이지에서 OFFSET을 사용하는 이유

관리자 페이지는 **사용자 경험(UX)**이 성능보다 우선시되는 경우가 많다:

**1. 임의 페이지 접근 (Random Access)**
```
[1] [2] [3] ... [500] ... [4999] [5000]
                  ↑
          "500페이지로 바로 가기"
```
- 관리자가 "500페이지의 데이터를 보고 싶다"고 할 때 바로 접근 가능
- Cursor는 1페이지부터 499페이지를 순차적으로 거쳐야 500페이지 도달

**2. 총 페이지 수 및 현재 위치 표시**
```
"현재 페이지: 500 / 5000"
"총 100,000건 중 9,981 ~ 10,000 표시 중"
```
- OFFSET은 `total` 값으로 전체 개수를 알 수 있음
- Cursor는 "다음이 있는지"만 알 수 있고, 전체 개수는 별도 쿼리 필요

**3. 양방향 탐색**
```
[처음] [이전] [다음] [끝]
```
- OFFSET: 어느 방향이든 자유롭게 이동
- Cursor: 순방향만 가능 (역방향은 별도 구현 필요)

**4. 페이지 번호 기반 UI**
```
[1] [2] [3] [4] [5] ... [10] [다음 10페이지]
```
- 전통적인 게시판 스타일 UI
- Cursor로는 이 UI 패턴 구현이 어려움

**OFFSET 사용 시 성능 완화 전략**

관리자 페이지에서 OFFSET을 사용하더라도 성능 저하를 줄이는 방법:

```sql
-- 1. 최대 페이지 제한
WHERE page <= 100  -- 뒤쪽 페이지 접근 제한

-- 2. 인덱스 활용 (커버링 인덱스)
CREATE INDEX idx_users_id_name ON users(id, name);

-- 3. 검색 조건 추가 (데이터 범위 축소)
WHERE created_at > '2025-01-01'
OFFSET 1000 LIMIT 20  -- 범위가 좁아져 OFFSET 영향 감소
```

**결론**: 관리자 페이지는 동시 사용자가 적고(10명 미만), UX가 중요하므로 OFFSET의 성능 저하를 감수할 만하다. 반면 일반 사용자용 API는 동시 사용자가 많고 순차 접근이 대부분이므로 Cursor가 적합하다.

### 4. Cursor 실무 확장

현재 구현은 `id` (PK) 기반이지만, 실무에서는:

```python
# created_at + id 복합 커서 (Base64 인코딩)
cursor = base64.encode(f"{created_at}:{id}")
```

이렇게 하면 정렬 기준이 `id`가 아닌 경우에도 Cursor 적용 가능.

---

## 다음 단계

- 10-db-column-overhead: 컬럼 수 및 데이터 타입별 오버헤드 측정
- 캐싱 시나리오 (14-15)와 비교하여 DB vs Application 캐싱 효과 분석

---

_Last updated: 2026-01-01_
