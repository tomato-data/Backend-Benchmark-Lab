// scenarios/08-concurrent-mixed.js
import http from "k6/http";
import { check } from "k6";
import { BASE_URL, defaultOptions } from "./config.js";

export const options = defaultOptions;

const headers = { "Content-Type": "application/json" };
const authHeaders = {
  Authorization: "Bearer test-token-12345",
  "X-Request-Id": "mixed-test",
};

export default function () {
  const rand = Math.random() * 100;

  if (rand < 5) {
    // 5%: health
    const res = http.get(`${BASE_URL}/health`);
    check(res, { "health 200": (r) => r.status === 200 });
  } else if (rand < 20) {
    // 15%: echo
    const payload = JSON.stringify({ message: "mixed", data: {} });
    const res = http.post(`${BASE_URL}/echo`, payload, { headers });
    check(res, { "echo 200": (r) => r.status === 200 });
  } else if (rand < 60) {
    // 40%: get users
    const res = http.get(`${BASE_URL}/users`);
    check(res, { "users 200": (r) => r.status === 200 });
  } else if (rand < 70) {
    // 10%: create user
    const uniqueId = `${__VU}_${__ITER}_${Date.now()}`;
    const payload = JSON.stringify({
      name: `Mixed User ${uniqueId}`,
      email: `mixed_${uniqueId}@benchmark.test`,
    });
    const res = http.post(`${BASE_URL}/users`, payload, { headers });
    check(res, { "create 201": (r) => r.status === 201 });
  } else if (rand < 85) {
    // 15%: external
    const res = http.get(`${BASE_URL}/external`);
    check(res, { "external 200": (r) => r.status === 200 });
  } else {
    // 15%: protected
    const res = http.get(`${BASE_URL}/protected`, { headers: authHeaders });
    check(res, { "protected 200": (r) => r.status === 200 });
  }
}
