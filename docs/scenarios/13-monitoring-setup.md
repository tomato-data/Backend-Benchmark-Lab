# Monitoring 구현

## 개요

벤치마크 시 컨테이너 리소스(CPU, Memory) 및 애플리케이션 레벨 메트릭을 수집하여 프레임워크별 비교 분석을 가능하게 한다.

### 목표

1. **벤치마크 후 분석** (Primary): 테스트 완료 후 리소스 사용량 비교
2. **실시간 대시보드** (Secondary): 벤치마크 진행 중 모니터링

---

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                         Docker Host                              │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │  FastAPI  │  │  Django   │  │  Express  │  │  ...      │    │
│  │  :8000    │  │  :8000    │  │  :8000    │  │           │    │
│  │  /metrics │  │  /metrics │  │  /metrics │  │           │    │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └───────────┘    │
│        │              │              │                          │
│        └──────────────┼──────────────┘                          │
│                       │ (app metrics)                           │
│                       ▼                                         │
│  ┌───────────────────────────────────────┐                     │
│  │             Prometheus                 │◄─── 메트릭 저장소   │
│  │             :9090                      │                     │
│  └───────────────────┬───────────────────┘                     │
│                      │                                          │
│        ┌─────────────┴─────────────┐                           │
│        │                           │                            │
│        ▼                           ▼                            │
│  ┌───────────┐              ┌───────────┐                      │
│  │  cAdvisor │              │  Grafana  │◄─── 시각화           │
│  │  :8080    │              │  :3000    │                      │
│  └───────────┘              └───────────┘                      │
│  (container metrics)                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 컴포넌트 설명

### 1. Prometheus

**역할**: 메트릭 수집 및 시계열 저장소

- Pull 기반: 주기적으로 타겟에서 메트릭을 가져옴
- PromQL: 강력한 쿼리 언어 제공
- 15초 기본 scrape interval

**수집 대상**:
- cAdvisor (컨테이너 메트릭)
- 각 애플리케이션의 `/metrics` 엔드포인트

### 2. cAdvisor (Container Advisor)

**역할**: Docker 컨테이너 리소스 메트릭 노출

**제공 메트릭**:
| 메트릭 | 설명 |
|--------|------|
| `container_cpu_usage_seconds_total` | 컨테이너 CPU 사용량 (누적) |
| `container_memory_usage_bytes` | 컨테이너 메모리 사용량 |
| `container_memory_working_set_bytes` | 실제 사용 중인 메모리 (캐시 제외) |
| `container_network_receive_bytes_total` | 네트워크 수신 바이트 |
| `container_network_transmit_bytes_total` | 네트워크 송신 바이트 |
| `container_fs_reads_bytes_total` | 디스크 읽기 |
| `container_fs_writes_bytes_total` | 디스크 쓰기 |

**특징**:
- Docker 소켓 마운트 필요 (`/var/run/docker.sock`)
- 오버헤드가 낮음 (자체 리소스 사용 최소)

### 3. Grafana

**역할**: 메트릭 시각화 대시보드

**기능**:
- Prometheus 데이터소스 연동
- 대시보드 JSON으로 버전 관리 가능
- 변수(Variables)로 프레임워크 선택 가능

---

## 메트릭 계층

### Layer 1: 컨테이너 메트릭 (cAdvisor)

인프라 레벨 - 모든 프레임워크에 코드 변경 없이 적용

```promql
# CPU 사용률 (%)
rate(container_cpu_usage_seconds_total{name=~".*fastapi.*|.*django.*"}[1m]) * 100

# 메모리 사용량 (MB)
container_memory_working_set_bytes{name=~".*fastapi.*|.*django.*"} / 1024 / 1024
```

### Layer 2: 애플리케이션 메트릭 (각 프레임워크에 추가)

더 상세한 분석을 위해 각 프레임워크에 Prometheus 클라이언트 추가

**공통 메트릭** (모든 프레임워크에 동일하게):

| 메트릭 이름 | 타입 | 설명 |
|-------------|------|------|
| `http_requests_total` | Counter | 총 요청 수 (method, endpoint, status) |
| `http_request_duration_seconds` | Histogram | 요청 처리 시간 분포 |
| `http_requests_in_progress` | Gauge | 현재 처리 중인 요청 수 |

**Python (FastAPI/Django) 예시**:
```python
# prometheus-client 라이브러리 사용
from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)
```

**TypeScript (Express/Fastify) 예시**:
```typescript
// prom-client 라이브러리 사용
import { Counter, Histogram, Registry } from 'prom-client';

const requestCounter = new Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'endpoint', 'status']
});
```

