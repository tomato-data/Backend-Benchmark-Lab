# Backend Benchmark Lab

[![Korean](https://img.shields.io/badge/lang-Korean-blue)](README.ko.md)

> **"Same Logic, Different Implementations"** — An empirical benchmark lab for backend frameworks

## Highlights

- **4 languages, 6 frameworks** on identical API specs — apples-to-apples comparison
- **26 real-world scenarios** (not "Hello World"): N+1, caching, auth, transactions, server config
- **105 server-config runs** proving deployment tuning beats framework choice
- Every number averaged over **10 k6 runs** in resource-constrained Docker containers

<!-- TODO: Add hero benchmark chart image -->

---

## Why I Built This

I was using FastAPI at work but couldn't explain **why** it was the right choice. "It's fast" is everywhere, but how fast, under what conditions, and how does it structurally differ from alternatives?

Instead of trusting synthetic benchmarks, I built real-world scenarios to **make data-driven technology decisions**.

---

## Project Structure

```
Backend-Benchmark-Lab/
├── implementations/          # Framework implementations (identical APIs)
│   ├── python-fastapi-pragmatic/    # FastAPI — Pragmatic architecture
│   ├── python-fastapi-strict/       # FastAPI — Clean Architecture
│   ├── python-django/               # Django — DRF ViewSet
│   ├── python-server-config/        # Server config experiments
│   ├── typescript-express/          # Express.js + Prisma
│   └── ruby-rails/                  # Rails 8 API-only + ActiveRecord
│
├── scenarios/                # k6 benchmark scripts (26 scenarios)
│   ├── basic/                #   01-08: Framework comparison
│   ├── db-advanced/          #   09-13: DB optimization
│   ├── caching/              #   14-16: Redis caching
│   ├── auth/                 #   17: JWT vs Session
│   ├── real-world/           #   18+: Aggregation, search
│   ├── server-config/        #   Server configuration
│   └── stress/               #   Stress testing
│
├── runner/                   # Automation scripts
└── monitoring/               # Prometheus + Grafana
```

---

## Tech Stack

| Area | Technology |
|------|-----------|
| **Benchmarking** | k6 (Grafana), 10 VUs, 30s, 10-run average |
| **Containers** | Docker Compose (profile-based switching) |
| **Database** | PostgreSQL 16 |
| **Cache** | Redis |
| **Monitoring** | Prometheus + cAdvisor + Grafana |
| **API Spec** | OpenAPI (Single Source of Truth) |

| Implementation | Language | Framework | Server | ORM | Validation |
|---------------|----------|-----------|--------|-----|-----------|
| python-fastapi | Python 3.12 | FastAPI | Uvicorn | SQLAlchemy (async) | Pydantic |
| python-django | Python 3.12 | Django 5 | Gunicorn | Django ORM | DRF Serializer |
| typescript-express | TypeScript | Express | Node.js 22 | Prisma | Zod (optional) |
| ruby-rails | Ruby 3.3+ | Rails 8 | Puma | ActiveRecord | — |

---

## Test Environment

| Item | Value |
|------|-------|
| Host | MacBook Apple Silicon |
| Container CPU | 2 cores (server), 2 cores (DB) |
| Container Memory | 2 GB (server), 1 GB (DB) |
| k6 VUs | 10 |
| k6 Duration | 30 seconds |
| Iterations | 10 runs (averaged) |

> Identical resource constraints across all frameworks for fair comparison.

---

## Framework Status

| Framework | Architecture | Implemented | Benchmarked |
|-----------|-------------|-------------|-------------|
| FastAPI | Pragmatic | ✅ | ✅ |
| FastAPI | Strict (Clean Architecture) | ✅ | ✅ |
| Django | DRF ViewSet | ✅ | ✅ |
| Express | Pragmatic + Prisma | ✅ | ✅ |
| Rails 8 | API-only MVC | ✅ | — |
| Go Fiber | — | — | — |

---

## Benchmark Results

### Basic: Express vs FastAPI vs Django

| Scenario | Express | FastAPI | Django | Winner |
|---------|---------|---------|--------|--------|
| 01-lightweight | **17,005** | 11,616 | 1,655 | Express |
| 03-db-read | **413** | 146 | 252 | Express |
| 04-db-write | **5,022** | 1,091 | 373 | Express |
| 05-external-api | 93 | 92 | 19 | Tie (I/O bound) |
| 08-mixed | **551** | 125 | 92 | Express |

> Express dominates in raw throughput (1.5-4.6x vs FastAPI). But at the I/O boundary, all frameworks converge. Real workloads narrow the gap significantly.

<!-- TODO: Add benchmark chart images -->

### Clean Architecture: Zero Performance Penalty

FastAPI Strict (Clean Architecture) vs Pragmatic: **3-6% faster** across all scenarios, with **+19.6% on DB writes** and dramatically lower standard deviation (2,469 vs 367 on lightweight). Layer separation improves both speed and stability.

### DB & Caching & Auth Highlights

- **Cursor pagination** is 1.7x faster than OFFSET at deep pages (index seek vs full scan)
- **Eager loading (JOIN)** solves N+1 with 4.1x speedup (21 queries down to 1)
- **Bulk INSERT** via Raw VALUES is 187x faster than individual inserts (commit count is everything)
- **Pessimistic lock** is the only safe choice under high concurrency (Serializable: 0.6% success rate)
- **Redis cache hit** delivers 10x throughput + eliminates tail latency spikes
- **Session auth beats JWT by 14%** in Python — GIL makes CPU-bound JWT verification slower than async Redis lookup

<!-- TODO: Add benchmark chart images -->

### Server Config: Deployment Recommendation

> 3 hypotheses, 5 rounds, 105 test runs (Uvicorn vs Gunicorn)

| vCPU | Recommended Config |
|------|--------------------|
| 0.25 - 0.5 | Uvicorn standalone |
| 1 | Uvicorn or Gunicorn 1 worker |
| 2+ | Gunicorn (workers = vCPU count) |

> **Golden rule**: Never set workers > vCPU count. Uvicorn + CPU-bound = 98% collapse. Proper server config yields 1.86x on the same framework.

---

## Key Insights

1. **"Nx faster" is a half-truth** — FastAPI is 7-9x faster than Django in lightweight, but only 1.4x in mixed workloads. Django is 1.6x faster for DB reads.
2. **The bottleneck is rarely the framework** — Optimization priority: DB queries > Caching > Infra config > Framework choice.
3. **Clean Architecture has zero performance penalty** — Actually 3-6% faster with much lower variance.
4. **Server config matters more than framework choice** — 1.86x improvement from proper worker configuration alone.
5. **Python's GIL reverses JWT vs Session** — Session is 14% faster; CPU-bound JWT verification suffers under the GIL.
6. **"Fewer queries = faster" is false** — 3 separate ORM queries beat 1 combined Raw SQL by 1.4x (optimizer picks better plans per query).
7. **Data type choice barely affects performance** — All types within +-7%. Choose based on data modeling, not speed.
8. **Commit count determines 99% of bulk performance** — Individual INSERT (2.98s) vs Raw VALUES (15.91ms) = 187x difference.
9. **Benchmarks have cold start effects** — First k6 call adds +10ms. Randomize order or add warmup for accuracy.

---

## Getting Started

### Start a benchmark target

```bash
cd implementations

# Choose a framework (pick one)
docker compose --profile fastapi-pragmatic up -d
docker compose --profile fastapi-strict up -d
docker compose --profile django up -d
docker compose --profile express up -d
```

### Run benchmarks

```bash
cd runner
./run-benchmark.sh          # All scenarios
./run-benchmark.sh 05       # Start from scenario 05
```

### Monitoring (optional)

```bash
cd monitoring
docker compose up -d
# Grafana: http://localhost:3000 (admin/admin)
```

---

## Roadmap

### Completed

- [x] Infrastructure (Docker, k6, Prometheus + Grafana)
- [x] Basic scenarios 01-08 (4 frameworks)
- [x] FastAPI Pragmatic vs Strict architecture comparison
- [x] DB Advanced 09-13 (Pagination, Column, N+1, Bulk, Transactions)
- [x] Caching 14-16 (Redis hit/miss)
- [x] Authentication 17 (JWT vs Session)
- [x] Aggregation 18 (ORM vs Raw SQL)
- [x] Server configuration experiment (Uvicorn vs Gunicorn, 105 runs)
- [x] Ruby Rails 8 implementation

### Planned

- [ ] Ruby Rails benchmarks
- [ ] Go Fiber implementation + JWT vs Session validation
- [ ] Flask, Fastify, NestJS implementations
- [ ] Text search (LIKE vs Full-text)
- [ ] E2E flow (Auth -> Read -> Write -> Response)
- [ ] Rails Solid Cache vs Redis
- [ ] Stress testing (spike traffic, long-running)
- [ ] Pydantic vs msgspec, SQLAlchemy vs Raw asyncpg

---

## License

This project is licensed under the [MIT License](LICENSE).
