// scenarios/07-file-upload.js
import http from "k6/http";
import { check } from "k6";
import { BASE_URL, defaultOptions } from "./config.js";

export const options = defaultOptions;

// 1KB 테스트 파일 생성
const fileContent = "x".repeat(1024);

export default function () {
  const data = {
    file: http.file(fileContent, "test.txt", "text/plain"),
  };

  const res = http.post(`${BASE_URL}/upload`, data);

  check(res, {
    "status is 200": (r) => r.status === 200,
    "size is 1024": (r) => r.json().size === 1024,
  });
}
