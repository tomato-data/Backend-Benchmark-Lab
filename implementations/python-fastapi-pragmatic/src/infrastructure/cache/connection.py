import os
from redis.asyncio import Redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Redis 클라이언트 (싱글톤)
redis_client: Redis | None = None


async def get_redis() -> Redis:
    """FastAPI 의존성 주입용"""
    global redis_client
    if redis_client is None:
        redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    return redis_client


async def close_redis():
    """앱 종료 시 연결 정리"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
