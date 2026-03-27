#!/bin/bash
set -e

# ============================================
# Server Config Experiment Runner
# ============================================
# Usage:
#   ./run-server-config.sh round1                                          # Round 1 전체
#   ./run-server-config.sh round2                                          # Round 2 전체
#   ./run-server-config.sh --config uvicorn --cpu 1 --scenario io-sleep --vu 50  # 특정 조합
#
# Rounds:
#   round1 - I/O-bound (io-sleep), 1 vCPU, VU: 10/50/100/200
#   round2 - CPU-bound (cpu-fibonacci), 2 vCPU, VU: 10/50/100
#   round3 - I/O-bound low CPU (io-sleep), 0.25 vCPU, VU: 10/50
#   round4 - CPU-bound low CPU (cpu-fibonacci), 0.25 vCPU, VU: 10
#   round5 - Mixed (mixed-report), 1+2 vCPU, VU: 50

# ============================================
# 설정
# ============================================
RUNS=3
WARMUP_VUS=5
WARMUP_DURATION="10s"
TEST_DURATION="60s"
COOLDOWN=30
SCENARIOS_DIR="../scenarios/server-config"
COMPOSE_FILE="../implementations/docker-compose.yml"
RESULTS_BASE="../results/server-config/$(date +%Y-%m-%d)"

# 색상
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================
# 헬퍼 함수
# ============================================
log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step()  { echo -e "${BLUE}[STEP]${NC} $1"; }

usage() {
  echo "Usage:"
  echo "  $0 <round>                                    # Round 전체 실행"
  echo "  $0 --config <config> --cpu <cpu> --scenario <scenario> --vu <vu>"
  echo ""
  echo "Rounds: round1, round2, round3, round4, round5"
  echo ""
  echo "Configs: uvicorn, gunicorn-2w, gunicorn-4w"
  echo "Scenarios: io-sleep, io-db, cpu-fibonacci, cpu-hash, mixed-report"
  echo ""
  echo "Examples:"
  echo "  $0 round1"
  echo "  $0 --config uvicorn --cpu 1 --scenario io-sleep --vu 50"
  exit 1
}

# ============================================
# Docker 관련 함수
# ============================================
start_postgres() {
  log_info "Starting PostgreSQL..."
  docker compose -f "$COMPOSE_FILE" up -d postgres

  log_info "Waiting for PostgreSQL to be healthy..."
  until docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U benchmark > /dev/null 2>&1; do
    sleep 1
  done
  log_info "PostgreSQL is ready!"
}

init_db() {
  log_info "Initializing database..."
  docker compose -f "$COMPOSE_FILE" exec -T postgres \
    psql -U benchmark -d benchmark -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" > /dev/null 2>&1

  cat ../implementations/scripts/init_db.sql | \
    docker compose -f "$COMPOSE_FILE" exec -T postgres \
    psql -U benchmark -d benchmark > /dev/null 2>&1

  log_info "Database initialized!"
}

