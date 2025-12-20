from fastapi import APIRouter

from src.presentation.schemas.common import EchoRequest, EchoResponse

router = APIRouter(tags=["echo"])


@router.post("/echo", response_model=EchoResponse)
async def echo(request: EchoRequest):
    """Echo endpoint - JSON esrialization performance"""
    return EchoResponse(message=request.message, data=request.data)
