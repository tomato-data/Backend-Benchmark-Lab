import http from "k6/http";
import { check } from "k6";
import { BASE_URL, experimentOptions } from "./config.js";

export const options = experimentOptions;

export default function () {
  const res = http.get(`${BASE_URL}/mixed/report`);

  check(res, {
    "status is 200": (r) => r.status === 200,
    "has summary": (r) => r.json().summary !== undefined,
    "has top_by_posts": (r) => r.json().top_by_posts.length > 0,
  });
}
