# 26. 서버 구성 실험: Uvicorn 단독 vs Gunicorn+Uvicorn 멀티프로세스

> **실험 목적**: 동일한 FastAPI 앱을 서로 다른 서버 구성(프로세스 모델)과 CPU 자원으로 실행했을 때, 워크로드 유형에 따라 성능이 어떻게 달라지는지 검증한다.

---

## 1. 핵심 가설 3개

| # | 가설 | 검증 라운드 |
|---|------|------------|
| H1 | I/O-bound에서는 비동기 단일 프로세스가 동기 멀티프로세스를 이긴다 | Round 1 |
| H2 | CPU-bound에서는 멀티프로세스가 비동기를 이긴다 | Round 2 |
| H3 | 저사양(0.25~0.5 vCPU)에서 멀티프로세스는 오히려 역효과다 | Round 3, 4 |

> **중요한 구분**: Gunicorn + UvicornWorker 조합은 진정한 WSGI가 아니다. 각 워커가 여전히 ASGI(비동기)로 동작한다. 실험의 본질은 **"단일 이벤트 루프 vs 다중 이벤트 루프(멀티프로세스)"** 비교다.

---

## 2. 실험 변수 설계

### 독립변수 (조작하는 것)

| 변수 | 값 | 비고 |
|------|----|------|
| **워크로드 유형** | I/O-bound, CPU-bound, Mixed | 엔드포인트로 구분 |
| **서버 구성** | Uvicorn 단독, Gunicorn 2워커, Gunicorn 4워커 | CMD만 변경 |
| **컨테이너 CPU** | 0.25, 0.5, 1, 2 vCPU | `deploy.resources.limits.cpus` |

### 종속변수 (측정하는 것)

| 측정 항목 | 출처 | 비고 |
|----------|------|------|
| RPS (초당 요청 수) | k6 `http_reqs` | 처리량 |
| P50 / P95 / P99 응답시간 | k6 `http_req_duration` | 레이턴시 |
| 에러율 | k6 `http_req_failed` | 안정성 |
| CPU 사용률 | docker stats | 자원 효율 |
| 메모리 사용량 | docker stats | 오버헤드 |

### 통제변수 (고정하는 것)

| 항목 | 값 | 이유 |
|------|----|------|
| 앱 코드 | 동일한 FastAPI 앱 | 변수 분리 |
| Python 버전 | 3.12 | 일관성 |
| 메모리 제한 | 2GB (넉넉히) | CPU만 변수로 |
| PostgreSQL | 동일 인스턴스 (cpus: 2) | DB가 병목이면 안 됨 |
| k6 VU 수 | 단계별 고정 (10→50→100→200) | 부하 통일 |
| 테스트 시간 | 60초 (+ 10초 워밍업) | 안정 수치 확보 |

---

## 3. 프로젝트 파일 구조

```
benchmark-lab/
├── implementations/
│   └── python-server-config/             # ← 새로 만들 구현체
│       ├── src/
│       │   └── main.py                   # FastAPI 앱 (실험 전용 엔드포인트)
│       ├── Dockerfile                    # 기존 패턴 그대로 + gunicorn 추가
│       └── pyproject.toml                # 의존성
│
├── experiments/                          # ← 새 디렉토리 (실험 전용)
│   └── server-config/
│       ├── docker-compose.yml            # 3개 서버 구성 × CPU 제한
│       ├── k6/
│       │   ├── config.js                 # 실험 전용 k6 설정
│       │   ├── io-sleep.js               # /io/sleep 시나리오
│       │   ├── io-db.js                  # /io/db 시나리오
│       │   ├── cpu-fibonacci.js          # /cpu/fibonacci 시나리오
│       │   ├── cpu-hash.js               # /cpu/hash 시나리오
│       │   └── mixed-report.js           # /mixed/report 시나리오
│       ├── runner.sh                     # 실험 자동화 스크립트
│       └── results/                      # 실험 결과 저장
│           └── YYYY-MM-DD/
│               ├── round1/
│               ├── round2/
│               ├── round3/
│               └── round4/
│
└── docs/
    └── 26-server-config-experiment.md    # 이 문서
```

> **왜 `experiments/` 디렉토리를 새로 만드는가?**
> - 기존 `scenarios/`는 "프레임워크 간 비교"용. 이 실험은 "같은 프레임워크, 다른 구성" 비교라서 성격이 다르다.
> - docker-compose, k6, runner가 하나의 실험 단위로 묶이는 게 깔끔하다.
> - 향후 다른 실험(e.g., 커넥션 풀 크기 실험)도 같은 구조로 추가할 수 있다.

