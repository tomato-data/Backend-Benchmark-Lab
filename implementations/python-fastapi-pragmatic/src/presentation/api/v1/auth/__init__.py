from fastapi import APIRouter

from .common import router as common_router
from .jwt import router as jwt_router
from .session import router as session_router


router = APIRouter()

router.include_router(common_router)
router.include_router(jwt_router)
router.include_router(session_router)
