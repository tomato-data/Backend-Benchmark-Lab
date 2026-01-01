from fastapi import APIRouter

from src.presentation.api.v1 import echo, external, health, users, protected, upload

router = APIRouter()

router.include_router(health.router)
router.include_router(echo.router)
router.include_router(users.router)
router.include_router(external.router)
router.include_router(protected.router)
router.include_router(upload.router)
