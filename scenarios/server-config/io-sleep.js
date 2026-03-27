import http from "k6/http";
import { check } from "k6";
import { BASE_URL, experimentOptions } from "./config.js";

export const options = experimentOptions;

export default function () {
  const res = http.get(`${BASE_URL}/io/sleep`);

  check(res, {
    "status is 200": (r) => r.status === 200,
    "slept 0.1s": (r) => r.json().slept === 0.1,
  });
}
