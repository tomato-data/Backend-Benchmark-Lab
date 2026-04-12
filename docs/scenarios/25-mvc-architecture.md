# MVC 아키텍처 — Rails, Django, FastAPI, Express 비교

> Ruby on Rails 구현 과정에서 발견한 아키텍처 패턴 비교.
> "왜 Rails는 아키텍처를 개발자가 정할 필요가 없는가?"에서 시작된 탐구.

---

## MVC란?

**Model - View - Controller** — 데이터, 표현, 제어를 분리하는 설계 원칙.

```
[사용자 요청] → Controller → Model → Controller → View → [응답]
                 (흐름 제어)   (데이터)              (표현)
```

| 계층 | 역할 | 핵심 질문 |
|------|------|----------|
| **M**odel | 데이터 + 비즈니스 로직 | "데이터를 어떻게 저장/검증하는가?" |
| **V**iew | 응답 표현 | "사용자에게 무엇을 보여주는가?" |
| **C**ontroller | 요청 처리 + 흐름 제어 | "요청을 받아서 어디로 보내는가?" |

---

## Rails의 MVC — Convention으로 강제

Rails는 `rails new`를 실행하면 MVC 디렉토리가 자동 생성되고, **파일 이름과 위치까지 Convention으로 고정**된다.

```
app/
├── models/          # M — 데이터 + 비즈니스 로직
│   └── user.rb
├── views/           # V — 응답 렌더링
│   └── users/
│       └── index.html.erb
├── controllers/     # C — 요청 처리 + 응답 반환
│   └── users_controller.rb
```

### Convention 예시

- `UsersController` → 반드시 `app/controllers/users_controller.rb`에 위치
- `User` 모델 → 반드시 `app/models/user.rb`에 위치
- `users` 라우팅 → 자동으로 `UsersController` 탐색

개발자가 아키텍처를 설계할 필요가 없다. **"The Rails Way"가 곧 아키텍처**.

### 장단점

| | 설명 |
|---|------|
| **장점** | 아키텍처 고민 불필요. 팀원 누구나 같은 구조 → 온보딩 빠름 |
| **단점** | 복잡한 비즈니스 로직이 커지면 모델이 비대해짐 ("Fat Model" 문제) |

> Fat Model 문제가 생기면 `app/services/`, `app/queries/` 같은 디렉토리를 추가하지만,
> 이는 Rails Convention이 아닌 개발자의 확장 영역이다.

---

## View는 프론트엔드만을 의미하는가?

**아니다.** View = "사용자에게 보여주는 응답"이다.

| 컨텍스트 | View의 형태 |
|---------|------------|
| 풀스택 웹 | HTML 템플릿 (ERB, Jinja2) |
| API 서버 | **JSON 응답** |
| 데스크톱 앱 | GUI 화면 |
| 모바일 앱 | UI 컴포넌트 |

MVC는 "데이터 / 표현 / 제어를 분리하라"는 설계 원칙이지, 프론트엔드 유무와는 관계없다.

### Rails API-only에서의 MVC

우리 벤치마크 프로젝트(API-only)에서도 MVC는 적용된다:

```
M (Model)      → app/models/user.rb                    — 데이터 + 검증
V (View)       → render json: user                     — JSON 직렬화 (코드 한 줄로 처리)
C (Controller) → app/controllers/users_controller.rb   — 요청 라우팅 + 흐름 제어
```

`app/views/` 디렉토리를 사용하지 않을 뿐, `render json:`이 View 역할을 한다.

### Rails 풀스택에서의 View

API가 아닌 풀스택 웹 앱을 만들 때는 `app/views/`에 ERB 템플릿을 사용한다:

```ruby
# 컨트롤러
class UsersController < ApplicationController
  def index
    @users = User.all
    # render를 명시하지 않아도 Convention으로 뷰 자동 탐색
  end
end
```

```erb
<!-- app/views/users/index.html.erb -->
<h1>사용자 목록</h1>
<% @users.each do |user| %>
  <p><%= user.name %> - <%= user.email %></p>
<% end %>
```

`UsersController#index` → `app/views/users/index.html.erb`를 **자동으로** 찾아서 렌더링한다.

### API-only vs 풀스택

| 항목 | API-only (우리) | 풀스택 |
|------|----------------|--------|
| 베이스 클래스 | `ActionController::API` | `ActionController::Base` |
| View | 없음 (`render json:`) | ERB/Haml 템플릿 |
| CSRF 보호 | 없음 | 있음 |
| 세션/쿠키 | 최소 | 풀 지원 |
| 프론트엔드 | React/Vue 등 별도 | Rails가 HTML 생성 |

---

## Django의 MTV — 이름만 다른 MVC

Django는 MVC를 **MTV (Model - Template - View)** 라고 부른다.

혼란의 핵심: **Django의 "View"는 MVC의 Controller 역할**이다.

| MVC (일반) | MTV (Django) | 역할 |
|-----------|-------------|------|
| **M**odel | **M**odel | 데이터 + 비즈니스 로직 |
| **V**iew | **T**emplate | 응답 표현 (HTML/JSON) |
| **C**ontroller | **V**iew | 요청 처리 + 흐름 제어 |

```python
# Django의 "View" — 사실상 Controller
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()        # M (Model)
    serializer_class = UserSerializer     # T (Template 역할 — JSON 직렬화)
```

```html
<!-- Django의 "Template" — 사실상 View (풀스택일 때만 사용) -->
<h1>{{ user.name }}</h1>
```

> Django 공식 문서에서도 "우리의 View는 전통적 MVC의 Controller에 가깝다"고 인정한다.

---

## 프레임워크별 MVC 대응표

### 역할 기준 비교

| 역할 | Rails | Django | FastAPI | Express |
|------|-------|--------|---------|---------|
| **데이터 (M)** | `app/models/` | `models.py` | `models.py` + SQLAlchemy | `prisma/schema.prisma` |
| **흐름 제어 (C)** | `app/controllers/` | `views.py` (ViewSet) | `routers/` | `routes/` |
| **응답 표현 (V)** | `render json:` / ERB | Serializer / Template | Pydantic 스키마 → JSON | `res.json()` |

### 아키텍처 자유도 비교

| 항목 | Rails | FastAPI | Django | Express |
|------|-------|---------|--------|---------|
| 아키텍처 | **MVC 강제** | 자유 (개발자 선택) | MTV 권장 | 자유 |
| 디렉토리 | Convention으로 고정 | 자유 배치 | 앱 단위 권장 | 자유 배치 |
| 파일명 규칙 | 클래스명에서 자동 유추 | 없음 | 느슨한 관례 | 없음 |

> **벤치마크 프로젝트에서의 시사점**:
> FastAPI에서는 pragmatic vs strict(Clean Architecture) 두 가지 아키텍처를 만들어 비교했다.
> Rails에서는 그런 선택지가 없다. Convention이 곧 아키텍처이므로 **구현 하나로 충분**하다.

---

## 핵심 정리

1. **MVC는 프론트엔드 유무와 무관한 설계 원칙**이다. JSON 응답도 View다.
2. **Rails는 MVC를 Convention으로 강제**한다. 개발자가 아키텍처를 고민할 필요가 없다.
3. **Django의 MTV는 MVC와 본질적으로 같다.** 이름만 다르고 View↔Controller가 뒤바뀌어 있다.
4. **FastAPI/Express는 아키텍처가 자유**다. 장점이자 단점 — 팀마다 구조가 다를 수 있다.
5. 결국 중요한 건 이름이 아니라 **"데이터 / 표현 / 제어의 분리"** 원칙을 지키는 것이다.

---

_Last updated: 2026-02-07_
