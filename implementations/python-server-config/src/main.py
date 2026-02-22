import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime

import bcrypt
from fastapi import FastAPI
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, func, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ============================================
# Configuration
# ============================================
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/benchmark",
)

SERVER_TYPE = os.getenv("SERVER_TYPE", "uvicorn")
WORKER_COUNT = int(os.getenv("WORKER_COUNT", "1"))
CPU_LIMIT = os.getenv("CPU_LIMIT", "unknown")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(bind=engine, expire_on_commit=False)


# ============================================
# ORM Models (기존 authors + posts 테이블 재사용)
# ============================================
class Base(DeclarativeBase):
    pass


class AuthorModel(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    bio: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    posts: Mapped[list["PostModel"]] = relationship(
        "PostModel", back_populates="author", lazy="select"
    )


class PostModel(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str | None] = mapped_column(Text)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    author: Mapped["AuthorModel"] = relationship(
        "AuthorModel", back_populates="posts"
    )


# ============================================
# App Lifespan
# ============================================
@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="Server Config Experiment",
    description="Uvicorn vs Gunicorn+Uvicorn benchmark",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================
# Utility Endpoints
# ============================================
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "server": SERVER_TYPE,
        "workers": WORKER_COUNT,
        "pid": os.getpid(),
        "cpu_limit": CPU_LIMIT,
    }


# ============================================
# I/O-bound Endpoints
# ============================================
@app.get("/io/sleep")
async def io_sleep():
    await asyncio.sleep(0.1)
    return {"status": "ok", "slept": 0.1}


@app.get("/io/db")
async def io_db():
    async with async_session() as session:
        stmt = (
            select(
                AuthorModel.id,
                AuthorModel.name,
                AuthorModel.email,
                func.count(PostModel.id).label("post_count"),
                func.coalesce(func.sum(PostModel.view_count), 0).label("total_views"),
            )
            .outerjoin(PostModel, AuthorModel.id == PostModel.author_id)
            .group_by(AuthorModel.id, AuthorModel.name, AuthorModel.email)
        )
        result = await session.execute(stmt)
        rows = result.all()

    return {
        "count": len(rows),
        "authors": [
            {
                "id": row.id,
                "name": row.name,
                "email": row.email,
                "post_count": row.post_count,
                "total_views": row.total_views,
            }
            for row in rows
        ],
    }


# ============================================
# CPU-bound Endpoints
# ============================================
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


@app.get("/cpu/fibonacci")
async def cpu_fibonacci(n: int = 32):
    result = fibonacci(n)
    return {"n": n, "result": result}


@app.get("/cpu/hash")
async def cpu_hash():
    password = b"benchmark_password_2024"
    hashed = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12))
    return {"status": "ok", "hash_length": len(hashed)}


@app.get("/cpu/json-serialize")
async def cpu_json_serialize():
    data = [
        {
            "id": i,
            "name": f"user_{i}",
            "email": f"user_{i}@example.com",
            "value": i * 1.5,
        }
        for i in range(10_000)
    ]
    serialized = json.dumps(data)
    return {"status": "ok", "items": 10_000, "bytes": len(serialized)}


# ============================================
# Mixed Endpoints
# ============================================
@app.get("/mixed/report")
async def mixed_report():
    # Phase 1: I/O - DB query
    async with async_session() as session:
        stmt = (
            select(
                AuthorModel.id,
                AuthorModel.name,
                func.count(PostModel.id).label("post_count"),
                func.coalesce(func.sum(PostModel.view_count), 0).label("total_views"),
            )
            .outerjoin(PostModel, AuthorModel.id == PostModel.author_id)
            .group_by(AuthorModel.id, AuthorModel.name)
        )
        result = await session.execute(stmt)
        rows = result.all()

    # Phase 2: CPU - aggregation
    authors_data = [
        {
            "id": row.id,
            "name": row.name,
            "post_count": row.post_count,
            "total_views": row.total_views,
            "avg_views": (
                row.total_views / row.post_count if row.post_count > 0 else 0
            ),
        }
        for row in rows
    ]

    top_by_posts = sorted(
        authors_data, key=lambda x: x["post_count"], reverse=True
    )[:10]
    top_by_views = sorted(
        authors_data, key=lambda x: x["total_views"], reverse=True
    )[:10]

    total_posts = sum(a["post_count"] for a in authors_data)
    total_views = sum(a["total_views"] for a in authors_data)

    # CPU: JSON round-trip (simulate real-world processing)
    json.loads(json.dumps(authors_data))

    return {
        "summary": {
            "total_authors": len(authors_data),
            "total_posts": total_posts,
            "total_views": total_views,
            "avg_posts_per_author": (
                total_posts / len(authors_data) if authors_data else 0
            ),
            "avg_views_per_post": (
                total_views / total_posts if total_posts > 0 else 0
            ),
        },
        "top_by_posts": top_by_posts,
        "top_by_views": top_by_views,
    }
