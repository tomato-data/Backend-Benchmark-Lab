# Ruby on Rails 구현

## 개요

Ruby on Rails (API-only) + ActiveRecord + Puma를 사용한 벤치마크 API 구현.

> **구현 원칙**: Rails의 관용적 방식("Convention over Configuration")을 따른다. 다른 프레임워크의 패턴을 억지로 적용하지 않는다.

---

## 기술 스택

| 항목 | 선택 | 이유 |
|------|------|------|
| 프레임워크 | Rails 8.x (API-only) | Convention over Configuration, 4번째 언어 추가 |
| 언어 | Ruby 3.3+ | 최신 안정 버전 |
| 서버 | Puma | Rails 기본 내장 서버, 멀티스레드 |
| ORM | ActiveRecord | Rails 내장 ORM |
| DB 드라이버 | pg gem | PostgreSQL 네이티브 드라이버 |

---

## 다른 프레임워크와의 비교

| 항목 | FastAPI (Python) | Django (Python) | Express (TypeScript) | **Rails (Ruby)** |
|------|------------------|-----------------|---------------------|-------------------|
| 패러다임 | 비동기 (ASGI) | 동기 (WSGI) | 비동기 (Node.js) | **멀티스레드 (Puma)** |
| 타입 검증 | Pydantic | DRF Serializer | Zod | **Strong Parameters** |
| ORM | SQLAlchemy | Django ORM | Prisma | **ActiveRecord** |
| 서버 | Uvicorn | Gunicorn | Node.js 내장 | **Puma** |
| 라우팅 | 데코레이터 기반 | urls.py 중앙 집중 | Router 기반 | **routes.rb DSL** |
| 철학 | 명시적 > 암묵적 | Batteries included | 미니멀 | **Convention > Configuration** |
| GIL | 있음 (GIL) | 있음 (GIL) | 없음 (이벤트 루프) | **있음 (GVL)** |

### GIL vs GVL — 뭐가 다른가?

> **GIL(Global Interpreter Lock)** = Python 용어
> **GVL(Global VM Lock)** = Ruby 용어
>
> 본질은 같다: **한 번에 하나의 스레드만 바이트코드 실행 가능**.
> 하지만 중요한 차이가 있다:
>
> - **Python (GIL)**: I/O 작업 시 GIL 해제 → 다른 스레드 실행 가능
> - **Ruby (GVL)**: 동일하게 I/O 시 GVL 해제, 하지만 **Ractor** 통해 진정한 병렬 실행 가능 (Ruby 3.0+)
>
> **Puma의 접근**: 멀티프로세스(workers) + 멀티스레드(threads) 조합
> - workers: 독립 프로세스 (GVL 독립)
> - threads: 같은 프로세스 내 I/O 대기 시간 활용
>
> **벤치마크 검증 과제**: Auth 시나리오에서 JWT(CPU 바운드) vs Session(I/O 바운드) 비교
> - Python에서는 GIL로 인해 CPU 바운드 JWT가 14% 느렸음
> - Ruby도 GVL이 있으므로 유사한 결과가 예상되지만, Puma의 멀티스레드 모델로 인한 차이 가능

---

## 프로젝트 구조

```
implementations/ruby-rails/
├── app/
│   ├── controllers/
│   │   ├── application_controller.rb    # 공통 베이스 컨트롤러
│   │   ├── health_controller.rb         # GET /health
│   │   ├── echo_controller.rb           # POST /echo
│   │   ├── users_controller.rb          # /users CRUD
│   │   ├── external_controller.rb       # GET /external
│   │   ├── protected_controller.rb      # GET /protected
│   │   └── upload_controller.rb         # POST /upload
│   └── models/
│       ├── application_record.rb        # 모델 베이스 클래스
│       └── user.rb                      # User 모델 (managed: false)
├── config/
│   ├── routes.rb                        # 라우팅 정의
│   ├── database.yml                     # DB 연결 설정
│   ├── puma.rb                          # Puma 서버 설정
│   ├── application.rb                   # Rails 앱 설정
│   └── environments/
│       ├── development.rb
│       └── production.rb
├── db/                                  # migration은 사용하지 않음
├── Gemfile                              # Ruby 의존성
├── Dockerfile
└── .env.example
```

> **참고**: `db/migrate/`는 비어 있음. Django와 동일하게 `managed = False` (Rails에서는 `self.table_name` 직접 지정) 패턴으로 기존 테이블 사용.

---

## Ruby 문법 기초 (Python/TypeScript 개발자용)

Rails 코드를 이해하기 위해 필요한 Ruby 핵심 문법.

### 심볼 (Symbol) — `:symbol`

```ruby
# Python의 문자열 상수와 비슷하지만, 메모리에 단 하나만 존재
:name          # 심볼
"name"         # 문자열

# 해시의 키로 주로 사용 (Python dict의 key와 동일 역할)
user = { name: "Alice", email: "alice@test.com" }
user[:name]    # => "Alice"

# Python 대응
# user = {"name": "Alice", "email": "alice@test.com"}
# user["name"]
```

