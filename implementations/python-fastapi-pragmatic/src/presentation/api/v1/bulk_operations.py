import time
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_db
from src.infrastructure.database.models import BulkItemModel
from src.presentation.schemas.bulk_operations import BulkOperationResult

router = APIRouter(prefix="/bulk-operations", tags=["bulk-operations"])

# 기본 건수
DEFAULT_COUNT = 1000


@router.delete("/cleanup")
async def cleanup(db: AsyncSession = Depends(get_db)):
    """테이블 초기화 (TRUNCATE)"""
    await db.execute(text("TRUNCATE TABLE bulk_items RESTART IDENTITY"))
    await db.commit()
    return {"message": "Table truncated"}


# ============================================
# A. Individual INSERT (1건씩 commit)
# ============================================
@router.post("/insert-individual", response_model=BulkOperationResult)
async def insert_individual(
    count: int = Query(DEFAULT_COUNT, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
):
    """1건씩 개별 INSERT + commit (가장 느림)"""
    start = time.perf_counter()

    for i in range(count):
        item = BulkItemModel(name=f"item_{i}", value=i)
        db.add(item)
        await db.commit()

    elapsed = (time.perf_counter() - start) * 1000
    return BulkOperationResult(
        operation="insert-individual", count=count, elapsed_ms=elapsed
    )


# ============================================
# B. Batch INSERT (add_all + 1회 commit)
# ============================================
@router.post("/insert-batch", response_model=BulkOperationResult)
async def insert_batch(
    count: int = Query(DEFAULT_COUNT, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
):
    """add_all로 모아서 1회 commit"""
    start = time.perf_counter()

    items = [BulkItemModel(name=f"item_{i}", value=i) for i in range(count)]
    db.add_all(items)
    await db.commit()

    elapsed = (time.perf_counter() - start) * 1000
    return BulkOperationResult(
        operation="insert-batch", count=count, elapsed_ms=elapsed
    )


# ============================================
# C. Raw INSERT (executemany 스타일)
# ============================================
@router.post("/insert-raw", response_model=BulkOperationResult)
async def insert_raw(
    count: int = Query(DEFAULT_COUNT, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
):
    """Raw SQL INSERT (VALUES 한번에)"""
    start = time.perf_counter()

    # VALUES 절 생성
    values = ", ".join([f"('item_{i}', {i}, NOW())" for i in range(count)])
    query = text(f"INSERT INTO bulk_items (name, value, created_at) VALUES {values}")
    await db.execute(query)
    await db.commit()

    elapsed = (time.perf_counter() - start) * 1000
    return BulkOperationResult(operation="insert-raw", count=count, elapsed_ms=elapsed)


# ============================================
# D. Individual UPDATE (1건씩)
# ============================================
@router.post("/update-individual", response_model=BulkOperationResult)
async def update_individual(
    count: int = Query(DEFAULT_COUNT, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
):
    """1건씩 개별 UPDATE"""
    start = time.perf_counter()

    for i in range(1, count + 1):
        stmt = update(BulkItemModel).where(BulkItemModel.id == i).values(value=i * 10)
        await db.execute(stmt)
        await db.commit()

    elapsed = (time.perf_counter() - start) * 1000
    return BulkOperationResult(
        operation="update-individual", count=count, elapsed_ms=elapsed
    )


# ============================================
# E. Bulk UPDATE (WHERE id IN)
# ============================================
@router.post("/update-bulk", response_model=BulkOperationResult)
async def update_bulk(
    count: int = Query(DEFAULT_COUNT, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
):
    """Bulk UPDATE (CASE WHEN 사용)"""
    start = time.perf_counter()

    # CASE WHEN으로 여러 row 한번에 UPDATE
    ids = list(range(1, count + 1))
    case_when = " ".join([f"WHEN id = {i} THEN {i * 10}" for i in ids])
    query = text(
        f"""
                 UPDATE bulk_items
                 SET value = CASE {case_when} END
                 WHERE id IN ({','.join(map(str, ids))})
                 """
    )
    await db.execute(query)
    await db.commit()

    elapsed = (time.perf_counter() - start) * 1000
    return BulkOperationResult(operation="update-bulk", count=count, elapsed_ms=elapsed)
