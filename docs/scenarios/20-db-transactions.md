# 20. DB Transactions (시나리오 13)

> 트랜잭션 락 경합(Lock Contention) 성능 및 데이터 정합성 비교

## 목적

동시성 환경에서 다양한 락 전략의 성능과 안전성 비교

## 시나리오: 재고 차감

```
10명이 동시에 같은 상품의 재고 1개씩 차감 요청
→ 초기 재고 1000개 → 정상이면 결과도 일관성 있어야 함
→ 락 없으면 Lost Update 발생 (재고가 마이너스가 될 수도!)
```

## 비교 포인트

| 방식 | 설명 | 특징 |
|------|------|------|
| A. No Lock | 락 없이 UPDATE | 빠르지만 Lost Update 발생 |
| B. Pessimistic | `SELECT ... FOR UPDATE` | 다른 트랜잭션 대기 |
| C. Optimistic | Version 컬럼 체크 | 충돌 시 재시도 |
| D. Serializable | 트랜잭션 격리 수준 최고 | DB 레벨 직렬화 |

## 테이블 스키마

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 0,  -- Optimistic Lock용
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/transactions/products/{id}` | GET | 상품 조회 |
| `/transactions/reset` | POST | 모든 상품 재고 1000으로 리셋 |
| `/transactions/decrement/no-lock` | POST | 락 없이 차감 |
| `/transactions/decrement/pessimistic` | POST | FOR UPDATE로 차감 |
| `/transactions/decrement/optimistic` | POST | Version 체크 차감 |
| `/transactions/decrement/serializable` | POST | Serializable 격리 수준 |

## 테스트 격리 전략

각 락 전략은 **서로 다른 상품**을 사용하여 독립적으로 테스트됩니다:

```javascript
const PRODUCTS = {
  noLock: 1,       // Product 1: No Lock 테스트용
  pessimistic: 2,  // Product 2: Pessimistic Lock 테스트용
  optimistic: 3,   // Product 3: Optimistic Lock 테스트용
  serializable: 4, // Product 4: Serializable 테스트용
};
```

이렇게 격리하면:
- 각 전략의 **순수 성능**을 측정 가능
- 다른 전략의 락이 간섭하지 않음
- teardown에서 각 상품별 최종 재고 확인 가능

## 벤치마크 결과 (2026-01-04, 격리 테스트)

### 테스트 환경
- k6: 10 VUs, 30s duration, 7388 iterations
- 각 VU가 **각 전략별 전용 상품**에 동시 요청 → 순수 락 경합 측정

### 결과

| 방식 | Product | 최종 재고 | 성공 횟수 | 성공률 | p(95) | 데이터 정합성 |
|------|---------|----------|----------|--------|-------|--------------|
| No Lock | 1 | -3977 | 4977 | 100% | 9.4ms | ❌ **32.6% Lost Update** |
| **Pessimistic** | 2 | **-6388** | **7388** | **100%** | **11ms** | ✅ **100% 정확** |
| Optimistic | 3 | -4261 | 5261 | 71% | 33.9ms | ✅ (성공 시) |
| Serializable | 4 | -4166 | 5166 | 69% | 10.8ms | ✅ (성공 시) |

### 데이터 정합성 검증

```
요청 횟수: 7388회 (10 VUs × 30초)
초기 재고: 1000

예상 최종 재고: 1000 - 7388 = -6388

실제 결과:
- Pessimistic: -6388 ✅ (100% 정확)
- No Lock:     -3977 ❌ (2411개 Lost Update, 32.6% 손실)
- Optimistic:  -4261 (5261회 성공, 2127회 충돌)
- Serializable: -4166 (5166회 성공, 2222회 직렬화 실패)
```

### 성능 비교 차트

```
데이터 정합성 (실제 반영된 차감 횟수)
─────────────────────────────────────────────────────
Pessimistic  │████████████████████████████████████████│ 7388 (100%) ✅
Optimistic   │████████████████████████████            │ 5261 (71%)
Serializable │███████████████████████████             │ 5166 (69%)
No Lock      │██████████████████████████              │ 4977 (67%) ⚠️ 데이터 손실!
─────────────────────────────────────────────────────

