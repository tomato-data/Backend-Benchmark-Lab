from fastapi import APIRouter

from src.presentation.api.v1 import (
    health,
    echo,
    users,
    external,
    protected,
    upload,
    column_overhead,
)

router = APIRouter()

# Include all routers
router.include_router(health.router)
router.include_router(echo.router)
router.include_router(users.router)
router.include_router(external.router)
router.include_router(protected.router)
router.include_router(upload.router)
router.include_router(column_overhead.router)
