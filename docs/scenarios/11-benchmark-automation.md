# Benchmark Automation

## 개요

각 시나리오를 10회 실행하고 평균을 계산하는 자동화 스크립트.

---

## 고려사항

### 1. Graceful Stop

각 실행 사이에 충분한 대기 시간 필요:

```bash
# k6 기본 gracefulStop: 30s
# 추가 안정화 시간: 5s
SLEEP_BETWEEN_RUNS=5
```

### 2. 서비스 상태 확인

벤치마크 전 서비스 health check:

```bash
until curl -s http://localhost:8000/health > /dev/null; do
  sleep 1
done
```

### 3. DB 초기화

`04-db-write`, `08-concurrent-mixed` 실행 후 DB 리셋:

```bash
cat scripts/init_db.sql | docker compose exec -T postgres psql -U benchmark -d benchmark
```

### 4. 결과 수집

k6 JSON 출력 활용:

```bash
k6 run --out json=results/01-lightweight-run1.json 01-lightweight.js
```

---

## 스크립트 구조

```
runner/
├── run-benchmark.sh    # 메인 실행 스크립트
├── parse-results.py    # 결과 파싱 및 평균 계산
└── config.sh           # 설정 (실행 횟수, 대기 시간 등)
```

---

## run-benchmark.sh

```bash
#!/bin/bash
set -e

# 설정
RUNS=10
SLEEP_BETWEEN=5
SCENARIOS_DIR="../scenarios"

# Health check 함수 + 서버 이름 추출
wait_for_server() {
  echo "Waiting for server..."
  until curl -s http://localhost:8000/health > /dev/null 2>&1; do
    sleep 1
  done

  # 서버 이름 추출 (전역 변수로 설정)
  SERVER_NAME=$(curl -s http://localhost:8000/health | jq -r '.server')
  echo "Server is ready: $SERVER_NAME"
}

# DB 리셋 함수
reset_db() {
  echo "Resetting database..."
  cat ../implementations/scripts/init_db.sql | \
    docker compose -f ../implementations/docker-compose.yml exec -T postgres \
    psql -U benchmark -d benchmark
}

# 시나리오 실행 함수
run_scenario() {
  local scenario=$1
  local name=$(basename "$scenario" .js)

  echo "=== Running $name on $SERVER_NAME ==="

  for i in $(seq 1 $RUNS); do
    echo "  Run $i/$RUNS..."
    k6 run --quiet --summary-export="$RESULTS_DIR/${name}-run${i}.json" "$scenario"
    sleep $SLEEP_BETWEEN
  done

  # DB 쓰기 시나리오 후 리셋
  if [[ "$name" == "04-db-write" || "$name" == "08-concurrent-mixed" ]]; then
    reset_db
  fi
}

# 메인 실행
wait_for_server
RESULTS_DIR="../results/${SERVER_NAME}/$(date +%Y-%m-%d)"
mkdir -p "$RESULTS_DIR"

for scenario in "$SCENARIOS_DIR"/0*.js; do
  run_scenario "$scenario"
done

echo "=== All benchmarks completed for $SERVER_NAME ==="
echo "Results saved to: $RESULTS_DIR"
```

---

## parse-results.py

