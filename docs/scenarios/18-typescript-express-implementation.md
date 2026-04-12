# TypeScript Express 구현

## 개요

Express.js + TypeScript + Prisma ORM을 사용한 벤치마크 API 구현.

> **구현 원칙**: Express의 관용적 방식을 따른다. Pragmatic 아키텍처로 간결하게 구현한다.

---

## 기술 스택

| 항목 | 선택 | 이유 |
|------|------|------|
| 프레임워크 | Express 5.x | Node.js 웹 프레임워크 사실상 표준 |
| 언어 | TypeScript 5.x | 타입 안정성 |
| ORM | Prisma 7.x | TypeScript 친화적, 타입 자동 생성 |
| 런타임 | Node.js 22 | 최신 LTS |

---

## FastAPI와의 비교

| 항목 | FastAPI (Python) | Express (TypeScript) |
|------|------------------|---------------------|
| 패러다임 | 비동기 (ASGI) | 비동기 (Node.js) |
| 타입 검증 | Pydantic | 수동 (또는 Zod) |
| ORM | SQLAlchemy | Prisma |
| 서버 | Uvicorn | Node.js 내장 |
| 라우팅 | 데코레이터 기반 | Router 기반 |

---

## 프로젝트 구조 (Pragmatic)

```
implementations/typescript-express/
├── src/
│   ├── app.ts              # Express 앱 + 서버 시작
│   ├── lib/
│   │   └── prisma.ts       # Prisma 클라이언트
│   ├── schemas/            # Zod 스키마 (런타임 검증)
│   │   ├── common.ts       # 공통 스키마
│   │   └── user.ts         # User 관련 스키마
│   └── routes/
│       ├── index.ts        # 라우터 통합
│       ├── health.ts       # GET /health
│       ├── echo.ts         # POST /echo
│       ├── users.ts        # /users CRUD
│       ├── external.ts     # GET /external
│       ├── protected.ts    # GET /protected
│       └── upload.ts       # POST /upload
├── prisma/
│   └── schema.prisma       # Prisma 스키마
├── generated/
│   └── prisma/             # Prisma Client 생성 위치
├── prisma.config.ts        # Prisma 7.x 설정
├── tsconfig.json
├── package.json
└── Dockerfile
```

---

## 구현 과정에서 발생한 이슈들

### 이슈 1: Prisma 7.x Breaking Changes

Prisma 7.x (2025년 11월 출시)에서 큰 변경이 있었다.

#### 문제: schema.prisma에서 datasource url 제거됨

```prisma
# Prisma 6.x 이전
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")  # 더 이상 지원 안 함!
}

# Prisma 7.x
datasource db {
  provider = "postgresql"
  # url 없음 - prisma.config.ts로 이동
}
```

#### 해결: prisma.config.ts 생성

```typescript
// prisma.config.ts
import 'dotenv/config'
import { defineConfig, env } from "prisma/config";

export default defineConfig({
  schema: 'prisma/schema.prisma',
  datasource: {
    url: env('DATABASE_URL'),
  },
});
```

---

### 이슈 2: PrismaClient 생성 시 adapter 필수

Prisma 7.x에서는 `PrismaClient` 생성 시 **adapter** 또는 **accelerateUrl**이 필수가 되었다.

#### 문제: 기존 방식이 동작하지 않음

```typescript
// Prisma 6.x 이전 - 동작함
const prisma = new PrismaClient();

// Prisma 7.x - 에러!
// PrismaClientInitializationError: `PrismaClient` needs to be constructed
// with a non-empty, valid `PrismaClientOptions`
```

#### 해결: @prisma/adapter-pg 사용

```bash
npm install @prisma/adapter-pg pg
npm install -D @types/pg
```

```typescript
// src/lib/prisma.ts
import "dotenv/config";
import { PrismaClient } from "../../generated/prisma";
import { PrismaPg } from "@prisma/adapter-pg";

const connectionString = process.env.DATABASE_URL!;

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

const adapter = new PrismaPg({ connectionString });

export const prisma = globalForPrisma.prisma ?? new PrismaClient({ adapter });

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.prisma = prisma;
}
```

---

### 이슈 3: Prisma generate 출력 경로

#### 문제: 기본 경로가 node_modules 안

Prisma는 기본적으로 `node_modules/.prisma/client`에 생성하는데, 명시적으로 관리하기 어렵다.

