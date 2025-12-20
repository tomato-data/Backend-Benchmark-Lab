import time
import logging
from fastapi import Request

logger = logging.getLogger(__name__)


async def log_request(request: Request) -> None:
    """요청 로깅 미들웨어"""
    logger.info(f"Request: {request.method} {request.url.path}")
