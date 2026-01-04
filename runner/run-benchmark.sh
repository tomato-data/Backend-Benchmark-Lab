#!/bin/bash
set -e

# ============================================
# Backend Benchmark Runner
# ============================================
# Usage: ./run-benchmark.sh <framework> [scenario]
#
# Examples:
#   ./run-benchmark.sh python-django           # Django 전체 (01~08)
#   ./run-benchmark.sh python-django 03        # Django 03번만
#   ./run-benchmark.sh typescript-express 03+  # Express 03번부터 끝까지
#
# Frameworks:
#   python-django, python-fastapi-pragmatic, python-fastapi-strict, typescript-express

# 설정
RUNS=10
SLEEP_BETWEEN=5
SCENARIOS_DIR="../scenarios/basic"
COMPOSE_FILE="../implementations/docker-compose.yml"

# 색상
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================
# 헬퍼 함수
# ============================================

log_info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Framework 이름 → Docker Compose profile 매핑
get_profile() {
  case $1 in
    python-django) echo "django" ;;
    python-fastapi-pragmatic) echo "fastapi-pragmatic" ;;
    python-fastapi-strict) echo "fastapi-strict" ;;
    typescript-express) echo "express" ;;
    *) echo "" ;;
  esac
}

# 사용법 출력
usage() {
  echo "Usage: $0 <framework> [scenario]"
  echo ""
  echo "Frameworks:"
  echo "  python-django"
  echo "  python-fastapi-pragmatic"
  echo "  python-fastapi-strict"
  echo "  typescript-express"
  echo ""
  echo "Scenario:"
  echo "  03    - Run only scenario 03"
  echo "  03+   - Run from scenario 03 to end"
  echo "  (none) - Run all scenarios (01+)"
  echo ""
  echo "Examples:"
  echo "  $0 python-django"
  echo "  $0 typescript-express 03"
  echo "  $0 python-fastapi-pragmatic 05+"
  exit 1
}

# ============================================
# Docker 관련 함수
# ============================================

# Postgres 시작 및 health check
start_postgres() {
  log_info "Starting PostgreSQL..."
  docker compose -f "$COMPOSE_FILE" up -d postgres

  log_info "Waiting for PostgreSQL to be healthy..."
  until docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U benchmark > /dev/null 2>&1; do
    sleep 1
  done
  log_info "PostgreSQL is ready!"
}

# DB 초기화 (DROP + CREATE + seed)
init_db() {
  log_info "Initializing database (full reset)..."
  docker compose -f "$COMPOSE_FILE" exec -T postgres \
    psql -U benchmark -d benchmark -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" > /dev/null 2>&1

  cat ../implementations/scripts/init_db.sql | \
    docker compose -f "$COMPOSE_FILE" exec -T postgres \
    psql -U benchmark -d benchmark > /dev/null 2>&1

  log_info "Database initialized!"
}

# Framework 컨테이너 시작
start_framework() {
  local profile=$1
  log_info "Building and starting $FRAMEWORK..."
  docker compose -f "$COMPOSE_FILE" --profile "$profile" up -d --build

  log_info "Waiting for server to be ready..."
  local max_attempts=30
  local attempt=0
  until curl -s http://localhost:8000/health > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
      log_error "Server failed to start after $max_attempts attempts"
      docker compose -f "$COMPOSE_FILE" --profile "$profile" logs --tail=50
      exit 1
    fi
    sleep 1
  done

  SERVER_NAME=$(curl -s http://localhost:8000/health | jq -r '.server')
  log_info "Server is ready: $SERVER_NAME"
}

# Framework 컨테이너 종료
stop_framework() {
  local profile=$1
  log_info "Stopping $FRAMEWORK..."
  docker compose -f "$COMPOSE_FILE" --profile "$profile" down
}

# 서버 재시작 (메모리 정리용)
restart_server() {
  local profile=$1
  log_info "Restarting server container to clear memory..."
  docker compose -f "$COMPOSE_FILE" --profile "$profile" restart "$FRAMEWORK"
  sleep 3

  until curl -s http://localhost:8000/health > /dev/null 2>&1; do
    sleep 1
  done
  log_info "Server restarted!"
}

# ============================================
# 벤치마크 함수
# ============================================

run_scenario() {
  local scenario=$1
  local name=$(basename "$scenario" .js)

  echo ""
  log_info "=== Running $name on $SERVER_NAME ==="

  for i in $(seq 1 $RUNS); do
    echo "  Run $i/$RUNS..."
    k6 run --quiet --summary-export="$RESULTS_DIR/${name}-run${i}.json" "$scenario"
    sleep $SLEEP_BETWEEN
  done

  # DB 쓰기 시나리오 후 리셋
  if [[ "$name" == "04-db-write" || "$name" == "08-concurrent-mixed" ]]; then
    init_db
  fi
}

# ============================================
# 메인 실행
# ============================================

# 인자 검증
if [ $# -lt 1 ]; then
  usage
fi

FRAMEWORK=$1
PROFILE=$(get_profile "$FRAMEWORK")

if [ -z "$PROFILE" ]; then
  log_error "Unknown framework: $FRAMEWORK"
  usage
fi

# 시나리오 인자 파싱
ARG=${2:-01+}
if [[ "$ARG" == *"+" ]]; then
  START_FROM=${ARG%+}
  SINGLE_ONLY=false
else
  START_FROM=$ARG
  SINGLE_ONLY=true
fi

# 결과 디렉토리 설정
RESULTS_DIR="../results/${FRAMEWORK}/$(date +%Y-%m-%d)"
mkdir -p "$RESULTS_DIR"

echo ""
echo "============================================"
echo "  Backend Benchmark Runner"
echo "============================================"
echo "  Framework: $FRAMEWORK"
echo "  Profile:   $PROFILE"
echo "  Mode:      $(if $SINGLE_ONLY; then echo "Single ($START_FROM only)"; else echo "Range ($START_FROM to end)"; fi)"
echo "  Results:   $RESULTS_DIR"
echo "============================================"
echo ""

# 1. Postgres 시작
start_postgres

# 2. DB 초기화
init_db

# 3. Framework 시작
start_framework "$PROFILE"

# 4. 벤치마크 실행
for scenario in "$SCENARIOS_DIR"/0*.js; do
  name=$(basename "$scenario" .js)
  scenario_num=${name:0:2}

  if [[ "$scenario_num" < "$START_FROM" ]]; then
    log_warn "Skipping $name..."
    continue
  fi

  # SINGLE_ONLY 모드에서 해당 번호 이후는 스킵
  if $SINGLE_ONLY && [[ "$scenario_num" > "$START_FROM" ]]; then
    log_warn "Skipping $name (single mode)..."
    continue
  fi

  # 08번 전에 서버 재시작 (메모리 정리)
  if [[ "$name" == "08-concurrent-mixed" ]]; then
    restart_server "$PROFILE"
  fi

  run_scenario "$scenario"
done

# 5. 완료
echo ""
log_info "============================================"
log_info "  All benchmarks completed for $FRAMEWORK"
log_info "  Results saved to: $RESULTS_DIR"
log_info "============================================"

# 6. 종료 여부 확인 (선택적)
read -p "Stop containers? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
  stop_framework "$PROFILE"
  log_info "Containers stopped."
else
  log_info "Containers still running. Stop manually with:"
  echo "  docker compose -f $COMPOSE_FILE --profile $PROFILE down"
fi
