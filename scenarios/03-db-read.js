// scenarios/03-db-read.js
import http from "k6/http";
import { check } from "k6";
import { BASE_URL, defaultOptions } from "./config.js";

export const options = defaultOptions;

export default function () {
  // 전체 목록 조회
  const listRes = http.get(`${BASE_URL}/users`);

  check(listRes, {
    "list status 200": (r) => r.status === 200,
    "list is array": (r) => Array.isArray(r.json()),
  });
}