#### 해결: output 명시

```prisma
generator client {
  provider = "prisma-client-js"
  output   = "../generated/prisma"
}
```

그리고 `.gitignore`에 추가:
```
**/generated/prisma/
```

---

### 이슈 4: Docker 빌드 시 DATABASE_URL 없음

#### 문제: prisma generate 실패

```dockerfile
RUN npx prisma generate
# Error: Cannot resolve environment variable: DATABASE_URL
```

빌드 시점에는 환경변수가 없다!

#### 해결: 더미 URL 제공

```dockerfile
# 빌드 시점에만 사용되는 더미 URL
ENV DATABASE_URL="postgresql://dummy:dummy@localhost:5432/dummy"
RUN npx prisma generate
```

`prisma generate`는 DB 연결 없이 타입만 생성하므로 더미 값으로 충분하다.

---

### 이슈 5: ESM vs CommonJS 충돌

#### 문제: verbatimModuleSyntax 에러

```
ECMAScript imports and CommonJS "require" calls may be intermingled
```

#### 해결: tsconfig.json 설정

```json
{
  "compilerOptions": {
    "module": "commonjs",
    "moduleResolution": "node",
    "esModuleInterop": true
    // verbatimModuleSyntax 제거
  }
}
```

---

### 이슈 6: 런타임 타입 검증 필요성 (Zod 도입)

#### 문제: TypeScript 타입은 컴파일 후 사라진다

TypeScript의 타입 검증은 **컴파일 타임**에만 동작한다. 빌드 후 JavaScript로 변환되면 타입 정보가 사라지므로, 외부 입력(API 요청)에 대한 **런타임 검증이 없다**.

```typescript
// 컴파일 타임에는 안전해 보이지만...
router.post("/", async (req, res) => {
  const { name, email } = req.body;  // req.body는 any!
  // 잘못된 데이터가 그대로 DB에 저장될 수 있음
});
```

#### 판단 과정: Zod 추가 여부

| 관점 | 분석 |
|------|------|
| **FastAPI Pragmatic** | Pydantic으로 모든 요청/응답 런타임 검증 |
| **Express (기본)** | 런타임 검증 없음 |
| **벤치마크 공정성** | FastAPI는 검증 비용 지불 중, Express만 검증 없으면 불공정 |
| **실무** | 프로덕션에서 Zod 없이 Express 쓰는 경우 거의 없음 |

**결론**: 공정한 비교를 위해 Zod 추가

#### 컴파일 타임 vs 런타임 검증

```
┌─────────────────────────────────────────────────────────────┐
│                    TypeScript 컴파일 타임                      │
│  ✅ 개발자 실수 방지 (잘못된 타입 사용)                          │
│  ❌ 외부 입력(API 요청) 검증 불가                               │
│     → req.body는 any 또는 unknown                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Zod 런타임 검증                             │
│  ✅ 외부 입력 검증 (악의적/잘못된 요청 차단)                      │
│  ✅ Pydantic과 동등한 역할                                     │
└─────────────────────────────────────────────────────────────┘
```

#### 해결: Zod 설치 및 적용

```bash
npm install zod
```

Pydantic 적용 범위와 동일하게 Zod 적용:

| 엔드포인트 | Request 검증 | Response 검증 |
|-----------|-------------|---------------|
| /health | - | HealthResponse |
| /echo | EchoRequest | EchoResponse |
| /users | UserCreate | UserResponse |
| /external | - | ExternalResponse |
| /protected | - | ProtectedResponse |
| /upload | - | UploadResponse |

#### Zod 스키마 예시

```typescript
// src/schemas/user.ts
import { z } from "zod";

export const UserCreateSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
});
export type UserCreate = z.infer<typeof UserCreateSchema>;

export const UserResponseSchema = z.object({
  id: z.number(),
  name: z.string(),
  email: z.string(),
  createdAt: z.date(),
});
export type UserResponse = z.infer<typeof UserResponseSchema>;
```

#### 라우터 적용 예시

```typescript
// routes/users.ts
import { UserCreateSchema } from "../schemas/user";

router.post("/", async (req, res) => {
  const result = UserCreateSchema.safeParse(req.body);

  if (!result.success) {
    return res.status(422).json({ detail: result.error.issues });
  }

  const { name, email } = result.data;  // 이제 타입 안전!
  const user = await prisma.user.create({ data: { name, email } });
  res.status(201).json(user);
});
```

