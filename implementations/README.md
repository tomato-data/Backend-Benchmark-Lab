# Implementations

각 백엔드 구현체를 동일한 환경에서 벤치마크하기 위한 디렉토리.

## 실행 방법

```bash
cd implementations

# PostgreSQL만 실행
docker compose up postgres -d

# 특정 백엔드 실행 (profile 사용)
docker compose --profile fastapi up
docker compose --profile django up
# ...

# 종료
docker compose down
```

## 설계 원칙

- 모든 백엔드는 **8000번 포트**로 통일
- 한 번에 하나의 백엔드만 실행하여 테스트
- k6 스크립트는 `http://localhost:8000` 고정
