// scenarios/db-advanced/10-db-column-overhead.js
import http from "k6/http";
import { check, group } from "k6";
import { BASE_URL, defaultOptions } from "../config.js";

const LIMIT = 100;

export const options = {
  ...defaultOptions,
  thresholds: {
    // A. 컬럼 수 비교
    "group_duration{group:::A. Column Count - Narrow (5)}": ["p(95)<100"],
    "group_duration{group:::A. Column Count - Wide (20)}": ["p(95)<200"],
    "group_duration{group:::A. Column Count - Extra Wide (50)}": ["p(95)<300"],
    // B. 데이터 타입별 비교
    "group_duration{group:::B. Data Type - INT}": ["p(95)<100"],
    "group_duration{group:::B. Data Type - VARCHAR}": ["p(95)<100"],
    "group_duration{group:::B. Data Type - TEXT}": ["p(95)<150"],
    "group_duration{group:::B. Data Type - JSONB}": ["p(95)<150"],
    "group_duration{group:::B. Data Type - TIMESTAMP}": ["p(95)<100"],
    "group_duration{group:::B. Data Type - UUID}": ["p(95)<100"],
  },
};

export default function () {
  // ============================================
  // A. 컬럼 수 비교
  // ============================================

  group("A. Column Count - Narrow (5)", function () {
    const res = http.get(`${BASE_URL}/column-overhead/narrow?limit=${LIMIT}`);
    check(res, {
      "narrow status 200": (r) => r.status === 200,
      "narrow has items": (r) => r.json().length > 0,
    });
  });

  group("A. Column Count - Wide (20)", function () {
    const res = http.get(`${BASE_URL}/column-overhead/wide?limit=${LIMIT}`);
    check(res, {
      "wide status 200": (r) => r.status === 200,
      "wide has items": (r) => r.json().length > 0,
    });
  });

  group("A. Column Count - Extra Wide (50)", function () {
    const res = http.get(
      `${BASE_URL}/column-overhead/extra-wide?limit=${LIMIT}`
    );
    check(res, {
      "extra-wide status 200": (r) => r.status === 200,
      "extra-wide has items": (r) => r.json().length > 0,
    });
  });

  // ============================================
  // B. 데이터 타입별 비교 (INT를 마지막으로 이동하여 cold start 영향 검증)
  // ============================================

  group("B. Data Type - VARCHAR", function () {
    const res = http.get(
      `${BASE_URL}/column-overhead/type/varchar?limit=${LIMIT}`
    );
    check(res, {
      "varchar status 200": (r) => r.status === 200,
    });
  });

  group("B. Data Type - TEXT", function () {
    const res = http.get(
      `${BASE_URL}/column-overhead/type/text?limit=${LIMIT}`
    );
    check(res, {
      "text status 200": (r) => r.status === 200,
    });
  });

  group("B. Data Type - JSONB", function () {
    const res = http.get(
      `${BASE_URL}/column-overhead/type/jsonb?limit=${LIMIT}`
    );
    check(res, {
      "jsonb status 200": (r) => r.status === 200,
    });
  });

  group("B. Data Type - TIMESTAMP", function () {
    const res = http.get(
      `${BASE_URL}/column-overhead/type/timestamp?limit=${LIMIT}`
    );
    check(res, {
      "timestamp status 200": (r) => r.status === 200,
    });
  });

  group("B. Data Type - UUID", function () {
    const res = http.get(
      `${BASE_URL}/column-overhead/type/uuid?limit=${LIMIT}`
    );
    check(res, {
      "uuid status 200": (r) => r.status === 200,
    });
  });

  group("B. Data Type - INT", function () {
    const res = http.get(`${BASE_URL}/column-overhead/type/int?limit=${LIMIT}`);
    check(res, {
      "int status 200": (r) => r.status === 200,
    });
  });
}