start_app() {
  local config=$1
  local cpu=$2
  local profile="server-${config}"

  log_info "Starting ${config} (CPU: ${cpu})..."
  CPU_LIMIT=$cpu docker compose -f "$COMPOSE_FILE" --profile "$profile" up -d --build

  log_info "Waiting for server to be ready..."
  local max_attempts=30
  local attempt=0
  until curl -s http://localhost:8000/health > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
      log_error "Server failed to start after $max_attempts attempts"
      CPU_LIMIT=$cpu docker compose -f "$COMPOSE_FILE" --profile "$profile" logs --tail=50
      exit 1
    fi
    sleep 1
  done

  local health=$(curl -s http://localhost:8000/health)
  log_info "Server ready: $health"
}

stop_app() {
  local config=$1
  local cpu=$2
  local profile="server-${config}"

  log_info "Stopping ${config}..."
  CPU_LIMIT=$cpu docker compose -f "$COMPOSE_FILE" --profile "$profile" down --remove-orphans 2>/dev/null
}

# ============================================
# 벤치마크 함수
# ============================================
run_warmup() {
  local scenario=$1

  log_info "Warming up (${WARMUP_VUS} VUs, ${WARMUP_DURATION})..."
  k6 run --quiet \
    --env VUS=$WARMUP_VUS \
    --env DURATION=$WARMUP_DURATION \
    "${SCENARIOS_DIR}/${scenario}.js" > /dev/null 2>&1
  log_info "Warmup complete!"
}

run_benchmark() {
  local config=$1
  local cpu=$2
  local scenario=$3
  local vu=$4
  local round_dir=$5

  local results_dir="${RESULTS_BASE}/${round_dir}"
  mkdir -p "$results_dir"

  echo ""
  log_step "=== ${config} | CPU:${cpu} | ${scenario} | VU:${vu} ==="

  for i in $(seq 1 $RUNS); do
    local outfile="${results_dir}/${config}-cpu${cpu}-${scenario}-vu${vu}-run${i}.json"
    echo "  Run ${i}/${RUNS}..."
    k6 run --quiet \
      --env VUS=$vu \
      --env DURATION=$TEST_DURATION \
      --summary-export="$outfile" \
      "${SCENARIOS_DIR}/${scenario}.js"
    sleep 5
  done
}

# 하나의 서버 구성으로 여러 VU 레벨 실행
run_config() {
  local config=$1
  local cpu=$2
  local scenario=$3
  local round_dir=$4
  shift 4
  local vus=("$@")

  start_app "$config" "$cpu"
  run_warmup "$scenario"

  for vu in "${vus[@]}"; do
    run_benchmark "$config" "$cpu" "$scenario" "$vu" "$round_dir"
  done

  stop_app "$config" "$cpu"

  log_info "Cooling down (${COOLDOWN}s)..."
  sleep $COOLDOWN
}

# ============================================
# 라운드 정의
# ============================================
run_round1() {
  log_step "========== Round 1: I/O-bound (1 vCPU) =========="
  local configs=("uvicorn" "gunicorn-2w" "gunicorn-4w")
  local vus=(10 50 100 200)

  for config in "${configs[@]}"; do
    run_config "$config" 1 "io-sleep" "round1" "${vus[@]}"
  done
}

run_round2() {
  log_step "========== Round 2: CPU-bound (2 vCPU) =========="
  local configs=("uvicorn" "gunicorn-2w" "gunicorn-4w")
  local vus=(10 50 100)

  for config in "${configs[@]}"; do
    run_config "$config" 2 "cpu-fibonacci" "round2" "${vus[@]}"
  done
}

run_round3() {
  log_step "========== Round 3: I/O-bound low CPU (0.25 vCPU) =========="
  local configs=("uvicorn" "gunicorn-2w" "gunicorn-4w")
  local vus=(10 50)

  for config in "${configs[@]}"; do
    run_config "$config" 0.25 "io-sleep" "round3" "${vus[@]}"
  done
}

run_round4() {
  log_step "========== Round 4: CPU-bound low CPU (0.25 vCPU) =========="
  local configs=("uvicorn" "gunicorn-4w")
  local vus=(10)

  for config in "${configs[@]}"; do
    run_config "$config" 0.25 "cpu-fibonacci" "round4" "${vus[@]}"
  done
}

run_round5() {
  log_step "========== Round 5: Mixed (1+2 vCPU) =========="
  local configs=("uvicorn" "gunicorn-2w" "gunicorn-4w")
  local vus=(50)

  for config in "${configs[@]}"; do
    run_config "$config" 1 "mixed-report" "round5" "${vus[@]}"
  done
  for config in "${configs[@]}"; do
    run_config "$config" 2 "mixed-report" "round5" "${vus[@]}"
  done
}

# ============================================
# 메인 실행
# ============================================
if [ $# -lt 1 ]; then
  usage
fi

echo ""
echo "============================================"
echo "  Server Config Experiment Runner"
echo "============================================"

# PostgreSQL 시작 (공통)
start_postgres
init_db

if [[ "$1" == round* ]]; then
  ROUND=$1
  echo "  Round:   $ROUND"
  echo "  Results: $RESULTS_BASE/$ROUND"
  echo "============================================"
  echo ""

  case $ROUND in
    round1) run_round1 ;;
    round2) run_round2 ;;
    round3) run_round3 ;;
    round4) run_round4 ;;
    round5) run_round5 ;;
    *) log_error "Unknown round: $ROUND"; usage ;;
  esac
else
  # 개별 조합 모드
  CONFIG=""
  CPU=""
  SCENARIO=""
  VU=""

  while [[ $# -gt 0 ]]; do
    case $1 in
      --config)   CONFIG=$2; shift 2 ;;
      --cpu)      CPU=$2; shift 2 ;;
      --scenario) SCENARIO=$2; shift 2 ;;
      --vu)       VU=$2; shift 2 ;;
      *) log_error "Unknown option: $1"; usage ;;
    esac
  done

  if [[ -z "$CONFIG" || -z "$CPU" || -z "$SCENARIO" || -z "$VU" ]]; then
    log_error "All options required: --config, --cpu, --scenario, --vu"
    usage
  fi

  echo "  Config:   $CONFIG"
  echo "  CPU:      $CPU"
  echo "  Scenario: $SCENARIO"
  echo "  VU:       $VU"
  echo "  Results:  $RESULTS_BASE/manual"
  echo "============================================"
  echo ""

  run_config "$CONFIG" "$CPU" "$SCENARIO" "manual" "$VU"
fi

echo ""
log_info "============================================"
log_info "  Experiment completed!"
log_info "  Results: $RESULTS_BASE"
log_info "============================================"
