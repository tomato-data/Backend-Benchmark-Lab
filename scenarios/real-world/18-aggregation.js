// scenarios/real-world/18-aggregation.js
import http from "k6/http";
import { check, group } from "k6";
import { BASE_URL, defaultOptions } from "../config.js";

export const options = {
  ...defaultOptions,
  thresholds: {
    // 실측 기반 threshold (2026-02-07)
    // ORM/Raw 동일 기준 — 비교는 결과 데이터로 판단
    "group_duration{group:::A. Count ORM}": ["p(95)<300"],
    "group_duration{group:::B. Count Raw}": ["p(95)<350"],
    "group_duration{group:::C. Country Stats ORM}": ["p(95)<250"],
    "group_duration{group:::D. Country Stats Raw}": ["p(95)<250"],
    "group_duration{group:::E. Author Stats ORM}": ["p(95)<150"],
    "group_duration{group:::F. Author Stats Raw}": ["p(95)<150"],
  },
};

export default function () {
  // ============================================
  // A. COUNT 비교 - ORM
  // ============================================
  group("A. Count ORM", function () {
    const res = http.get(`${BASE_URL}/aggregation/count/orm`);
    check(res, {
      "count orm status 200": (r) => r.status === 200,
      "count orm has count_star": (r) => r.json().count_star > 0,
    });
  });
  // ============================================
  // B. COUNT 비교 - Raw SQL
  // ============================================
  group("B. Count Raw", function () {
    const res = http.get(`${BASE_URL}/aggregation/count/raw`);
    check(res, {
      "count raw status 200": (r) => r.status === 200,
      "count raw has count_star": (r) => r.json().count_star > 0,
    });
  });
  // ============================================
  // C. 국가별 통계 - ORM
  // ============================================
  group("C. Country Stats ORM", function () {
    const res = http.get(`${BASE_URL}/aggregation/stats/country/orm?limit=10`);
    check(res, {
      "country orm status 200": (r) => r.status === 200,
      "country orm has results": (r) => r.json().length > 0,
      "country orm has user_count": (r) => r.json()[0].user_count > 0,
    });
  });
  // ============================================
  // D. 국가별 통계 - Raw SQL
  // ============================================
  group("D. Country Stats Raw", function () {
    const res = http.get(`${BASE_URL}/aggregation/stats/country/raw?limit=10`);
    check(res, {
      "country raw status 200": (r) => r.status === 200,
      "country raw has results": (r) => r.json().length > 0,
      "country raw has user_count": (r) => r.json()[0].user_count > 0,
    });
  });
  // ============================================
  // E. 작가별 통계 - ORM (JOIN + GROUP BY)
  // ============================================
  group("E. Author Stats ORM", function () {
    const res = http.get(`${BASE_URL}/aggregation/stats/author/orm?limit=10`);
    check(res, {
      "author orm status 200": (r) => r.status === 200,
      "author orm has results": (r) => r.json().length > 0,
      "author orm has post_count": (r) => r.json()[0].post_count > 0,
    });
  });
  // ============================================
  // F. 작가별 통계 - Raw SQL (JOIN + GROUP BY)
  // ============================================
  group("F. Author Stats Raw", function () {
    const res = http.get(`${BASE_URL}/aggregation/stats/author/raw?limit=10`);
    check(res, {
      "author raw status 200": (r) => r.status === 200,
      "author raw has results": (r) => r.json().length > 0,
      "author raw has post_count": (r) => r.json()[0].post_count > 0,
    });
  });
}
