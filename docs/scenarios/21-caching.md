# 21. Caching 시나리오 (Redis)

> **목적**: 캐시 도입 전/후 성능 차이 측정
>
> - 14번: 캐시 없는 환경 (순수 DB) - 기준선
> - 15번: 캐시 있는 환경 (Redis) - Hit/Miss 혼합
> - 16-a번: 100% 캐시 히트 - 순수 Redis 성능
> - 16-b번: 100% 캐시 미스 - 캐시 저장 오버헤드 측정

---

## 개요

### 왜 캐싱인가?

데이터베이스 조회는 디스크 I/O, 네트워크 왕복, 쿼리 파싱 등의 오버헤드가 있습니다. 자주 조회되는 데이터를 메모리 기반 캐시(Redis)에 저장하면:

- **응답 시간**: 10~100배 단축 (ms → μs)
- **DB 부하**: 캐시 히트율만큼 감소
- **확장성**: DB 병목 해소

### 시나리오 구성

| 시나리오 | 파일 | Redis | 설명 |
|---------|------|-------|------|
| 14 | `14-no-cache.js` | 불필요 | 순수 DB 성능 (기준선) |
| 15 | `15-with-cache.js` | **필요** | 캐시 Hit/Miss 혼합 |
| 16-a | `16-a-pure-hit.js` | **필요** | 100% 캐시 히트 |
| 16-b | `16-b-pure-miss.js` | **필요** | 100% 캐시 미스 → DB → Set |

**비교 포인트:**
- 14 vs 15: 캐시 도입 효과 (혼합 환경)
- 14 vs 16-a: 캐시 히트 효과 (최대 이득)
- 14 vs 16-b: 캐시 미스 오버헤드 (최악 시나리오)
- 16-a vs 16-b: 순수 Hit vs Miss 차이

---

## 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                      k6 Load Test                        │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     FastAPI Server                       │
├─────────────────────────────────────────────────────────┤
│  GET /cache/users/{id}/no-cache  → DB 직접 조회         │
│  GET /cache/users/{id}/cached    → Redis 우선 조회      │
│  POST /cache/warmup              → 캐시 워밍업          │
│  DELETE /cache/flush             → 캐시 초기화          │
│  DELETE /cache/users/{id}        → 특정 캐시 삭제       │
└─────────────────────────────────────────────────────────┘
          │                              │
          ▼                              ▼
    ┌──────────┐                  ┌──────────┐
    │ PostgreSQL│                  │  Redis   │
    │  (users)  │                  │ (cache)  │
    └──────────┘                  └──────────┘
```

---

## 엔드포인트

### GET /cache/users/{id}/no-cache

캐시를 사용하지 않고 항상 DB에서 조회합니다.

```python
@router.get("/users/{user_id}/no-cache")
async def get_user_no_cache(user_id: int, db: AsyncSession):
    result = await db.execute(
        select(UserModel).where(UserModel.id == user_id)
    )
    user = result.scalar_one_or_none()
    return {"source": "database", ...}
```

### GET /cache/users/{id}/cached

캐시 우선 조회, 미스 시 DB 조회 후 캐시에 저장합니다.

```python
@router.get("/users/{user_id}/cached")
async def get_user_cached(user_id: int, db: AsyncSession, redis: Redis):
    cache_key = f"user:{user_id}"

    # 1. 캐시 조회
    cached = await redis.get(cache_key)
    if cached:
        return {"source": "cache", ...}

    # 2. 캐시 미스 → DB 조회
    user = await db.execute(...)

    # 3. 캐시 저장 (TTL 5분)
    await redis.setex(cache_key, 300, json.dumps(user_data))

    return {"source": "database", ...}
```

---

## k6 시나리오

### 14-no-cache.js (기준선)

```javascript
// Redis 불필요 - 순수 DB 성능 측정
export default function () {
  const userId = Math.floor(Math.random() * 1000) + 1;

  group("No Cache (DB only)", function () {
    const res = http.get(`${BASE_URL}/cache/users/${userId}/no-cache`);
    check(res, {
      "status 200": (r) => r.status === 200,
      "source is database": (r) => r.json().source === "database",
    });
  });
}
```

### 15-with-cache.js (캐시 환경)

```javascript
// Redis 필요 - 캐시 Hit/Miss 혼합
export function setup() {
  http.del(`${BASE_URL}/cache/flush`);
  // 1~100만 워밍업 (10% 히트율)
  http.post(`${BASE_URL}/cache/warmup?count=100`);
}