> **왜 심볼?**: 문자열은 매번 새 객체 생성, 심볼은 한 번만 생성 → 해시 키 비교 시 더 빠름

### 해시 (Hash) — `{key: value}`

```ruby
# 모던 Ruby (1.9+): 심볼 키 축약
params = { name: "Alice", email: "alice@test.com" }

# 옛날 Ruby: 로켓 문법 (=> 사용)
params = { :name => "Alice", :email => "alice@test.com" }

# 두 가지 모두 동일. 모던 방식 사용 권장.

# Python 대응
# params = {"name": "Alice", "email": "alice@test.com"}
```

### 블록 (Block) — `do...end` 또는 `{}`

```ruby
# 블록 = 다른 메서드에 전달하는 코드 조각 (Python의 lambda/callback과 유사)

# do...end (여러 줄)
users.each do |user|
  puts user.name
end

# {} (한 줄)
users.each { |user| puts user.name }

# Python 대응
# for user in users:
#     print(user.name)
#
# 또는: [print(user.name) for user in users]
```

### 클래스 상속 — `<`

```ruby
# Ruby
class UsersController < ApplicationController
  # ...
end

# Python 대응
# class UsersController(ApplicationController):
#     ...

# TypeScript 대응
# class UsersController extends ApplicationController { }
```

### 묵시적 리턴 (Implicit Return)

```ruby
# Ruby: 마지막 표현식이 자동으로 반환됨
def greeting
  "Hello, World!"   # return 없이도 이 값이 반환됨
end

# Python 대응: 반드시 return 필요
# def greeting():
#     return "Hello, World!"
```

### nil — Ruby의 null

```ruby
user = User.find_by(id: 999)  # 없으면 nil 반환
user.nil?   # => true

# Python: None
# TypeScript: null / undefined
```

---

## 구현 단계

### Phase 1: 프로젝트 셋업 ✅ 완료

#### Step 1.1: Ruby 설치 확인

```bash
# Ruby 버전 확인
ruby --version    # 3.3+ 필요

# rbenv 사용 시 (macOS)
brew install rbenv ruby-build
rbenv install 3.3.6
rbenv global 3.3.6

# 또는 Docker만 사용할 경우 로컬 설치 불필요
```

- [x] Ruby 3.3+ 로컬 설치 확인 (rbenv으로 3.3.6 설치)

#### Step 1.2: Rails 프로젝트 생성

```bash
cd implementations

# Rails 설치
gem install rails

# API-only 모드로 프로젝트 생성
rails new ruby-rails --api --database=postgresql --skip-test --skip-action-mailer --skip-action-mailbox --skip-active-storage --skip-action-cable --skip-action-text --skip-jbuilder
```

**플래그 설명**:

| 플래그 | 의미 | 왜 사용? |
|--------|------|---------|
| `--api` | API-only 모드 (뷰/에셋 제외) | REST API만 제공 |
| `--database=postgresql` | PostgreSQL 사용 | 벤치마크 공통 DB |
| `--skip-test` | 테스트 프레임워크 제외 | 벤치마크에 불필요 |
| `--skip-action-mailer` | 메일 기능 제외 | 불필요 |
| `--skip-action-mailbox` | 수신 메일 처리 제외 | 불필요 |
| `--skip-active-storage` | 파일 스토리지 제외 | 자체 구현 |
| `--skip-action-cable` | WebSocket 제외 | 불필요 |
| `--skip-action-text` | 리치 텍스트 제외 | 불필요 |
| `--skip-jbuilder` | JSON 빌더 제외 | `render json:` 직접 사용 |

> **참고**: `rails new`는 자동으로 `bundle install`을 실행한다. Gemfile과 Gemfile.lock이 생성됨.

- [x] `rails new ruby-rails --api --database=postgresql --skip-test --skip-action-mailer --skip-action-mailbox --skip-active-storage --skip-action-cable --skip-action-text --skip-jbuilder`

#### Step 1.3: Gemfile 정리

```ruby
# Gemfile
source "https://rubygems.org"

ruby ">= 3.3"

gem "rails", "~> 8.0"     # Rails 8.x
gem "pg", "~> 1.5"         # PostgreSQL 드라이버
gem "puma", ">= 5"         # 웹 서버

# 필요한 gem만 남기고 나머지 제거
# solid_cache, solid_queue, solid_cable 등은 Phase 7에서 추가 예정
```

**Rails vs Django vs Express 의존성 비교**:

| 역할 | Rails | Django | Express |
|------|-------|--------|---------|
| 프레임워크 | `rails` gem | `django` pip | `express` npm |
| DB 드라이버 | `pg` gem | `psycopg2` pip | `@prisma/adapter-pg` npm |
| 서버 | `puma` gem (내장) | `gunicorn` pip | Node.js 내장 |
| JSON 직렬화 | 내장 (`render json:`) | `djangorestframework` pip | `express.json()` 내장 |

