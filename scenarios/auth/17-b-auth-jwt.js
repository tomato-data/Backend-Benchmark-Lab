import http from "k6/http";
import { check, group } from "k6";
import { Trend } from "k6/metrics";
import { BASE_URL, defaultOptions } from "../config.js";

export const options = defaultOptions;

const jwtProtectedDuration = new Trend("jwt_protected_duration", true);

export function setup() {
  const loginRes = http.post(`${BASE_URL}/auth/login/jwt?user_id=1`);

  check(loginRes, {
    "login successful": (r) => r.status === 200,
    "has access_token": (r) => r.json().access_token !== undefined,
  });

  return { token: loginRes.json().access_token };
}

export default function (data) {
  group("17-b: JWT Protected", () => {
    const res = http.get(`${BASE_URL}/auth/protected/jwt`, {
      headers: {
        Authorization: `Bearer ${data.token}`,
      },
    });

    check(res, {
      "status is 200": (r) => r.status === 200,
      "auth_type is jwt": (r) => r.json().auth_type === "jwt",
    });

    jwtProtectedDuration.add(res.timings.duration);
  });
}

export function handleSummary(data) {
  const duration = data.metrics.jwt_protected_duration;
  console.log("\n=== 17-b: JWT Auth Results ===");
  console.log(`Median: ${duration.values.med.toFixed(2)}ms`);
  console.log(`P95: ${duration.values["p(95)"].toFixed(2)}ms`);
  console.log(`Throughput: ${data.metrics.http_reqs.values.rate.toFixed(2)} req/s`);
  return {};
}
