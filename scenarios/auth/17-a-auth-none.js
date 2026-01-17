import http from "k6/http";
import { check, group } from "k6";
import { Trend } from "k6/metrics";
import { BASE_URL, defaultOptions } from "../config.js";

export const options = defaultOptions;

const authNoneDuration = new Trend("auth_none_duration", true);

export default function () {
  group("17-a: No Auth", () => {
    const res = http.get(`${BASE_URL}/auth/public`);

    check(res, {
      "status is 200": (r) => r.status === 200,
      "has message": (r) => r.json().message === "public endpoint",
    });

    authNoneDuration.add(res.timings.duration);
  });
}

export function handleSummary(data) {
  const duration = data.metrics.auth_none_duration;
  console.log("\n=== 17-a: No Auth Results ===");
  console.log(`Median: ${duration.values.med.toFixed(2)}ms`);
  console.log(`P95: ${duration.values["p(95)"].toFixed(2)}ms`);
  console.log(`Throughput: ${data.metrics.http_reqs.values.rate.toFixed(2)} req/s`);
  return {};
}
