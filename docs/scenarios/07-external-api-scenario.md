# 05-external-api 시나리오

## 개요

`GET /external` 엔드포인트를 통해 외부 API 호출 시 비동기 처리 성능을 측정한다.

---

## 측정 목표

- 비동기 I/O 처리 효율성
- 동시 요청 시 블로킹 여부
- 이벤트 루프 / 스레드 풀 활용도

---

## 엔드포인트 동작

현재 FastAPI 구현:

```python
@router.get("/external")
async def call_external_api():
    # 100ms 외부 API 지연 시뮬레이션
    await asyncio.sleep(0.1)
    return ExternalResponse(...)
```

실제 외부 API 대신 `asyncio.sleep(100ms)`으로 네트워크 지연을 시뮬레이션한다.

---

## k6 스크립트

```javascript
// scenarios/05-external-api.js
import http from "k6/http";
import { check } from "k6";
import { BASE_URL, defaultOptions } from "./config.js";

export const options = defaultOptions;

export default function () {
  const res = http.get(`${BASE_URL}/external`);

  check(res, {
    "status is 200": (r) => r.status === 200,
    "has latency_ms": (r) => r.json().latency_ms !== undefined,
  });
}
```

---

## 핵심 포인트

### 비동기 vs 동기 프레임워크 차이

| 프레임워크 | 방식 | 100ms 지연 시 예상 |
|-----------|------|-------------------|
| FastAPI (async) | 비동기 | 10 VU → ~100 RPS |
| Flask (sync) | 동기 | 10 VU → ~10 RPS (블로킹) |
| Express (async) | 비동기 | 10 VU → ~100 RPS |

### 왜 중요한가?

실제 서비스에서 외부 API 호출(결제, 인증, 써드파티)은 흔함.
I/O 대기 시간 동안 다른 요청을 처리할 수 있는지가 처리량에 큰 영향.

---

## 동기/비동기 & 서버 아키텍처 요약

| 구분 | 동기 (WSGI) | 비동기 (ASGI) |
|-----|------------|--------------|
| 서버 | Gunicorn | Uvicorn |
| 동시성 모델 | 스레드/프로세스 | 코루틴 (이벤트 루프) |
| I/O 대기 시 | 스레드 블로킹 | yield → 다른 코루틴 실행 |
| 메모리 효율 | 낮음 (스레드당 ~1MB) | 높음 (코루틴당 ~KB) |
| 적합한 상황 | CPU-bound | I/O-bound |

### 핵심 차이

- **Gunicorn + Flask**: 워커(프로세스/스레드) 수 = 동시 처리 수
- **Uvicorn + FastAPI**: 단일 스레드에서 수천 개 코루틴 동시 처리

### 이 시나리오에서의 예상 동작

**FastAPI (비동기)**:
1. 10개 VU가 동시에 `/external` 요청
2. 각 요청이 `await asyncio.sleep(0.1)` 도달
3. 코루틴이 yield → 이벤트 루프가 다른 요청 처리
4. 100ms 후 모든 요청이 거의 동시에 완료
5. 결과: **~100 RPS** (10 VU × 10회/초)

**Flask (동기, 가정)**:
1. 10개 VU가 동시에 요청
2. 워커 4개라면 4개만 처리, 6개는 대기
3. 각 워커가 100ms 동안 블로킹
4. 결과: **~40 RPS** (4 워커 × 10회/초)

→ 상세 내용은 별도 지식 베이스 참조

---

## 예상 결과

- 100ms sleep이므로 단일 요청 최소 ~100ms
- 비동기 프레임워크: 10 VU × (1000ms / 100ms) = ~100 RPS
- 동기 프레임워크: 10 VU × 1 = ~10 RPS

---

## 실행 방법

```bash
k6 run 05-external-api.js
```