#### Pydantic vs Zod 비교

| 항목 | Pydantic (Python) | Zod (TypeScript) |
|------|-------------------|------------------|
| 스키마 정의 | `class Model(BaseModel)` | `z.object({})` |
| 타입 추론 | 자동 | `z.infer<typeof Schema>` |
| 검증 | 자동 (함수 파라미터) | 수동 (`safeParse()`) |
| 에러 응답 | 자동 422 | 수동 구현 필요 |
| 성능 비용 | 있음 | 있음 (동등) |

> **핵심**: FastAPI는 Pydantic이 프레임워크에 통합되어 자동 검증되지만,
> Express는 Zod를 수동으로 호출해야 한다. 이 차이가 DX(개발자 경험)의 차이.

---

## 엔드포인트 구현

### routes/health.ts

```typescript
import { Router } from "express";

const router = Router();

router.get("/", (req, res) => {
  res.json({ status: "ok", server: "typescript-express" });
});

export default router;
```

### routes/echo.ts

```typescript
import { Router } from "express";

const router = Router();

router.post("/", (req, res) => {
  res.json(req.body);
});

export default router;
```

### routes/users.ts

```typescript
import { Router } from "express";
import { prisma } from "../lib/prisma";

const router = Router();

// GET /users - 목록
router.get("/", async (req, res) => {
  const users = await prisma.user.findMany({ take: 100 });
  res.json(users);
});

// POST /users - 생성
router.post("/", async (req, res) => {
  const { name, email } = req.body;
  const user = await prisma.user.create({
    data: { name, email },
  });
  res.status(201).json(user);
});

// GET /users/:id - 상세
router.get("/:id", async (req, res) => {
  const id = parseInt(req.params.id);
  const user = await prisma.user.findUnique({ where: { id } });

  if (!user) {
    return res.status(404).json({ error: "User not found" });
  }
  res.json(user);
});

export default router;
```

### routes/external.ts

```typescript
import { Router } from "express";

const router = Router();

// 외부 API 호출 시뮬레이션 (100ms 지연)
router.get("/", async (req, res) => {
  const start = performance.now();

  await new Promise((resolve) => setTimeout(resolve, 100));

  const latency = performance.now() - start;

  res.json({
    source: "simulated_external_api",
    latency_ms: Math.round(latency * 100) / 100,
    data: { message: "External API response" },
  });
});

export default router;
```

### routes/protected.ts

```typescript
import { Router } from "express";

const router = Router();

router.get("/", (req, res) => {
  const authorization = req.headers.authorization;

  if (!authorization) {
    return res.status(401).json({ detail: "Authorization header required" });
  }

  if (!authorization.startsWith("Bearer ")) {
    return res.status(401).json({ detail: "Invalid authorization format" });
  }

  const token = authorization.replace("Bearer ", "");

  if (token.length < 10) {
    return res.status(401).json({ detail: "Invalid token" });
  }

  res.json({
    message: "Access granted",
    user: `user_from_token_${token.slice(0, 8)}`,
  });
});

export default router;
```

### routes/upload.ts

```typescript
import { Router } from "express";
import multer from "multer";

const router = Router();
const upload = multer({ storage: multer.memoryStorage() });

router.post("/", upload.single("file"), (req, res) => {
  const file = req.file;

  if (!file) {
    return res.status(400).json({ detail: "No file uploaded" });
  }

  res.json({
    filename: file.originalname,
    size: file.size,
    content_type: file.mimetype,
  });
});

export default router;
```

### routes/index.ts (라우터 통합)

```typescript
import { Router } from "express";
import healthRouter from "./health";
import echoRouter from "./echo";
import usersRouter from "./users";
import protectedRouter from "./protected";
import externalRouter from "./external";
import uploadRouter from "./upload";

const router = Router();

router.use("/health", healthRouter);
router.use("/echo", echoRouter);
router.use("/users", usersRouter);
router.use("/protected", protectedRouter);
router.use("/external", externalRouter);
router.use("/upload", uploadRouter);

export default router;
```

### app.ts (진입점)

```typescript
import express from "express";
import routes from "./routes";

const app = express();
const PORT = process.env.PORT || 8000;

app.use(express.json());
app.use(routes);

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

---

## Docker 설정

### Dockerfile

```dockerfile
FROM node:22-alpine

