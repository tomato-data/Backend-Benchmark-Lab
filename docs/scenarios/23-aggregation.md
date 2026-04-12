# 23. 집계 쿼리 벤치마크 (Aggregation)

> Phase 7: 실제 서비스 패턴 - 시나리오 18
>
> ORM vs Raw SQL 집계 쿼리 성능 비교 + 인덱스 효과 검증

---

## 1. 개요

### 목적

- **ORM vs Raw SQL**: 집계(COUNT, SUM, AVG, GROUP BY) 시 성능 차이 측정
- **인덱스 효과**: 인덱스 유무에 따른 집계 쿼리 성능 변화 검증
- **쿼리 분리 vs 합침**: 같은 결과를 얻을 때 쿼리를 분리하는 것과 하나로 합치는 것의 차이

### 대상 테이블

| 테이블 | 행 수 | 용도 |
|--------|-------|------|
| `users_wide` | 100,000건 | COUNT, GROUP BY (country, status) |
| `authors` | 1,000건 | JOIN + GROUP BY |
| `posts` | ~21,000건 | JOIN + GROUP BY |

### 엔드포인트 (6개)

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /aggregation/count/orm` | COUNT 3종 비교 (ORM, 쿼리 3개 분리) |
| `GET /aggregation/count/raw` | COUNT 3종 비교 (Raw SQL, 쿼리 1개 합침) |
| `GET /aggregation/stats/country/orm` | 국가별 통계 GROUP BY (ORM) |
| `GET /aggregation/stats/country/raw` | 국가별 통계 GROUP BY (Raw SQL) |
| `GET /aggregation/stats/author/orm` | 작가별 통계 JOIN + GROUP BY (ORM) |
| `GET /aggregation/stats/author/raw` | 작가별 통계 JOIN + GROUP BY (Raw SQL) |

---

## 2. 구현 핵심

### Count ORM - 쿼리 3개 분리

```python
# 각각 별도 쿼리로 실행
result_star = await db.execute(select(func.count()).select_from(UserWideModel))
result_id = await db.execute(select(func.count(UserWideModel.id)))
result_distinct = await db.execute(select(func.count(func.distinct(UserWideModel.status))))
```

### Count Raw - 쿼리 1개 합침

```sql
SELECT
    COUNT(*) as count_star,
    COUNT(id) as count_id,
    COUNT(DISTINCT status) as count_distinct_status
FROM users_wide
```

**같은 결과**를 반환하지만, 쿼리 구조가 근본적으로 다르다.

---

## 3. 벤치마크 결과

### k6 설정

| 항목 | 값 |
|-----|---|
| VUs | 10 |
| Duration | 30s |
| 프레임워크 | FastAPI Pragmatic |

### 3-1. 인덱스 추가 전 (Before) - 2026-01-25

| 시나리오 | p(95) | Threshold | 결과 |
|---------|-------|-----------|------|
| A. Count ORM | 373.87ms | <100ms | ❌ |
| B. Count Raw | 299.72ms | <50ms | ❌ |
| C. Country Stats ORM | 205.27ms | <200ms | ❌ |
| D. Country Stats Raw | 203.06ms | <100ms | ❌ |
| E. Author Stats ORM | 109.4ms | <200ms | ✅ |
| F. Author Stats Raw | 100.75ms | <100ms | ❌ |

**이상 현상**: COUNT가 JOIN보다 느림, ORM vs Raw 차이 미미

### 3-2. 인덱스 추가 후 (After) - 2026-02-07

추가한 인덱스:

```sql
CREATE INDEX idx_users_wide_country ON users_wide(country);
CREATE INDEX idx_users_wide_status ON users_wide(status);
```

| 시나리오 | p(95) | Threshold | 결과 |
|---------|-------|-----------|------|
| A. Count ORM | 196.69ms | <100ms | ❌ |
| B. Count Raw | 290.45ms | <50ms | ❌ |
| C. Country Stats ORM | 199.3ms | <200ms | ✅ |
| D. Country Stats Raw | 198.37ms | <100ms | ❌ |
| E. Author Stats ORM | 108.2ms | <200ms | ✅ |
| F. Author Stats Raw | 105.54ms | <100ms | ❌ |

### 3-3. Before vs After 비교

| 시나리오 | Before | After | 변화 |
|---------|--------|-------|------|
| Count ORM | 373.87ms | **196.69ms** | **-47% (1.9배 개선)** |
| Count Raw | 299.72ms | 290.45ms | -3% (거의 변화 없음) |
| Country ORM | 205.27ms | 199.3ms | -3% |
| Country Raw | 203.06ms | 198.37ms | -2% |
| Author ORM | 109.4ms | 108.2ms | -1% |
| Author Raw | 100.75ms | 105.54ms | +5% (오차 범위) |

**핵심 발견**: 인덱스가 **Count ORM만 극적으로 개선**하고, Count Raw에는 거의 영향 없음.

---

## 4. EXPLAIN ANALYZE 분석

### 4-1. Count Raw (합친 쿼리, 1개)

```sql
SELECT COUNT(*), COUNT(id), COUNT(DISTINCT status) FROM users_wide;
```

```
Aggregate  (actual time=55.882..55.883)
  → Sort  (Sort Method: external merge  Disk: 2160kB)  (actual time=47.919..51.779)
      Sort Key: status
      → Seq Scan on users_wide  (actual time=0.009..34.629 rows=100000)
