import { Router } from "express";
import { EchoRequestSchema } from "../schemas/common";

const router = Router();

router.post("/", (req, res) => {
  const result = EchoRequestSchema.safeParse(req.body);

  if (!result.success) {
    return res.status(422).json({ detail: result.error.issues });
  }

  res.json(result.data);
});

export default router;
