// scenarios/caching/14-cache-hit.js
import http from "k6/http";
import { check, group } from "k6";
import { BASE_URL, defaultOptions } from "../config.js";

// 테스트할 사용자 ID 범위 (users 테이블에 1~1000명 존재)
const WARMUP_COUNT = 100; // 워밍업할 사용자 수
const MAX_USER_ID = 1000;

export const options = {
  ...defaultOptions,
  thresholds: {
    "group_duration{group:::A. No Cache (DB only)}": ["p(95)<100"],
    "group_duration{group:::B. Cache Hit}": ["p(95)<20"], // 5배 이상 빠름 예상
    "group_duration{group:::C. Cache Miss}": ["p(95)<100"],
  },
};

export function setup() {
  // 1. 캐시 초기화
  http.del(`${BASE_URL}/cache/flush`);

  // 2. 워밍업 (user 1~100을 캐시에 저장)
  const warmupRes = http.post(`${BASE_URL}/cache/warmup?count=${WARMUP_COUNT}`);
  console.log(`Warmup: ${warmupRes.json().warmed_count} users cached`);

  return { warmedIds: WARMUP_COUNT };
}

export default function (data) {
  // 워밍업된 ID (1~100): 캐시 히트
  // 워밍업 안 된 ID (101~1000): 캐시 미스
  // ============================================
  // A. No Cache (항상 DB 조회)
  // ============================================
  group("A. No Cache (DB only)", function () {
    const userId = Math.floor(Math.random() * MAX_USER_ID) + 1;
    const res = http.get(`${BASE_URL}/cache/users/${userId}/no-cache`);
    check(res, {
      "no-cache status 200": (r) => r.status === 200,
      "no-cache source is database": (r) => r.json().source === "database",
    });
  });
  // ============================================
  // B. Cache Hit (워밍업된 사용자)
  // ============================================
  group("B. Cache Hit", function () {
    // 1~100 중 랜덤 (워밍업된 사용자)
    const userId = Math.floor(Math.random() * WARMUP_COUNT) + 1;
    const res = http.get(`${BASE_URL}/cache/users/${userId}/cached`);
    check(res, {
      "cache-hit status 200": (r) => r.status === 200,
      "cache-hit source is cache": (r) => r.json().source === "cache",
    });
  });
  // ============================================
  // C. Cache Miss → DB → Set
  // ============================================
  group("C. Cache Miss", function () {
    // 101~1000 중 랜덤 (워밍업 안 된 사용자)
    const userId =
      Math.floor(Math.random() * (MAX_USER_ID - WARMUP_COUNT)) +
      WARMUP_COUNT +
      1;
    const res = http.get(`${BASE_URL}/cache/users/${userId}/cached`);
    check(res, {
      "cache-miss status 200": (r) => r.status === 200,
      // 첫 호출은 database, 이후는 cache (VU 간 공유되므로 둘 다 가능)
      "cache-miss has source": (r) =>
        ["cache", "database"].includes(r.json().source),
    });
  });
}

export function teardown(data) {
  // 캐시 정리
  http.del(`${BASE_URL}/cache/flush`);
  console.log("Cache flushed after test");
}