Planning Time: 0.338 ms
Execution Time: 56.086 ms
```

**문제점**:
- **Seq Scan** 강제 사용 (인덱스 무시)
- `COUNT(DISTINCT status)` 때문에 **Sort** 필요
- Sort가 메모리에 안 담겨서 **디스크로 넘침** (external merge, 2160kB)
- 총 **56ms**

### 4-2. Count ORM (분리 쿼리, 3개)

**쿼리 1: `SELECT COUNT(*) FROM users_wide`**

```
Aggregate  (actual time=8.973..8.973)
  → Index Only Scan using idx_users_wide_status  (actual time=0.014..5.255 rows=100000)
      Heap Fetches: 0
Execution Time: 9.016 ms
```

**쿼리 2: `SELECT COUNT(id) FROM users_wide`**

```
Aggregate  (actual time=9.741..9.741)
  → Index Only Scan using users_wide_pkey  (actual time=0.017..6.101 rows=100000)
      Heap Fetches: 0
Execution Time: 9.776 ms
```

**쿼리 3: `SELECT COUNT(DISTINCT status) FROM users_wide`**

```
Aggregate  (actual time=9.346..9.347)
  → Index Only Scan using idx_users_wide_status  (actual time=0.012..4.834 rows=100000)
      Heap Fetches: 0
Execution Time: 9.387 ms
```

**핵심**:
- 3개 모두 **Index Only Scan** (테이블 데이터를 읽지 않음)
- **Heap Fetches: 0** (인덱스만으로 완전히 해결)
- 각 9~10ms, 합계 **~28ms**

### 4-3. Country Stats GROUP BY

```sql
SELECT country, COUNT(id), SUM(login_count), AVG(login_count)
FROM users_wide GROUP BY country ORDER BY user_count DESC LIMIT 10;
```

```
Limit  (actual time=11.189..12.542)
  → Sort  (Sort Method: top-N heapsort  Memory: 25kB)
      → Finalize GroupAggregate
          → Gather Merge (Workers Planned: 2, Workers Launched: 2)
              → Partial HashAggregate
                  → Parallel Seq Scan on users_wide  (rows=33333 per worker)
Execution Time: 12.649 ms
```

- **Parallel Seq Scan** 사용 (2 workers)
- SUM, AVG가 필요하므로 login_count 컬럼도 읽어야 함 → 인덱스만으로 불가
- 그래도 병렬 처리로 **13ms**

### 4-4. Author Stats JOIN + GROUP BY

```sql
SELECT a.id, a.name, COUNT(p.id), SUM(p.view_count), AVG(p.view_count)
FROM authors a JOIN posts p ON a.id = p.author_id
GROUP BY a.id, a.name ORDER BY post_count DESC LIMIT 10;
```

```
Limit  (actual time=6.300..6.302)
  → Sort  (Sort Method: top-N heapsort  Memory: 25kB)
      → HashAggregate
          → Hash Join (Hash Cond: p.author_id = a.id)
              → Seq Scan on posts  (rows=21000)
              → Hash → Seq Scan on authors  (rows=1000)
