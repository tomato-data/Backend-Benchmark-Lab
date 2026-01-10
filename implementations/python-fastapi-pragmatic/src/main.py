from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.infrastructure.cache.connection import close_redis
from src.infrastructure.database.connection import engine
from src.infrastructure.database.models import Base
from src.presentation.api.v1.router import router as v1_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup: Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: Close connections
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title="FastAPI Benchmark",
    description="Backend Benchmark Lab - FastAPI Implementation",
    version="1.0.0",
    lifespan=lifespan,
)

# Include API router
app.include_router(v1_router)


@app.get("/")
async def root():
    return {"message": "FastAPI Benchmark API", "docs": "/docs"}
