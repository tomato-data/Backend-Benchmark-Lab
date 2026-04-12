# Django 구현

## 개요

Django + DRF(Django REST Framework)를 사용한 벤치마크 API 구현.

> **구현 원칙**: Django의 관용적 방식을 따른다. FastAPI 스타일을 억지로 적용하지 않는다.

---

## 기술 스택

| 항목 | 선택 | 이유 |
|------|------|------|
| 프레임워크 | Django 5.x | 최신 안정 버전 |
| REST API | DRF 3.x | Django REST 사실상 표준 |
| 서버 | Gunicorn (sync WSGI) | Django 프로덕션 표준 |
| DB 드라이버 | psycopg2 | Django 기본 PostgreSQL 드라이버 |

---

## FastAPI와의 차이점

| 항목 | FastAPI | Django |
|------|---------|--------|
| 패러다임 | 비동기 (ASGI) | 동기 (WSGI) |
| 직렬화 | Pydantic | DRF Serializer |
| ORM | SQLAlchemy | Django ORM |
| 서버 | Uvicorn | Gunicorn |
| 의존성 주입 | Depends() | 없음 (미들웨어/데코레이터) |
| 라우팅 | 데코레이터 기반 | urls.py 중앙 집중 |

---

## 프로젝트 구조

```
implementations/python-django/
├── config/              # Django 프로젝트 설정
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── api/                 # API 앱
│   ├── __init__.py
│   ├── models.py        # User 모델
│   ├── views.py         # API 뷰
│   ├── serializers.py   # DRF 시리얼라이저
│   └── urls.py          # 앱 라우팅
├── Dockerfile
├── pyproject.toml
└── manage.py
```

---

## 구현 단계

### Phase 1: 프로젝트 셋업

#### Step 1.1: 디렉토리 생성 및 uv 초기화

```bash
mkdir -p implementations/python-django
cd implementations/python-django

# uv로 프로젝트 초기화
uv init

# 의존성 추가
uv add django djangorestframework psycopg2-binary gunicorn requests
```

이 명령으로 자동 생성되는 파일들:
- `pyproject.toml` - 프로젝트 설정 및 의존성
- `uv.lock` - 의존성 lock 파일
- `.python-version` - Python 버전

#### Step 1.2: Django 프로젝트 생성

```bash
uv run django-admin startproject config .
uv run python manage.py startapp api
```

- `config .`: 현재 디렉토리에 프로젝트 생성 (config/ 폴더 + manage.py)
- `startapp api`: api 앱 생성

---

### Phase 2: 기본 설정

#### Step 2.1: settings.py 수정

`config/settings.py`에서 수정할 부분:

```python
import os

INSTALLED_APPS = [
    # ... 기본 앱들
    'rest_framework',
    'api',
]

# 데이터베이스 (환경변수에서 읽기)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'benchmark'),
        'USER': os.environ.get('DB_USER', 'benchmark'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'benchmark'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# DRF 설정
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'UNAUTHENTICATED_USER': None,
}

# 타임존
TIME_ZONE = 'UTC'
USE_TZ = True
```

#### Step 2.2: User 모델 정의

`api/models.py`:
```python
from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'
        managed = False  # Django가 테이블을 관리하지 않음
```

> **`managed = False` 사용 이유**
> - 모든 프레임워크가 같은 PostgreSQL을 공유
> - 테이블 스키마는 `implementations/scripts/init_db.sql`에서 관리 (Single Source of Truth)
> - Django 마이그레이션으로 인한 테이블 충돌 방지
> - `makemigrations`, `migrate` 불필요

---

### Phase 3: API 엔드포인트 구현

#### Step 3.1: Serializers 정의

`api/serializers.py`:
```python
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'created_at']
        read_only_fields = ['id', 'created_at']

class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'email']

# EchoSerializer 불필요 - view에서 request.data를 그대로 반환
# (DRF Serializer의 'data' property와 필드명 충돌 방지)
```

#### Step 3.2: Views 구현

