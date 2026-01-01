// scenarios/06-middleware-chain.js
import http from "k6/http";
import { check } from "k6";
import { BASE_URL, defaultOptions } from "./config.js";

export const options = defaultOptions;

export default function () {
  const headers = {
    Authorization: "Bearer test-token-12345",
    "X-Request-Id": `req-${__VU}-${__ITER}`,
  };

  const res = http.get(`${BASE_URL}/protected`, { headers });

  check(res, {
    "status is 200": (r) => r.status === 200,
    "access granted": (r) => r.json().message === "Access granted",
  });
}
