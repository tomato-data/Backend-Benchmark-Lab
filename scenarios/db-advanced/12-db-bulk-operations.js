// scenarios/db-advanced/12-db-bulk-operations.js
import http from "k6/http";
import { check, group } from "k6";
import { BASE_URL, defaultOptions } from "../config.js";

const COUNT = 1000; // 벌크 작업 건수

export const options = {
  ...defaultOptions,
  thresholds: {
    "group_duration{group:::A. Individual INSERT}": ["p(95)<30000"], // 느림 예상
    "group_duration{group:::B. Batch INSERT}": ["p(95)<1000"],
    "group_duration{group:::C. Raw INSERT}": ["p(95)<500"],
    "group_duration{group:::D. Individual UPDATE}": ["p(95)<30000"],
    "group_duration{group:::E. Bulk UPDATE}": ["p(95)<1000"],
  },
};

export function setup() {
  // 테이블 초기화
  http.del(`${BASE_URL}/bulk-operations/cleanup`);
}

export default function () {
  // ============================================
  // A. Individual INSERT (가장 느림)
  // ============================================
  group("A. Individual INSERT", function () {
    http.del(`${BASE_URL}/bulk-operations/cleanup`);

    const res = http.post(
      `${BASE_URL}/bulk-operations/insert-individual?count=${COUNT}`
    );
    check(res, {
      "individual insert status 200": (r) => r.status === 200,
      "individual insert count match": (r) => r.json().count === COUNT,
    });
  });
  // ============================================
  // B. Batch INSERT (add_all)
  // ============================================
  group("B. Batch INSERT", function () {
    http.del(`${BASE_URL}/bulk-operations/cleanup`);

    const res = http.post(
      `${BASE_URL}/bulk-operations/insert-batch?count=${COUNT}`
    );
    check(res, {
      "batch insert status 200": (r) => r.status === 200,
      "batch insert count match": (r) => r.json().count === COUNT,
    });
  });
  // ============================================
  // C. Raw INSERT (가장 빠름)
  // ============================================
  group("C. Raw INSERT", function () {
    http.del(`${BASE_URL}/bulk-operations/cleanup`);

    const res = http.post(
      `${BASE_URL}/bulk-operations/insert-raw?count=${COUNT}`
    );
    check(res, {
      "raw insert status 200": (r) => r.status === 200,
      "raw insert count match": (r) => r.json().count === COUNT,
    });
  });

  // ============================================
  // D. Individual UPDATE
  // ============================================
  group("D. Individual UPDATE", function () {
    // UPDATE 테스트를 위해 먼저 데이터 삽입
    http.del(`${BASE_URL}/bulk-operations/cleanup`);
    http.post(`${BASE_URL}/bulk-operations/insert-raw?count=${COUNT}`);

    const res = http.post(
      `${BASE_URL}/bulk-operations/update-individual?count=${COUNT}`
    );
    check(res, {
      "individual update status 200": (r) => r.status === 200,
    });
  });
  // ============================================
  // E. Bulk UPDATE
  // ============================================
  group("E. Bulk UPDATE", function () {
    http.del(`${BASE_URL}/bulk-operations/cleanup`);
    http.post(`${BASE_URL}/bulk-operations/insert-raw?count=${COUNT}`);

    const res = http.post(
      `${BASE_URL}/bulk-operations/update-bulk?count=${COUNT}`
    );
    check(res, {
      "bulk update status 200": (r) => r.status === 200,
    });
  });
}
