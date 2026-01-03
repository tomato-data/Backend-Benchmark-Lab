import { Router } from "express";

const router = Router();

router.get("/", (req, res) => {
  const authorization = req.headers.authorization;
  const xRequestId = req.headers["x-request-id"];

  // 1. Authorization 헤더 필수
  if (!authorization) {
    return res.status(401).json({ detail: "Authorization header required" });
  }

  // 2. Bearer 포맷 검증
  if (!authorization.startsWith("Bearer ")) {
    return res.status(401).json({ detail: "Invalid authorization format" });
  }

  const token = authorization.replace("Bearer ", "");

  // 3. 토큰 최소 길이 검증
  if (token.length < 10) {
    return res.status(401).json({ detail: "Invalid token" });
  }

  // 성공
  res.json({
    message: "Access granted",
    user: `user_from_token_${token.slice(0, 8)}`,
  });
});

export default router;
