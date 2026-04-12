# 04-db-write 시나리오

## 개요

`POST /users` 엔드포인트를 통해 DB 쓰기 성능을 측정한다.

---

## 측정 목표

- INSERT 쿼리 성능
- 트랜잭션 커밋 오버헤드
- 유니크 제약조건 처리

---

## 엔드포인트 스펙

```
POST /users
Content-Type: application/json

Request Body:
{
  "name": "string",
  "email": "string"
}

Response: { id, name, email }
```

---

## k6 스크립트

```javascript
// scenarios/04-db-write.js
import http from "k6/http";
import { check } from "k6";
import { BASE_URL, defaultOptions } from "./config.js";

export const options = defaultOptions;

// 유니크 이메일 생성을 위해 VU ID + iteration 사용
export default function () {
  const uniqueId = `${__VU}_${__ITER}_${Date.now()}`;

  const payload = JSON.stringify({
    name: `Test User ${uniqueId}`,
    email: `test_${uniqueId}@benchmark.test`,
  });

  const headers = { "Content-Type": "application/json" };

  const res = http.post(`${BASE_URL}/users`, payload, { headers });

  check(res, {
    "status is 201": (r) => r.status === 201,
    "has id": (r) => r.json().id !== undefined,
  });
}
```

---

## 핵심 포인트

### 유니크 이메일 문제

email 컬럼에 UNIQUE 제약이 있으므로 매 요청마다 고유한 이메일 필요:

- `__VU`: Virtual User 번호
- `__ITER`: 해당 VU의 반복 횟수
- `Date.now()`: 밀리초 타임스탬프

### 테스트 후 정리

벤치마크 후 생성된 테스트 데이터 정리 필요:

```bash
cat scripts/init_db.sql | docker compose exec -T postgres psql -U benchmark -d benchmark
```

---

## 실행 방법

```bash
k6 run 04-db-write.js
```
