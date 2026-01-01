// scenarios/05-external-api.js
import http from "k6/http";
import { check } from "k6";
import { BASE_URL, defaultOptions } from "./config.js";

export const options = defaultOptions;

export default function () {
  const res = http.get(`${BASE_URL}/external`);

  check(res, {
    "status is 200": (r) => r.status === 200,
    "has latency_ms": (r) => r.json().latency_ms !== undefined,
  });
}
