// scenarios/db-advanced/11-db-n-plus-one.js
import http from "k6/http";
import { check, group } from "k6";
import { BASE_URL, defaultOptions } from "../config.js";

// N+1 테스트는 author 수 (limit)가 핵심
const LIMIT = 20;
const MAX_AUTHORS = 1000;

export const options = {
  ...defaultOptions,
  thresholds: {
    // Lazy (N+1)는 느릴 것으로 예상
    "group_duration{group:::A. Lazy Loading (N+1)}": ["p(95)<500"],
    // Eager (JOIN)은 빠를 것으로 예상
    "group_duration{group:::B. Eager Loading (JOIN)}": ["p(95)<100"],
    // Subquery (IN)도 빠를 것으로 예상
    "group_duration{group:::C. Subquery Loading (IN)}": ["p(95)<100"],
  },
};

export default function () {
  //각 iteration마다 다른 offset (캐시 영향 분산)
  const randomOffset = Math.floor(Math.random() * (MAX_AUTHORS - LIMIT));

  // ============================================
  // A. Lazy Loading (N+1 문제)
  // ============================================
  group("A. Lazy Loading (N+1)", function () {
    const res = http.get(
      `${BASE_URL}/n-plus-one/lazy?limit=${LIMIT}&offset=${randomOffset}`
    );
    check(res, {
      "lazy status 200": (r) => r.status === 200,
      "lazy has authors": (r) => r.json().length > 0,
      "lazy has posts": (r) => r.json()[0].posts.length > 0,
    });
  });
  // ============================================
  // B. Eager Loading (joinedload)
  // ============================================
  group("B. Eager Loading (JOIN)", function () {
    const res = http.get(
      `${BASE_URL}/n-plus-one/eager?limit=${LIMIT}&offset=${randomOffset}`
    );
    check(res, {
      "eager status 200": (r) => r.status === 200,
      "eager has authors": (r) => r.json().length > 0,
      "eager has posts": (r) => r.json()[0].posts.length > 0,
    });
  });
  // ============================================
  // C. Subquery Loading (selectinload)
  // ============================================
  group("C. Subquery Loading (IN)", function () {
    const res = http.get(
      `${BASE_URL}/n-plus-one/subquery?limit=${LIMIT}&offset=${randomOffset}`
    );
    check(res, {
      "subquery status 200": (r) => r.status === 200,
      "subquery has authors": (r) => r.json().length > 0,
      "subquery has posts": (r) => r.json()[0].posts.length > 0,
    });
  });
}
