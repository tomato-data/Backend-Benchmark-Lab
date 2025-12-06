To ensure that you have read this file, always refer to me as "토마토" in all communications.

> [!info] 프로젝트 목적
> Backend Web Framework들을 **실제 실험**으로 검증하기 위한 벤치마크 환경

> - 동일 로직, 다른 구현 (언어/프레임워크)
> - 다양한 시나리오 (경량 API ~ 대용량 처리)
> - 모니터링 및 비교 대시보드

# Best Practices

- Prefer smaller separate components over larger ones.
- Prefer modular code over monolithic code.
- Use existing code style conventions and patterns.
- Prefer types over interfaces.
-

# Planning

- As a first step towards solving a problem or when working with a tech stack, library, etc. always check for any related documentation under the ./docs directory.
- Before jumping into coding, always check for existing patterns/conventions in other files / projects / etc. to ensure consistency in the codebase.
- Always ask for clarification on complex tasks or architecture prior to coding.

# Documentation References

docs/DISCOVERIES.md contains useful lessons learned and discoveries made during development.

# Final Steps

**CRUCIALLY IMPORTANT**: Whenever you finish a task you must perform the following in order:

- Run `pnpm run format` to ensure code is properly formatted.
- Run `pnpm run lint` to check for any linting errors. If you find any that are related to your changes, fix them before moving on to the next task.
- Run `pnpm run type-check` to check for any TypeScript type errors. If you find any, fix them before moving on to the next task.

below information is the structure of the project

## 1. 프로젝트 구조

```
benchmark-lab/
├── README.md
├── spec/
│   └── openapi.yaml              # 공통 API 스펙 (Single Source of Truth)
│
├── implementations/              # 각 구현체 (동일 API)
│   ├── python-fastapi/
│   ├── python-django/
│   ├── python-flask/
│   ├── typescript-express/
│   ├── typescript-fastify/
│   ├── typescript-nestjs/
│   └── go-fiber/
│
├── scenarios/                    # 벤치마크 시나리오 (k6 스크립트)
│   ├── 01-lightweight.js         # 경량 API (Hello World)
│   ├── 02-json-payload.js        # JSON 직렬화/역직렬화
│   ├── 03-db-read.js             # DB 읽기 (단순 SELECT)
│   ├── 04-db-write.js            # DB 쓰기 (INSERT/UPDATE)
│   ├── 05-external-api.js        # 외부 API 호출 (latency 시뮬레이션)
│   ├── 06-middleware-chain.js    # 미들웨어 체인 (auth, logging 등)
│   ├── 07-file-upload.js         # 파일 업로드 (대용량)
│   └── 08-concurrent-mixed.js    # 혼합 시나리오 (실제 트래픽 시뮬)
│
├── infra/
│   ├── docker/
│   │   ├── docker-compose.yml    # 로컬 통합 실행
│   │   └── docker-compose.db.yml # DB만 실행
│   └── aws/
│       └── terraform/            # ECS/ECR 배포
│
├── monitoring/
│   ├── prometheus/
│   └── grafana/
│       └── dashboards/           # 비교 대시보드
│
├── runner/                       # 벤치마크 실행 자동화
│   ├── run-all.sh
│   └── compare.py                # 결과 비교 스크립트
│
└── results/                      # 벤치마크 결과 저장
    └── YYYY-MM-DD/
```

---

## 2. 공통 API 스펙

모든 구현체가 **동일한 API**를 제공해야 비교가 유효함:

| 엔드포인트    | 메서드 | 시나리오    | 설명                         |
| ------------- | ------ | ----------- | ---------------------------- |
| `/health`     | GET    | 1. 경량     | Health check (최소 오버헤드) |
| `/echo`       | POST   | 2. JSON     | JSON 에코 (직렬화 성능)      |
| `/users`      | GET    | 3. DB 읽기  | 사용자 목록                  |
| `/users`      | POST   | 4. DB 쓰기  | 사용자 생성                  |
| `/users/{id}` | GET    | 3. DB 읽기  | 사용자 상세                  |
| `/external`   | GET    | 5. 외부 API | 외부 API 호출 시뮬레이션     |
| `/protected`  | GET    | 6. 미들웨어 | 인증 + 로깅 + 검증           |
| `/upload`     | POST   | 7. 파일     | 파일 업로드                  |

---

## 3. 비교 대상 매트릭스

### 언어/프레임워크

| 구현체             | 언어       | 프레임워크 | 서버     | 비고            |
| ------------------ | ---------- | ---------- | -------- | --------------- |
| python-fastapi     | Python     | FastAPI    | Uvicorn  | 비동기 ASGI     |
| python-django      | Python     | Django     | Gunicorn | 동기 WSGI       |
| python-flask       | Python     | Flask      | Gunicorn | 동기 WSGI       |
| typescript-express | TypeScript | Express    | Node.js  | 가장 보편적     |
| typescript-fastify | TypeScript | Fastify    | Node.js  | 성능 중심       |
| typescript-nestjs  | TypeScript | NestJS     | Node.js  | 엔터프라이즈    |
| go-fiber           | Go         | Fiber      | -        | 성능 베이스라인 |

### 서버 구성 실험 (Python)

| 구성                     | 설명          |
| ------------------------ | ------------- |
| Uvicorn 단독 (1 worker)  | 기본          |
| Uvicorn 단독 (N workers) | `--workers N` |
| Gunicorn + Uvicorn       | 프로덕션 권장 |

워커 수 실험: 1, 2, 4, 8, (2\*CPU+1)

---

## 4. 벤치마크 시나리오

| #   | 시나리오      | 측정 포인트         | 예상 병목      |
| --- | ------------- | ------------------- | -------------- |
| 1   | 경량 API      | 프레임워크 오버헤드 | 라우팅, 직렬화 |
| 2   | JSON 페이로드 | 직렬화 성능         | JSON 파싱      |
| 3   | DB 읽기       | 커넥션 풀, 쿼리     | DB 드라이버    |
| 4   | DB 쓰기       | 트랜잭션            | DB 락          |
| 5   | 외부 API      | 비동기 처리         | I/O 대기       |
| 6   | 미들웨어      | 체인 오버헤드       | 미들웨어 수    |
| 7   | 파일 업로드   | 스트리밍            | 메모리         |
| 8   | 혼합          | 실제 트래픽         | 종합           |
