# 02-json-payload 시나리오

## 개요

`POST /echo` 엔드포인트를 통해 JSON 직렬화/역직렬화 성능을 측정한다.

---

## 측정 목표

- JSON 파싱 속도 (request body → 객체)
- JSON 직렬화 속도 (객체 → response body)
- Pydantic/Validation 오버헤드

---

## 엔드포인트 스펙

```
POST /echo
Content-Type: application/json

Request Body:
{
  "message": "string",
  "timestamp": number,
  "data": { ... }  // 임의 객체
}

Response: 동일한 JSON 반환
```

---

## k6 스크립트

```javascript
// scenarios/02-json-payload.js
import http from "k6/http";
import { check } from "k6";
import { BASE_URL, defaultOptions } from "./config.js";

export const options = defaultOptions;

const payload = JSON.stringify({
  message: "Hello, benchmark!",
  timestamp: Date.now(),
  data: {
    items: [1, 2, 3, 4, 5],
    nested: { key: "value" },
  },
});

const headers = { "Content-Type": "application/json" };

export default function () {
  const res = http.post(`${BASE_URL}/echo`, payload, { headers });

  check(res, {
    "status is 200": (r) => r.status === 200,
    "echo matches": (r) => r.json().message === "Hello, benchmark!",
  });
}
```

---

## 실행 방법

```bash
cd scenarios
k6 run 02-json-payload.js
```

---

## 핵심 포인트

### 왜 JSON 성능이 중요한가?

대부분의 API는 JSON으로 통신한다. 직렬화/역직렬화는 모든 요청마다 발생하므로:

- 초당 10,000 요청 × 직렬화 2회 = 초당 20,000번 JSON 처리
- 작은 오버헤드도 누적되면 큰 차이

### 프레임워크별 차이점

| Framework | JSON 처리 방식 |
|-----------|---------------|
| FastAPI | Pydantic + orjson (선택) |
| Express | JSON.parse/stringify |
| Go Fiber | encoding/json |

---

## 예상 결과

- 01-lightweight 대비 RPS 감소 예상
- JSON 크기에 따라 성능 차이 발생
