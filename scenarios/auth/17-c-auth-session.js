import http from "k6/http";
import { check, group } from "k6";
import { Trend } from "k6/metrics";
import { BASE_URL, defaultOptions } from "../config.js";

export const options = defaultOptions;

const sessionProtectedDuration = new Trend("session_protected_duration", true);

export function setup() {
  const loginRes = http.post(`${BASE_URL}/auth/login/session?user_id=1`);

  check(loginRes, {
    "login successful": (r) => r.status === 200,
    "has session_token": (r) => r.json().session_token !== undefined,
  });

  return { token: loginRes.json().session_token };
}

export default function (data) {
  group("17-c: Session Protected", () => {
    const res = http.get(`${BASE_URL}/auth/protected/session`, {
      headers: {
        Authorization: `Bearer ${data.token}`,
      },
    });

    check(res, {
      "status is 200": (r) => r.status === 200,
      "auth_type is session": (r) => r.json().auth_type === "session",
    });

    sessionProtectedDuration.add(res.timings.duration);
  });
}

export function handleSummary(data) {
  const duration = data.metrics.session_protected_duration;
  console.log("\n=== 17-c: Session Auth Results ===");
  console.log(`Median: ${duration.values.med.toFixed(2)}ms`);
  console.log(`P95: ${duration.values["p(95)"].toFixed(2)}ms`);
  console.log(`Throughput: ${data.metrics.http_reqs.values.rate.toFixed(2)} req/s`);
  return {};
}
