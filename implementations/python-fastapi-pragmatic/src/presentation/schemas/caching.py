from pydantic import BaseModel


class CacheResult(BaseModel):
    """캐시 조회 결과"""

    source: str  # "cache" | "database"
    user_id: int
    name: str
    email: str
    elapsed_ms: float


class CacheStats(BaseModel):
    """캐시 통계"""

    total_keys: int
    memory_used: str


class CacheWarmupResult(BaseModel):
    """워밍업 결과"""

    warmed_count: int
    elapsed_ms: float
