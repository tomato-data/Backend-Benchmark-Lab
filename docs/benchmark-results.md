# Benchmark Results

벤치마크 결과 비교표. 각 프레임워크별 시나리오 결과를 기록한다.

---

## 결과 테이블 읽는 법

### 메트릭 설명

| 메트릭 | 의미 | 좋은 값 |
|-------|------|--------|
| **RPS (avg±std)** | 초당 요청 처리 수 (평균 ± 표준편차) | 높을수록 좋음 |
| **Latency avg** | 평균 응답 시간 | 낮을수록 좋음 |
| **Latency p95** | 95번째 백분위 응답 시간 (상위 5% 제외) | 낮을수록 좋음 |
| **Latency p99** | 99번째 백분위 응답 시간 (상위 1% 제외) | 낮을수록 좋음 |
| **Runs** | 테스트 실행 횟수 (평균 계산에 사용) | 10회 |

### RPS 해석

```
13772.6±374.31
   │      └── 표준편차: 실행마다 ±374 정도 변동
   └── 평균: 초당 13,772개 요청 처리
```

- **표준편차가 작을수록** 성능이 안정적
- **평균이 높을수록** 처리량이 좋음

### Latency 해석

```
avg: 0.707ms   →  평균적으로 0.7ms 소요
p95: 0.994ms   →  95%의 요청이 1ms 이내 완료
```

- **p95가 avg보다 훨씬 높으면** 간헐적 지연(spike)이 있다는 의미
- 실제 서비스에서는 **p95/p99**가 사용자 경험에 중요

### 시나리오별 특성

| 시나리오 | 측정 대상 | 예상 병목 |
|---------|----------|----------|
| 01-lightweight | 프레임워크 오버헤드 | 라우팅, 직렬화 |
| 02-json-payload | JSON 파싱/직렬화 | Pydantic, JSON 라이브러리 |
| 03-db-read | DB 읽기 | 커넥션 풀, ORM |
| 04-db-write | DB 쓰기 | 트랜잭션, 락 |
| 05-external-api | 비동기 I/O | 이벤트 루프 |
| 06-middleware-chain | 미들웨어 체인 | 헤더 파싱, 검증 |
| 07-file-upload | 파일 처리 | 멀티파트 파싱 |
| 08-concurrent-mixed | 종합 성능 | 리소스 경합 |

---

## 테스트 환경

### k6 설정

| 항목 | 값 |
|-----|---|
| VUs | 10 |
| Duration | 30s |
| Runs | 10 (평균 계산) |

### 호스트 머신

| 항목 | 값 |
|-----|---|
| Machine | Apple M5 Pro |
| CPU | 18 cores (arm64) |
| Memory | 48 GB |
| OS | macOS 26.4 |

### 컨테이너 리소스 제한 (docker-compose.yml)

| 서비스 | CPU | Memory |
|--------|-----|--------|
| postgres | 2 cores | 1 GB |
| Backend (각 프레임워크) | 2 cores | 2 GB |

> 모든 프레임워크에 동일한 리소스 제한을 적용하여 공정한 비교를 보장함.

### 테스트 절차

- 각 프레임워크별로 **컨테이너를 완전히 내리고 다시 시작** (clean state 보장)
- DB 쓰기 시나리오 (04, 08) 후 DB 초기화
- 시나리오 08 전에 서버 재시작 (메모리 정리)
- 프레임워크 간 실행 순서: fastapi-pragmatic → fastapi-strict → django → express → rails

---

## 결과 요약 (2026-03-27)

### typescript-express

| Scenario | RPS (avg±std) | Latency avg | Latency p95 | Latency p99 |
|----------|---------------|-------------|-------------|-------------|
| 01-lightweight | 20,491.80±55.62 | 0.475ms | 0.835ms | 1.363ms |
| 02-json-payload | 17,403.32±116.99 | 0.557ms | 0.975ms | 1.534ms |
| 03-db-read | 498.47±23.75 | 19.308ms | 26.981ms | 29.355ms |
| 04-db-write | 5,874.79±220.38 | 1.665ms | 2.556ms | 3.371ms |
| 05-external-api | 92.32±0.23 | 108.171ms | 113.683ms | 114.613ms |
| 06-middleware-chain | 18,770.77±135.22 | 0.515ms | 0.909ms | 1.480ms |
| 07-file-upload | 10,063.36±1,706.38 | 1.007ms | 1.861ms | 2.554ms |
| 08-concurrent-mixed | 244.22±110.60 | 46.996ms | 133.417ms | 155.879ms |

---

### python-fastapi-pragmatic

