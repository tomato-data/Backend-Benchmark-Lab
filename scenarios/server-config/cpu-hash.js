import http from "k6/http";
import { check } from "k6";
import { BASE_URL, experimentOptions } from "./config.js";

export const options = experimentOptions;

export default function () {
  const res = http.get(`${BASE_URL}/cpu/hash`);

  check(res, {
    "status is 200": (r) => r.status === 200,
    "hash generated": (r) => r.json().hash_length > 0,
  });
}
