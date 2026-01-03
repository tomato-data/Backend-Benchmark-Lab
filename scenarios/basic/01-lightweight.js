// scenarios/01-lightweight.js
import http from "k6/http";
import { check } from "k6";
import { BASE_URL, defaultOptions } from "../config.js";

export const options = defaultOptions;

export default function () {
  const res = http.get(`${BASE_URL}/health`);

  check(res, {
    "status is 200": (r) => r.status === 200,
  });
}