> **핵심 차이**: Rails는 "Batteries Included"가 Django보다 더 극단적. Gemfile이 매우 간결함.

- [x] Gemfile 정리 (불필요한 gem 제거, pg gem 확인)
- [x] `bundle install` 실행

#### Step 1.4: database.yml 설정

```yaml
# config/database.yml
default: &default
  adapter: postgresql
  encoding: unicode
  pool: <%= ENV.fetch("RAILS_MAX_THREADS") { 5 } %>
  url: <%= ENV["DATABASE_URL"] %>

development:
  <<: *default

production:
  <<: *default
```

**Ruby 문법 포인트**:
- `<%= ... %>`: ERB 템플릿 — 환경변수를 YAML에 임베드
- `ENV.fetch("KEY") { default }`: 환경변수가 없으면 블록의 기본값 사용
- `&default` / `<<: *default`: YAML 앵커/머지 — DRY 패턴

> **Django 대응**: `settings.py`의 `DATABASES` 딕셔너리
> **Express 대응**: `prisma.config.ts`의 `datasource.url`

- [x] database.yml에서 DATABASE_URL 환경변수 사용 설정

#### Step 1.5: Puma 벤치마크용 설정

```ruby
# config/puma.rb

# 워커 수 (프로세스) — 각 워커는 독립 GVL
workers ENV.fetch("WEB_CONCURRENCY") { 2 }

# 스레드 수 (워커당) — I/O 대기 시 다른 스레드 실행
threads_count = ENV.fetch("RAILS_MAX_THREADS") { 5 }
threads threads_count, threads_count

# 포트
port ENV.fetch("PORT") { 8000 }

# 환경
environment ENV.fetch("RAILS_ENV") { "production" }

# 워커 부팅 시 DB 커넥션 재설정 (fork 후 필수)
before_worker_boot do
  ActiveRecord::Base.establish_connection
end

# Preload (워커 간 메모리 공유)
preload_app!
```

**Puma vs Gunicorn vs Uvicorn**:

| 설정 | Puma (Rails) | Gunicorn (Django) | Uvicorn (FastAPI) |
|------|-------------|-------------------|-------------------|
| 프로세스 | `workers 2` | `--workers 2` | `--workers 2` (gunicorn) |
| 스레드 | `threads 5, 5` | N/A (sync) | N/A (async) |
| I/O 모델 | 멀티스레드 | 프로세스 기반 | 이벤트 루프 |
| 커넥션 풀 | `pool: 5` (per worker) | DB 설정 | SQLAlchemy 설정 |

> **핵심**: Puma는 **멀티프로세스 + 멀티스레드** 하이브리드 모델.
> - workers(프로세스) = GVL 독립 → CPU 바운드 병렬 처리
> - threads = 같은 프로세스 내 I/O 대기 활용 → DB 쿼리, HTTP 호출 동시 처리
>
> 벤치마크 Docker 리소스(CPU 2, RAM 2GB) 기준: **workers=2, threads=5** 가 적절

- [x] puma.rb 벤치마크용 설정 (workers=2, threads=5, `before_worker_boot` 사용)

---

### Phase 2: Docker 설정 ✅ 완료

#### Step 2.1: Dockerfile

```dockerfile
# 멀티 스테이지 빌드
FROM ruby:3.3-slim AS base

# 런타임 의존성
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y \
    libpq5 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 빌드 스테이지
FROM base AS build

# 빌드 의존성
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Gem 설치
COPY Gemfile Gemfile.lock ./
RUN bundle config set --local deployment true && \
    bundle config set --local without 'development test' && \
    bundle install

# 소스 복사
COPY . .

# Asset precompile 불필요 (API-only)

# 런타임 스테이지
FROM base

# 빌드 결과 복사
COPY --from=build /app /app
COPY --from=build /usr/local/bundle /usr/local/bundle

ENV RAILS_ENV=production
ENV RAILS_LOG_TO_STDOUT=true

EXPOSE 8000

CMD ["bundle", "exec", "puma", "-C", "config/puma.rb"]
```

**멀티 스테이지 빌드란?**

```
┌─────────────────────────────────┐
│ Stage 1: base                   │
│ - Ruby 런타임만                  │
│ - libpq5 (PostgreSQL 클라이언트) │
└─────────────┬───────────────────┘
              │
┌─────────────▼───────────────────┐
│ Stage 2: build (FROM base)      │
│ - build-essential (gcc 등)      │
│ - libpq-dev (pg gem 빌드용)     │
│ - bundle install                │
│ → 빌드 도구 포함 (이미지 큼)      │
└─────────────┬───────────────────┘
              │ COPY --from=build
┌─────────────▼───────────────────┐
│ Stage 3: runtime (FROM base)    │
│ - 빌드 결과만 복사               │
│ - 빌드 도구 없음 → 이미지 작음   │
└─────────────────────────────────┘
```