```python
#!/usr/bin/env python3
"""Parse k6 summary JSON results and calculate averages."""

import json
import sys
from pathlib import Path
from statistics import mean, stdev

SCENARIOS = [
    "01-lightweight",
    "02-json-payload",
    "03-db-read",
    "04-db-write",
    "05-external-api",
    "06-middleware-chain",
    "07-file-upload",
    "08-concurrent-mixed",
]


def parse_summary_json(filepath: Path) -> dict[str, float] | None:
    """Extract key metrics from k6 --summary-export JSON."""
    try:
        with open(filepath) as f:
            data = json.load(f)

        metrics = data.get("metrics", {})

        return {
            "rps": float(metrics.get("http_reqs", {}).get("rate", 0)),
            "latency_avg": float(metrics.get("http_req_duration", {}).get("avg", 0)),
            "latency_p95": float(metrics.get("http_req_duration", {}).get("p(95)", 0)),
        }
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def extract_scenario(filename: str) -> str | None:
    """Extract scenario name from filename."""
    # 파일명: {scenario}-run{i}.json
    # 예: 01-lightweight-run1.json
    for scenario in SCENARIOS:
        if filename.startswith(f"{scenario}-run"):
            return scenario
    return None


def find_all_results(results_dir: Path) -> dict[str, dict[str, list[Path]]]:
    """Find all result files, grouped by server and scenario."""
    # 구조: results/{server}/{date}/{scenario}-run{i}.json
    results: dict[str, dict[str, list[Path]]] = {}

    for server_dir in results_dir.iterdir():
        if not server_dir.is_dir():
            continue

        server = server_dir.name
        if server not in results:
            results[server] = {}

        # 날짜 디렉토리 순회
        for date_dir in server_dir.iterdir():
            if not date_dir.is_dir():
                continue

            for f in date_dir.glob("*.json"):
                scenario = extract_scenario(f.name)
                if scenario:
                    if scenario not in results[server]:
                        results[server][scenario] = []
                    results[server][scenario].append(f)

    return results


def calculate_averages(files: list[Path]) -> dict[str, float | int] | None:
    """Calculate average metrics from a list of result files."""
    if not files:
        return None

    rps_list = []
    latency_avg_list = []
    latency_p95_list = []

    for f in files:
        if not f.exists():
            continue
        metrics = parse_summary_json(f)
        if metrics:
            rps_list.append(metrics["rps"])
            latency_avg_list.append(metrics["latency_avg"])
            latency_p95_list.append(metrics["latency_p95"])

    if not rps_list:
        return None

    return {
        "runs": len(rps_list),
        "rps_avg": round(mean(rps_list), 2),
        "rps_std": round(stdev(rps_list), 2) if len(rps_list) > 1 else 0,
        "latency_avg": round(mean(latency_avg_list), 3),
        "latency_p95": round(mean(latency_p95_list), 3),
    }


def print_markdown_table(results: dict[str, dict[str, dict[str, float | int]]]) -> None:
    """Print results as markdown table."""
    if not results:
        print("No results to display.")
        return

    print("| Server | Scenario | Runs | RPS (avg±std) | Latency avg | Latency p95 |")
    print("|--------|----------|------|---------------|-------------|-------------|")

    for server in sorted(results.keys()):
        for scenario in SCENARIOS:
            if scenario in results[server]:
                data = results[server][scenario]
                rps = f"{data['rps_avg']}±{data['rps_std']}"
                print(f"| {server} | {scenario} | {data['runs']} | {rps} | {data['latency_avg']}ms | {data['latency_p95']}ms |")


if __name__ == "__main__":
    results_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

    if not results_dir.exists():
        print(f"Directory not found: {results_dir}")
        sys.exit(1)

    # 존재하는 JSON 파일에서 서버/시나리오 자동 탐지
    all_results = find_all_results(results_dir)

    if not all_results:
        print("No result files found.")
        sys.exit(1)

    # 평균 계산
    aggregated: dict[str, dict[str, dict[str, float | int]]] = {}
    for server, scenarios in all_results.items():
        if server not in aggregated:
            aggregated[server] = {}
        for scenario, files in scenarios.items():
            data = calculate_averages(files)
            if data:
                aggregated[server][scenario] = data

    print_markdown_table(aggregated)
```

---

## 더 간단한 대안: k6 --summary-export

```bash
k6 run --summary-export=result.json scenario.js
```

JSON summary만 추출 (전체 로그보다 가벼움):

```json
{
  "metrics": {
    "http_reqs": { "count": 10000, "rate": 333.33 },
    "http_req_duration": { "avg": 1.5, "p(95)": 2.5 }
  }
}
```

---

## 실행 방법

```bash
cd runner
chmod +x run-benchmark.sh
./run-benchmark.sh
```

---

## 결과 디렉토리 구조

```
results/
├── python-fastapi-pragmatic/
│   └── 2025-12-07/
│       ├── 01-lightweight-run1.json
│       ├── 01-lightweight-run2.json
│       ├── ...
│       └── 08-concurrent-mixed-run10.json
├── python-django/
│   └── 2025-12-07/
│       └── ...
└── go-fiber/
    └── ...
```

- 1차 분류: **서버 이름**
- 2차 분류: **날짜**
- 파일명 형식: `{scenario}-run{i}.json`
