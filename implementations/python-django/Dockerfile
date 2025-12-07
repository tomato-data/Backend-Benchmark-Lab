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