export default function () {
  const userId = Math.floor(Math.random() * 1000) + 1;
  // 1~100: Cache Hit, 101~1000: Cache Miss → Set

  group("With Cache (Hit/Miss)", function () {
    const res = http.get(`${BASE_URL}/cache/users/${userId}/cached`);
    check(res, {
      "status 200": (r) => r.status === 200,
      "has valid source": (r) =>
        ["cache", "database"].includes(r.json().source),
    });
  });
}
```

### 16-a-pure-hit.js (100% 캐시 히트)

```javascript
// 전체 사용자 워밍업 후 100% 히트
export function setup() {
  http.del(`${BASE_URL}/cache/flush`);
  http.post(`${BASE_URL}/cache/warmup?count=1000`); // 전체 워밍업
}

export default function () {
  const userId = Math.floor(Math.random() * 1000) + 1;

  group("Pure Hit", function () {
    const res = http.get(`${BASE_URL}/cache/users/${userId}/cached`);
    check(res, {
      "status 200": (r) => r.status === 200,
      "source is cache": (r) => r.json().source === "cache",
    });
  });
}
```

### 16-b-pure-miss.js (100% 캐시 미스)

```javascript
// 매 요청마다 캐시 삭제 → 항상 Miss
export default function () {
  const userId = Math.floor(Math.random() * 1000) + 1;

  group("Pure Miss", function () {
    // 1. 해당 키 삭제 (항상 miss 보장)
    http.del(`${BASE_URL}/cache/users/${userId}`);

    // 2. 캐시 조회 (miss → DB → set)
    const res = http.get(`${BASE_URL}/cache/users/${userId}/cached`);
    check(res, {
      "status 200": (r) => r.status === 200,
      "source is database": (r) => r.json().source === "database",
    });
  });
}
```

---

## 실행 방법

### 14번: 캐시 없는 환경

```bash
# Redis 없이 실행 가능
docker-compose up -d postgres fastapi-pragmatic

# 벤치마크 실행
k6 run scenarios/caching/14-no-cache.js
```

### 15번: 캐시 있는 환경

```bash
# Redis 필수
docker-compose up -d postgres redis fastapi-pragmatic

# 벤치마크 실행
k6 run scenarios/caching/15-with-cache.js
```

### 16번: Pure Hit / Pure Miss

```bash
# Redis 필수
docker-compose up -d postgres redis fastapi-pragmatic

# 16-a: 100% 캐시 히트
k6 run scenarios/caching/16-a-pure-hit.js

