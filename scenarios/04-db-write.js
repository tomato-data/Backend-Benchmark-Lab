// scenarios/04-db-write.js
import http from "k6/http";
import { check } from "k6";
import { BASE_URL, defaultOptions } from "./config.js";

export const options = defaultOptions;

// 유니크 이메일 생성을 위해 VU ID + iteration 사용
export default function () {
  const uniqueId = `${__VU}_${__ITER}_${Date.now()}`;

  const payload = JSON.stringify({
    name: `Test User ${uniqueId}`,
    email: `test_${uniqueId}@benchmark.test`,
  });

  const headers = { "Content-Type": "application/json" };

  const res = http.post(`${BASE_URL}/users`, payload, { headers });

  check(res, {
    "status is 201": (r) => r.status === 201,
    "has id": (r) => r.json().id !== undefined,
  });
}