| Scenario | RPS (avg±std) | Latency avg | Latency p95 | Latency p99 |
|----------|---------------|-------------|-------------|-------------|
| 01-lightweight | 14,225.34±264.53 | 0.683ms | 0.794ms | 0.899ms |
| 02-json-payload | 11,789.88±158.13 | 0.812ms | 0.915ms | 1.099ms |
| 03-db-read | 146.93±3.93 | 66.072ms | 89.881ms | 217.342ms |
| 04-db-write | 1,279.56±17.35 | 7.750ms | 13.871ms | 28.201ms |
| 05-external-api | 93.94±0.30 | 106.224ms | 109.539ms | 110.404ms |
| 06-middleware-chain | 9,798.53±137.68 | 0.982ms | 1.077ms | 1.376ms |
| 07-file-upload | 6,028.80±24.77 | 1.614ms | 1.706ms | 1.849ms |
| 08-concurrent-mixed | 122.06±56.37 | 94.101ms | 235.676ms | 367.957ms |

---

### python-fastapi-strict

| Scenario | RPS (avg±std) | Latency avg | Latency p95 | Latency p99 |
|----------|---------------|-------------|-------------|-------------|
| 01-lightweight | 13,928.07±37.68 | 0.699ms | 0.800ms | 0.896ms |
| 02-json-payload | 11,634.73±29.63 | 0.823ms | 0.918ms | 1.044ms |
| 03-db-read | 170.25±3.21 | 57.416ms | 133.259ms | 179.973ms |
| 04-db-write | 1,528.02±32.13 | 6.490ms | 13.619ms | 25.657ms |
| 05-external-api | 93.36±0.51 | 106.905ms | 112.662ms | 114.330ms |
| 06-middleware-chain | 10,455.18±189.73 | 0.921ms | 1.012ms | 1.121ms |
| 07-file-upload | 6,083.49±19.53 | 1.599ms | 1.691ms | 1.831ms |
| 08-concurrent-mixed | 133.39±65.67 | 86.857ms | 220.375ms | 338.525ms |

---

### ruby-rails

| Scenario | RPS (avg±std) | Latency avg | Latency p95 | Latency p99 |
|----------|---------------|-------------|-------------|-------------|
| 01-lightweight | 3,631.68±41.83 | 2.736ms | 4.202ms | 4.851ms |
| 02-json-payload | 4,200.02±24.63 | 2.360ms | 2.708ms | 10.476ms |
| 03-db-read | 1,523.93±9.95 | 6.376ms | 10.076ms | 10.844ms |
| 04-db-write | 1,718.86±26.50 | 5.767ms | 8.240ms | 9.070ms |
| 05-external-api | 90.02±3.85 | 111.042ms | 133.879ms | 136.621ms |
| 06-middleware-chain | 3,518.97±30.79 | 2.817ms | 4.276ms | 4.961ms |
| 07-file-upload | 3,149.62±28.86 | 3.140ms | 5.904ms | 10.348ms |
| 08-concurrent-mixed | 557.44±32.10 | 17.929ms | 104.670ms | 111.427ms |

---

### python-django

| Scenario | RPS (avg±std) | Latency avg | Latency p95 | Latency p99 |
|----------|---------------|-------------|-------------|-------------|
| 01-lightweight | 2,898.50±22.88 | 0.673ms | 1.186ms | 1.497ms |
| 02-json-payload | 2,620.62±221.90 | 0.740ms | 1.551ms | 1.946ms |
| 03-db-read | 288.22±6.42 | 33.603ms | 41.768ms | 45.841ms |
| 04-db-write | 411.04±2.81 | 24.078ms | 27.911ms | 29.609ms |
| 05-external-api | 18.59±0.06 | 533.411ms | 551.311ms | 555.968ms |
| 06-middleware-chain | 2,560.42±149.38 | 0.688ms | 1.377ms | 1.752ms |
| 07-file-upload | 2,622.20±56.00 | 0.837ms | 1.555ms | 1.961ms |
| 08-concurrent-mixed | 92.76±6.78 | 107.783ms | 232.943ms | 275.905ms |

---

## 프레임워크 비교 (2026-03-27)

### 전체 RPS 비교표

| Scenario | Express | FastAPI Pragmatic | FastAPI Strict | Rails | Django |
|----------|---------|-------------------|----------------|-------|--------|
| 01-lightweight | **20,492** | 14,225 | 13,928 | 3,632 | 2,899 |
| 02-json-payload | **17,403** | 11,790 | 11,635 | 4,200 | 2,621 |
| 03-db-read | 498 | 147 | 170 | **1,524** | 288 |
| 04-db-write | **5,875** | 1,280 | 1,528 | 1,719 | 411 |
| 05-external-api | 92 | **94** | 93 | 90 | 19 |
| 06-middleware-chain | **18,771** | 9,799 | 10,455 | 3,519 | 2,560 |
| 07-file-upload | **10,063** | 6,029 | 6,084 | 3,150 | 2,622 |
| 08-concurrent-mixed | 244 | 122 | 133 | **557** | 93 |

### 시나리오별 순위

