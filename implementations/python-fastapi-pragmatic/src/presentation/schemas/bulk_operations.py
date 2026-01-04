from pydantic import BaseModel
from datetime import datetime


class BulkItemCreate(BaseModel):
    name: str
    value: int = 0


class BulkItemResponse(BaseModel):
    id: int
    name: str
    value: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BulkOperationResult(BaseModel):
    """벌크 작업 결과"""

    operation: str
    count: int
    elapsed_ms: float