---

## 4. 구현체: `implementations/python-server-config/`

### 4.1 엔드포인트 설계

기존 BBL 8개 엔드포인트와는 별개로, 이 실험 전용 엔드포인트를 만든다.

#### I/O-bound 엔드포인트

| 엔드포인트 | 동작 | 왜 이것인가 |
|-----------|------|-------------|
| `GET /io/sleep` | `await asyncio.sleep(0.1)` | 순수 I/O 대기. 외부 변수 0. 가장 깔끔한 기준선 |
| `GET /io/db` | PostgreSQL `SELECT u.*, COUNT(o.id) FROM users u LEFT JOIN orders o ...` | 실제 DB I/O. 현실감 추가 |
| `GET /io/external` | `httpx.AsyncClient`로 외부 HTTP 호출 시뮬레이션 | 네트워크 I/O (실제 외부 서비스 대신 별도의 지연 서비스 호출) |

#### CPU-bound 엔드포인트

| 엔드포인트 | 동작 | 왜 이것인가 |
|-----------|------|-------------|
| `GET /cpu/fibonacci?n=35` | 재귀 피보나치 (순수 Python) | `await` 없는 순수 연산. n으로 부하 미세 조절 가능 |
| `GET /cpu/hash` | bcrypt 해싱 (rounds=12) | 현실적 CPU-bound. 비밀번호 처리 시나리오 |
| `GET /cpu/json-serialize` | 10,000개 항목 딕셔너리 반복 직렬화 | 메모리 + CPU 복합 |

#### Mixed 엔드포인트

| 엔드포인트 | 동작 | 왜 이것인가 |
|-----------|------|-------------|
| `GET /mixed/report` | DB 조회(I/O) → 데이터 집계/가공(CPU) → 결과 반환 | 실무에서 가장 흔한 패턴 |

#### 유틸리티 엔드포인트

| 엔드포인트 | 동작 | 용도 |
|-----------|------|------|
| `GET /health` | `{"status": "ok", "server": "...", "workers": N, "pid": ...}` | 서버 구성 확인 + health check |

### 4.2 `/health` 응답에 포함할 메타데이터

실험 결과를 해석할 때 "이게 어떤 구성이었는지" 알아야 하므로, health 응답에 다음을 포함:

```
{
  "status": "ok",
  "server": "uvicorn" | "gunicorn+uvicorn",
  "workers": 1 | 2 | 4,
  "pid": 현재_프로세스_ID,
  "cpu_limit": "환경변수에서 읽기"
}
```

> 토마토 힌트: `os.getpid()`로 PID, `os.cpu_count()`로 가용 CPU 수를 알 수 있다. `SERVER_TYPE`과 `WORKER_COUNT` 환경변수를 넘겨서 health에서 읽으면 된다.

### 4.3 의존성 (`pyproject.toml`)

기존 `python-fastapi-pragmatic`의 의존성 + 추가분:

| 패키지 | 용도 | 기존 대비 |
|--------|------|----------|
| `fastapi` | 웹 프레임워크 | 기존 |
| `uvicorn[standard]` | ASGI 서버 | 기존 |
| `gunicorn` | 멀티프로세스 매니저 | **신규** |
| `asyncpg` | PostgreSQL 비동기 드라이버 | 기존 |
| `sqlalchemy[asyncio]` | ORM | 기존 |
| `httpx` | 비동기 HTTP 클라이언트 | 기존 |
| `bcrypt` | 비밀번호 해싱 | **신규** |

### 4.4 Dockerfile

기존 `python-fastapi-pragmatic/Dockerfile`을 거의 그대로 사용. 차이점:
- `gunicorn` 패키지가 추가됨 (pyproject.toml에 포함되므로 Dockerfile 수정 불필요)
- CMD는 docker-compose에서 override할 것이므로 기본값은 Uvicorn 단독으로

### 4.5 앱 구조 (간결하게)

이 실험 앱은 기존 pragmatic 버전처럼 계층을 분리할 필요가 없다. **실험의 순수성**이 더 중요하므로 단일 `main.py`에 모든 엔드포인트를 넣는 것이 적절하다.

```
src/
└── main.py          # 모든 엔드포인트 (10개 미만이므로 분리 불필요)
```

> 복잡한 아키텍처가 성능에 미치는 영향을 제거하기 위해 의도적으로 단순화.