응답 시간 p(95)
─────────────────────────────────────────────────────
No Lock      │█████████                               │ 9.4ms
Serializable │███████████                             │ 10.8ms
Pessimistic  │███████████                             │ 11.0ms ✅
Optimistic   │██████████████████████████████████      │ 33.9ms
─────────────────────────────────────────────────────
```

## 핵심 인사이트

### 1. No Lock은 절대 사용 금지

```python
# ❌ 이렇게 하면 안 됨
product = await db.get(Product, id)
product.stock -= 1  # Race Condition!
await db.commit()
```

- 빠르지만 **데이터 정합성 보장 안 됨**
- 재고가 마이너스가 되는 심각한 버그 발생

### 2. Pessimistic Lock이 동시성 높은 환경에서 최적

```python
# ✅ 권장
result = await db.execute(
    select(Product)
    .where(Product.id == id)
    .with_for_update()  # 다른 트랜잭션 대기
)
```

- **100% 성공률 + 빠른 응답** (13ms)
- 락 대기 시간이 있지만, 데이터 안전성 보장

### 3. Optimistic Lock은 충돌 적은 환경에서만

```python
# 충돌 감지
update_result = await db.execute(
    update(Product)
    .where(Product.id == id)
    .where(Product.version == old_version)  # 버전 체크
    .values(stock=new_stock, version=old_version + 1)
)
if update_result.rowcount == 0:
    # 충돌! 재시도 필요
```

- 충돌률 29% → 재시도 오버헤드로 느려짐 (p95: 33.9ms)
- **충돌이 드문 환경**에서만 효율적 (예: 사용자별 데이터)

### 4. Serializable은 격리 환경에서 의외로 선방

```python
await db.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
```

- 격리 테스트에서 **69% 성공률** (이전 혼합 테스트 0.6%에서 대폭 개선)
- 다른 락 전략과 경합이 없으면 상당히 쓸만함
- 여전히 Pessimistic보다는 낮은 성공률

## 실무 적용 가이드

| 상황 | 권장 방식 |
|------|----------|
| 재고 차감, 좌석 예약 | **Pessimistic Lock** |
| 사용자 프로필 수정 | Optimistic Lock |
| 금융 거래 | Pessimistic + 트랜잭션 로그 |
| 읽기 전용 집계 | Serializable (선택적) |

## 구현 코드 핵심

### Pessimistic Lock (FOR UPDATE)

```python
@router.post("/decrement/pessimistic")
async def decrement_pessimistic(product_id: int, db: AsyncSession):
    result = await db.execute(
        select(ProductModel)
        .where(ProductModel.id == product_id)
        .with_for_update()  # 핵심!
    )
    product = result.scalar_one()
    product.stock -= 1
    await db.commit()
```

### Optimistic Lock (Version 체크)

```python
@router.post("/decrement/optimistic")
async def decrement_optimistic(product_id: int, db: AsyncSession):
    while retries < max_retries:
        product = await db.get(ProductModel, product_id)
        old_version = product.version

        result = await db.execute(
            update(ProductModel)
            .where(ProductModel.id == product_id)
            .where(ProductModel.version == old_version)
            .values(stock=product.stock - 1, version=old_version + 1)
        )

        if result.rowcount == 1:
            await db.commit()
            return  # 성공

        retries += 1  # 충돌, 재시도
```

## 학습 포인트

1. **Lost Update**: 락 없이 동시 수정하면 **32.6% 데이터 손실** 발생
2. **Pessimistic Lock**: 동시성 높은 환경에서 **유일하게 100% 정확**
3. **Optimistic vs Serializable**: 격리 환경에서 비슷한 성공률 (69-71%)
4. **테스트 격리의 중요성**: 혼합 테스트 vs 격리 테스트 결과가 크게 다름
5. **트레이드오프**: 안전성 ↔ 성능 (Pessimistic이 최적 균형점)

---

_Last updated: 2026-01-04 (격리 테스트 결과 반영)_
