from fastapi import APIRouter, UploadFile, File

from src.presentation.schemas.common import UploadResponse

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """File upload endpoint - streaming performance"""
    content = await file.read()
    size = len(content)

    return UploadResponse(
        filename=file.filename or "unknown",
        size=size,
        content_type=file.content_type,
    )
