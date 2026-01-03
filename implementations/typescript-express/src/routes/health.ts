import { Router } from "express";

const router = Router();

router.get("/", (req, res) => {
  res.json({ status: "ok", server: "typescript-express" });
});

export default router;