---

## 구현 단계

### Phase 1: 인프라 구성 (컨테이너 메트릭만)

코드 변경 없이 cAdvisor + Prometheus + Grafana 구성

#### Step 1.1: 디렉토리 구조 생성

```bash
mkdir -p monitoring/prometheus
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p monitoring/grafana/provisioning/dashboards
mkdir -p monitoring/grafana/dashboards
```

#### Step 1.2: Prometheus 설정

`monitoring/prometheus/prometheus.yml`:
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Prometheus 자체 메트릭
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # cAdvisor (컨테이너 메트릭)
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
```

#### Step 1.3: Grafana 데이터소스 프로비저닝

`monitoring/grafana/provisioning/datasources/prometheus.yml`:
```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
```

#### Step 1.4: docker-compose 확장

`monitoring/docker-compose.yml`:
```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=7d'
    networks:
      - monitoring

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    ports:
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge

volumes:
  prometheus_data:
  grafana_data:
```

#### Step 1.5: 실행 및 확인

```bash
cd monitoring
docker compose up -d

# 확인
# Prometheus: http://localhost:9090
# cAdvisor: http://localhost:8080
# Grafana: http://localhost:3000 (admin/admin)
```

---

### Phase 2: Grafana 대시보드 생성

#### Step 2.1: 컨테이너 비교 대시보드

주요 패널:
1. **CPU Usage by Container** (Time series)
2. **Memory Usage by Container** (Time series)
3. **Network I/O** (Time series)
4. **Container Summary Table**

PromQL 예시:
```promql
# CPU 사용률 (컨테이너별)
sum(rate(container_cpu_usage_seconds_total{name=~".*(fastapi|django|express).*"}[1m])) by (name) * 100

# 메모리 사용량 (컨테이너별, MB)
sum(container_memory_working_set_bytes{name=~".*(fastapi|django|express).*"}) by (name) / 1024 / 1024
```

#### Step 2.2: 대시보드 JSON 저장

Grafana에서 대시보드 생성 후 JSON 익스포트 → `monitoring/grafana/dashboards/` 에 저장

---

### Phase 3: 애플리케이션 메트릭 추가 (선택)

각 프레임워크에 `/metrics` 엔드포인트 추가

#### Python (FastAPI)

```bash
cd implementations/python-fastapi
uv add prometheus-client
```

미들웨어로 메트릭 수집 + `/metrics` 엔드포인트 노출

#### Python (Django)

```bash
cd implementations/python-django
uv add django-prometheus
```

`django-prometheus`는 Django에 맞게 최적화된 메트릭 제공

#### TypeScript (Express/Fastify/NestJS)

```bash
npm install prom-client
```

---

## 벤치마크 워크플로우

### 통합 실행

```bash
# 1. 모니터링 스택 시작
cd monitoring
docker compose up -d

# 2. 벤치마크 대상 프레임워크 시작
cd ../implementations
docker compose --profile fastapi-pragmatic up -d

# 3. k6 벤치마크 실행
cd ../runner
./run-benchmark.sh

# 4. Grafana에서 결과 확인
# http://localhost:3000
```

### 네트워크 연결

모니터링 스택과 벤치마크 컨테이너가 통신하려면 같은 네트워크에 있어야 함.

방법 1: 외부 네트워크 사용
```yaml
# implementations/docker-compose.yml
networks:
  default:
    name: benchmark-network
    external: true
```

방법 2: docker-compose 파일 병합
```bash
docker compose -f implementations/docker-compose.yml -f monitoring/docker-compose.yml up
```

---

## 주의사항

### macOS에서 cAdvisor

macOS는 Linux와 cgroup 구조가 달라 일부 메트릭이 제한될 수 있음.

대안:
- Docker Desktop의 내장 메트릭 사용
- 또는 Linux VM에서 테스트

### 리소스 오버헤드

모니터링 스택 자체도 리소스를 사용함:
- Prometheus: ~100MB RAM
- cAdvisor: ~50MB RAM
- Grafana: ~100MB RAM

벤치마크 정확도를 위해 모니터링 스택에도 리소스 제한 권장.

---

## 다음 단계

- [ ] Phase 1 완료: 기본 인프라 구성
- [ ] Phase 2 완료: Grafana 대시보드 생성
- [ ] Phase 3 완료: 애플리케이션 메트릭 추가 (선택)
- [ ] 벤치마크 결과에 리소스 사용량 추가
