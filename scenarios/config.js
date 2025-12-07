export const BASE_URL = "http://localhost:8000";

export const defaultOptions = {
  vus: 10, // Virtual Users (동시 사용자)
  duration: "30s", // 테스트 지속 시간
  summaryTrendStats: ["avg", "min", "med", "max", "p(90)", "p(95)", "p(99)"],
};