| Scenario | 1위 | 2위 | 3위 | 4위 | 5위 |
|----------|-----|-----|-----|-----|-----|
| 01-lightweight | Express (20,492) | FastAPI-P (14,225) | FastAPI-S (13,928) | Rails (3,632) | Django (2,899) |
| 02-json-payload | Express (17,403) | FastAPI-P (11,790) | FastAPI-S (11,635) | Rails (4,200) | Django (2,621) |
| 03-db-read | **Rails (1,524)** | Express (498) | Django (288) | FastAPI-S (170) | FastAPI-P (147) |
| 04-db-write | Express (5,875) | Rails (1,719) | FastAPI-S (1,528) | FastAPI-P (1,280) | Django (411) |
| 05-external-api | FastAPI-P (94) | FastAPI-S (93) | Express (92) | Rails (90) | Django (19) |
| 06-middleware-chain | Express (18,771) | FastAPI-S (10,455) | FastAPI-P (9,799) | Rails (3,519) | Django (2,560) |
| 07-file-upload | Express (10,063) | FastAPI-S (6,084) | FastAPI-P (6,029) | Rails (3,150) | Django (2,622) |
| 08-concurrent-mixed | **Rails (557)** | Express (244) | FastAPI-S (133) | FastAPI-P (122) | Django (93) |

---

### Express vs FastAPI Pragmatic 비교

| Scenario | Express RPS | FastAPI RPS | 비율 | 승자 |
|----------|-------------|-------------|------|------|
| 01-lightweight | 20,492 | 14,225 | 1.4x | **Express** |
| 02-json-payload | 17,403 | 11,790 | 1.5x | **Express** |
| 03-db-read | 498 | 147 | 3.4x | **Express** |
| 04-db-write | 5,875 | 1,280 | 4.6x | **Express** |
| 05-external-api | 92 | 94 | 1.0x | 동등 |
| 06-middleware-chain | 18,771 | 9,799 | 1.9x | **Express** |
| 07-file-upload | 10,063 | 6,029 | 1.7x | **Express** |
| 08-concurrent-mixed | 244 | 122 | 2.0x | **Express** |

**분석**: Express가 대부분의 시나리오에서 우위. 특히 DB 쓰기(4.6x)에서 Prisma의 효율성이 두드러짐. I/O 바운드(05)에서만 동등 - 외부 API 100ms 지연이 프레임워크 차이를 상쇄.

---

### FastAPI Pragmatic vs Strict 비교

| Scenario | Pragmatic RPS | Strict RPS | 비율 | 차이 |
|----------|---------------|------------|------|------|
| 01-lightweight | 14,225 | 13,928 | 0.98x | -2.1% |
| 02-json-payload | 11,790 | 11,635 | 0.99x | -1.3% |
| 03-db-read | 147 | 170 | 1.16x | **+15.9%** |
| 04-db-write | 1,280 | 1,528 | 1.19x | **+19.4%** |
| 05-external-api | 94 | 93 | 1.00x | -0.6% |
| 06-middleware-chain | 9,799 | 10,455 | 1.07x | +6.7% |
| 07-file-upload | 6,029 | 6,084 | 1.01x | +0.9% |
| 08-concurrent-mixed | 122 | 133 | 1.09x | +9.3% |

**분석**:
- **Strict(Clean Architecture)가 DB 작업에서 15-19% 빠름** - 명확한 레이어 분리로 인한 트랜잭션 경계 최적화
- **경량 API에서는 거의 동등** (1-2% 차이는 오차 범위)
- **Strict의 표준편차가 극히 낮음** (01번: 37.68 vs 264.53) → 훨씬 안정적인 성능
- **결론**: Clean Architecture는 성능 저하 없이 오히려 안정성 + DB 성능 향상 제공

---

### FastAPI vs Django 비교

| Scenario | FastAPI RPS | Django RPS | 비율 | 승자 |
|----------|-------------|------------|------|------|
| 01-lightweight | 14,225 | 2,899 | 4.9x | **FastAPI** |
| 02-json-payload | 11,790 | 2,621 | 4.5x | **FastAPI** |
| 03-db-read | 147 | 288 | 0.5x | **Django** |
| 04-db-write | 1,280 | 411 | 3.1x | **FastAPI** |
| 05-external-api | 94 | 19 | 5.0x | **FastAPI** |
| 06-middleware-chain | 9,799 | 2,560 | 3.8x | **FastAPI** |
| 07-file-upload | 6,029 | 2,622 | 2.3x | **FastAPI** |
| 08-concurrent-mixed | 122 | 93 | 1.3x | **FastAPI** |

**분석**:
- **FastAPI가 경량 API에서 4.5-4.9배 빠름** (비동기 ASGI vs 동기 WSGI)
- **Django가 DB 읽기에서 2배 빠름** - Django ORM의 SELECT 최적화 + Pydantic 검증 오버헤드 없음
- **External API에서 5배 차이** - Django는 동기 처리로 100ms sleep이 ~530ms로 증가 (Gunicorn 2 workers blocking)
- **혼합 워크로드에서 격차 축소** (1.3x) - I/O 병목이 지배적

