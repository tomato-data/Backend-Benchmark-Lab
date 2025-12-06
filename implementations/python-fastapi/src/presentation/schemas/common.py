from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class EchoRequest(BaseModel):
    message: str
    data: dict[str, Any] | None = None


class EchoResponse(BaseModel):
    message: str
    data: dict[str, Any] | None = None


class ExternalResponse(BaseModel):
    source: str
    latency_ms: float
    data: dict[str, Any] | None = None


class ProtectedResponse(BaseModel):
    message: str
    user: str | None = None


class UploadResponse(BaseModel):
    filename: str
    size: int
    content_type: str | None = None