> **왜 멀티 스테이지?**: `pg` gem은 네이티브 확장(C 코드)을 컴파일해야 함.
> 빌드 도구(gcc, make 등)는 런타임에 불필요하므로 최종 이미지에서 제거 → 이미지 크기 대폭 감소.

- [x] Dockerfile 작성 (멀티 스테이지 빌드, `libyaml-dev`/`libyaml-0-2` 추가 필요)

#### Step 2.2: docker-compose.yml에 서비스 추가

`implementations/docker-compose.yml`에 추가할 내용:

```yaml
  ruby-rails:
    build: ./ruby-rails
    profiles: ["rails"]
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://benchmark:benchmark@postgres:5432/benchmark
      RAILS_ENV: production
      RAILS_LOG_TO_STDOUT: "true"
      SECRET_KEY_BASE: benchmark-secret-key-base-for-testing-only
    depends_on:
      postgres:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 2G
```

**Rails 특이점**:
- `SECRET_KEY_BASE`: Rails가 프로덕션 모드에서 필수로 요구하는 비밀 키 (세션/쿠키 암호화용). API-only에서도 필요.
- `RAILS_LOG_TO_STDOUT`: Docker 로그로 출력 (기본은 파일)
- `RAILS_ENV: production`: 개발 모드의 자동 리로딩/디버깅 비활성화 → 벤치마크에 적합

- [x] docker-compose.yml에 ruby-rails 서비스 추가 (profile: "rails")

#### Step 2.3: 빌드 및 기동 테스트

```bash
cd implementations

# 빌드 및 실행
docker compose --profile rails up --build -d

# 로그 확인
docker compose --profile rails logs -f ruby-rails

# 종료
docker compose --profile rails down
```

- [x] 컨테이너 빌드 및 기동 테스트

---

### Phase 3: 기본 엔드포인트 (경량) ✅ 완료

#### Step 3.1: 라우팅 설정

```ruby
# config/routes.rb
Rails.application.routes.draw do
  # 루트에 직접 매핑 (namespace 없이)
  get  "health",    to: "health#show"
  post "echo",      to: "echo#create"
  get  "users",     to: "users#index"
  post "users",     to: "users#create"
  get  "users/:id", to: "users#show"
  get  "external",  to: "external#show"
  get  "protected", to: "protected#show"
  post "upload",    to: "upload#create"
end
```

**Rails 라우팅 문법**:

```ruby
# "health" 경로로 GET 요청 → HealthController의 show 액션
get "health", to: "health#show"

#  ↓ 분해하면:
#  HTTP 메서드: GET
#  경로: /health
#  컨트롤러: HealthController (자동으로 *_controller.rb에서 찾음)
#  액션: show 메서드
```

**다른 프레임워크 대응**:

| 라우팅 방식 | FastAPI | Django | Express | **Rails** |
|------------|---------|--------|---------|-----------|
| 정의 위치 | 핸들러 데코레이터 | urls.py | Router 체인 | **routes.rb** |
| 스타일 | `@app.get("/health")` | `path('health', view)` | `router.get("/")` | **`get "health", to: "health#show"`** |
| 중앙 집중 | 아니오 | 예 | 아니오 | **예** |

> **참고**: Rails에는 `resources :users`라는 RESTful 라우팅 매크로가 있지만,
> 다른 프레임워크와의 공정한 비교를 위해 명시적으로 매핑한다.

- [x] config/routes.rb 설정

#### Step 3.2: ApplicationController

```ruby
# app/controllers/application_controller.rb
class ApplicationController < ActionController::API
  # API-only 모드: ActionController::API 상속
  # (일반 Rails는 ActionController::Base 상속 — 뷰, CSRF 등 포함)
end
```

**`ActionController::API` vs `ActionController::Base`**:

| 항목 | API (우리가 사용) | Base (풀 Rails) |
|------|-------------------|-----------------|
| CSRF 보호 | 없음 | 있음 |
| 쿠키/세션 | 최소 | 풀 지원 |
| 뷰 렌더링 | JSON만 | HTML, ERB 등 |
| 미들웨어 | 경량 | 모든 미들웨어 |

#### Step 3.3: GET /health

```ruby
# app/controllers/health_controller.rb
class HealthController < ApplicationController
  def show
    render json: { status: "ok", server: "ruby-rails" }
  end
end
```

**Ruby/Rails 문법 포인트**:
- `render json:` — Rails의 JSON 응답 메서드. Python의 `JSONResponse`, Express의 `res.json()`
- `{ status: "ok" }` — Ruby 해시 (Python dict와 동일)
- **메서드 정의**: `def show ... end` (Python: `def show(self):`, JS: `show() { }`)

- [x] GET /health 구현 → `{"status":"ok","server":"ruby-rails"}`

#### Step 3.4: POST /echo