# 16-b: 100% 캐시 미스
k6 run scenarios/caching/16-b-pure-miss.js
```

---

## 벤치마크 결과 (2026-01-17)

### 테스트 환경

- VUs: 10
- Duration: 30s
- FastAPI Pragmatic + PostgreSQL + Redis

### 전체 결과 비교

| 시나리오 | RPS | avg | p(95) | p(99) | vs 14번 |
|----------|-----|-----|-------|-------|---------|
| **14-no-cache** | 1,238 | 8.00ms | 23.27ms | 55.62ms | 기준선 |
| **15-with-cache** | 5,532 | 1.74ms | 2.26ms | 4.55ms | **10.3배 빠름** |
| **16-a-pure-hit** | 5,605 | 1.72ms | 2.24ms | 3.23ms | **10.4배 빠름** |
| **16-b-pure-miss** | 534 | 9.30ms | 31.06ms | 47.70ms | **1.3배 느림** |

### 상세 결과

#### 14-no-cache (순수 DB)

```
http_req_duration: avg=8ms  med=4.52ms  p(90)=14.59ms  p(95)=23.27ms  p(99)=55.62ms
http_reqs: 37,179 (1,238/s)
checks: 100% passed (source=database)
```

#### 15-with-cache (Redis Hit/Miss 혼합)

```
http_req_duration: avg=1.74ms  med=1.6ms  p(90)=2.02ms  p(95)=2.26ms  p(99)=4.55ms
http_reqs: 166,098 (5,532/s)
checks: 100% passed (source=cache|database)
```

#### 16-a-pure-hit (100% 캐시 히트)

```
http_req_duration: avg=1.72ms  med=1.64ms  p(90)=2.02ms  p(95)=2.24ms  p(99)=3.23ms
http_reqs: 168,816 (5,605/s)
checks: 100% passed (source=cache)
```

#### 16-b-pure-miss (100% 캐시 미스)

```
http_req_duration: avg=9.3ms  med=4.62ms  p(90)=22.74ms  p(95)=31.06ms  p(99)=47.7ms
iterations: 16,057 (534/s)  # DELETE + GET 2회 요청
checks: 99.9% passed (source=database)
```

### 핵심 분석

#### 1. 캐시 히트 효과 (16-a vs 14)

| 메트릭 | 14-no-cache | 16-a-pure-hit | 개선율 |
|--------|-------------|---------------|--------|
| p(95) | 23.27ms | 2.24ms | **10.4배 빠름** |
| RPS | 1,238 | 5,605 | **4.5배 증가** |

→ 캐시 히트 시 **10배 이상** 빠른 응답

#### 2. 캐시 미스 오버헤드 (16-b vs 14)

| 메트릭 | 14-no-cache | 16-b-pure-miss | 차이 |
|--------|-------------|----------------|------|
| p(95) | 23.27ms | 31.06ms | **1.3배 느림** |
| avg | 8.00ms | 9.30ms | **16% 오버헤드** |

→ 캐시 미스 시 **Redis 확인 + Redis 저장** 오버헤드 발생

#### 3. Pure Hit vs Pure Miss (16-a vs 16-b)

| 메트릭 | 16-a-pure-hit | 16-b-pure-miss | 차이 |
|--------|---------------|----------------|------|
| p(95) | 2.24ms | 31.06ms | **13.9배 차이** |
| RPS | 5,605 | 534 | **10.5배 차이** |

→ 히트율이 성능을 결정하는 핵심 요소

### 왜 응답시간 10배 개선인데 처리량은 4.5배일까?

**avg 기준으로 보면 거의 정확히 일치한다:**

| 메트릭 | 14-no-cache | 15-with-cache | 비율 |
|--------|-------------|---------------|------|
| **avg** | 8.00ms | 1.74ms | **4.6배** |
| **p(95)** | 23.27ms | 2.26ms | **10.3배** |
| **RPS** | 1,238 | 5,532 | **4.5배** |

**Little's Law**가 잘 작동한 것이다:
```
처리량 ≈ VUs / 평균응답시간
```

**p(95)가 10.3배인 이유는 응답시간 분포가 더 일관되어졌기 때문:**

| 시나리오 | avg | p(95) | p(95)/avg |
|----------|-----|-------|-----------|
| 14-no-cache | 8ms | 23ms | **2.9배** |
| 15-with-cache | 1.74ms | 2.26ms | **1.3배** |
| 16-a-pure-hit | 1.72ms | 2.24ms | **1.3배** |
| 16-b-pure-miss | 9.3ms | 31ms | **3.3배** |

- **DB 조회**: 변동이 큼 (디스크 I/O, 쿼리 플랜, 버퍼 캐시 상태 등)
- **Redis 조회**: 변동이 적음 (순수 메모리 조회)
- **캐시 미스**: DB 변동 + Redis 저장 오버헤드로 변동 더 큼

**결론**: 코드단 오버헤드가 아니라, 캐시가 응답시간을 더 **일관되게** 만든 것이다. p(95)의 큰 개선은 "꼬리 지연(tail latency) 감소"를 의미하며, 사용자 경험 측면에서 중요한 개선이다.

---

## 핵심 인사이트

### 1. 캐시 도입 효과 (실측)

- **캐시 히트**: p(95) 23ms → 2.2ms (**10.4배 빠름**)
- **캐시 미스**: p(95) 23ms → 31ms (**1.3배 느림**, 16% 오버헤드)
- **결론**: 히트율이 높을수록 이득, 낮으면 오히려 손해

### 2. 캐시 전략

| 전략 | 설명 | 적합한 경우 |
|------|------|------------|
| Cache Aside | 앱에서 직접 관리 (현재 구현) | 읽기 중심 워크로드 |
| Write Through | 쓰기 시 캐시도 갱신 | 일관성 중요 |
| Write Behind | 캐시 먼저, DB는 비동기 | 쓰기 성능 중요 |

### 3. TTL (Time To Live)

현재 설정: **5분 (300초)**

- 너무 짧으면: 캐시 히트율 저하
- 너무 길면: 데이터 불일치 위험

### 4. 캐시 키 설계

```
user:{id}  → "user:123"
```

실무에서는 버전 포함 권장:
```
v1:user:{id}  → 스키마 변경 시 무효화 용이
```

---

## 주의사항

### Redis 연결 실패 시

현재 구현은 Redis 연결 실패 시 에러를 반환합니다. 프로덕션에서는 fallback 로직 필요:

```python
# TODO: 프로덕션용 fallback
try:
    cached = await redis.get(cache_key)
except RedisError:
    # Redis 장애 시 DB로 fallback
    pass
```

### 캐시 무효화 (Cache Invalidation)

사용자 정보 수정 시 캐시 무효화 필요:

```python
@router.put("/users/{user_id}")
async def update_user(user_id: int, ...):
    # 1. DB 업데이트
    # 2. 캐시 삭제
    await redis.delete(f"user:{user_id}")
```

---

## 다음 단계

- [x] 벤치마크 실행 및 결과 기록 (14, 15번) ✅
- [x] Pure Hit / Pure Miss 비교 (16번) ✅
- [ ] 캐시 히트율별 성능 비교 (10%, 50%, 90%)
- [ ] TTL 변화에 따른 영향 측정
- [ ] 캐시 무효화 시나리오 추가

---

_Last updated: 2026-01-17_