Execution Time: 6.384 ms
```

- **Hash Join** 사용 (가장 효율적인 Join 방식)
- 데이터 규모가 작아서 (authors 1K + posts 21K) **6ms**

---

## 5. 실행 계획 비교 요약

| 쿼리 | 실행 계획 | Scan 방식 | 실행 시간 |
|------|----------|----------|----------|
| Count Raw (합침) | Aggregate → Sort → Seq Scan | **Seq Scan + Disk Sort** | 56ms |
| COUNT(*) 단독 | Aggregate → Index Only Scan | **Index Only Scan** | 9ms |
| COUNT(id) 단독 | Aggregate → Index Only Scan | **Index Only Scan** | 10ms |
| COUNT(DISTINCT status) 단독 | Aggregate → Index Only Scan | **Index Only Scan** | 9ms |
| Country GROUP BY | Parallel Seq Scan + HashAggregate | Parallel Seq Scan | 13ms |
| Author JOIN + GROUP BY | Hash Join + HashAggregate | Seq Scan (소규모) | 6ms |

---

## 6. 핵심 인사이트

### 인사이트 1: "쿼리 1개 = 더 빠르다"는 거짓

| | Raw (1개 합침) | ORM (3개 분리) |
|---|---|---|
| DB 실행 시간 | 56ms | ~28ms (9+10+9) |
| 실행 계획 | Seq Scan + Disk Sort | Index Only Scan × 3 |
| k6 p(95) | 290ms | 197ms |

**이유**: 여러 집계를 하나의 SELECT에 합치면 PostgreSQL이 **하나의 실행 계획만 선택**해야 한다. `COUNT(DISTINCT status)`의 Sort 요구사항 때문에 전체 쿼리가 Seq Scan으로 강제된다.

반면 분리하면 각 쿼리가 **개별 최적화**되어 Index Only Scan을 활용할 수 있다.

### 인사이트 2: 인덱스가 모든 쿼리에 효과적이진 않다

- **Count ORM**: -47% (Index Only Scan 활용)
- **Count Raw**: -3% (Seq Scan 강제, 인덱스 무시)
- **Country GROUP BY**: -2~3% (SUM/AVG 때문에 테이블 데이터 필요 → 인덱스만으로 불충분)

**인덱스가 효과적인 조건**: 쿼리가 인덱스에 포함된 컬럼**만** 필요할 때 (Index Only Scan 가능)

### 인사이트 3: ORM vs Raw SQL 차이보다 쿼리 구조가 중요

ORM/Raw 차이: 1~9% (무의미)
쿼리 구조 차이: **2배** (56ms vs 28ms)

병목은 "ORM 오버헤드"가 아니라 **쿼리 플래너가 선택하는 실행 계획**이다.

### 인사이트 4: 테이블 규모가 성능을 좌우

| 테이블 | 행 수 | 쿼리 실행 시간 |
|--------|-------|-------------|
| authors + posts | 1K + 21K | 6ms |
| users_wide | 100K | 13~56ms |

같은 GROUP BY라도 데이터 규모에 따라 2~9배 차이가 난다.

### 인사이트 5: Disk Sort는 성능의 적

Count Raw 쿼리에서 `Sort Method: external merge Disk: 2160kB`가 발생했다.
PostgreSQL의 `work_mem` (기본 4MB)이 부족하면 Sort가 디스크로 넘치면서 급격한 성능 저하가 일어난다.

---

## 7. 실무 가이드라인

### 집계 쿼리 최적화 체크리스트

1. **인덱스 설계**: GROUP BY, WHERE에 사용되는 컬럼에 인덱스 추가
2. **Index Only Scan 가능성 확인**: SELECT에 인덱스 외 컬럼이 있으면 효과 감소
3. **복합 집계 분리 고려**: 하나의 거대한 쿼리보다 작은 쿼리 여러 개가 빠를 수 있음
4. **EXPLAIN ANALYZE 필수**: 직관과 실제 실행 계획은 다를 수 있음
5. **work_mem 튜닝**: Disk Sort가 발생하면 work_mem 증가 검토

### "ORM이 느리다"는 편견에 대해

이번 실험에서 ORM이 Raw SQL보다 빨랐다. 그 이유는:
- ORM의 "한 쿼리씩 분리" 패턴이 결과적으로 더 나은 실행 계획을 유도
- Raw SQL의 "하나로 합치기" 패턴이 오히려 최적화를 방해

**결론**: ORM/Raw SQL 선택보다 **쿼리가 실제로 어떤 실행 계획을 타는지**가 훨씬 중요하다.

---

## 8. Threshold 분석

현재 threshold는 비현실적이다. EXPLAIN ANALYZE 기준 순수 DB 실행 시간과 k6 p(95) 사이에 큰 괴리가 있다.

| 시나리오 | DB 실행 시간 | k6 p(95) | 괴리 |
|---------|------------|---------|------|
| Count ORM | ~28ms | 197ms | ~7배 |
| Count Raw | 56ms | 290ms | ~5배 |
| Country | 13ms | ~199ms | ~15배 |
| Author | 6ms | ~107ms | ~18배 |

괴리 원인: 네트워크 오버헤드, Pydantic 직렬화, 비동기 컨텍스트 스위칭, 동시 부하(10 VUs), DB 커넥션 풀 대기

Threshold는 실측 기반으로 조정이 필요하다.

---

## 9. 다른 RDBMS에서도 동일한 현상인가?

### 9-1. 범용적 현상: "합친 쿼리가 개별 최적화를 못 받는 것"

이건 PostgreSQL만의 특성이 **아니다**. 근본적인 이유:

> **옵티마이저는 하나의 SELECT에 대해 하나의 실행 계획만 선택한다.**

`COUNT(*)`, `COUNT(id)`, `COUNT(DISTINCT status)`를 합치면, 세 집계를 **모두 만족하는** 단 하나의 스캔 방식을 골라야 한다. `COUNT(DISTINCT)`가 정렬/해싱을 요구하면, 나머지 두 개도 그 방식에 끌려간다.

이 제약은 MySQL(InnoDB), Oracle, SQL Server 모두 동일하다.

### 9-2. RDBMS별 대처 능력 차이

| RDBMS | 차이점 |
|-------|--------|
| **PostgreSQL** | `COUNT(DISTINCT)` → Sort 방식 선호. `work_mem` 부족 시 **Disk Sort** 발생. 이번에 관측한 현상 |
| **MySQL (InnoDB)** | 비슷한 구조. `COUNT(*)` 자체가 PG와 비슷하게 느림 (InnoDB도 MVCC라 모든 행 가시성 체크 필요). 다만 Loose Index Scan으로 DISTINCT를 최적화하는 경우가 있음 |
| **Oracle** | **Bitmap Index Scan**으로 여러 인덱스를 합칠 수 있어서 합친 쿼리도 잘 처리할 가능성이 높음. 옵티마이저가 가장 성숙함 |
| **SQL Server** | **Batch Mode** 처리와 **Columnstore Index**가 있으면 집계 쿼리를 매우 다르게 처리. Hash Aggregate를 적극 사용 |

### 9-3. PostgreSQL에서 "더 두드러지는" 이유

PostgreSQL 특유의 요소가 이번 결과를 악화시켰다:

- **Disk Sort**: PostgreSQL의 `work_mem` 기본값이 **4MB**로 보수적. Sort가 이 한도를 넘으면 디스크로 넘친다. Oracle이나 SQL Server는 메모리 관리가 더 유연해서 같은 상황에서도 in-memory로 처리할 가능성이 높다.
- **COUNT(\*)**: MyISAM(MySQL 레거시 엔진)은 테이블 메타데이터에 행 수를 저장해서 `COUNT(*)`가 O(1)이었다. 하지만 InnoDB와 PostgreSQL은 MVCC 때문에 매번 행을 세야 하므로 이 부분은 동일하다.

### 9-4. 요약

| 현상 | 범용적? |
|------|--------|
| 합친 쿼리가 개별 최적화를 못 받음 | **Yes** — 모든 RDBMS |
| Index Only Scan vs Seq Scan 차이 | **Yes** — 대부분의 RDBMS (covering index 개념은 범용) |
| Disk Sort로 인한 급격한 성능 저하 | **PostgreSQL에서 더 심함** — work_mem 기본값이 보수적 |
| "3개 분리가 1개 합침보다 빠름" | **경우에 따라** — Oracle은 합쳐도 잘 처리할 수 있음 |

**결론**: "옵티마이저가 합친 쿼리에 하나의 실행 계획만 쓰는 것"은 범용적 제약이지만, **PostgreSQL의 보수적인 메모리 설정(work_mem)이 Disk Sort를 유발**해서 차이가 더 극적으로 드러났다.

---

## 10. 쿼리 구조 차이를 해소하는 방법

### 레벨 1: DB 설정 튜닝 (가장 간단)

이번 케이스의 직접적 원인은 Disk Sort였다. `work_mem`을 올리면 합친 쿼리도 빨라진다.

```sql
-- 세션 단위로 work_mem 올리기
SET LOCAL work_mem = '64MB';
SELECT COUNT(*), COUNT(id), COUNT(DISTINCT status) FROM users_wide;
```

이걸로 Disk Sort → In-Memory Sort로 바뀌면 합친 쿼리도 충분히 빨라질 수 있다.
**코드를 안 건드리고도** 해결 가능한 경우가 있다는 뜻이다.

### 레벨 2: 쿼리 구조 변경

"쿼리를 잘 쓰는 것"은 Raw SQL이냐 ORM이냐의 문제가 아니라, **옵티마이저에게 힌트를 주는 구조**를 만드는 것이다.

예를 들어 합친 쿼리를 서브쿼리로 분리하면:

```sql
-- DISTINCT를 포함한 각 집계를 별도 서브쿼리로 분리
SELECT
    (SELECT COUNT(*) FROM users_wide) as count_star,
    (SELECT COUNT(id) FROM users_wide) as count_id,
    (SELECT COUNT(DISTINCT status) FROM users_wide) as count_distinct_status;
