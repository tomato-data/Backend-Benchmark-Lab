from pydantic import BaseModel
from datetime import datetime


class ProductResponse(BaseModel):
    id: int
    name: str
    stock: int
    version: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class StockUpdateRequest(BaseModel):
    """재고 차감 요청"""

    product_id: int
    quantity: int = 1  # 차감할 수량


class TransactionResult(BaseModel):
    """트랜잭션 결과"""

    success: bool
    method: str
    product_id: int
    old_stock: int
    new_stock: int
    retries: int = 0  # Optimistic Lock 재시도 횟수
    elapsed_ms: float
    error: str | None = None
