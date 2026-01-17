// scenarios/caching/16-a-pure-hit.js
// 100% 캐시 히트 - 순수 Redis GET 성능 측정
import http from "k6/http";
import { check, group } from "k6";
import { BASE_URL, defaultOptions } from "../config.js";

const MAX_USER_ID = 1000;

export const options = {
  ...defaultOptions,
  thresholds: {
    "group_duration{group:::Pure Hit}": ["p(95)<10"],
  },
};

export function setup() {
  console.log("=== 16-a. Pure Hit Scenario ===");

  // 1. 캐시 초기화
  http.del(`${BASE_URL}/cache/flush`);

  // 2. 전체 사용자 워밍업 (1~1000 전부)
  const warmupRes = http.post(`${BASE_URL}/cache/warmup?count=${MAX_USER_ID}`);
  console.log(`Warmup: ${warmupRes.json().warmed_count} users cached (100%)`);

  return {};
}

export default function () {
  const userId = Math.floor(Math.random() * MAX_USER_ID) + 1;

  group("Pure Hit", function () {
    const res = http.get(`${BASE_URL}/cache/users/${userId}/cached`);
    check(res, {
      "status 200": (r) => r.status === 200,
      "source is cache": (r) => r.json().source === "cache",
    });
  });
}

export function teardown() {
  http.del(`${BASE_URL}/cache/flush`);
  console.log("Cache flushed after test");
}