WORKDIR /app

# 의존성 설치
COPY package*.json ./
RUN npm ci

# Prisma 설정 복사 및 generate
COPY prisma ./prisma/
COPY prisma.config.ts ./

# 빌드 시점에만 사용되는 더미 URL
ENV DATABASE_URL="postgresql://dummy:dummy@localhost:5432/dummy"
RUN npx prisma generate

# 소스 복사
COPY tsconfig.json ./
COPY src ./src/

# 빌드
RUN npm run build

EXPOSE 8000

CMD ["node", "dist/app.js"]
```

### docker-compose.yml 추가

```yaml
typescript-express:
  build: ./typescript-express
  profiles: ["express"]
  ports:
    - "8000:8000"
  environment:
    DATABASE_URL: postgresql://benchmark:benchmark@postgres:5432/benchmark
  depends_on:
    postgres:
      condition: service_healthy
  deploy:
    resources:
      limits:
        cpus: "2"
        memory: 2G
```

---

## 실행 방법

### 로컬 개발

```bash
cd implementations/typescript-express

# 의존성 설치
npm install

# Prisma generate
npx prisma generate

# 개발 서버 실행
npm run dev
```

### Docker

```bash
cd implementations

# 빌드 및 실행
docker compose --profile express up -d

# 로그 확인
docker compose --profile express logs -f

# 종료
docker compose --profile express down
```

---

## 테스트

```bash
# Health check
curl http://localhost:8000/health
# {"status":"ok","server":"typescript-express"}

# Echo
curl -X POST http://localhost:8000/echo \
  -H "Content-Type: application/json" \
  -d '{"hello":"world"}'
# {"hello":"world"}

# Users 목록
curl http://localhost:8000/users

# External API
curl http://localhost:8000/external
# {"source":"simulated_external_api","latency_ms":104.79,...}

# Protected (인증 성공)
curl http://localhost:8000/protected \
  -H "Authorization: Bearer test-token-12345"
# {"message":"Access granted","user":"user_from_token_test-tok"}
```

---

## Prisma vs SQLAlchemy 비교

| 작업 | Prisma (TypeScript) | SQLAlchemy (Python) |
|------|---------------------|---------------------|
| 목록 조회 | `findMany()` | `select().all()` |
| 단건 조회 | `findUnique()` | `get()` |
| 생성 | `create()` | `add() + commit()` |
| 수정 | `update()` | `update() + commit()` |
| 삭제 | `delete()` | `delete() + commit()` |
| 관계 로딩 | `include: {}` | `joinedload()` |
| 트랜잭션 | `$transaction()` | `async with session.begin()` |

---

## 핵심 인사이트

### 1. Prisma 7.x 마이그레이션 주의

- 2025년 11월에 출시된 버전으로, 온라인 자료 대부분이 6.x 기준
- datasource URL, PrismaClient 생성 방식 등 주요 변경 있음
- 공식 마이그레이션 가이드 필수 참고: https://www.prisma.io/docs/orm/more/upgrade-guides/upgrading-versions/upgrading-to-prisma-7

### 2. Driver Adapter 패턴

Prisma 7.x는 DB 연결을 adapter로 추상화:

```typescript
// PostgreSQL
import { PrismaPg } from "@prisma/adapter-pg";
const adapter = new PrismaPg({ connectionString });

// MySQL
import { PrismaMysql } from "@prisma/adapter-mysql2";
const adapter = new PrismaMysql({ connectionString });

// SQLite
import { PrismaSqlite } from "@prisma/adapter-sqlite";
const adapter = new PrismaSqlite(":memory:");
```

### 3. Express Pragmatic vs Strict

| 구분 | Pragmatic | Strict |
|------|-----------|--------|
| 구조 | Route → Handler (직접 DB) | Route → Controller → Service → Repository |
| 복잡도 | 낮음 | 높음 |
| 테스트 | 통합 테스트 위주 | 단위 테스트 용이 |
| 적합한 규모 | 소~중형 | 대형 |

현재 구현은 Pragmatic으로, FastAPI Pragmatic과 동일한 수준.

---

## 다음 단계

- [ ] k6 벤치마크 실행 및 FastAPI와 비교
- [ ] Express Strict 아키텍처 구현 (선택)
- [ ] N+1 시나리오 구현 (Prisma include)

---

_Last updated: 2026-01-03_
