# 08-concurrent-mixed 시나리오

## 개요

여러 엔드포인트를 혼합 호출하여 실제 트래픽 패턴을 시뮬레이션한다.

---

## 측정 목표

- 실제 서비스 환경에서의 종합 성능
- 다양한 요청 타입 동시 처리 능력
- 리소스 경합 상황에서의 안정성

---

## 트래픽 비율

실제 서비스를 가정한 요청 분포:

| 엔드포인트 | 비율 | 이유 |
|-----------|------|------|
| GET /health | 5% | 헬스체크 |
| POST /echo | 15% | 일반 API 호출 |
| GET /users | 40% | 읽기가 대부분 |
| POST /users | 10% | 쓰기는 적음 |
| GET /external | 15% | 외부 연동 |
| GET /protected | 15% | 인증 필요 요청 |

> 파일 업로드는 빈도가 낮아 혼합 시나리오에서 제외

---

## k6 스크립트

```javascript
// scenarios/08-concurrent-mixed.js
import http from "k6/http";
import { check } from "k6";
import { BASE_URL, defaultOptions } from "./config.js";

export const options = defaultOptions;

const headers = { "Content-Type": "application/json" };
const authHeaders = {
  "Authorization": "Bearer test-token-12345",
  "X-Request-Id": "mixed-test",
};

export default function () {
  const rand = Math.random() * 100;

  if (rand < 5) {
    // 5%: health
    const res = http.get(`${BASE_URL}/health`);
    check(res, { "health 200": (r) => r.status === 200 });

  } else if (rand < 20) {
    // 15%: echo
    const payload = JSON.stringify({ message: "mixed", data: {} });
    const res = http.post(`${BASE_URL}/echo`, payload, { headers });
    check(res, { "echo 200": (r) => r.status === 200 });

  } else if (rand < 60) {
    // 40%: get users
    const res = http.get(`${BASE_URL}/users`);
    check(res, { "users 200": (r) => r.status === 200 });

  } else if (rand < 70) {
    // 10%: create user
    const uniqueId = `${__VU}_${__ITER}_${Date.now()}`;
    const payload = JSON.stringify({
      name: `Mixed User ${uniqueId}`,
      email: `mixed_${uniqueId}@benchmark.test`,
    });
    const res = http.post(`${BASE_URL}/users`, payload, { headers });
    check(res, { "create 201": (r) => r.status === 201 });

  } else if (rand < 85) {
    // 15%: external
    const res = http.get(`${BASE_URL}/external`);
    check(res, { "external 200": (r) => r.status === 200 });

  } else {
    // 15%: protected
    const res = http.get(`${BASE_URL}/protected`, { headers: authHeaders });
    check(res, { "protected 200": (r) => r.status === 200 });
  }
}
```

---

## 핵심 포인트

### 왜 혼합 시나리오가 중요한가?

단일 엔드포인트 테스트와 달리:
- DB 커넥션 풀 경합
- 메모리 사용 패턴 변화
- 이벤트 루프 / 스레드 풀 활용도

### 실제 서비스 vs 벤치마크

| 항목 | 실제 | 벤치마크 |
|-----|------|---------|
| 사용자 수 | 가변 | 고정 (10 VU) |
| 요청 패턴 | 불규칙 | 균일 분포 |
| 에러 처리 | 중요 | 최소화 |

---

## 실행 방법

```bash
k6 run 08-concurrent-mixed.js
```

## 실행 후 정리

```bash
cat scripts/init_db.sql | docker compose exec -T postgres psql -U benchmark -d benchmark
```
