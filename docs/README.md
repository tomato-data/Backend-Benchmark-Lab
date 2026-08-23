# docs — Backend Benchmark Lab

> Claude가 작성한 시나리오 스펙·가이드·계획을 모아둔 디렉터리. 사용자 산출물(Q&A·회고·발견)은 `../learnings/`에 둔다.

관련 파일
- `benchmark-results.md` — 프레임워크별 RPS/Latency 결과 비교표와 측정 환경
- `scenarios/` — 시나리오 01~27 가이드
- `plans/` — `/tdd-plan` 등 Claude가 생성한 설계 문서 (필요 시 추가)

---

## Scenario 인덱스

| # | 주제 | 파일 |
|---|---|---|
| 01 | Infrastructure setup | [01-infrastructure-setup.md](scenarios/01-infrastructure-setup.md) |
| 02 | k6 benchmark setup | [02-k6-benchmark-setup.md](scenarios/02-k6-benchmark-setup.md) |
| 03 | JSON payload | [03-json-payload-scenario.md](scenarios/03-json-payload-scenario.md) |
| 04 | DB read | [04-db-read-scenario.md](scenarios/04-db-read-scenario.md) |
| 05 | Init DB setup | [05-init-db-setup.md](scenarios/05-init-db-setup.md) |
| 06 | DB write | [06-db-write-scenario.md](scenarios/06-db-write-scenario.md) |
| 07 | External API | [07-external-api-scenario.md](scenarios/07-external-api-scenario.md) |
| 08 | Middleware chain | [08-middleware-chain-scenario.md](scenarios/08-middleware-chain-scenario.md) |
| 09 | File upload | [09-file-upload-scenario.md](scenarios/09-file-upload-scenario.md) |
| 10 | Concurrent mixed | [10-concurrent-mixed-scenario.md](scenarios/10-concurrent-mixed-scenario.md) |
| 11 | Benchmark automation | [11-benchmark-automation.md](scenarios/11-benchmark-automation.md) |
| 12 | Django implementation | [12-django-implementation.md](scenarios/12-django-implementation.md) |
| 13 | Monitoring setup | [13-monitoring-setup.md](scenarios/13-monitoring-setup.md) |
| 14 | FastAPI strict clean architecture | → `learnings/retrospectives/14-*.md` (회고) |
| 15 | DB pagination | [15-db-pagination.md](scenarios/15-db-pagination.md) |
| 16 | DB column overhead | [16-db-column-overhead.md](scenarios/16-db-column-overhead.md) |
| 17 | DB N+1 | [17-db-n-plus-one.md](scenarios/17-db-n-plus-one.md) |
| 18 | TypeScript Express implementation | [18-typescript-express-implementation.md](scenarios/18-typescript-express-implementation.md) |
| 19 | DB bulk operations | [19-db-bulk-operations.md](scenarios/19-db-bulk-operations.md) |
| 20 | DB transactions | [20-db-transactions.md](scenarios/20-db-transactions.md) |
| 21 | Caching | [21-caching.md](scenarios/21-caching.md) |
| 22 | Auth | [22-auth.md](scenarios/22-auth.md) |
| 23 | Aggregation | [23-aggregation.md](scenarios/23-aggregation.md) |
| 24 | Ruby Rails | [24-ruby-rails.md](scenarios/24-ruby-rails.md) |
| 25 | MVC architecture | [25-mvc-architecture.md](scenarios/25-mvc-architecture.md) |
| 26 | Server config experiment | [26-server-config-experiment.md](scenarios/26-server-config-experiment.md) |
| 27 | Server config results | [27-server-config-results.md](scenarios/27-server-config-results.md) |
| 28 | Java Spring Boot implementation | [28-java-spring-boot-implementation.md](scenarios/28-java-spring-boot-implementation.md) |

진행 상태는 `../roadmap.md`를 정본으로 삼는다.

---

## Benchmark Results

프레임워크별 결과 비교표·메트릭 해석·측정 환경은 [benchmark-results.md](benchmark-results.md)를 참조.
