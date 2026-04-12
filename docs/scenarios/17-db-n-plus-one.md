# 11-db-n-plus-one 시나리오

## 개요

ORM 사용 시 흔히 발생하는 N+1 문제를 재현하고, 다양한 로딩 전략(Lazy, Eager, Subquery)의 성능 차이를 측정한다.

---

## 측정 목표

- N+1 문제의 실제 성능 영향 정량화
- Lazy Loading vs Eager Loading(joinedload) vs Subquery Loading(selectinload) 비교
- SQLAlchemy async 환경에서의 N+1 해결 패턴 학습

---

## N+1 문제란?

```python
# N+1 문제 발생 패턴
authors = session.query(Author).limit(20).all()  # 1번 쿼리
for author in authors:
    print(author.posts)  # 각 author마다 추가 쿼리 (N번)
# 총 1 + 20 = 21번 쿼리 실행!
```

| 로딩 전략 | 쿼리 수 | 설명 |
|-----------|---------|------|
| Lazy (N+1) | 1 + N | 관계 접근 시마다 개별 쿼리 |
| Eager (JOIN) | 1 | LEFT JOIN으로 한 번에 로드 |
| Subquery (IN) | 2 | IN 절로 관계 데이터 일괄 로드 |

---

## 테이블 구조

### Authors 테이블 (1,000건)

```sql
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    bio TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Posts 테이블 (8,000건, author당 8개)

```sql
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    author_id INTEGER NOT NULL REFERENCES authors(id),
    title VARCHAR(200) NOT NULL,
    content TEXT,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- FK 인덱스 (Eager loading 성능에 필수)