```ruby
# app/controllers/echo_controller.rb
class EchoController < ApplicationController
  def create
    render json: request.raw_post.present? ? JSON.parse(request.raw_post) : {}
  end
end
```

> **주의**: `params`를 사용하면 Rails가 자동으로 파라미터를 래핑/필터링한다.
> 벤치마크에서는 받은 JSON을 그대로 반환해야 하므로 `request.raw_post`를 파싱하여 사용.
>
> **대안**: `params.except(:controller, :action).permit!.to_h`도 가능하지만,
> Rails의 파라미터 래핑 동작(`wrap_parameters`)을 비활성화해야 한다.

**FastAPI/Django/Express 대응**:

```python
# FastAPI: request body 자동 파싱
@app.post("/echo")
async def echo(body: dict):
    return body

# Django DRF: request.data
def post(self, request):
    return Response(request.data)
```

```typescript
// Express: req.body (express.json() 미들웨어)
router.post("/", (req, res) => {
  res.json(req.body);
});
```

- [x] POST /echo 구현 → JSON body 에코

---

### Phase 4: DB 엔드포인트 ✅ 완료

#### Step 4.1: User 모델

```ruby
# app/models/application_record.rb
class ApplicationRecord < ActiveRecord::Base
  primary_abstract_class
end

# app/models/user.rb
class User < ApplicationRecord
  self.table_name = "users"   # 기존 테이블 사용 (migration 없이)

  validates :name, presence: true, length: { maximum: 100 }
  validates :email, presence: true, uniqueness: true
end
```

**ActiveRecord vs Django ORM vs SQLAlchemy vs Prisma**:

| 작업 | ActiveRecord (Rails) | Django ORM | SQLAlchemy | Prisma |
|------|---------------------|------------|------------|--------|
| 전체 조회 | `User.all` | `User.objects.all()` | `select(User)` | `user.findMany()` |
| 단건 조회 | `User.find(id)` | `User.objects.get(id=id)` | `session.get(User, id)` | `user.findUnique()` |
| 조건 조회 | `User.where(name: "A")` | `User.objects.filter(name="A")` | `select(User).where(...)` | `user.findMany({where:})` |
| 생성 | `User.create(attrs)` | `serializer.save()` | `session.add(user)` | `user.create({data:})` |
| 예외 | `ActiveRecord::RecordNotFound` | `User.DoesNotExist` | - | - |

**`self.table_name = "users"` 왜 필요?**

Rails의 Convention: 모델명 `User` → 테이블명 `users` (자동 복수화).
우리 경우 이미 `users` 테이블이 맞지만, **명시적으로 선언**하여 Convention에 의존하지 않는다.

> **Django 대응**: `class Meta: db_table = 'users'; managed = False`
> **Prisma 대응**: `@@map("users")` in schema.prisma

- [x] User 모델 생성 (`self.table_name = "users"`)

#### Step 4.2: GET /users — 전체 사용자 목록

```ruby
# app/controllers/users_controller.rb
class UsersController < ApplicationController
  # GET /users
  def index
    users = User.all.limit(100)
    render json: users, only: [:id, :name, :email, :created_at]
  end
end
```

**Rails의 `render json:` 옵션**:
- `only:` — 특정 컬럼만 포함 (Projection)
- `except:` — 특정 컬럼 제외
- `include:` — 연관 모델 포함 (N+1 관련)

> **Django 대응**: Serializer의 `fields = ['id', 'name', 'email', 'created_at']`
> **FastAPI 대응**: Pydantic 모델의 필드 정의
> **Express 대응**: Prisma `select: { id: true, name: true, ... }`

#### Step 4.3: POST /users — 사용자 생성

```ruby
# app/controllers/users_controller.rb (계속)
class UsersController < ApplicationController
  # POST /users
  def create
    user = User.new(user_params)

    if user.save
      render json: user, only: [:id, :name, :email, :created_at], status: :created
    else
      render json: { errors: user.errors.full_messages }, status: :unprocessable_entity
    end
  end

  private

  def user_params
    params.expect(user: [:name, :email])
  end
end
```

**Strong Parameters 설명**:

```ruby
# Strong Parameters = Rails의 Mass Assignment 보호
# 클라이언트가 보낸 데이터 중 허용된 필드만 통과

def user_params
  params.expect(user: [:name, :email])
  # expect는 Rails 8에서 추가된 메서드
  # 기존: params.require(:user).permit(:name, :email)
end

# 만약 클라이언트가 { user: { name: "A", email: "a@test.com", admin: true } } 를 보내면
# admin 필드는 자동으로 무시됨 → 보안!
```

**다른 프레임워크의 Mass Assignment 보호**:

| 프레임워크 | 방어 메커니즘 |
|-----------|-------------|
| Rails | Strong Parameters (`params.expect`) |
| Django | DRF Serializer의 `fields` |
| FastAPI | Pydantic 모델 (허용 필드만 정의) |
| Express | Zod 스키마 (`safeParse`) |