---

### Rails 분석

| Scenario | Rails RPS | 특기사항 |
|----------|-----------|---------|
| 01-lightweight | 3,632 | Express의 18%, FastAPI의 26% |
| 02-json-payload | 4,200 | Express의 24%, FastAPI의 36% |
| 03-db-read | **1,524** | **전체 1위** - ActiveRecord의 효율적인 SELECT |
| 04-db-write | 1,719 | Express(5,875) 다음 2위, FastAPI-S(1,528)보다 12% 빠름 |
| 05-external-api | 90 | 다른 프레임워크와 동등 (I/O 바운드) |
| 06-middleware-chain | 3,519 | 경량 API와 비슷한 수준 |
| 07-file-upload | 3,150 | 중간 수준 |
| 08-concurrent-mixed | **557** | **전체 1위** - Express(244)의 2.3배, Puma의 멀티스레드 처리 |

**Rails 핵심 인사이트**:
- **DB 시나리오에서 강력한 성능**: 03-db-read에서 1위 (1,524 RPS), ActiveRecord의 효율적인 쿼리 생성
- **혼합 워크로드에서 압도적 1위**: 08번에서 557 RPS - Puma의 멀티스레드 아키텍처가 동시성 처리에 유리
- **경량 API에서는 약세**: Ruby 인터프리터 오버헤드로 인해 경량 시나리오에서 하위권
- **안정성 최상위**: 표준편차가 전반적으로 매우 낮음 (01번: 41.83, 04번: 26.50)

---

### 안정성 분석 (변동계수 CV = std/mean)

| Scenario | Express | FastAPI-P | FastAPI-S | Rails | Django |
|----------|---------|-----------|-----------|-------|--------|
| 01-lightweight | 0.3% | 1.9% | **0.3%** | 1.2% | 0.8% |
| 02-json-payload | 0.7% | 1.3% | **0.3%** | 0.6% | 8.5% |
| 03-db-read | 4.8% | 2.7% | 1.9% | **0.7%** | 2.2% |
| 04-db-write | 3.8% | 1.4% | 2.1% | 1.5% | **0.7%** |
| 05-external-api | **0.2%** | 0.3% | 0.5% | 4.3% | 0.3% |
| 06-middleware-chain | 0.7% | 1.4% | 1.8% | **0.9%** | 5.8% |
| 07-file-upload | 17.0% | **0.4%** | 0.3% | 0.9% | 2.1% |
| 08-concurrent-mixed | 45.3% | 46.2% | 49.2% | **5.8%** | 7.3% |

**안정성 결론**:
- **Rails**: 08번 혼합 워크로드에서 CV 5.8%로 가장 안정적 (다른 프레임워크는 45%+)
- **FastAPI-Strict**: 경량 시나리오에서 가장 안정적 (CV 0.3%)
- **Express**: 07번에서 CV 17%로 파일 업로드 성능 변동이 큼
- **08번은 모든 프레임워크에서 변동이 큼** (Rails 제외) - 리소스 경합의 비결정적 특성

---

## 5개 프레임워크 종합 분석 (2026-03-27)

### 프레임워크별 특성 요약

| 프레임워크 | 강점 | 약점 | 적합한 유즈케이스 |
|-----------|------|------|-----------------|
| **Express** | 경량 API 최강 (20k RPS), DB 쓰기 최강 | 혼합 워크로드 불안정 (CV 45%) | 높은 처리량이 필요한 경량 API |
| **FastAPI-Strict** | 안정적 성능 + Clean Architecture | Python 런타임 한계 | 타입 안전성과 유지보수성이 중요한 API |
| **FastAPI-Pragmatic** | 빠른 개발, 유연한 구조 | Strict보다 변동 큼 | 프로토타이핑, 빠른 MVP |
| **Rails** | DB 읽기 1위, 혼합 워크로드 1위, 최고 안정성 | 경량 API 약세 | DB 중심 + 동시성이 중요한 서비스 |
| **Django** | DB 읽기 준수, 안정적 | 외부 API 동기 처리 병목 | 동기 워크로드 중심 서비스 |

### 핵심 인사이트

1. **프레임워크 오버헤드는 경량 시나리오에서만 유의미**: Express 20k vs Django 2.9k (7배) 차이가 나지만, DB나 외부 API가 개입하면 격차가 급격히 줄어듦
2. **Rails의 DB 성능이 예상 외로 강력**: ActiveRecord + Puma 조합이 DB 읽기에서 Express(Prisma)조차 3배 이상 앞섬
3. **혼합 워크로드 = 실제 트래픽**: 08번에서 Rails가 1위 → 실제 서비스에서의 성능을 가장 잘 대변
4. **Clean Architecture는 공짜**: FastAPI Strict가 Pragmatic보다 DB 작업에서 15-19% 빠르고 안정성도 높음
5. **I/O 바운드에서 프레임워크는 무의미**: 05번에서 모든 프레임워크가 90-94 RPS (Django 제외 - 동기 처리 한계)
6. **Django의 외부 API 병목**: 동기 WSGI + Gunicorn 2 workers로 인해 외부 API 호출이 5배 느림