CREATE INDEX idx_posts_author_id ON posts(author_id);
```

---

## 엔드포인트 스펙

```
GET /n-plus-one/lazy?limit=20&offset=0
GET /n-plus-one/eager?limit=20&offset=0
GET /n-plus-one/subquery?limit=20&offset=0
```

모든 엔드포인트는 동일한 응답 형식:

```json
[
  {
    "id": 1,
    "name": "Author1",
    "email": "author1@benchmark.com",
    "bio": "Bio for author 1...",
    "created_at": "2025-11-15T13:32:03",
    "posts": [
      {
        "id": 1,
        "title": "Post 1 by Author 1",
        "content": "Content...",
        "view_count": 6200,
        "created_at": "2025-11-16T13:32:03"
      }
    ]
  }
]
```

---

## 구현 코드

### SQLAlchemy 모델 (Relationship 정의)

```python
class AuthorModel(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    bio: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationship (lazy loading by default)
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

    author: Mapped["AuthorModel"] = relationship("AuthorModel", back_populates="posts")
```

### 라우터 구현

#### Lazy Loading (N+1 시뮬레이션)

```python
@router.get("/lazy", response_model=list[AuthorWithPostsResponse])
async def get_authors_lazy(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    # 1. Authors 조회 (1번 쿼리)
    authors_query = select(AuthorModel).offset(offset).limit(limit)
    result = await db.execute(authors_query)
    authors = result.scalars().all()

    # 2. 각 author마다 개별 posts 쿼리 (N번 쿼리!)
    response = []
    for author in authors:
        posts_query = select(PostModel).where(PostModel.author_id == author.id)
        posts_result = await db.execute(posts_query)
        posts = posts_result.scalars().all()
        # dict로 변환하여 반환 (async SQLAlchemy lazy loading 우회)
        response.append({...})

    return response
```

> **참고**: Async SQLAlchemy는 의도적으로 lazy loading을 차단함 (MissingGreenlet 에러).
> 이는 "숨겨진 I/O"를 방지하기 위한 설계. 벤치마크를 위해 수동으로 N+1을 시뮬레이션함.

#### Eager Loading (joinedload)

```python
@router.get("/eager", response_model=list[AuthorWithPostsResponse])
async def get_authors_eager(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(AuthorModel)
        .options(joinedload(AuthorModel.posts))  # LEFT JOIN
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    authors = result.unique().scalars().all()  # unique() 필수!
    return authors
```

#### Subquery Loading (selectinload)

```python
@router.get("/subquery", response_model=list[AuthorWithPostsResponse])
async def get_authors_subquery(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(AuthorModel)
        .options(selectinload(AuthorModel.posts))  # IN 절
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    authors = result.scalars().all()
    return authors
```

---

## k6 스크립트

```javascript
// scenarios/db-advanced/11-db-n-plus-one.js
import http from "k6/http";
import { check, group } from "k6";
import { BASE_URL, defaultOptions } from "../config.js";

const LIMIT = 20;
const MAX_AUTHORS = 1000;

export const options = {
  ...defaultOptions,
  thresholds: {
    "group_duration{group:::A. Lazy Loading (N+1)}": ["p(95)<500"],
    "group_duration{group:::B. Eager Loading (JOIN)}": ["p(95)<100"],
    "group_duration{group:::C. Subquery Loading (IN)}": ["p(95)<100"],
  },
};

export default function () {
  // 랜덤 offset으로 DB 캐시 영향 분산
  const randomOffset = Math.floor(Math.random() * (MAX_AUTHORS - LIMIT));

  group("A. Lazy Loading (N+1)", function () {
    const res = http.get(
      `${BASE_URL}/n-plus-one/lazy?limit=${LIMIT}&offset=${randomOffset}`
    );
    check(res, {
      "lazy status 200": (r) => r.status === 200,
      "lazy has authors": (r) => r.json().length > 0,
      "lazy has posts": (r) => r.json()[0].posts.length > 0,
    });
  });

  group("B. Eager Loading (JOIN)", function () {
    const res = http.get(
      `${BASE_URL}/n-plus-one/eager?limit=${LIMIT}&offset=${randomOffset}`
    );
    check(res, { "eager status 200": (r) => r.status === 200, ... });
  });

  group("C. Subquery Loading (IN)", function () {
    const res = http.get(
      `${BASE_URL}/n-plus-one/subquery?limit=${LIMIT}&offset=${randomOffset}`
    );
    check(res, { "subquery status 200": (r) => r.status === 200, ... });
  });
}
```

---

## 실행 방법

```bash
# 서버 실행
docker compose --profile fastapi-pragmatic up -d

# DB 시드 데이터 확인
# - authors: 1,000건
# - posts: 8,000건 (author당 8개)
cat scripts/init_db.sql | docker compose exec -T postgres psql -U benchmark -d benchmark

# k6 테스트 실행
k6 run scenarios/db-advanced/11-db-n-plus-one.js
```

---

## 벤치마크 결과 (2026-01-03)

### 환경

- 데이터: authors 1,000건, posts 8,000건
- VUs: 10
- Duration: 30s
- Limit: 20건/요청
- Offset: 랜덤 (0~980)

### 로딩 전략별 성능 비교

| 로딩 전략 | 쿼리 수 | p(95) | Lazy 대비 |
|-----------|---------|-------|-----------|
| **Lazy (N+1)** | 1 + 20 = 21 | 102.71ms | 1.0x (기준) |
| **Eager (JOIN)** | 1 | 24.86ms | **4.1x 빠름** |
| **Subquery (IN)** | 2 | 27.99ms | **3.7x 빠름** |

### 전체 HTTP 메트릭

| 메트릭 | 값 |
|--------|-----|
| http_req_duration (avg) | 31.93ms |
| http_req_duration (med) | 13.75ms |
| http_req_duration (p95) | 84.58ms |
| http_req_duration (max) | 179.24ms |
| http_reqs | 9,273 (308/s) |
| iterations | 3,091 (103/s) |
| 성공률 | 100% (27,819 checks) |
| data_received | 316 MB (11 MB/s) |

### 모든 체크 통과

```
✓ lazy status 200
✓ lazy has authors
✓ lazy has posts
✓ eager status 200
✓ eager has authors
✓ eager has posts
✓ subquery status 200
✓ subquery has authors
✓ subquery has posts
```

---

## 핵심 인사이트

### 1. N+1의 실제 비용

- 쿼리 수: 21번 vs 1번 (21배 차이)
- 응답 시간: 102.71ms vs 24.86ms (**4.1배 차이**)
- 쿼리 수 증가가 그대로 응답 시간에 반영되지는 않음 (DB 캐시, 커넥션 풀 재사용)
- 그러나 **무시할 수 없는 오버헤드** 발생

### 2. Eager vs Subquery

| 비교 항목 | Eager (joinedload) | Subquery (selectinload) |
|-----------|-------------------|------------------------|
| 쿼리 수 | 1번 | 2번 |
| p(95) | 24.86ms | 27.99ms |
| 장점 | 최소 쿼리 | 중복 데이터 없음 |
| 단점 | 카테시안 곱 (중복) | 추가 쿼리 1회 |
| 권장 상황 | 1:1, 1:Few 관계 | 1:Many 관계 |

### 3. Async SQLAlchemy의 N+1 방지

```python
# Sync SQLAlchemy - N+1 발생 가능 (암묵적 I/O)
for author in authors:
    print(author.posts)  # 자동으로 쿼리 발생

# Async SQLAlchemy - 에러 발생!
for author in authors:
    print(author.posts)  # MissingGreenlet 에러
# → 명시적 로딩 강제 (설계 의도)
```

> Async SQLAlchemy는 의도적으로 lazy loading을 차단하여 "숨겨진 I/O"를 방지함.
> 이는 N+1 문제를 **컴파일 타임에** 발견하게 해주는 장점이 있음.

### 4. 실무 적용 가이드

| 상황 | 권장 전략 |
|------|----------|
| 목록 조회 + 연관 데이터 | `selectinload` (subquery) |
| 단건 조회 + 연관 데이터 | `joinedload` (eager) |
| 연관 데이터 불필요 | 로딩 옵션 없이 기본 쿼리 |
| 대량 데이터 (1000건+) | `selectinload` + 페이지네이션 |

### 5. 코드 패턴

```python
# 안티패턴: N+1 발생
authors = await db.execute(select(Author))
for author in authors:
    # 각 author마다 추가 쿼리!
    posts = await db.execute(select(Post).where(Post.author_id == author.id))

# 권장: Eager Loading
authors = await db.execute(
    select(Author).options(joinedload(Author.posts))
)

# 권장: Subquery Loading (1:Many에 적합)
authors = await db.execute(
    select(Author).options(selectinload(Author.posts))
)
```

---

## 다음 단계

- 12-db-bulk-operations: 대량 INSERT/UPDATE (1000건+)
- 13-db-transactions: 복합 트랜잭션 (락 경합)

---

_Last updated: 2026-01-03_
