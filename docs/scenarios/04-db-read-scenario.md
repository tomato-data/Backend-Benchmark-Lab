# 03-db-read 시나리오

## 개요

`GET /users` 엔드포인트를 통해 DB 읽기 성능을 측정한다.

---

## 측정 목표

- DB 커넥션 풀 효율성
- ORM 쿼리 실행 속도
- 결과 직렬화 오버헤드

---

## 엔드포인트 스펙

```
GET /users
Response: [{ id, name, email }, ...]

GET /users/{id}
Response: { id, name, email }
```

---

## k6 스크립트

```javascript
// scenarios/03-db-read.js
import http from "k6/http";
import { check } from "k6";
import { BASE_URL, defaultOptions } from "./config.js";

export const options = defaultOptions;

export default function () {
  // 전체 목록 조회
  const listRes = http.get(`${BASE_URL}/users`);

  check(listRes, {
    "list status 200": (r) => r.status === 200,
    "list is array": (r) => Array.isArray(r.json()),
  });
}
```

---

## 실행 방법

```bash
k6 run 03-db-read.js
```

---

## 핵심 포인트

### 커넥션 풀

FastAPI에서 SQLAlchemy async는 기본적으로 커넥션 풀을 사용한다:

```python
create_async_engine(url, pool_size=5, max_overflow=10)
```

- `pool_size`: 유지할 커넥션 수
- `max_overflow`: 추가로 생성 가능한 커넥션 수

### 빈 테이블 vs 데이터 있는 테이블

현재 테스트는 빈/소량 데이터 기준. 실제 성능은 데이터 양에 따라 달라짐.