---

## 역대 벤치마크 기록

### 이전 측정 결과

<details>
<summary>python-fastapi-pragmatic (2025-12-07)</summary>

| Scenario | RPS (avg±std) | Latency avg | Latency p95 | Latency p99 |
|----------|---------------|-------------|-------------|-------------|
| 01-lightweight | 13,998.91±403.24 | 0.696ms | 0.922ms | 1.247ms |
| 02-json-payload | 11,610.93±354.42 | 0.831ms | 1.073ms | 1.461ms |
| 03-db-read | 157.64±2.66 | 62.064ms | 143.895ms | 193.334ms |
| 04-db-write | 1,294.57±31.29 | 7.669ms | 15.913ms | 31.493ms |
| 05-external-api | 94.12±1.9 | 106.115ms | 109.518ms | 111.197ms |
| 06-middleware-chain | 10,249.65±261.54 | 0.933ms | 1.126ms | 1.456ms |
| 07-file-upload | 6,343.78±170.55 | 1.52ms | 1.771ms | 2.179ms |
| 08-concurrent-mixed | 130.67±55.29 | 86.059ms | 222.689ms | 312.395ms |

</details>

<details>
<summary>python-fastapi-pragmatic (2026-01-03)</summary>

| Scenario | RPS (avg±std) | Latency avg | Latency p95 | Latency p99 |
|----------|---------------|-------------|-------------|-------------|
| 01-lightweight | 11,616.06±2,469.33 | 0.872ms | 1.093ms | 1.399ms |
| 02-json-payload | 9,554.85±2,151.14 | 1.06ms | 1.33ms | 1.8ms |
| 03-db-read | 146.08±12.19 | 67.318ms | 119.57ms | 212.951ms |
| 04-db-write | 1,090.7±210.36 | 9.439ms | 17.892ms | 34.338ms |
| 05-external-api | 92.26±2.92 | 108.328ms | 111.978ms | 113.96ms |
| 06-middleware-chain | 8,696.61±1,604.06 | 1.144ms | 1.315ms | 1.6ms |
| 07-file-upload | 5,313.17±1,436.22 | 3.39ms | 1.975ms | 2.336ms |
| 08-concurrent-mixed | 124.79±52.63 | 90.799ms | 229.996ms | 342.918ms |

</details>

<details>
<summary>python-fastapi-strict (2026-01-04)</summary>

| Scenario | RPS (avg±std) | Latency avg | Latency p95 | Latency p99 |
|----------|---------------|-------------|-------------|-------------|
| 01-lightweight | 11,982.88±367.1 | 0.804ms | 1.029ms | 1.526ms |
| 02-json-payload | 9,922.09±120.66 | 0.961ms | 1.169ms | 1.777ms |
| 03-db-read | 153.32±2.95 | 63.76ms | 148.034ms | 197.865ms |
| 04-db-write | 1,304.75±126.97 | 7.673ms | 17.687ms | 36.413ms |
| 05-external-api | 92.57±0.66 | 107.799ms | 112.206ms | 113.917ms |
| 06-middleware-chain | 9,204.77±99.65 | 1.042ms | 1.23ms | 1.708ms |
| 07-file-upload | 5,623.38±231.94 | 1.723ms | 1.966ms | 2.496ms |
| 08-concurrent-mixed | 122.93±54.51 | 93.152ms | 235.615ms | 345.383ms |

</details>

<details>
<summary>python-django (2026-01-04)</summary>

| Scenario | RPS (avg±std) | Latency avg | Latency p95 | Latency p99 |
|----------|---------------|-------------|-------------|-------------|
| 01-lightweight | 1,655.21±120.32 | 1.59ms | 2.408ms | 4.1ms |
| 02-json-payload | 1,651.64±82.17 | 1.628ms | 2.464ms | 4.072ms |
| 03-db-read | 252.15±4.94 | 38.398ms | 47.026ms | 52.34ms |
| 04-db-write | 373.04±23.1 | 26.657ms | 32.593ms | 37.955ms |
| 05-external-api | 18.75±0.22 | 528.995ms | 542.067ms | 545.536ms |
| 06-middleware-chain | 1,339.08±148.49 | 1.684ms | 2.579ms | 4.465ms |
| 07-file-upload | 1,417.32±103.13 | 1.942ms | 2.904ms | 4.787ms |
| 08-concurrent-mixed | 92.14±6.57 | 108.523ms | 231.464ms | 277.532ms |

</details>

<details>
<summary>typescript-express (2026-01-03)</summary>