```

이러면 **1번의 HTTP 요청에 1개의 SQL**이지만, PostgreSQL이 각 서브쿼리를 **개별 최적화**할 수 있다. ORM의 "3개 분리"와 Raw SQL의 "1개 합침"의 장점을 둘 다 가져가는 구조다.

이건 ORM으로도 똑같이 작성할 수 있다:

```python
# ORM에서 scalar subquery 사용
from sqlalchemy import select, func

sub_star = select(func.count()).select_from(UserWideModel).scalar_subquery()
sub_id = select(func.count(UserWideModel.id)).scalar_subquery()
sub_distinct = select(func.count(func.distinct(UserWideModel.status))).scalar_subquery()

result = await db.execute(select(sub_star, sub_id, sub_distinct))
```

### 레벨 3: 아키텍처 레벨

실시간 집계 자체를 피하는 방법:

- **Materialized View**: 주기적으로 집계를 미리 계산해두는 뷰
- **Summary Table**: 이벤트 발생 시 카운터를 증감 (예: 사용자 가입 시 country별 카운트 +1)
- **캐싱**: 시나리오 15~16에서 검증한 Redis 캐시 (10배 이상 빠름)

### 최적화 판단 순서

```
EXPLAIN ANALYZE로 병목 확인
     ↓
DB 설정으로 해결 가능? (work_mem, shared_buffers 등)
     ↓
