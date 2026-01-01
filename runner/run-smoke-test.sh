#!/bin/bash

# Smoke Test: 모든 엔드포인트가 정상 동작하는지 빠르게 확인
# Usage: ./run-smoke-test.sh [BASE_URL]

BASE_URL="${1:-http://localhost:8000/api/v1}"

echo "=========================================="
echo "  Smoke Test - Endpoint Health Check"
echo "  Target: $BASE_URL"
echo "=========================================="

PASS=0
FAIL=0

# 테스트 함수
test_get() {
    local name="$1"
    local endpoint="$2"
    local auth_header="$3"

    echo -n "[$name] GET $endpoint ... "

    if [ -n "$auth_header" ]; then
        response=$(curl -s -w "\n%{http_code}" -H "Authorization: $auth_header" "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    fi

    check_response "$response"
}

test_post_json() {
    local name="$1"
    local endpoint="$2"
    local data="$3"

    echo -n "[$name] POST $endpoint ... "
    response=$(curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$BASE_URL$endpoint")
    check_response "$response"
}

test_post_file() {
    local name="$1"
    local endpoint="$2"

    echo -n "[$name] POST $endpoint ... "
    echo "test content" > /tmp/smoke_test_file.txt
    response=$(curl -s -w "\n%{http_code}" -X POST -F "file=@/tmp/smoke_test_file.txt" "$BASE_URL$endpoint")
    rm -f /tmp/smoke_test_file.txt
    check_response "$response"
}

check_response() {
    local response="$1"
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [[ "$http_code" =~ ^2[0-9][0-9]$ ]]; then
        echo "✅ PASS ($http_code)"
        ((PASS++))
    else
        echo "❌ FAIL ($http_code)"
        echo "   Response: $body"
        ((FAIL++))
    fi
}

echo ""

# 01 - Health
test_get "01-lightweight" "/health"

# 02 - Echo
test_post_json "02-json-payload" "/echo" '{"message":"test","data":{"key":"value"}}'

# 03 - Users GET
test_get "03-db-read" "/users"

# 04 - Users POST
RANDOM_EMAIL="smoke_$(date +%s)@test.com"
test_post_json "04-db-write" "/users" "{\"name\":\"SmokeTest\",\"email\":\"$RANDOM_EMAIL\"}"

# 05 - External
test_get "05-external-api" "/external"

# 06 - Protected
test_get "06-middleware" "/protected" "Bearer test-token-12345"

# 07 - Upload
test_post_file "07-file-upload" "/upload"

echo ""
echo "=========================================="
echo "  Results: $PASS passed, $FAIL failed"
echo "=========================================="

if [ $FAIL -gt 0 ]; then
    exit 1
fi