---

## 5. Docker Compose 전략

### 5.1 핵심 아이디어

**하나의 이미지, 세 개의 서비스, 네 개의 CPU 프로파일.**

docker-compose에서 같은 이미지를 `command`만 바꿔서 3개 서비스로 정의하고, CPU 제한은 실행 시 환경변수로 주입한다.

### 5.2 서비스 구성

```
experiments/server-config/docker-compose.yml
```

| 서비스 이름 | 프로파일 | CMD | 포트 |
|------------|---------|-----|------|
| `postgres` | (항상) | - | 5432 |
| `app-uvicorn` | `uvicorn` | `uvicorn src.main:app --host 0.0.0.0 --port 8000` | 8000 |
| `app-gunicorn-2w` | `gunicorn-2w` | `gunicorn src.main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000` | 8000 |
| `app-gunicorn-4w` | `gunicorn-4w` | `gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000` | 8000 |

### 5.3 CPU 제한 방식

`deploy.resources.limits.cpus`를 환경변수로 치환:

```yaml
# docker-compose.yml 핵심 구조 (토마토가 실제 작성할 것)

# 환경변수 CPU_LIMIT로 제어
# 실행: CPU_LIMIT=0.25 docker compose --profile uvicorn up -d

services:
  app-uvicorn:
    build: ../../implementations/python-server-config
    profiles: ["uvicorn"]
    command: ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
    environment:
      SERVER_TYPE: uvicorn
      WORKER_COUNT: 1
      CPU_LIMIT: ${CPU_LIMIT:-1}
    deploy:
      resources:
        limits:
          cpus: "${CPU_LIMIT:-1}"
          memory: 2G
```

> **핵심 포인트**: 같은 포트(8000)를 쓰므로 한 번에 하나의 서비스만 실행. 이건 기존 BBL 패턴(프레임워크별 profile 선택)과 동일하다.

### 5.4 PostgreSQL 분리

이 실험의 postgres는 기존 `implementations/docker-compose.yml`의 postgres와 **별도로** 띄운다:
- 포트 충돌 방지 (5433 사용 또는 internal network만)
- 실험용 DB가 기존 벤치마크 데이터를 오염시키지 않도록

또는, 기존 postgres를 그대로 공유하되 **다른 데이터베이스 이름**을 사용:
- `benchmark` (기존) vs `benchmark_experiment` (실험용)

> 토마토 판단: 둘 다 장단점이 있다. 단순함을 위해 실험 전용 compose에 postgres를 포함하는 것을 추천.

---

## 6. k6 시나리오 설계

### 6.1 공통 설정 (`config.js`)

기존 BBL k6 config와 비슷하되, 실험 특화 설정:

```
- BASE_URL: http://localhost:8000
- 워밍업: 10초, 5 VU
- 본 테스트: 60초, 고정 VU
- VU 단계: 10 → 50 → 100 → 200
- 통계: avg, min, med, max, p(90), p(95), p(99)
- 반복: 3회
```

### 6.2 시나리오 파일

| 파일 | 대상 엔드포인트 | VU 패턴 | 비고 |
|------|----------------|---------|------|
| `io-sleep.js` | `GET /io/sleep` | 고정 VU × 60s | 가장 먼저 실행. 기준선 |
| `io-db.js` | `GET /io/db` | 고정 VU × 60s | DB 커넥션 풀 영향 관찰 |
| `cpu-fibonacci.js` | `GET /cpu/fibonacci?n=35` | 고정 VU × 60s | 이벤트 루프 블로킹 관찰 |
| `cpu-hash.js` | `GET /cpu/hash` | 고정 VU × 60s | 현실적 CPU-bound |
| `mixed-report.js` | `GET /mixed/report` | 고정 VU × 60s | 복합 패턴 |

### 6.3 VU 단계 전략

각 시나리오를 **4개 VU 레벨**로 실행. k6의 `stages`가 아닌 **별도 실행**으로 분리하는 것을 추천:

```
io-sleep.js를 VU=10으로 60초
→ 30초 쿨다운
→ io-sleep.js를 VU=50으로 60초
→ 30초 쿨다운
→ io-sleep.js를 VU=100으로 60초
→ ...
```

> 왜 stages가 아닌 별도 실행? → 각 VU 레벨의 결과가 깔끔하게 분리된 JSON으로 저장됨. stages를 쓰면 구간별 분리가 복잡.

### 6.4 k6 실행 옵션

