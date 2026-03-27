import http from "k6/http";
import { check } from "k6";
import { BASE_URL, experimentOptions } from "./config.js";

export const options = experimentOptions;

const N = __ENV.FIB_N || "32";

export default function () {
  const res = http.get(`${BASE_URL}/cpu/fibonacci?n=${N}`);

  check(res, {
    "status is 200": (r) => r.status === 200,
    "has result": (r) => r.json().result !== undefined,
  });
}