인덱스로 해결 가능? (Index Only Scan 유도)
     ↓
쿼리 구조로 해결 가능? (서브쿼리 분리, CTE)
     ↓
아키텍처로 해결? (캐시, Materialized View, Summary Table)
```

**핵심**: "Raw SQL로 개발자가 직접 쓰면 빠르다"는 **절반만 맞다**. 진짜 중요한 건 ORM/Raw SQL 선택이 아니라 **EXPLAIN ANALYZE를 읽고 옵티마이저가 뭘 하는지 이해하는 것**이다. 그 이해가 있으면 ORM으로든 Raw SQL로든 동일하게 최적화할 수 있다.

이번 실험이 정확히 그걸 보여줬다 — ORM이 "우연히" 더 나은 구조를 만들었고, Raw SQL이 "직관적으로" 합쳤다가 오히려 느려졌다.

---

## 11. work_mem 이해

### 동작 원리

```
쿼리 실행 중 Sort / Hash 필요
        ↓
  work_mem 이내? ──→ Yes ──→ In-Memory 처리 (빠름)
        ↓
       No
        ↓
  디스크에 임시 파일 생성 (external merge) ──→ 느림
```

이번 EXPLAIN ANALYZE에서 증거가 관측됐다:

```
-- 합친 쿼리: Disk Sort 발생
Sort Method: external merge  Disk: 2160kB   ← 디스크 사용 (느림)

-- 분리 쿼리: Index Only Scan이라 Sort 자체가 불필요 (빠름)
```

### work_mem의 적용 범위

`work_mem`은 **쿼리 전체가 아니라 각 Sort/Hash 연산마다** 개별 적용된다.

| 상황 | 최대 메모리 사용량 |
|------|-----------------|
| Sort 1개인 쿼리 | work_mem × 1 |
| Sort 3개인 쿼리 | work_mem × 3 |
| 동시 접속 10명, 각 Sort 3개 | work_mem × 3 × 10 |

PostgreSQL이 기본값을 **4MB**로 보수적으로 잡아둔 이유:
무작정 올리면 동시 접속이 많을 때 **서버 메모리가 폭발**할 수 있기 때문이다.

예시: `work_mem = 64MB`, Sort 3개 쿼리, 동시 접속 100명
→ 최대 `64MB × 3 × 100 = 19.2GB` 메모리 사용 가능

따라서 `work_mem` 튜닝은 **동시 접속 수와 쿼리 복잡도를 함께 고려**해야 한다.

---

_작성일: 2026-02-07_
_프레임워크: FastAPI Pragmatic (Python)_
_DB: PostgreSQL 16 (Docker, 2 CPU / 1GB RAM)_
