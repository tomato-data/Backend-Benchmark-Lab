import { Router } from "express";
import healthRouter from "./health";
import echoRouter from "./echo";
import usersRouter from "./users";
import protectedRouter from "./protected";
import externalRouter from "./external";
import uploadRouter from "./upload";

const router = Router();

router.use("/health", healthRouter);
router.use("/echo", echoRouter);
router.use("/users", usersRouter);
router.use("/protected", protectedRouter);
router.use("/external", externalRouter);
router.use("/upload", uploadRouter);

export default router;
