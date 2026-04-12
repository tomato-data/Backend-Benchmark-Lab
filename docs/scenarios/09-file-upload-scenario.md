# 07-file-upload 시나리오

## 개요

`POST /upload` 엔드포인트를 통해 파일 업로드 성능을 측정한다.

---

## 측정 목표

- 멀티파트 폼 데이터 파싱 속도
- 파일 스트리밍 효율성
- 메모리 사용량 (대용량 파일 시)

---

## 엔드포인트 동작

현재 FastAPI 구현:

```python
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    return UploadResponse(
        filename=file.filename,
        size=len(content),
        content_type=file.content_type,
    )
```

---

## k6 스크립트

```javascript
// scenarios/07-file-upload.js
import http from "k6/http";
import { check } from "k6";
import { BASE_URL, defaultOptions } from "./config.js";

export const options = defaultOptions;

// 1KB 테스트 파일 생성
const fileContent = "x".repeat(1024);

export default function () {
  const data = {
    file: http.file(fileContent, "test.txt", "text/plain"),
  };

  const res = http.post(`${BASE_URL}/upload`, data);

  check(res, {
    "status is 200": (r) => r.status === 200,
    "size is 1024": (r) => r.json().size === 1024,
  });
}
```

---

## 핵심 포인트

### 파일 크기 선택

| 크기 | 용도 | 측정 포인트 |
|-----|------|------------|
| 1KB | 소형 파일 다량 | 파싱 오버헤드 |
| 1MB | 중형 파일 | 처리량 |
| 10MB+ | 대형 파일 | 메모리, 스트리밍 |

기본 벤치마크는 **1KB**로 진행 (파싱 오버헤드 측정).

### k6의 http.file()

```javascript
http.file(data, filename, contentType)
```

멀티파트 폼 데이터로 자동 변환됨.

---

## 실행 방법

```bash
k6 run 07-file-upload.js
```
