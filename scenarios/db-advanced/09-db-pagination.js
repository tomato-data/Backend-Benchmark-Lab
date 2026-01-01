// scenarios/db-advanced/09-db-pagination.js
import http from "k6/http";
import { check, group } from "k6";
import { randomIntBetween } from "https://jslib.k6.io/k6-utils/1.2.0/index.js";

// 상위 디렉토리의 config 참조
import { BASE_URL, defaultOptions } from "../config.js";

const TOTAL_RECORDS = 100000;
const PAGE_SIZE = 20;
const TOTAL_PAGES = Math.floor(TOTAL_RECORDS / PAGE_SIZE);

export const options = {
  ...defaultOptions,
  thresholds: {
    "group_duration{group:::OFFSET pagination}": ["p(95)<500"],
    "group_duration{group:::Cursor pagination}": ["p(95)<200"],
  },
};

export default function () {
  // 랜덤 페이지/커서로 DB 캐싱 효과 최소화
  const randomPage = randomIntBetween(1, TOTAL_PAGES);
  const randomCursor = randomIntBetween(0, TOTAL_RECORDS - PAGE_SIZE);

  group("OFFSET pagination", function () {
    const res = http.get(
      `${BASE_URL}/users/offset?page=${randomPage}&size=${PAGE_SIZE}`
    );
    check(res, {
      "offset status 200": (r) => r.status === 200,
      "offset has items": (r) => r.json().items && r.json().items.length > 0,
      "offset has total": (r) => r.json().total === TOTAL_RECORDS,
    });
  });

  group("Cursor pagination", function () {
    const res = http.get(
      `${BASE_URL}/users/cursor?cursor=${randomCursor}&size=${PAGE_SIZE}`
    );
    check(res, {
      "cursor status 200": (r) => r.status === 200,
      "cursor has items": (r) => r.json().items && r.json().items.length > 0,
    });
  });
}