> **참고**: 요청 JSON이 `{ "name": "A", "email": "a@test.com" }` 형태(user 키 없이)인 경우,
> `params.expect(user: [:name, :email])` 대신 `params.permit(:name, :email)`를 사용하거나
> `wrap_parameters` 설정으로 자동 래핑을 활용할 수 있다.
> 기존 다른 프레임워크들은 user 키 없이 flat JSON을 받으므로, 이 점 주의.

- [x] POST /users 구현 (201 Created)

#### Step 4.4: GET /users/:id — 단일 사용자

```ruby
# app/controllers/users_controller.rb (계속)
class UsersController < ApplicationController
  # GET /users/:id
  def show
    user = User.find(params[:id])
    render json: user, only: [:id, :name, :email, :created_at]
  rescue ActiveRecord::RecordNotFound
    render json: { detail: "Not found" }, status: :not_found
  end
end
```

**Ruby 예외 처리**:

```ruby
# Ruby
begin
  user = User.find(id)
rescue ActiveRecord::RecordNotFound
  # 404 반환
end

# Python 대응
# try:
#     user = User.objects.get(id=id)
# except User.DoesNotExist:
#     return Response(status=404)

# TypeScript 대응
# const user = await prisma.user.findUnique({ where: { id } });
# if (!user) return res.status(404).json({...});
```

> **`find` vs `find_by`**:
> - `User.find(id)` — 없으면 `ActiveRecord::RecordNotFound` 예외 발생
> - `User.find_by(id: id)` — 없으면 `nil` 반환 (예외 없음)
> - 어느 것을 쓰든 선택. `find`가 더 Rails-관용적.

- [x] GET /users/:id 구현 (404 처리 포함)

---

### Phase 5: 나머지 엔드포인트 ✅ 완료

#### Step 5.1: GET /external — 외부 API 호출 시뮬레이션

```ruby
# app/controllers/external_controller.rb
class ExternalController < ApplicationController
  def show
    start = Process.clock_gettime(Process::CLOCK_MONOTONIC)

    sleep(0.1)  # 100ms 지연 시뮬레이션

    latency = ((Process.clock_gettime(Process::CLOCK_MONOTONIC) - start) * 1000).round(2)

    render json: {
      source: "simulated_external_api",
      latency_ms: latency,
      data: { message: "External API response" }
    }
  end
end
```

**sleep의 동작 차이**:

| 프레임워크 | sleep 동작 |
|-----------|----------|
| FastAPI (async) | `await asyncio.sleep(0.1)` — 이벤트 루프 블록하지 않음 |
| Django (sync) | `time.sleep(0.1)` — 워커 스레드 블록 |
| Express (async) | `setTimeout/Promise` — 이벤트 루프 블록하지 않음 |
| **Rails (Puma)** | **`sleep(0.1)` — 현재 스레드 블록, 다른 스레드는 실행 가능** |

> Puma의 멀티스레드 모델 덕분에 `sleep`이 다른 요청을 블록하지 않음.

- [x] GET /external 구현 (100ms sleep 시뮬레이션)

#### Step 5.2: GET /protected — Authorization 헤더 검증

```ruby
# app/controllers/protected_controller.rb
class ProtectedController < ApplicationController
  def show
    authorization = request.headers["Authorization"]

    if authorization.blank?
      return render json: { detail: "Authorization header required" }, status: :unauthorized
    end

    unless authorization.start_with?("Bearer ")
      return render json: { detail: "Invalid authorization format" }, status: :unauthorized
    end

    token = authorization.delete_prefix("Bearer ")

    if token.length < 10
      return render json: { detail: "Invalid token" }, status: :unauthorized
    end

    render json: {
      message: "Access granted",
      user: "user_from_token_#{token[0, 8]}"
    }
  end
end
```

**Ruby 문자열 메서드**:

```ruby
# Ruby                          # Python 대응
str.blank?                      # not str (None/빈문자열 모두 체크)
str.start_with?("Bearer ")      # str.startswith("Bearer ")
str.delete_prefix("Bearer ")    # str.removeprefix("Bearer ")
str[0, 8]                       # str[:8]
"hello_#{variable}"             # f"hello_{variable}" (문자열 보간)
```

- [x] GET /protected 구현 (Authorization 헤더 검증)

#### Step 5.3: POST /upload — 파일 업로드

```ruby
# app/controllers/upload_controller.rb
class UploadController < ApplicationController
  def create
    file = params[:file]

    if file.blank?
      return render json: { detail: "No file uploaded" }, status: :bad_request
    end

    render json: {
      filename: file.original_filename,
      size: file.size,
      content_type: file.content_type
    }
  end
end
```

**파일 업로드 처리 비교**:

| 프레임워크 | 파일 접근 | 파일 객체 |
|-----------|---------|----------|
| FastAPI | `UploadFile` 타입 힌트 | `file.filename`, `file.size` |
| Django | `request.FILES['file']` | `file.name`, `file.size` |
| Express | `multer` 미들웨어 | `req.file.originalname`, `req.file.size` |
| **Rails** | **`params[:file]`** | **`file.original_filename`, `file.size`** |

> Rails는 `multipart/form-data`를 자동으로 파싱한다. 별도 미들웨어 불필요.
> 파일은 `ActionDispatch::Http::UploadedFile` 객체로 전달됨.

- [x] POST /upload 구현 (파일 업로드 처리)

---

### Phase 6: 검증 및 벤치마크 🔄 진행 중

#### Step 6.1: curl 수동 테스트

```bash
# 1. Health check
curl http://localhost:8000/health
# 기대: {"status":"ok","server":"ruby-rails"}

# 2. Echo
curl -X POST http://localhost:8000/echo \
  -H "Content-Type: application/json" \
  -d '{"hello":"world","number":42}'
# 기대: {"hello":"world","number":42}

# 3. Users 목록
curl http://localhost:8000/users
# 기대: [{"id":1,"name":"User1","email":"user1@benchmark.com","created_at":"..."},...]

# 4. User 생성
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name":"RailsUser","email":"rails@benchmark.com"}'
# 기대: {"id":...,"name":"RailsUser","email":"rails@benchmark.com","created_at":"..."} (201)

# 5. User 상세
curl http://localhost:8000/users/1
# 기대: {"id":1,"name":"User1",...}

# 6. User 404
curl http://localhost:8000/users/999999
# 기대: {"detail":"Not found"} (404)

# 7. External API
curl http://localhost:8000/external
# 기대: {"source":"simulated_external_api","latency_ms":100.xx,...}

# 8. Protected (성공)
curl http://localhost:8000/protected \
  -H "Authorization: Bearer test-token-12345"
# 기대: {"message":"Access granted","user":"user_from_token_test-tok"}

# 9. Protected (실패)
curl http://localhost:8000/protected
# 기대: {"detail":"Authorization header required"} (401)

# 10. Upload
curl -X POST http://localhost:8000/upload \
  -F "file=@/path/to/test-file.txt"
# 기대: {"filename":"test-file.txt","size":...,"content_type":"text/plain"}
```

- [x] curl로 8개 엔드포인트 수동 테스트 (2026-02-07 전체 통과)

#### Step 6.2: k6 벤치마크 실행

```bash
cd runner

# 전체 basic 시나리오 실행
./run-benchmark.sh

# 또는 개별 실행
k6 run ../scenarios/basic/01-lightweight.js
k6 run ../scenarios/basic/02-json-payload.js
k6 run ../scenarios/basic/03-db-read.js
k6 run ../scenarios/basic/04-db-write.js
k6 run ../scenarios/basic/05-external-api.js
k6 run ../scenarios/basic/06-middleware-chain.js
k6 run ../scenarios/basic/07-file-upload.js
k6 run ../scenarios/basic/08-concurrent-mixed.js
```

- [ ] k6 basic(01-08) 벤치마크 실행
- [ ] 결과 기록 (docs/99-benchmark-results.md)

---

### Phase 7: (향후) Solid Trio vs Redis

> Rails 8의 핵심 혁신인 **Solid Trio** (Solid Cache, Solid Queue, Solid Cable)를
> 기존 Redis 기반 인프라와 성능 비교하는 벤치마크.

#### Solid Trio란?

| 컴포넌트 | 역할 | 기존 대안 | 핵심 아이디어 |
|---------|------|---------|-------------|
| **Solid Cache** | 캐시 | Redis | DB를 캐시로 사용 (NVMe SSD가 충분히 빠름) |
| **Solid Queue** | 비동기 작업 | Sidekiq (Redis) | DB 기반 작업 큐 |
| **Solid Cable** | WebSocket | Redis pub/sub | DB 기반 pub/sub |

**왜 벤치마크 가치가 있는가?**

DHH(Rails 창시자)의 주장: "2024년 기준, NVMe SSD + DB = Redis에 비해 인프라 복잡도 감소, 성능은 충분"

우리 벤치마크로 검증할 것:
1. **Solid Cache vs Redis** — 캐싱 시나리오(14-16) 재실행
2. **레이턴시 차이**: Redis(인메모리) vs PostgreSQL(SSD)
3. **인프라 복잡도**: Redis 서비스 제거 가능 여부

#### 구현 계획

- [ ] Gemfile에 `solid_cache` gem 추가
- [ ] Solid Cache 설정 (cache store를 PostgreSQL로)
- [ ] 캐싱 엔드포인트 구현 (기존 FastAPI 패턴 참조)
- [ ] Redis 캐싱 엔드포인트도 구현 (비교용)
- [ ] 시나리오 14-16 벤치마크 비교
- [ ] 결과 분석: Solid Cache vs Redis 성능 차이
- [ ] 문서화

---

## 수정할 기존 파일

