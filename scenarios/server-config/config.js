export const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export const experimentOptions = {
  vus: parseInt(__ENV.VUS || "10"),
  duration: __ENV.DURATION || "60s",
  summaryTrendStats: ["avg", "min", "med", "max", "p(90)", "p(95)", "p(99)"],
};
