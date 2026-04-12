# DB 초기화 스크립트

## 개요

벤치마크 테스트를 위한 더미 데이터 생성. 모든 백엔드 구현체가 동일한 데이터로 테스트되어야 공정한 비교가 가능하다.

---

## 파일 위치

```
implementations/
├── scripts/
│   └── init_db.sql    # 공용 초기화 스크립트
├── docker-compose.yml
└── python-fastapi/
```

특정 백엔드가 아닌 `implementations/scripts/`에 배치하여 공용임을 명확히 한다.

---

## 스크립트 내용

```sql
-- implementations/scripts/init_db.sql
DELETE FROM users;

INSERT INTO users (name, email)
SELECT
    'User' || g,
    'user' || g || '@benchmark.test
FROM generate_series(1, 1000) AS g;
```

### 설명

| 구문 | 역할 |
|-----|------|
| `DELETE FROM users` | 기존 데이터 초기화 |
| `generate_series(1, 1000)` | PostgreSQL 내장 함수, 1~1000 시퀀스 생성 |
| `'User' \|\| g` | 문자열 연결 (User1, User2, ...) |

---

## 실행 방법

```bash
cd implementations

# PostgreSQL 컨테이너에 SQL 전달
cat scripts/init_db.sql | docker compose exec -T postgres psql -U benchmark -d benchmark
```

### 옵션 설명

| 옵션 | 의미 |
|-----|------|
| `exec -T` | TTY 할당 없이 실행 (파이프 사용 시 필요) |
| `-U benchmark` | PostgreSQL 사용자 |
| `-d benchmark` | 데이터베이스 이름 |

---

## 데이터 양 선택 근거

| 규모 | 행 수 | 비고 |
|-----|------|------|
| 소규모 | 100 | 테스트용 |
| **선택** | **1,000** | 벤치마크 적정 |
| 대규모 | 10,000+ | 페이지네이션 필요 |

1,000개는 전체 반환(`GET /users`)해도 응답 크기가 적절하며, DB 성능 차이를 측정하기에 충분하다.