### 1. `implementations/docker-compose.yml`

Phase 2에서 작성한 ruby-rails 서비스 추가 (위 내용 참조).

### 2. `roadmap.md`

Phase 7에 Solid Trio 시나리오 추가:

```markdown
### Rails Solid Trio vs Redis ⏳ 예정

| 비교 대상 | 설명 | 상태 |
|-----------|------|------|
| Solid Cache vs Redis | 캐싱 시나리오(14-16) 재실행 | ⏳ 예정 |
| Solid Queue vs Sidekiq | 비동기 작업 큐 (새 시나리오) | ⏳ 예정 |
```

---

## 트러블슈팅 (실제 경험)

### 1. SECRET_KEY_BASE 누락

```
ArgumentError: Missing `secret_key_base` for 'production' environment
```

→ 해결: 환경변수 `SECRET_KEY_BASE` 설정 (docker-compose.yml에 포함됨)

### 2. DB 연결 실패

```
PG::ConnectionBad: could not connect to server
```

→ 해결: `depends_on: postgres: condition: service_healthy` 확인

### 3. params 래핑 이슈

Rails가 JSON 요청을 자동으로 모델명으로 래핑할 수 있음:

```json
// 클라이언트가 보낸 것
{ "name": "Alice", "email": "alice@test.com" }

// Rails가 내부적으로 변환
{ "name": "Alice", "email": "alice@test.com", "user": { "name": "Alice", "email": "alice@test.com" } }
```

→ 해결: `wrap_parameters` 설정 확인 또는 `params.permit(:name, :email)` 직접 사용

### 4. created_at 타임존

Rails는 기본적으로 UTC를 사용하지만, JSON 직렬화 시 포맷이 다를 수 있음.

→ 해결: `config/application.rb`에서 `config.active_record.default_timezone = :utc` 확인

### 5. psych gem 빌드 실패 (libyaml 누락)

```
yaml.h not found
An error occurred while installing psych (5.3.1)
```

→ 원인: `psych` gem이 `libyaml` C 라이브러리를 필요로 하지만, Dockerfile에 없었음
→ 해결: base 스테이지에 `libyaml-0-2`, build 스테이지에 `libyaml-dev` 추가

### 6. ActionMailer 상수 에러

```
uninitialized constant ActionMailer (NameError)
class ApplicationMailer < ActionMailer::Base
```

→ 원인: `config/application.rb`에서 `action_mailer` railtie를 주석 처리했지만, `app/mailers/application_mailer.rb` 파일이 남아있었음
→ 해결: `app/mailers/`, `app/jobs/`, `app/views/layouts/mailer.*` 불필요 파일 삭제

### 7. Solid Cache/Queue 설정 에러

→ 원인: `config/environments/production.rb`에 `solid_cache_store`, `solid_queue` 설정이 활성화 되어있었지만, 해당 gem이 Gemfile에 없음
→ 해결: production.rb에서 solid 관련 설정 주석 처리

### 8. Gemfile.lock 불일치 (frozen mode)

```
The dependencies in your gemfile changed, but the lockfile can't be updated because frozen mode is set
```

→ 원인: Gemfile에 `rubocop` gem을 추가한 후 `bundle install`을 로컬에서 실행하지 않음
→ 해결: 로컬에서 `bundle install` 실행하여 Gemfile.lock 업데이트 후 다시 빌드

### 9. on_worker_boot deprecation 경고

```
Use 'before_worker_boot', 'on_worker_boot' is deprecated and will be removed in v8
```

→ 해결: puma.rb에서 `on_worker_boot` → `before_worker_boot`로 변경

### 10. 모노레포 .gitignore 충돌

루트 `.gitignore`에 `lib/`, `*.log` 같은 범용 패턴이 있어 Ruby 파일이 git에서 무시됨
→ 해결: `lib/` → `**/python-*/lib/`, `*.log` → `**/python-*/*.log`로 스코프 제한, Ruby 전용 패턴 추가

---

## 참고: Rails "Convention over Configuration" vs 명시적 프레임워크

| 측면 | Rails (Convention) | FastAPI/Express (Explicit) |
|------|-------------------|---------------------------|
| 파일 이름 | `users_controller.rb` → `UsersController` 자동 | 직접 import |
| 테이블 이름 | `User` 모델 → `users` 테이블 자동 | 직접 지정 |
| 라우팅 | `resources :users` → 7개 RESTful 라우트 자동 | 각각 정의 |
| 직렬화 | `render json: @user` → 자동 | Pydantic/Zod 스키마 필요 |
| DB 연결 | `database.yml` → 자동 풀 관리 | 직접 커넥션 풀 설정 |

> **벤치마크 관점**: Convention 기반의 "마법"이 성능에 미치는 영향을 측정.
> Rails가 자동으로 해주는 것들(직렬화, 파라미터 처리 등)의 오버헤드는?

---

_Last updated: 2026-02-07_
