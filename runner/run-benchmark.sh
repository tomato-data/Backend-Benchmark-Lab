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
