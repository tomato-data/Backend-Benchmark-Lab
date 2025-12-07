import asyncio
import time

from fastapi import APIRouter

from src.presentation.schemas.common import ExternalResponse

router = APIRouter(tags=["external"])


@router.get("/external", response_model=ExternalResponse)
async def call_external_api():
    """External API call simulation - async I/O performance"""
    start = time.perf_counter()

    # Simulate external API latency (100ms)
    await asyncio.sleep(0.1)

    latency = (time.perf_counter() - start) * 1000

    return ExternalResponse(
        source="simulated_external_api",
        latency_ms=round(latency, 2),
        data={"message": "External API response"},
    )
