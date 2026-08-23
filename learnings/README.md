# learnings — Backend Benchmark Lab

> **토마토 관점의 산출물** — 질문·회고·발견을 모아둔다. Claude가 작성한 스펙·가이드는 `../docs/`에 있다.
>
> **작성 주체**: 실제 타이핑은 **Claude가 담당**한다. 토마토는 질문을 던지고 방향성을 제공하며, 답변 과정에서 문서화할 가치가 있는 내용이 나오면 Claude가 이 디렉터리에 누적한다. 즉 `docs/`는 "Claude가 설계·기획한 스펙"이고, `learnings/`는 "토마토의 질문에서 파생된 Q&A·회고·발견"이다.
>
> 「learnings/가 학습 프로젝트의 진짜 산출물이다.」 — 학습 프로젝트 문서 표준

---

## 구조

- `qna/scenarioNN.md` — 시나리오 진행 중 나온 Q&A
- `retrospectives/scenarioNN-{topic}.md` — 시나리오 완료 회고
- `topics/{topic}.md` — 여러 시나리오를 관통하는 크로스커팅 심화
- `DISCOVERIES.md` — 실행 중 발견 로그 (시나리오와 독립)

---

## Scenario 맵

시나리오 01~27 진행 상태는 `../roadmap.md`를 정본으로 삼는다.

| Scenario | 배운 것 (2줄) | Q&A | 회고 |
|---|---|---|---|
| 01~13 | _(회고 백필 예정)_ | — | — |
| 14 | Pragmatic vs Strict Clean Architecture — 레이어 경계를 지키는 대가와 성능 영향 | — | [14-fastapi-strict-clean-architecture](retrospectives/14-fastapi-strict-clean-architecture.md) |
| 15~27 | _(회고 백필 예정)_ | — | — |

`qna/`와 `retrospectives/`는 새 시나리오를 시작하는 시점부터 채워 나간다.

---

## Cross-cutting Topics

| 파일 | 설명 |
|---|---|
| [fastapi-app-structure](topics/fastapi-app-structure.md) | FastAPI 구현체 전체 구조(Pragmatic Architecture) 상세 |
| [fastapi-clean-architecture-progress](topics/fastapi-clean-architecture-progress.md) | Clean Architecture 적용 경과 기록 |
| [fastapi-type-validation-misconception](topics/fastapi-type-validation-misconception.md) | FastAPI 타입 검증에 대한 오해 정정 |
| [pydantic-vs-native-validators](topics/pydantic-vs-native-validators.md) | Pydantic vs 네이티브 validator 비교 |
| [python-serialization-and-clean-architecture-tradeoffs](topics/python-serialization-and-clean-architecture-tradeoffs.md) | Python 직렬화와 Clean Architecture의 트레이드오프 |

---

## Discoveries

[DISCOVERIES.md](DISCOVERIES.md) — 시나리오 경계를 넘나드는 글로벌 발견 로그.
