# 06-middleware-chain 시나리오

## 개요

`GET /protected` 엔드포인트를 통해 미들웨어 체인 오버헤드를 측정한다.

---

## 측정 목표

- 인증 미들웨어 처리 비용
- 헤더 파싱/검증 오버헤드
- 미들웨어 체인 누적 비용

---

## 엔드포인트 동작

현재 FastAPI 구현:

```python
@router.get("/protected")
async def protected_endpoint(
    authorization: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
):
    # 1. Authorization 헤더 존재 확인
    # 2. Bearer 형식 검증
    # 3. 토큰 길이 검증 (최소 10자)
    return ProtectedResponse(...)
```

---

## k6 스크립트

```javascript
// scenarios/06-middleware-chain.js
import http from "k6/http";
import { check } from "k6";
import { BASE_URL, defaultOptions } from "./config.js";

export const options = defaultOptions;

export default function () {
  const headers = {
    "Authorization": "Bearer test-token-12345",
    "X-Request-Id": `req-${__VU}-${__ITER}`,
  };

  const res = http.get(`${BASE_URL}/protected`, { headers });

  check(res, {
    "status is 200": (r) => r.status === 200,
    "access granted": (r) => r.json().message === "Access granted",
  });
}
```

---

## 핵심 포인트

### 미들웨어 체인이란?

요청이 핸들러에 도달하기 전 거치는 처리 단계:

```
Request → Auth → Logging → Validation → Handler → Response
```

### 실제 서비스에서의 미들웨어

| 미들웨어 | 역할 |
|---------|------|
| Authentication | JWT 검증, 세션 확인 |
| Authorization | 권한 체크 |
| Logging | 요청/응답 로깅 |
| Rate Limiting | 요청 제한 |
| CORS | 크로스 오리진 처리 |

### 현재 테스트 범위

- Header 파싱
- 간단한 토큰 검증 (실제 JWT 검증 아님)

→ 실제 JWT 검증 시 더 큰 오버헤드 예상

---

## 예상 결과

- 01-lightweight 대비 약간의 오버헤드 추가
- 헤더 파싱 + 문자열 검증 비용

---

## 실행 방법

```bash
k6 run 06-middleware-chain.js
```