```bash
k6 run --vus ${VU} --duration 60s \
  --summary-export results/${ROUND}/${CONFIG}-${SCENARIO}-vu${VU}-run${RUN}.json \
  k6/${SCENARIO}.js
```

파일명 컨벤션: `{서버구성}-{시나리오}-vu{VU수}-run{반복횟수}.json`

예: `uvicorn-io-sleep-vu50-run2.json`

---

## 7. 실험 라운드 설계

### Round 1: I/O-bound에서 비동기 우위 증명

**가설 H1 검증**

| 고정 변수 | 값 |
|----------|-----|
| 워크로드 | `/io/sleep` (순수 I/O) |
| CPU | 1 vCPU |
| VU | 10 → 50 → 100 → 200 |

| 서버 구성 | 예상 | 관찰 포인트 |
|----------|------|------------|
| Uvicorn 단독 | 높은 RPS, 낮은 P99 | 단일 이벤트 루프가 I/O 대기를 효율적으로 멀티플렉싱 |
| Gunicorn 2워커 | 비슷하거나 약간 낮음 | 워커 간 분산 오버헤드. 이미 비동기라 워커 추가 이득 미미 |
| Gunicorn 4워커 | 비슷. 메모리만 증가 | 메모리 4배 사용, RPS 이득 없음 → 자원 낭비 증명 |

**추가 실행 (선택)**: `/io/db`로 동일 조건 반복. 순수 sleep과 실제 DB I/O의 차이 관찰.

---

### Round 2: CPU-bound에서 멀티프로세스 우위 증명

**가설 H2 검증**

| 고정 변수 | 값 |
|----------|-----|
| 워크로드 | `/cpu/fibonacci?n=35` |
| CPU | **2 vCPU** (멀티프로세스가 활용할 수 있도록) |
| VU | 10 → 50 → 100 |

| 서버 구성 | 예상 | 관찰 포인트 |
|----------|------|------------|
| Uvicorn 단독 | 낮은 RPS | GIL + 단일 프로세스 = 하나의 요청이 이벤트 루프를 점유 |
| Gunicorn 2워커 | ~2배 RPS | 2개 프로세스 = 2개 GIL = 병렬 실행 |
| Gunicorn 4워커 | ~2배 RPS (2vCPU 한계) | vCPU보다 워커가 많으면 컨텍스트 스위칭만 추가 |

**관찰할 것**: Uvicorn 단독에서 VU를 올리면 P99가 **선형으로** 증가하는지. 이벤트 루프가 블로킹되면 큐잉 효과가 발생해야 한다.

---

### Round 3: 저사양 + I/O-bound (멀티프로세스 역효과)

**가설 H3 검증 (I/O)**

| 고정 변수 | 값 |
|----------|-----|
| 워크로드 | `/io/sleep` |
| CPU | **0.25 vCPU** |
| VU | 10 → 50 |

| 서버 구성 | 예상 | 관찰 포인트 |
|----------|------|------------|
| Uvicorn 단독 | 기준선 | 0.25 vCPU로도 I/O 대기는 충분히 처리 |
| Gunicorn 2워커 | RPS 하락 | 프로세스 스케줄링 오버헤드 > 병렬화 이득 |
| Gunicorn 4워커 | 더 하락 + 메모리 폭발 | 4개 프로세스가 0.25 vCPU를 나눠 씀 |

**핵심 관찰**: 메모리 사용량. Gunicorn 4워커의 메모리가 Uvicorn 단독의 3~4배인지.

---

### Round 4: 저사양 + CPU-bound (최악의 조합)

**가설 H3 검증 (CPU)**

| 고정 변수 | 값 |
|----------|-----|
| 워크로드 | `/cpu/fibonacci?n=35` |
| CPU | **0.25 vCPU** |
| VU | 10 |

| 서버 구성 | 예상 | 관찰 포인트 |
|----------|------|------------|
| Uvicorn 단독 | 느리지만 기준선 | CPU 시간 전체를 연산에 사용 |
| Gunicorn 4워커 | 더 느림 | 동일한 CPU 시간을 4개 프로세스가 나눔 + 스케줄링 오버헤드 |

**추가 관찰**: P99 레이턴시. Gunicorn에서 특정 워커만 CPU를 받지 못해 starvation이 발생하면 P99가 비정상적으로 높아질 수 있다.

---

### Round 5 (보너스): Mixed 워크로드

