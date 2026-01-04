import { Router } from "express";
import { prisma } from "../lib/prisma";
import { UserCreateSchema } from "../schemas/user";

const router = Router();

// GET /users - 목록 (전체 반환 - FastAPI와 동일)
router.get("/", async (req, res) => {
  const users = await prisma.user.findMany();
  res.json(users);
});

// POST /users - 생성
router.post("/", async (req, res) => {
  const result = UserCreateSchema.safeParse(req.body);

  if (!result.success) {
    return res.status(422).json({ detail: result.error.issues });
  }

  const { name, email } = result.data;
  const user = await prisma.user.create({
    data: { name, email },
  });
  res.status(201).json(user);
});

// GET /users/:id - 상세
router.get("/:id", async (req, res) => {
  const id = parseInt(req.params.id);
  const user = await prisma.user.findUnique({ where: { id } });

  if (!user) {
    return res.status(404).json({ error: "User not found" });
  }
  res.json(user);
});

export default router;