| Scenario | RPS (avg±std) | Latency avg | Latency p95 | Latency p99 |
|----------|---------------|-------------|-------------|-------------|
| 01-lightweight | 17,004.83±1,597.67 | 0.579ms | 1.106ms | 1.675ms |
| 02-json-payload | 14,111.61±1,250.65 | 0.695ms | 1.276ms | 1.937ms |
| 03-db-read | 413.09±4.87 | 23.111ms | 31.582ms | 36.028ms |
| 04-db-write | 5,022.18±163.67 | 1.937ms | 3.018ms | 4.38ms |
| 05-external-api | 92.53±0.83 | 107.938ms | 112.007ms | 112.89ms |
| 06-middleware-chain | 14,309.25±4,777.37 | 1.312ms | 1.191ms | 1.815ms |
| 07-file-upload | 9,436.3±906.3 | 1.049ms | 2.074ms | 2.941ms |
| 08-concurrent-mixed | 551.02±177.79 | 32.257ms | 101.688ms | 106.183ms |

</details>

### 2026-03-27 vs 이전 측정 비교 (주요 변화)

| 프레임워크 | 시나리오 | 이전 RPS | 현재 RPS | 변화 | 비고 |
|-----------|---------|----------|---------|------|------|
| Express | 01-lightweight | 17,005 | 20,492 | **+20%** | 호스트 머신 영향 |
| Express | 06-middleware | 14,309 | 18,771 | **+31%** | |
| FastAPI-P | 01-lightweight | 11,616 | 14,225 | **+22%** | 표준편차 대폭 감소 (2,469→265) |
| FastAPI-S | 01-lightweight | 11,983 | 13,928 | **+16%** | |
| Django | 01-lightweight | 1,655 | 2,899 | **+75%** | 가장 큰 개선 |
| Django | 06-middleware | 1,339 | 2,560 | **+91%** | |

> 전반적으로 이전 측정 대비 성능이 향상됨. 호스트 머신(Apple M5 Pro) 및 Docker 환경 변화 영향으로 추정.
> 이전 호스트 머신 스펙이 기록되어 있지 않아 정확한 비교는 불가.

---

## 서버 구성 벤치마크: Uvicorn vs Gunicorn (2026-03-02)

동일한 FastAPI 앱을 Uvicorn 단독 / Gunicorn+Uvicorn 2워커 / 4워커로 실행하여 워크로드 유형(I/O vs CPU)과 CPU 자원(0.25~2 vCPU)에 따른 성능 차이를 측정. 5 Round × 35조합 × 3회 = **105 runs**.

**실험 본질**: "단일 이벤트 루프 vs 다중 이벤트 루프(멀티프로세스)" 비교.
Gunicorn + UvicornWorker 조합은 진정한 WSGI가 아니다 — 각 워커가 여전히 ASGI(비동기)로 동작한다.

### 가설 검증 결과

| 가설 | 내용 | 결과 | 핵심 데이터 |
|------|------|------|------------|
| H1 | I/O-bound에서 비동기 단일 프로세스 우세 | **기각** | gunicorn-4w가 3~6% 우세, P99에서 13% 격차 |
| H2 | CPU-bound에서 멀티프로세스 우세 | **채택** | gunicorn-2w가 **1.86배** (GIL 우회) |
| H3 | 저사양에서 멀티프로세스 역효과 | **조건부 채택** | I/O → 역효과 없음, CPU → **98% 성능 하락** |

### Round 1: I/O-bound (1 vCPU)

워크로드: `/io/sleep` (`await asyncio.sleep(0.1)`)

| VU | uvicorn RPS | gunicorn-4w RPS | 차이 | P99 격차 |
|----|-------------|-----------------|------|----------|
| 10 | 93.11 | 95.01 | +2% | 미미 |
| 50 | 446.84 | 467.81 | +5% | 126ms vs 116ms |
| 100 | 879.14 | 926.19 | +5% | 140ms vs 119ms |
| 200 | 1742.7 | 1851.64 | +6% | **145ms vs 126ms** |

**H1 기각 이유**: 멀티워커가 코루틴 스케줄링 부하를 분산. VU=200에서 단일 이벤트 루프의 200개 코루틴 스케줄링 오버헤드가 P99에서 드러남.

### Round 2: CPU-bound (2 vCPU)

워크로드: `/cpu/fibonacci?n=32` (재귀 피보나치, 이벤트 루프 블로킹)

| VU | uvicorn RPS | gunicorn-2w RPS | 배율 | uvicorn P99 |
|----|-------------|-----------------|------|-------------|
| 10 | 8.53 | **15.89** | 1.86x | 1,190ms |
| 50 | 8.61 | **15.13** | 1.76x | **59,291ms** |
| 100 | 9.31 | **14.87** | 1.60x | **60,000ms** (타임아웃) |

