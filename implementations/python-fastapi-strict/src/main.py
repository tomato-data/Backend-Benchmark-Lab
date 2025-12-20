from contextlib import asynccontextmanager

from fastapi import FastAPI

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
    await engine.dispose()


app = FastAPI(
    title="FastAPI Strict Clean Architecture",
    description="Backend Benchmark Lab - Strict Implementation",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(v1_router)


@app.get("/")
async def root():
    return {"message": "FastAPI Strict Benchmark API", "docs": "/docs"}