Round 1~4의 결과를 확인한 후, `/mixed/report`로 현실적 시나리오 검증.

| 고정 변수 | 값 |
|----------|-----|
| 워크로드 | `/mixed/report` |
| CPU | 1 vCPU, 2 vCPU |
| VU | 50 |

> 이 라운드는 결과를 예측하기 어렵다. I/O와 CPU가 혼합되므로 "어떤 부분이 병목이냐"에 따라 달라진다. 이게 오히려 가장 현실적인 학습이 될 것.

---

## 8. 실험 자동화 (`runner.sh`)

### 8.1 기본 흐름

```
1. 인자 파싱 (라운드, 서버 구성, VU 등)
2. PostgreSQL 기동 + health check
3. 서버 컨테이너 기동 (지정된 구성 + CPU 제한)
4. health check (서버 준비 확인)
5. 워밍업 (10초, 5 VU)
6. 벤치마크 실행 (60초, 지정 VU, 3회 반복)
7. 결과 저장
8. 서버 컨테이너 종료
9. 쿨다운 (30초)
10. 다음 구성으로 반복
```

### 8.2 실행 예시

```bash
# Round 1 전체 실행
./runner.sh round1

# 특정 조합만
./runner.sh --config uvicorn --cpu 1 --scenario io-sleep --vu 50

# Round 2 전체 실행
./runner.sh round2
```

### 8.3 라운드별 자동 매트릭스

runner.sh가 라운드 번호를 받으면 해당 라운드의 모든 조합을 순차 실행:

```
Round 1 = {
  configs: [uvicorn, gunicorn-2w, gunicorn-4w],
  cpu: [1],
  scenario: [io-sleep],
  vu: [10, 50, 100, 200],
  runs: 3
}
→ 3 configs × 1 cpu × 1 scenario × 4 vu × 3 runs = 36 runs
→ 36 × (10초 워밍업 + 60초 테스트 + 30초 쿨다운) ≈ 60분
```

### 8.4 결과 디렉토리 구조

```
experiments/server-config/results/2026-02-22/
├── round1/
│   ├── uvicorn-io-sleep-vu10-run1.json
│   ├── uvicorn-io-sleep-vu10-run2.json
│   ├── uvicorn-io-sleep-vu10-run3.json
│   ├── uvicorn-io-sleep-vu50-run1.json
│   ├── ...
│   ├── gunicorn-2w-io-sleep-vu10-run1.json
│   ├── ...
│   └── gunicorn-4w-io-sleep-vu200-run3.json
├── round2/
│   └── ...
├── docker-stats/                    # docker stats 로그 (선택)
│   ├── uvicorn-1cpu-io-sleep-vu50.log
│   └── ...
└── summary.md                       # 결과 요약 (수동 작성 또는 스크립트)
```

---

## 9. 실행 순서 권장

### Phase 1: 기반 구축

| 순서 | 작업 | 산출물 |
|------|------|--------|
| 1 | `implementations/python-server-config/` 앱 구현 | `src/main.py`, `Dockerfile`, `pyproject.toml` |
| 2 | 로컬에서 Uvicorn 단독으로 앱 기동 테스트 | 모든 엔드포인트 수동 확인 |
| 3 | Gunicorn으로 앱 기동 테스트 | `gunicorn src.main:app -w 2 -k uvicorn.workers.UvicornWorker` |
| 4 | `experiments/server-config/docker-compose.yml` 작성 | 3개 서비스 정의 |
| 5 | Docker로 각 구성 기동 테스트 | health 엔드포인트로 확인 |

### Phase 2: k6 시나리오 작성

| 순서 | 작업 | 산출물 |
|------|------|--------|
| 6 | `io-sleep.js` 작성 및 수동 실행 | k6 결과 확인 |
| 7 | `cpu-fibonacci.js` 작성 및 수동 실행 | k6 결과 확인 |
| 8 | 나머지 시나리오 작성 | 5개 시나리오 |

### Phase 3: 자동화 및 실험

| 순서 | 작업 | 산출물 |
|------|------|--------|
| 9 | `runner.sh` 작성 | 자동화 스크립트 |
| 10 | **Round 1** 실행 | I/O-bound 결과 |
| 11 | 결과 분석 및 검증 | H1 검증 |
| 12 | **Round 2** 실행 | CPU-bound 결과 |
| 13 | 결과 분석 및 검증 | H2 검증 |
| 14 | **Round 3, 4** 실행 | 저사양 결과 |
| 15 | 전체 결과 정리 | 실험 보고서 |

