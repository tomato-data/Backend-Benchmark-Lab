// scenarios/caching/16-b-pure-miss.js
// 100% 캐시 미스 - Redis GET(miss) + DB + Redis SET 성능 측정
import http from "k6/http";
import { check, group } from "k6";
import { BASE_URL, defaultOptions } from "../config.js";

const MAX_USER_ID = 1000;

export const options = {
  ...defaultOptions,
  thresholds: {
    "group_duration{group:::Pure Miss}": ["p(95)<50"],
  },
};

export function setup() {
  console.log("=== 16-b. Pure Miss Scenario ===");

  // 캐시 초기화 (빈 상태로 시작)
  http.del(`${BASE_URL}/cache/flush`);
  console.log("Cache flushed - starting with empty cache");

  return {};
}

export default function () {
  const userId = Math.floor(Math.random() * MAX_USER_ID) + 1;

  group("Pure Miss", function () {
    // 1. 해당 키 삭제 (항상 miss 보장)
    http.del(`${BASE_URL}/cache/users/${userId}`);

    // 2. 캐시 조회 (miss → DB → set)
    const res = http.get(`${BASE_URL}/cache/users/${userId}/cached`);
    check(res, {
      "status 200": (r) => r.status === 200,
      "source is database": (r) => r.json().source === "database",
    });
  });
}

export function teardown() {
  http.del(`${BASE_URL}/cache/flush`);
  console.log("Cache flushed after test");
}
