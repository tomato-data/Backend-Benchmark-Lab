import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError, DBAPIError

from src.infrastructure.database.connection import get_db
from src.infrastructure.database.models import ProductModel
from src.presentation.schemas.transactions import TransactionResult, ProductResponse


router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """상품 조회"""
    result = await db.execute(select(ProductModel).where(ProductModel.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/reset")
async def reset_stock(db: AsyncSession = Depends(get_db)):
    """모든 상품 재고를 1000으로 리셋"""
    await db.execute(update(ProductModel).values(stock=1000, version=0))
    await db.commit()
    return {"message": "All stocks reset to 1000"}


# ============================================
# A. No Lock (락 없이 - Lost Update 발생 가능)
# ============================================
@router.post("/decrement/no-lock", response_model=TransactionResult)
async def decrement_no_lock(
    product_id: int = 1,
    quantity: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """락 없이 재고 차감 (동시성 문제 발생 가능)"""
    start = time.perf_counter()

    # 1. 현재 재고 조회
    result = await db.execute(select(ProductModel).where(ProductModel.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    old_stock = product.stock

    # 2. 재고 차감 (락 없음 - Race Condition 가능)
    new_stock = old_stock - quantity
    product.stock = new_stock
    await db.commit()

    elapsed = (time.perf_counter() - start) * 1000
    return TransactionResult(
        success=True,
        method="no-lock",
        product_id=product_id,
        old_stock=old_stock,
        new_stock=new_stock,
        elapsed_ms=elapsed,
    )


# ============================================
# B. Pessimistic Lock (SELECT FOR UPDATE)
# ============================================
@router.post("/decrement/pessimistic", response_model=TransactionResult)
async def decrement_pessimistic(
    product_id: int = 1,
    quantity: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """Pessimistic Lock으로 재고 차감"""
    start = time.perf_counter()

    # SELECT ... FOR UPDATE (다른 트랜잭션 대기)
    result = await db.execute(
        select(ProductModel).where(ProductModel.id == product_id).with_for_update()
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    old_stock = product.stock
    new_stock = old_stock - quantity
    product.stock = new_stock
    await db.commit()

    elapsed = (time.perf_counter() - start) * 1000
    return TransactionResult(
        success=True,
        method="pessimistic",
        product_id=product_id,
        old_stock=old_stock,
        new_stock=new_stock,
        elapsed_ms=elapsed,
    )


# ============================================
# C. Optimistic Lock (Version 체크)
# ============================================
@router.post("/decrement/optimistic", response_model=TransactionResult)
async def decrement_optimistic(
    product_id: int = 1,
    quantity: int = 1,
    max_retries: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """Optimistic Lock으로 재고 차감 (충돌 시 재시도)"""
    start = time.perf_counter()
    retries = 0

    while retries < max_retries:
        # 1. 현재 상태 조회
        result = await db.execute(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        old_stock = product.stock
        old_version = product.version
        new_stock = old_stock - quantity

        # 2. Version 체크하며 UPDATE (CAS - Compare And Swap)
        update_result = await db.execute(
            update(ProductModel)
            .where(ProductModel.id == product_id)
            .where(ProductModel.version == old_version)  # 버전 일치 확인
            .values(stock=new_stock, version=old_version + 1)
        )
        await db.commit()

        # 3. 업데이트 성공 여부 확인
        if update_result.rowcount == 1:  # type: ignore[union-attr]
            elapsed = (time.perf_counter() - start) * 1000
            return TransactionResult(
                success=True,
                method="optimistic",
                product_id=product_id,
                old_stock=old_stock,
                new_stock=new_stock,
                retries=retries,
                elapsed_ms=elapsed,
            )

        # 4. 충돌 발생 - 재시도
        retries += 1
        await db.rollback()

    # 최대 재시도 초과
    elapsed = (time.perf_counter() - start) * 1000
    return TransactionResult(
        success=False,
        method="optimistic",
        product_id=product_id,
        old_stock=old_stock,
        new_stock=new_stock,  # 변경 안됨
        retries=retries,
        elapsed_ms=elapsed,
        error="Max retries exceeded",
    )


# ============================================
# D. Serializable 격리 수준
# ============================================
@router.post("/decrement/serializable", response_model=TransactionResult)
async def decrement_serializable(
    product_id: int = 1,
    quantity: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """Serializable 격리 수준으로 재고 차감"""
    start = time.perf_counter()

    try:
        # Serializable 격리 수준 설정
        await db.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
        result = await db.execute(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        old_stock = product.stock
        new_stock = old_stock - quantity
        product.stock = new_stock
        await db.commit()

        elapsed = (time.perf_counter() - start) * 1000
        return TransactionResult(
            success=True,
            method="serializable",
            product_id=product_id,
            old_stock=old_stock,
            new_stock=new_stock,
            elapsed_ms=elapsed,
        )
    except (OperationalError, DBAPIError) as e:
        await db.rollback()
        elapsed = (time.perf_counter() - start) * 1000
        return TransactionResult(
            success=False,
            method="serializable",
            product_id=product_id,
            old_stock=0,
            new_stock=0,
            elapsed_ms=elapsed,
            error=str(e),
        )