---

## 10. 실험 주의사항 체크리스트

### 실행 전

- [ ] Docker Desktop의 CPU/메모리 할당 확인 (최소 4 CPU, 8GB 메모리 권장)
- [ ] 다른 무거운 프로세스 종료 (브라우저 탭, IDE 등)
- [ ] 기존 BBL 컨테이너 모두 종료 (`docker compose down`)
- [ ] k6 설치 확인 (`k6 version`)

### 실행 중

- [ ] 각 테스트 전 **10초 워밍업** (JIT, 커넥션 풀 안정화)
- [ ] 테스트 간 **30초 쿨다운** (잔여 부하 제거)
- [ ] 같은 조건 **최소 3회 반복** (노이즈 제거, 중앙값 사용)
- [ ] `docker stats`로 CPU/메모리 실시간 확인 (별도 터미널)
- [ ] 순서: 반드시 **`/io/sleep` 먼저** (기준선 확보 후 다른 시나리오)

### 실행 후

- [ ] 이상치(outlier) 확인: 3회 반복 중 1회만 유독 다르면 해당 run 재실행
- [ ] 결과 커밋 전 JSON 파일 검증 (빈 파일, 에러 결과 제외)

---

## 11. 예상 학습 포인트

이 실험이 끝나면 다음 질문에 **데이터로** 답할 수 있게 된다:

1. **"Fargate 0.25 vCPU에서 Gunicorn 4워커 쓰면 빨라지나요?"** → Round 3이 답
2. **"FastAPI는 왜 Uvicorn 단독으로도 빠른가요?"** → Round 1이 답 (이벤트 루프 멀티플렉싱)
3. **"CPU-heavy 작업에서 Python이 느린 건 GIL 때문인가요?"** → Round 2가 답 (멀티프로세스로 GIL 우회)
4. **"워커 수는 vCPU 수와 일치시켜야 하나요?"** → Round 2에서 4워커 vs 2워커 비교가 답
5. **"우리 서비스는 어떤 구성을 써야 하나요?"** → Round 5(Mixed)가 현실적 가이드

---

## 12. `/io/external` 엔드포인트 구현 시 주의사항

자기 자신의 `/io/sleep`을 호출하는 방식은 **추천하지 않는다**. 이유:
- 컨테이너 안에서 자기 자신에게 HTTP 요청을 보내면, 그 요청도 같은 이벤트 루프/워커에서 처리해야 함
- 부하 테스트 시 외부 호출과 내부 처리가 같은 자원을 놓고 경쟁 → 변수가 복잡해짐

대안:
1. **별도의 지연 서비스 컨테이너**를 docker-compose에 추가 (nginx + lua로 100ms sleep, 또는 간단한 Python 앱)
2. 또는 Round 1~4에서는 `/io/external`을 **생략**하고, `/io/sleep`과 `/io/db`만으로 충분히 검증

> 첫 실험에서는 변수를 최소화하는 게 좋으므로, `/io/external`은 후속 실험으로 미루는 것을 추천.

---

## 13. fibonacci n값 캘리브레이션

`n=35`는 대략 3~5초 걸린다 (Python 3.12, M1 기준). 이건 벤치마크에서 너무 오래 걸릴 수 있다.

**사전 캘리브레이션 필요:**

```
n=30 → ~0.3초
n=32 → ~0.8초
n=35 → ~3초
n=38 → ~15초
```

**권장**: `n=32`부터 시작해서 1 vCPU 환경에서 1회 응답이 0.5~1초 정도 나오는 값을 찾을 것. 너무 짧으면 프레임워크 오버헤드와 구분이 안 되고, 너무 길면 k6 타임아웃.

---

## 요약: 전체 매트릭스

| 라운드 | 워크로드 | CPU | 서버 구성 | VU | 조합 수 |
|--------|---------|-----|----------|-----|---------|
| R1 | io-sleep | 1 | 3종 | 4단계 | 12 |
| R2 | cpu-fibonacci | 2 | 3종 | 3단계 | 9 |
| R3 | io-sleep | 0.25 | 3종 | 2단계 | 6 |
| R4 | cpu-fibonacci | 0.25 | 2종 | 1단계 | 2 |
| R5 | mixed-report | 1, 2 | 3종 | 1단계 | 6 |
| | | | | **총 조합** | **35** |
| | | | | **× 3회 반복** | **105 runs** |
| | | | | **예상 소요** | **~3시간** |
