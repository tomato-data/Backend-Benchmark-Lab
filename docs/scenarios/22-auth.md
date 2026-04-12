# 22. 인증 방식 벤치마크 (Auth Benchmark)

> Phase 7: 실제 서비스 패턴 - 인증 오버헤드 측정

---

## 개요

인증 방식별 성능 오버헤드를 측정하여 Stateless(JWT)와 Stateful(Session Store) 인증의 실제 비용을 비교한다.

### 테스트 환경

- **프레임워크**: FastAPI Pragmatic
- **JWT 라이브러리**: python-jose (HS256)
- **Session Store**: Redis
- **DB**: PostgreSQL (사용자 조회)

---

## 인증 방식 비교

### 아키텍처 차이

| 방식 | 토큰 저장 | 검증 방식 | 특징 |
|------|----------|----------|------|
| **No Auth** | - | - | 기준선 측정용 |
| **JWT (Stateless)** | 클라이언트 | 서명 검증 (CPU) | 서버 상태 불필요 |
| **Session (Stateful)** | Redis | Redis 조회 (네트워크) | 즉시 무효화 가능 |

### 요청 흐름

```
17-a No Auth:
  Request → Response

17-b JWT:
  Request → JWT 서명 검증 → DB 조회 → Response

17-c Session:
  Request → Redis 조회 → DB 조회 → Response
```

---

## 벤치마크 결과 (2026-01-17)

### 전체 결과

| 시나리오 | Median | P95 | Throughput | vs No Auth |
|----------|--------|-----|------------|------------|
| **17-a: No Auth** | 0.92ms | 1.48ms | 9,532 req/s | 기준선 |
| **17-b: JWT** | 4.98ms | 22.35ms | 1,283 req/s | **7.4배 느림** |
| **17-c: Session** | 4.75ms | 17.39ms | 1,464 req/s | **6.5배 느림** |

### JWT vs Session 비교

| 메트릭 | JWT | Session | 승자 |
|--------|-----|---------|------|
| Median | 4.98ms | 4.75ms | **Session** (+4.8%) |
| P95 | 22.35ms | 17.39ms | **Session** (+28.5%) |
| Throughput | 1,283 req/s | 1,464 req/s | **Session** (+14.1%) |

---

## 분석

### 예상과 다른 결과

**예상**: JWT(CPU만)가 Session(Redis 네트워크)보다 빠를 것

**실제**: Session이 JWT보다 **14% 빠름**

### 원인 분석

#### 1. JWT 서명 검증 오버헤드

```python
# JWT 검증 (CPU 바운드)
payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```

- HS256 서명 검증은 CPU 집약적
- Python의 GIL로 인해 CPU 바운드 작업이 병목
- python-jose 라이브러리 오버헤드

#### 2. Redis 조회의 효율성

```python
# Redis 조회 (I/O 바운드)
user_id_str = await redis.get(f"session:{token}")
```

- Redis는 메모리 기반으로 매우 빠름 (~0.1ms)
- 비동기 I/O로 다른 요청 처리 가능
- 네트워크 오버헤드가 예상보다 작음

#### 3. DB 조회는 동일

두 방식 모두 사용자 존재 확인을 위해 DB 조회:

```python
result = await db.execute(select(UserModel).where(UserModel.id == user_id))
```

### P95 차이가 큰 이유 (22ms vs 17ms)

- JWT: CPU 바운드 작업이 GIL 경합으로 지연
- Session: I/O 바운드로 비동기 처리 효율적

---

## Stateless vs Stateful 선택 기준

### JWT (Stateless) 선택 시

| 장점 | 단점 |
|------|------|
| ✅ 서버 간 공유 저장소 불필요 | ❌ 즉시 로그아웃 불가 |
| ✅ 수평 확장 용이 | ❌ 토큰 만료까지 유효 |
| ✅ 마이크로서비스에 적합 | ❌ 다중 로그인 제어 어려움 |

**적합한 경우**:
- 마이크로서비스 아키텍처
- 서비스 간 인증 (M2M)
- Redis 인프라 없는 환경

### Session Store (Stateful) 선택 시

| 장점 | 단점 |
|------|------|
| ✅ 즉시 로그아웃 가능 | ❌ Redis 등 공유 저장소 필요 |
| ✅ 다중 로그인 제어 | ❌ 저장소 장애 시 인증 불가 |
| ✅ 이상 탐지 가능 | ❌ 세션 동기화 필요 |
| ✅ **성능 우위 (+14%)** | |

**적합한 경우**:
- 보안이 중요한 서비스 (금융, 의료)
- 즉시 로그아웃이 필요한 서비스
- 동시 접속 제한이 필요한 서비스

---

## 구현 상세

### 엔드포인트

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /api/v1/auth/public` | No Auth 기준선 |
| `POST /api/v1/auth/login/jwt?user_id=N` | JWT 토큰 발급 |
| `GET /api/v1/auth/protected/jwt` | JWT 보호 리소스 |
| `POST /api/v1/auth/login/session?user_id=N` | 세션 토큰 발급 |
| `GET /api/v1/auth/protected/session` | 세션 보호 리소스 |

### 파일 구조

```
src/presentation/api/v1/auth/
├── __init__.py      # 라우터 통합
├── common.py        # 공통 설정 + No Auth 엔드포인트
├── jwt.py           # JWT 인증
└── session.py       # Session 인증
```

### k6 시나리오

```
scenarios/auth/
├── 17-a-auth-none.js     # No Auth 기준선
├── 17-b-auth-jwt.js      # JWT 인증
└── 17-c-auth-session.js  # Session 인증
```

---

## 핵심 인사이트

1. **Session이 JWT보다 14% 빠름** (예상과 반대)
2. CPU 바운드(JWT 서명)가 I/O 바운드(Redis)보다 Python에서 비효율적
3. 인증 추가 시 처리량 **6.5~7.4배 감소** (인증 오버헤드)
4. 보안 요구사항에 따라 선택, 성능은 Session이 우위

---

## 향후 개선

- [ ] RS256 (RSA) vs HS256 비교
- [ ] Redis Cluster 환경 테스트
- [ ] 토큰 갱신(Refresh Token) 오버헤드 측정
- [ ] Phase 10에서 암호 해시(Argon2 vs bcrypt) 비교

---

_Last updated: 2026-01-17_