**핵심**: Uvicorn 단독에서 VU를 10배 올려도 RPS가 거의 불변(8.53→9.31). 이벤트 루프 블로킹으로 사실상 직렬 처리. VU=100에서 P99=60초(=테스트 전체 시간) → 서비스 장애 수준.

### Round 3: I/O-bound 저사양 (0.25 vCPU)

| Config | VU=10 RPS (±std) | VU=50 RPS (±std) |
|--------|------------------|------------------|
| uvicorn | 93.07±0.16 | 442.17±2.77 |
| gunicorn-2w | 94.09±0.34 | 460.86±4.3 |
| gunicorn-4w | 95.6±0.6 | 463.66±1.18 |

**발견**: 0.25 vCPU에서 3가지 서버 구성 모두 안정적. I/O 대기 시간이 지배적이라 CPU 경합이 미미.

**핵심 비교**: uvicorn@1vCPU(447 RPS) ≈ uvicorn@0.25vCPU(442 RPS). I/O-bound에서는 CPU 0.25로도 충분.

### Round 4: CPU-bound 저사양 (0.25 vCPU)

| Config | VU=10 RPS | P99 |
|--------|-----------|-----|
| uvicorn | **0.92** | 27,727ms |
| gunicorn-4w | 0.27 | **60,001ms** (타임아웃) |

**Uvicorn이 3.4배 우세**. gunicorn-4w는 0.25 vCPU를 4개 워커가 나눠 씀(워커당 0.0625 vCPU) → 60초에 16개 요청만 처리.

**붕괴 비율**: gunicorn-4w 2vCPU(15.24 RPS) → 0.25vCPU(0.27 RPS) = **1/56로 감소** (비례 이상의 붕괴).

### Round 5: Mixed (1+2 vCPU)

워크로드: `/mixed/report` (DB 조회 → 집계/가공)

| CPU | uvicorn | gunicorn-2w | gunicorn-4w | Winner |
|-----|---------|-------------|-------------|--------|
| 1 vCPU | **203.7** | 191.25 | 100.48 | uvicorn |
| 2 vCPU | 205.12 | **351.82** | 297.39 | gunicorn-2w |

**1 vCPU**: Uvicorn 단독 최고. 멀티워커의 컨텍스트 스위칭이 CPU 가공 단계에서 역효과.
**2 vCPU**: Gunicorn-2w가 **1.7배** (워커 수 = vCPU 수 최적 재확인). Uvicorn은 CPU를 늘려도 성능 동일(204→205).

### 배포 가이드

| 워크로드 유형 | 1 vCPU 이하 | 2+ vCPU |
|--------------|-------------|---------|
| **I/O-bound** (API 호출, DB 쿼리) | Uvicorn 단독 | Gunicorn + N워커 (약간 이득) |
| **CPU-bound** (연산, 해싱) | Uvicorn 단독 | **Gunicorn + N워커 필수** (N = vCPU 수) |
| **Mixed** (현실적 서비스) | Uvicorn 단독 | **Gunicorn + N워커 필수** (N = vCPU 수) |

#### Fargate 배포 권장 구성

| Fargate 스펙 | 권장 구성 | 이유 |
|-------------|-----------|------|
| 0.25 vCPU | Uvicorn 단독 | 멀티워커 오버헤드가 성능을 잡아먹음 |
| 0.5 vCPU | Uvicorn 단독 | 동일 |
| 1 vCPU | Uvicorn 단독 또는 Gunicorn 1워커 | Mixed에서 Uvicorn이 근소 우세 |
| 2 vCPU | Gunicorn + 2워커 | CPU-bound/Mixed에서 확실한 이득 |
| 4 vCPU | Gunicorn + 4워커 | 병렬 처리 극대화 |

### 교훈

1. **워커 수 ≤ vCPU 수**: vCPU보다 워커가 많으면 CPU-bound에서 서비스 장애 수준의 성능 하락 (I/O-bound에서는 영향 미미)
2. **"ASGI = 항상 빠르다"는 거짓**: CPU-bound 작업이 이벤트 루프를 블로킹하면 VU 수와 무관하게 직렬 처리
3. **I/O-bound에서 CPU는 거의 무관**: 0.25 vCPU와 1 vCPU의 I/O 처리량이 거의 동일
4. **저사양 + CPU-bound + 멀티프로세스 = 최악의 조합**: 98% 성능 하락
5. **단일 프로세스로는 추가 CPU를 활용할 수 없다**: Uvicorn@1vCPU ≈ Uvicorn@2vCPU (Mixed Round 5)

---

## 캐싱 시나리오 결과 (2026-01-17)

캐시 도입 전/후 성능 비교. FastAPI Pragmatic + PostgreSQL + Redis 환경.

### 전체 결과

