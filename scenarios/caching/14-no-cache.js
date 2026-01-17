// scenarios/caching/14-no-cache.js
// 캐시 없는 환경 (순수 DB만 사용) - 기준선 측정
// Redis 불필요: 이 시나리오는 캐시를 사용하지 않음
import http from "k6/http";
import { check, group } from "k6";
import { BASE_URL, defaultOptions } from "../config.js";

// 사용자 ID 범위 (users 테이블에 1~1000명 존재)
const MAX_USER_ID = 1000;

export const options = {
  ...defaultOptions,
  thresholds: {
    "group_duration{group:::No Cache (DB only)}": ["p(95)<100"],
  },
};

export function setup() {
  console.log("=== 14. No Cache Scenario ===");
  console.log("Testing pure DB performance without caching");
  console.log("This is the baseline for comparison with cached scenario");
  return {};
}

export default function () {
  const userId = Math.floor(Math.random() * MAX_USER_ID) + 1;

  // ============================================
  // No Cache: 항상 DB에서 조회
  // 캐시 오버헤드 없이 순수 DB 성능만 측정
  // ============================================
  group("No Cache (DB only)", function () {
    const res = http.get(`${BASE_URL}/cache/users/${userId}/no-cache`);
    check(res, {
      "status 200": (r) => r.status === 200,
      "source is database": (r) => r.json().source === "database",
    });
  });
}

export function teardown() {
  console.log("No Cache scenario completed");
}
