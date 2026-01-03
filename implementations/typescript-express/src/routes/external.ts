import { Router } from "express";

const router = Router();

// 외부 API 호출 시뮬레이션 (100ms 지연)
router.get("/", async (req, res) => {
  const start = performance.now();

  await new Promise((resolve) => setTimeout(resolve, 100));

  const latency = performance.now() - start;

  res.json({
    source: "simulated_external_api",
    latency_ms: Math.round(latency * 100) / 100, // 소수점 2자리
    data: { message: "External API response" },
  });
});

export default router;