| 시나리오 | RPS | avg | p(95) | p(99) | vs 14번 |
|----------|-----|-----|-------|-------|---------|
| **14-no-cache** | 1,238 | 8.00ms | 23.27ms | 55.62ms | 기준선 |
| **15-with-cache** | 5,532 | 1.74ms | 2.26ms | 4.55ms | **10.3배 빠름** |
| **16-a-pure-hit** | 5,605 | 1.72ms | 2.24ms | 3.23ms | **10.4배 빠름** |
| **16-b-pure-miss** | 534 | 9.30ms | 31.06ms | 47.70ms | **1.3배 느림** |

### 핵심 비교

| 비교 | p(95) 차이 | 의미 |
|------|------------|------|
| 16-a vs 14 | 10.4배 빠름 | 캐시 히트 효과 (최대 이득) |
| 16-b vs 14 | 1.3배 느림 | 캐시 미스 오버헤드 (16%) |
| 16-a vs 16-b | 13.9배 차이 | 히트 vs 미스 순수 차이 |

### 인사이트

- 캐시 히트 시 **10배 이상** 빠른 응답
- 캐시 미스 시 **16% 오버헤드** 발생 (Redis 확인 + 저장)
- 히트율이 성능을 결정하는 핵심 요소

---

## 인증 시나리오 결과 (2026-01-17)

인증 방식별 오버헤드 비교. FastAPI Pragmatic + PostgreSQL + Redis 환경.

### 전체 결과

| 시나리오 | Median | P95 | Throughput | vs No Auth |
|----------|--------|-----|------------|------------|
| **17-a: No Auth** | 0.92ms | 1.48ms | 9,532 req/s | 기준선 |
| **17-b: JWT** | 4.98ms | 22.35ms | 1,283 req/s | **7.4배 느림** |
| **17-c: Session** | 4.75ms | 17.39ms | 1,464 req/s | **6.5배 느림** |

### JWT vs Session 비교

| 메트릭 | JWT | Session | 승자 |
|--------|-----|---------|------|
| Median | 4.98ms | 4.75ms | **Session** (+4.8%) |
| P95 | 22.35ms | 17.39ms | **Session** (+28.5%) |
| Throughput | 1,283 req/s | 1,464 req/s | **Session** (+14.1%) |

### 인사이트

- **Session이 JWT보다 14% 빠름** (예상과 반대)
- JWT 서명 검증(CPU 바운드)이 Redis 조회(I/O 바운드)보다 Python에서 비효율적
- 인증 추가 시 처리량 **6.5~7.4배 감소**
- 보안 요구사항에 따라 선택, 성능은 Session이 우위

---

## 집계 쿼리 시나리오 결과 (2026-02-07)

ORM vs Raw SQL 집계 쿼리 성능 비교. FastAPI Pragmatic + PostgreSQL 환경. `users_wide` 테이블에 인덱스 추가 후 측정.

### 전체 결과

| 시나리오 | p(95) | Threshold | 결과 |
|---------|-------|-----------|------|
| **A. Count ORM** (쿼리 3개 분리) | 199.86ms | <300ms | PASS |
| **B. Count Raw** (쿼리 1개 합침) | 289.58ms | <350ms | PASS |
| **C. Country Stats ORM** | 204.32ms | <250ms | PASS |
| **D. Country Stats Raw** | 209.61ms | <250ms | PASS |
| **E. Author Stats ORM** (JOIN) | 117.24ms | <150ms | PASS |
| **F. Author Stats Raw** (JOIN) | 109.73ms | <150ms | PASS |

### ORM vs Raw SQL 비교

| 쿼리 유형 | ORM p(95) | Raw p(95) | 차이 | 승자 |
|----------|-----------|-----------|------|------|
| Count | 199.86ms | 289.58ms | **ORM 1.4배 빠름** | **ORM** |
| Country Stats | 204.32ms | 209.61ms | 거의 동등 (-2.5%) | 동등 |
| Author Stats | 117.24ms | 109.73ms | Raw 6.8% 빠름 | Raw (미미) |

### 인사이트

- **"쿼리 1개 = 더 빠르다"는 거짓**: ORM(3개 분리)이 Raw(1개 합침)보다 1.4배 빠름
- **원인**: 합친 쿼리는 `COUNT(DISTINCT)`의 Sort 요구 때문에 Seq Scan + Disk Sort 강제. 분리 쿼리는 각각 Index Only Scan 활용
- **ORM vs Raw 차이는 미미** (1~9%): 병목은 ORM 오버헤드가 아니라 쿼리 실행 계획
- 상세 분석: `docs/23-aggregation.md`

---

## 완료된 프레임워크

- [x] python-fastapi-pragmatic (2026-03-27) ✅ 최신
- [x] python-fastapi-strict (2026-03-27) ✅ 최신
- [x] python-django (2026-03-27) ✅ 최신
- [x] typescript-express (2026-03-27) ✅ 최신
- [x] ruby-rails (2026-03-27) ✅ 최신 (최초 측정)

## 추가 예정 프레임워크

- [ ] python-flask
- [ ] typescript-fastify
- [ ] typescript-nestjs
- [ ] go-fiber
