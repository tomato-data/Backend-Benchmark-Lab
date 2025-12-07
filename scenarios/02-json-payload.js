// scenarios/02-json-payload.js
import http from "k6/http";
import { check } from "k6";
import { BASE_URL, defaultOptions } from "./config.js";

export const options = defaultOptions;

const payload = JSON.stringify({
  message: "Hello, benchmark!",
  timestamp: Date.now(),
  data: {
    items: [1, 2, 3, 4, 5],
    nested: { key: "value" },
  },
});

const headers = { "Content-Type": "application/json" };

export default function () {
  const res = http.post(`${BASE_URL}/echo`, payload, { headers });

  check(res, {
    "status is 200": (r) => r.status === 200,
    "echo matches": (r) => r.json().message === "Hello, benchmark!",
  });
}
