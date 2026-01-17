// scenarios/caching/15-with-cache.js
// 캐시 있는 환경 (Redis 사용) - Cache Hit/Miss 혼합
// Redis 필요: docker-compose에서 redis 서비스 실행 필수
import http from "k6/http";
import { check, group } from "k6";
import { BASE_URL, defaultOptions } from "../config.js";

// 사용자 ID 범위 (users 테이블에 1~1000명 존재)
const WARMUP_COUNT = 100; // 1~100만 워밍업 (10% 캐시 히트 보장)
const MAX_USER_ID = 1000;

export const options = {
  ...defaultOptions,
  thresholds: {
    "group_duration{group:::With Cache (Hit/Miss)}": ["p(95)<50"],
  },
};

export function setup() {
  console.log("=== 15. With Cache Scenario ===");

  // 1. 캐시 초기화
  const flushRes = http.del(`${BASE_URL}/cache/flush`);
  if (flushRes.status !== 200) {
    console.error("Failed to flush cache - is Redis running?");
  }

  // 2. 부분 워밍업 (1~100만 캐시에 저장)
  // 전체 1000명 중 100명만 워밍업 → 약 10% 히트율 예상
  const warmupRes = http.post(`${BASE_URL}/cache/warmup?count=${WARMUP_COUNT}`);
  const warmedCount = warmupRes.json().warmed_count;
  console.log(`Warmup: ${warmedCount} users cached (${warmedCount}/${MAX_USER_ID} = ${(warmedCount/MAX_USER_ID*100).toFixed(0)}%)`);

  return { warmedCount: warmedCount };
}

export default function (data) {
  // 전체 범위(1~1000)에서 랜덤 선택
  // - 1~100: Cache Hit (워밍업됨)
  // - 101~1000: Cache Miss → DB → Set (이후 Hit)
  const userId = Math.floor(Math.random() * MAX_USER_ID) + 1;

  // ============================================
  // With Cache: Redis 캐시 사용
  // - Hit: Redis에서 바로 반환 (빠름)
  // - Miss: DB 조회 → Redis 저장 → 반환
  // ============================================
  group("With Cache (Hit/Miss)", function () {
    const res = http.get(`${BASE_URL}/cache/users/${userId}/cached`);
    check(res, {
      "status 200": (r) => r.status === 200,
      "has valid source": (r) =>
        ["cache", "database"].includes(r.json().source),
    });
  });
}

export function teardown(data) {
  http.del(`${BASE_URL}/cache/flush`);
  console.log("Cache flushed after test");
}