`api/views.py`:
```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests

from .models import User
from .serializers import UserSerializer, UserCreateSerializer

SERVER_NAME = "python-django"

class HealthView(APIView):
    def get(self, request):
        return Response({"status": "ok", "server": SERVER_NAME})

class EchoView(APIView):
    def post(self, request):
        return Response(request.data)  # 받은 JSON 그대로 반환

class UserListView(APIView):
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

class UserDetailView(APIView):
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserSerializer(user).data)

class ExternalAPIView(APIView):
    def get(self, request):
        # 100ms 지연 시뮬레이션
        response = requests.get("https://httpbin.org/delay/0.1")
        return Response({
            "source": "external",
            "status": response.status_code
        })

class ProtectedView(APIView):
    def get(self, request):
        # 헤더 검증
        auth = request.headers.get("Authorization", "")
        request_id = request.headers.get("X-Request-ID", "")

        if not auth.startswith("Bearer "):
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({
            "message": "access granted",
            "request_id": request_id
        })

class UploadView(APIView):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"detail": "No file"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "filename": file.name,
            "size": file.size
        })
```

#### Step 3.3: URL 라우팅

`api/urls.py`:
```python
from django.urls import path
from . import views

urlpatterns = [
    path('health', views.HealthView.as_view()),
    path('echo', views.EchoView.as_view()),
    path('users', views.UserListView.as_view()),
    path('users/<int:user_id>', views.UserDetailView.as_view()),
    path('external', views.ExternalAPIView.as_view()),
    path('protected', views.ProtectedView.as_view()),
    path('upload', views.UploadView.as_view()),
]
```

`config/urls.py`:
```python
from django.urls import path, include

urlpatterns = [
    path("", include("api.urls")),
]
```

> Django가 생성한 주석은 그대로 두어도 됩니다. `urlpatterns`만 위처럼 수정하면 됩니다.

---

### Phase 4: Docker 및 배포

#### Step 4.1: Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 의존성 설치
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 소스 복사
COPY . .

# collectstatic (필요시)
# RUN uv run python manage.py collectstatic --noinput

EXPOSE 8000

# Gunicorn으로 실행
CMD ["uv", "run", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

#### Step 4.2: docker-compose.yml에 profile 추가

`implementations/docker-compose.yml`에 추가:
```yaml
  python-django:
    build: ./python-django
    profiles: ["django"]
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=postgres
      - DB_NAME=benchmark
      - DB_USER=benchmark
      - DB_PASSWORD=benchmark
    depends_on:
      postgres:
        condition: service_healthy
```

---

## 실행 방법

```bash
cd implementations
docker compose --profile django up --build
```

---

## Gunicorn 워커 설정

### CPU 대비 워커 수 공식

Gunicorn 공식 권장:
```
workers = 2 * CPU + 1
```

| CPU 코어 | 권장 워커 수 |
|----------|-------------|
| 1 | 3 |
| 2 | 5 |
| 4 | 9 |
| 8 | 17 |

### 제한된 리소스에서의 조정

docker-compose.yml에서 **CPU 2 cores**로 제한한 경우:
- 공식대로면 5 workers
- 하지만 메모리 제한(2GB)도 있으므로 **2~3 workers**가 적절
- 워커가 너무 많으면 오히려 리소스 경합으로 성능 저하

### 현재 설정

```dockerfile
CMD ["uv", "run", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
```

> **참고**: 워커 수에 따른 성능 변화는 추후 실험 대상 (CLAUDE.md: "워커 수 실험: 1, 2, 4, 8, (2*CPU+1)")

---

## 추후 비교 실험 (TODO)

| 비교 주제 | 옵션 A | 옵션 B |
|-----------|--------|--------|
| Sync vs Async | Gunicorn (WSGI) | Uvicorn (ASGI) + async views |
| ViewSet vs APIView | ModelViewSet | 개별 APIView |
| ORM vs Raw SQL | Django ORM | `connection.cursor()` |
| 워커 수 | 2 workers | 4 workers |
