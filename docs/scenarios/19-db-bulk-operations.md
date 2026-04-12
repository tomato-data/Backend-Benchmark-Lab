# 19. DB Bulk Operations (시나리오 12)

> 대량 INSERT/UPDATE 시 다양한 방식의 성능 비교

## 목적

ORM의 개별 처리 vs 배치 처리 vs Raw SQL 성능 차이 측정

## 비교 포인트

| 방식 | 설명 | 쿼리/커밋 수 |
|------|------|-------------|
| A. Individual INSERT | 1건씩 add + commit | N회 |
| B. Batch INSERT | add_all + 1회 commit | 1회 |
| C. Raw INSERT | VALUES (...), (...) | 1회 |
| D. Individual UPDATE | 1건씩 update + commit | N회 |
| E. Bulk UPDATE | CASE WHEN + WHERE IN | 1회 |

## 테이블 스키마

```sql
CREATE TABLE bulk_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    value INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/bulk-operations/cleanup` | DELETE | 테이블 초기화 (TRUNCATE) |
| `/bulk-operations/insert-individual?count=1000` | POST | 1건씩 개별 INSERT |
| `/bulk-operations/insert-batch?count=1000` | POST | add_all로 배치 INSERT |
| `/bulk-operations/insert-raw?count=1000` | POST | Raw SQL INSERT |
| `/bulk-operations/update-individual?count=1000` | POST | 1건씩 개별 UPDATE |
| `/bulk-operations/update-bulk?count=1000` | POST | CASE WHEN Bulk UPDATE |

## 벤치마크 결과 (2026-01-04)

### 테스트 환경
- k6: 10 VUs, 30s duration
- 건수: 1000건/요청

### 결과 (p95 기준)

| 방식 | p(95) | Individual 대비 |
|------|-------|-----------------|
| A. Individual INSERT | **2.98s** | 기준 |
| B. Batch INSERT | 38.86ms | **77배 빠름** |
| C. Raw INSERT | 15.91ms | **187배 빠름** |
| D. Individual UPDATE | **2.96s** | 기준 |
| E. Bulk UPDATE | 23.86ms | **124배 빠름** |

### 성능 비교 차트

```
INSERT 성능 (p95, 1000건)
─────────────────────────────────────────────────────
Individual │████████████████████████████████████████│ 2980ms
Batch      │█                                       │ 39ms
Raw        │                                        │ 16ms
─────────────────────────────────────────────────────

UPDATE 성능 (p95, 1000건)
─────────────────────────────────────────────────────
Individual │████████████████████████████████████████│ 2960ms
Bulk       │█                                       │ 24ms
─────────────────────────────────────────────────────
```

## 핵심 인사이트

### 1. commit 횟수가 결정적
- Individual: 1000번 commit → ~3초
- Batch/Raw: 1번 commit → 수십 ms
- **트랜잭션 오버헤드가 성능의 99%를 차지**

### 2. ORM vs Raw SQL 오버헤드
- Batch (add_all): 38.86ms
- Raw (VALUES): 15.91ms
- **ORM 오버헤드: 약 2.4배**

### 3. UPDATE도 동일 패턴
- 개별 UPDATE vs CASE WHEN 패턴
- Bulk UPDATE가 124배 빠름

## 구현 코드 핵심

### Batch INSERT (add_all)
```python
items = [BulkItemModel(name=f"item_{i}", value=i) for i in range(count)]
db.add_all(items)
await db.commit()  # 1회만 commit
```

### Raw INSERT (VALUES)
```python
values = ", ".join([f"('item_{i}', {i}, NOW())" for i in range(count)])
query = text(f"INSERT INTO bulk_items (name, value, created_at) VALUES {values}")
await db.execute(query)
await db.commit()
```

### Bulk UPDATE (CASE WHEN)
```python
case_when = " ".join([f"WHEN id = {i} THEN {i * 10}" for i in ids])
query = text(f"""
    UPDATE bulk_items
    SET value = CASE {case_when} END
    WHERE id IN ({','.join(map(str, ids))})
""")
await db.execute(query)
await db.commit()
```

## 실무 적용 가이드

| 상황 | 권장 방식 |
|------|----------|
| 소량 (< 100건) | Batch (add_all) - 코드 가독성 우선 |
| 중량 (100~10,000건) | Raw SQL - 성능과 유지보수 균형 |
| 대량 (> 10,000건) | PostgreSQL COPY 또는 배치 분할 |

## 학습 포인트

1. **트랜잭션 단위**: commit 횟수가 성능에 가장 큰 영향
2. **ORM 오버헤드**: 편의성 vs 성능 트레이드오프 (2~3배 차이)
3. **Bulk UPDATE 패턴**: CASE WHEN으로 단일 쿼리 처리 가능
4. **실무 선택 기준**: 건수와 빈도에 따라 적절한 방식 선택

---

_Last updated: 2026-01-04_
