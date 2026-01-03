import { Router } from "express";
import multer from "multer";

const router = Router();

// 메모리 스토리지 (파일을 디스크에 저장하지 않음)
const upload = multer({ storage: multer.memoryStorage() });

router.post("/", upload.single("file"), (req, res) => {
  const file = req.file;

  if (!file) {
    return res.status(400).json({ detail: "No file uploaded" });
  }

  res.json({
    filename: file.originalname,
    size: file.size,
    content_type: file.mimetype,
  });
});

export default router;
