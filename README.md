# Backend Benchmark Lab

[![Korean](https://img.shields.io/badge/lang-Korean-blue)](README.ko.md)

> **"Same Logic, Different Implementations"** — An empirical benchmark lab for backend frameworks

## Highlights

- **4 languages, 5 frameworks** on identical API specs — apples-to-apples comparison
- **26 real-world scenarios** (not "Hello World"): N+1, caching, auth, transactions, server config
- **105 server-config runs** proving deployment tuning beats framework choice
- Every number averaged over **10 k6 runs** in resource-constrained Docker containers

![Framework RPS Comparison](assets/charts/01-framework-rps.png)

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
| Host | Apple M5 Pro, 18 cores, 48 GB |
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
| Rails 8 | API-only MVC | ✅ | ✅ |
| Go Fiber | — | — | — |

---

## Benchmark Results (2026-03-27)

### Full Comparison: 5 Frameworks (RPS)

| Scenario | Express | FastAPI-P | FastAPI-S | Rails | Django |
|----------|---------|-----------|-----------|-------|--------|
| 01-lightweight | **20,492** | 14,225 | 13,928 | 3,632 | 2,899 |
| 02-json-payload | **17,403** | 11,790 | 11,635 | 4,200 | 2,621 |
| 03-db-read | 498 | 147 | 170 | **1,524** | 288 |
| 04-db-write | **5,875** | 1,280 | 1,528 | 1,719 | 411 |
| 05-external-api | 92 | **94** | 93 | 90 | 19 |
| 06-middleware | **18,771** | 9,799 | 10,455 | 3,519 | 2,560 |
| 07-file-upload | **10,063** | 6,029 | 6,084 | 3,150 | 2,622 |
| 08-mixed | 244 | 122 | 133 | **557** | 93 |

> Express leads in lightweight throughput, but **Rails wins in DB reads (3x over Express) and mixed workloads (2.3x over Express)**. At the I/O boundary (05), all async frameworks converge. Django's synchronous processing is the bottleneck for external API calls.

![Framework RPS Comparison](assets/charts/01-framework-rps.png)

### Rails: The Surprise Performer

- **DB Read #1** — ActiveRecord's efficient SELECT outperforms even Prisma (1,524 vs 498 RPS)
- **Mixed Workload #1** — Puma's multi-threaded architecture excels at concurrency (557 vs 244 RPS)
- **Most Stable** — Lowest coefficient of variation in mixed workload (CV 5.8% vs 45%+ for others)
- Weak in lightweight scenarios (Ruby interpreter overhead)

### Clean Architecture: Zero Performance Penalty

FastAPI Strict (Clean Architecture) vs Pragmatic: **DB writes +19.4% faster**, standard deviation dramatically lower (lightweight: 37 vs 265). Layer separation improves both speed and stability.

![Clean Architecture vs Pragmatic](assets/charts/02-clean-architecture.png)

### DB, Caching & Auth Highlights

- **Cursor pagination** is 1.7x faster than OFFSET at deep pages (index seek vs full scan)
- **Eager loading (JOIN)** solves N+1 with 4.1x speedup (21 queries down to 1)
- **Bulk INSERT** via Raw VALUES is 187x faster than individual inserts (commit count is everything)
- **Pessimistic lock** is the only safe choice under high concurrency (Serializable: 0.6% success rate)
- **Redis cache hit** delivers 10x throughput + eliminates tail latency spikes
- **Session auth beats JWT by 14%** in Python — GIL makes CPU-bound JWT verification slower than async Redis lookup

![Caching Impact](assets/charts/03-caching-impact.png)

### Server Config: Uvicorn vs Gunicorn (2026-03-02)

> Same FastAPI app, 3 server configs (Uvicorn / Gunicorn+Uvicorn 2w / 4w), 5 rounds × 35 combinations × 3 runs = **105 total runs**

**Hypothesis Validation**

| Hypothesis | Content | Result | Key Data |
|------------|---------|--------|----------|
| H1 | Single async process wins on I/O-bound | **Rejected** | gunicorn-4w is 3-6% faster, P99 gap 13% |
| H2 | Multi-process wins on CPU-bound | **Accepted** | gunicorn-2w is **1.86x** faster (GIL bypass) |
| H3 | Multi-process hurts on low CPU | **Conditional** | I/O: no harm, CPU: **98% collapse** |

**Key Results**

| Round | Workload | CPU | Winner | Key Data |
|-------|----------|-----|--------|----------|
| R1 | I/O (sleep) | 1 vCPU | gunicorn-4w | +6% RPS, P99 126→145ms gap at VU=200 |
| R2 | CPU (fibonacci) | 2 vCPU | gunicorn-2w | **1.86x** RPS, uvicorn P99=60s timeout |
| R3 | I/O (sleep) | 0.25 vCPU | ~tie | All 3 configs stable, <5% diff |
| R4 | CPU (fibonacci) | 0.25 vCPU | uvicorn | **3.4x** — gunicorn-4w gets 0.27 RPS |
| R5 | Mixed (DB+compute) | 1/2 vCPU | depends | 1 vCPU: uvicorn, 2 vCPU: gunicorn-2w (1.7x) |

**Deployment Guide**

| Workload | ≤1 vCPU | 2+ vCPU |
|----------|---------|---------|
| **I/O-bound** (API calls, DB) | Uvicorn standalone | Gunicorn + N workers (slight gain) |
| **CPU-bound** (compute, hashing) | Uvicorn standalone | **Gunicorn + N workers required** (N = vCPU) |
| **Mixed** (real-world) | Uvicorn standalone | **Gunicorn + N workers required** (N = vCPU) |

**Lessons**: (1) Workers > vCPU = service-level failure on CPU-bound, (2) Single event loop can't utilize additional CPUs — Uvicorn@1vCPU ≈ Uvicorn@2vCPU, (3) I/O-bound needs almost no CPU — 0.25 vCPU ≈ 1 vCPU throughput.

![Server Config Benchmark](assets/charts/04-server-config.png)

---

## Key Insights

1. **"Nx faster" is a half-truth** — Express is 7x faster than Django in lightweight, but Rails beats everyone in DB reads and mixed workloads.
2. **The bottleneck is rarely the framework** — Optimization priority: DB queries > Caching > Infra config > Framework choice.
3. **Rails DB performance is surprisingly strong** — ActiveRecord + Puma beats Express (Prisma) 3x in DB reads and 2.3x in mixed workloads.
4. **Clean Architecture has zero performance penalty** — Actually 15-19% faster on DB operations with much lower variance.
5. **Server config matters more than framework choice** — 1.86x improvement from proper worker configuration alone.
6. **Python's GIL reverses JWT vs Session** — Session is 14% faster; CPU-bound JWT verification suffers under the GIL.
7. **"Fewer queries = faster" is false** — 3 separate ORM queries beat 1 combined Raw SQL by 1.4x (optimizer picks better plans per query).
8. **Commit count determines 99% of bulk performance** — Individual INSERT (2.98s) vs Raw VALUES (15.91ms) = 187x difference.
9. **Mixed workload = real-world proxy** — Scenario 08 results (Rails #1) best represent actual production traffic patterns.

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
docker compose --profile rails up -d
```

### Run benchmarks

```bash
cd runner
./run-benchmark.sh python-fastapi-pragmatic    # All scenarios for FastAPI
./run-benchmark.sh typescript-express 05        # Single scenario
./run-benchmark.sh ruby-rails 03+              # From scenario 03 onwards
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
- [x] Basic scenarios 01-08 (5 frameworks)
- [x] FastAPI Pragmatic vs Strict architecture comparison
- [x] DB Advanced 09-13 (Pagination, Column, N+1, Bulk, Transactions)
- [x] Caching 14-16 (Redis hit/miss)
- [x] Authentication 17 (JWT vs Session)
- [x] Aggregation 18 (ORM vs Raw SQL)
- [x] Server configuration experiment (Uvicorn vs Gunicorn, 105 runs)
- [x] Ruby Rails 8 implementation + benchmarks

### Planned

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
