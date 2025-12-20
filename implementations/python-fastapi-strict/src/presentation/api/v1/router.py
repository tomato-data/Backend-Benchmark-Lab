from fastapi import APIRouter

from src.presentation.api.v1 import echo, external, health, users

router = APIRouter(prefix="/api/v1")

router.include_router(health.router)
router.include_router(echo.router)
router.include_router(users.router)
router.include_router(external.router)
