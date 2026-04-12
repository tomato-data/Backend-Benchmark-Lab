# k6 Benchmark Setup

## 개요

k6는 Grafana Labs에서 만든 현대적인 부하 테스트 도구다. JavaScript로 시나리오를 작성하고, Go로 구현되어 높은 성능을 제공한다.

---

## Step 1: k6 설치

### macOS

```bash
brew install k6
```

### 설치 확인

```bash
k6 version
```

---

## Step 2: 공통 설정 파일

모든 시나리오에서 공유할 설정을 `scenarios/config.js`에 정의한다.

### 왜 공통 설정인가?

- `BASE_URL` 변경 시 한 곳만 수정
- 테스트 옵션(VU 수, 시간 등) 일관성 유지
- DRY(Don't Repeat Yourself) 원칙

### 파일 내용

```javascript
// scenarios/config.js
export const BASE_URL = "http://localhost:8000";

export const defaultOptions = {
  vus: 10,           // Virtual Users (동시 사용자)
  duration: "30s",   // 테스트 지속 시간
};
```

### k6 핵심 개념

| 개념 | 설명 |
|-----|------|
| VU (Virtual User) | 가상 사용자. 동시에 요청을 보내는 사용자 수 |
| Duration | 테스트가 실행되는 총 시간 |
| Iteration | 각 VU가 default 함수를 실행하는 횟수 |
| RPS | Requests Per Second. 초당 요청 수 |

---

## Step 3: 시나리오 작성

### 시나리오 목록

| 파일 | 엔드포인트 | 측정 목표 |
|-----|-----------|----------|
| `01-lightweight.js` | `GET /health` | 프레임워크 오버헤드 |
| `02-json-payload.js` | `POST /echo` | JSON 직렬화 성능 |
| `03-db-read.js` | `GET /users` | DB 읽기 성능 |
| `04-db-write.js` | `POST /users` | DB 쓰기 성능 |
| `05-external-api.js` | `GET /external` | 비동기 I/O 처리 |
| `06-middleware-chain.js` | `GET /protected` | 미들웨어 체인 오버헤드 |
| `07-file-upload.js` | `POST /upload` | 파일 스트리밍 |
| `08-concurrent-mixed.js` | 혼합 | 실제 트래픽 시뮬레이션 |

### 01-lightweight.js 예시

```javascript
import http from "k6/http";
import { check } from "k6";
import { BASE_URL, defaultOptions } from "./config.js";

export const options = defaultOptions;

export default function () {
  const res = http.get(`${BASE_URL}/health`);

  check(res, {
    "status is 200": (r) => r.status === 200,
  });
}
```

### k6 스크립트 구조 설명

1. **import**: k6 모듈 및 공통 설정 불러오기
2. **options**: 테스트 설정 (VU, duration 등)
3. **default function**: 각 VU가 반복 실행하는 로직

---

## Step 4: 테스트 실행

```bash
# 1. 백엔드 실행
cd implementations
docker compose --profile fastapi up -d

# 2. k6 실행
cd ../scenarios
k6 run 01-lightweight.js
```

### 결과 해석

```
     checks.....................: 100.00% ✓ 5000  ✗ 0
     http_req_duration..........: avg=1.2ms  min=0.5ms  max=15ms  p(95)=2.5ms
     http_reqs..................: 5000    166.67/s
     vus........................: 10      min=10  max=10
```

| 메트릭 | 의미 |
|-------|------|
| checks | 검증 통과율 |
| http_req_duration | 요청 응답 시간 (avg, p95 중요) |
| http_reqs | 총 요청 수 및 RPS |

---

## 다음 단계

각 시나리오를 순서대로 작성하며 테스트 진행.
