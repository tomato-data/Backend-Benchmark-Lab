# Scenario 28 — Java + Spring Boot 구현 Q&A

> 토마토의 질문에서 파생된 Q&A 로그. 스펙·구현 해설은 `../../docs/scenarios/28-java-spring-boot-implementation.md`를 본다.
>
> 작성 주체: Claude. 토마토가 질문하고, 답변 중 문서화할 가치가 있는 내용을 Claude가 시간순으로 이 파일에 누적한다.

---

## Java / JVM 기초

### Q: Java 처음인데 Spring Boot 첫 뼈대가 Django의 `startproject`와 어떤 점에서 같고 어떤 점에서 다른가?

`docs/scenarios/28-java-spring-boot-implementation.md` §1 "Django 뼈대와의 대응" 참조.

핵심 차이 두 가지:
1. Spring Boot는 **클래스패스 기반 자동 설정**이라 Django의 `INSTALLED_APPS`처럼 수동 등록이 없다. 의존성에 `spring-boot-starter-web`을 넣기만 하면 Tomcat이 자동으로 기동된다.
2. Java는 컴파일 언어라 **빌드 도구(Gradle/Maven)가 필수**다. `.java` → `.class` 바이트코드 변환 + 의존성 해결 + uber-JAR 패키징을 Gradle이 담당한다.

---

## Gradle / build.gradle.kts

### Q: Gradle이 뭐고 왜 `build.gradle.kts`가 있어야 하나?

Python은 스크립트를 바로 실행할 수 있지만 Java는 `.java` → `.class` 바이트코드로 **먼저 컴파일**되어야 JVM이 돌릴 수 있다. 그 컴파일을 담당하는 것이 빌드 도구고, Gradle이 JVM 진영의 사실상 표준 중 하나다(다른 하나는 Maven).

Gradle은 단순히 컴파일만 하는 것이 아니라:
- **의존성 해결**: `build.gradle.kts`에 적힌 라이브러리를 Maven Central 등에서 다운로드
- **컴파일**: `.java` → `.class`
- **테스트 실행**: `./gradlew test`
- **JAR 패키징**: 실행 가능한 단일 JAR 생성
- **개발 서버 실행**: `./gradlew bootRun`

Django 비유로는 `requirements.txt` + `setup.py` + `Makefile`을 합친 파일이다.

`.kts`는 **Kotlin Script** 확장자. Gradle은 전통적으로 Groovy DSL(`build.gradle`)을 썼지만, 요즘은 Kotlin DSL(`build.gradle.kts`)이 대세다 — IDE 자동완성·타입 체크가 훨씬 좋기 때문. 이 프로젝트는 이후 Kotlin+Spring 구현을 추가할 예정이라 일관성을 위해 처음부터 `.kts`로 시작했다.

### Q: `implementation` / `runtimeOnly` / `testImplementation` 차이가 뭐야?

Gradle은 의존성을 "언제 필요한가"로 분류한다. 목적은 **컴파일 클래스패스를 가볍게**, **IDE 자동완성을 깨끗하게** 유지하는 것.

| 범위 | 컴파일 | 런타임 | 테스트 | 예 |
|---|---|---|---|---|
| `implementation` | ✅ | ✅ | ✅ | Spring MVC, Jackson 등 대부분 |
| `runtimeOnly` | ❌ | ✅ | ✅ | PostgreSQL JDBC 드라이버 |
| `testImplementation` | ❌ | ❌ | ✅ | JUnit, Mockito |
| `testRuntimeOnly` | ❌ | ❌ | 런타임만 | JUnit Platform Launcher |

**PostgreSQL 드라이버가 왜 `runtimeOnly`인가?** 우리 코드는 JDBC 표준 API(`java.sql.Connection`)만 쓰고, 이 인터페이스는 JDK 표준에 포함되어 있다. 드라이버 구현 클래스를 코드에서 직접 참조하지 않기 때문에 컴파일 타임엔 필요 없고, 런타임에 JDBC URL(`jdbc:postgresql://...`)을 보고 동적으로 로드된다. Django의 `psycopg2`가 `requirements.txt`에는 있지만 `import psycopg2`를 우리가 직접 안 하는 것과 같은 구조.

### Q: Spring Boot 의존성에 버전 숫자가 안 적혀 있는데 어떻게 돌아가는 거야?

**BOM (Bill of Materials)** 메커니즘 덕분이다. Spring Boot가 "이 Spring Boot 버전에서 검증된 모든 서드파티 라이브러리의 호환 버전 조합"을 하나의 BOM으로 관리한다. `io.spring.dependency-management` 플러그인이 그 BOM을 읽어서 버전을 자동 주입한다.

그래서 `implementation("org.springframework.boot:spring-boot-starter-web")`만 써도 버전 충돌 없이 돌아간다. Python에서 `django>=4.2,<5.0` 같은 범위를 일일이 쓰는 것과 대조적. JVM 진영의 "수십 개 라이브러리 버전 지옥"을 해결하는 핵심 장치다.

---

## Spring Boot 개념

### Q: `@SpringBootApplication` 한 줄이 실제로 무슨 일을 하는 거야?

이 어노테이션은 사실 **세 개의 합성**이다:

1. **`@Configuration`**: "이 클래스는 Bean 정의의 원천". 필요하면 이 클래스 안에 `@Bean` 메서드를 추가해 수동으로 Bean을 등록할 수 있다.
2. **`@EnableAutoConfiguration`**: **Spring Boot의 핵심 마법**. 클래스패스에 뭐가 있는지 훑어서 조건에 맞는 설정을 자동 적용한다. `spring-boot-starter-web`이 있으면 Tomcat + `DispatcherServlet`이 자동 구성되고, `spring-boot-starter-data-jpa` + `postgresql`이 있으면 `DataSource` + `EntityManagerFactory` + HikariCP 커넥션 풀이 자동 조립된다. Django의 `INSTALLED_APPS`에 수동으로 앱을 추가하는 것을 대체하는 메커니즘.
3. **`@ComponentScan`**: 메인 클래스가 있는 패키지(`com.benchmark.javaspring`)와 **모든 하위 패키지**를 훑어서 `@Controller`/`@Service`/`@Repository`/`@Component` 애노테이션이 붙은 클래스를 자동으로 Bean으로 등록한다.

> **중요한 제약**: `@ComponentScan`의 스캔 루트는 메인 클래스의 패키지다. 앞으로 만들 Controller/Service/Repository는 반드시 `com.benchmark.javaspring.*` 하위에 두어야 자동 발견된다. 다른 위치에 두면 스캔이 안 되어 HTTP 404가 된다.

### Q: `Bean`이 정확히 뭐야?

Spring의 IoC 컨테이너(= Application Context)가 **생명주기를 관리하는 객체**. 컨테이너가 생성·주입·소멸을 담당한다. `@Autowired`나 생성자 주입으로 꺼내 쓸 수 있다.

Django로 치면 settings.py에 등록된 설정 객체, Middleware 인스턴스, DB 연결 풀 등이 "Django가 관리하는 객체"인 것과 비슷하지만, Spring은 이 컨셉을 **더 광범위하고 일관되게** 적용한다. Controller, Service, Repository, 심지어 설정 클래스까지 전부 Bean이다.

### Q: `public static void main(String[] args)` 라는 암호는 뭐야?

Java의 실행 진입점. 모든 Java 프로그램은 JVM이 이 메서드를 호출하면서 시작한다(Python의 `if __name__ == "__main__":`과 같은 역할).

| 토큰 | 뜻 |
|---|---|
| `public` | 바깥(JVM)에서 호출 가능 |
| `static` | 인스턴스 없이 클래스 수준에서 호출 가능 |
| `void` | 반환값 없음 |
| `main` | 진입점 이름(JVM 관례) |
| `String[] args` | 커맨드라인 인자 배열 |

그리고 그 안의 `SpringApplication.run(JavaSpringApplication.class, args)`가 내부적으로 Application Context 생성 → 컴포넌트 스캔 → Auto-Configuration → Bean 주입 → 내장 Tomcat 기동 → 요청 수락까지 전부 처리한다.

---

## 프로젝트 구조

### Q: `src/main/java/com/benchmark/javaspring/` 왜 이렇게 깊은 경로가 필요해?

두 가지 관례가 겹친 결과다.

1. **Maven 표준 디렉토리 레이아웃(Standard Directory Layout)**: `src/main/java`(프로덕션 코드), `src/main/resources`(설정·정적 파일), `src/test/java`(테스트 코드). 거의 모든 Java 프로젝트가 이 구조를 따른다. Gradle도 그대로 답습.
2. **Java 패키지 경로**: `com.benchmark.javaspring`이라는 논리 이름을 디렉토리로 펼치면 `com/benchmark/javaspring/`이 된다. 패키지 이름과 디렉토리 경로는 컴파일러가 강제하는 **1:1 매핑**.

**`com.`으로 시작하는 이유**: "조직 도메인의 역순"이라는 Java 초창기 관례(`apache.org` → `org.apache`). 전 세계에서 unique한 이름 충돌 방지 목적. 필수는 아니지만 관례이고, 오픈소스 라이브러리는 전부 이 규칙을 따른다.

### Q: Gradle Wrapper(`gradlew`)는 왜 있어?

로컬에 Gradle CLI가 설치되어 있지 않아도 **`./gradlew <태스크>`** 한 줄이면 프로젝트가 지정한 정확한 Gradle 버전을 자동으로 다운받아 실행한다. `gradle/wrapper/gradle-wrapper.properties`의 `distributionUrl`이 버전을 고정한다.

이점:
- 팀/CI/개인 PC 전부가 **동일한 Gradle 버전**을 사용해 재현성 보장
- Gradle 자체를 별도 설치 안 해도 되어 진입장벽 낮춤
- 프로젝트마다 다른 Gradle 버전을 충돌 없이 관리

관례상 `gradlew`, `gradlew.bat`, `gradle-wrapper.jar`는 **전부 git에 커밋**한다. 이 프로젝트 루트 `.gitignore`에도 `!gradle/wrapper/gradle-wrapper.jar` 패턴이 있어(무시 예외) 안전하게 추적된다.

---

## Java 언어 기능

### Q: `record`가 정확히 뭐야? FastAPI의 `dataclass` 같은 건가?

**짧은 답**: 네, 거의 맞다. 더 정확하게는 **Python `@dataclass(frozen=True)`** 가 가장 가까운 비유다(일반 `@dataclass`는 기본이 가변이라 미묘하게 다름).

**길게**: `record`는 Java 16(2021)의 정식 언어 기능으로, 불변 데이터 클래스를 한 줄로 선언한다.

```java
public record HealthResponse(String status, String server) {}
```

컴파일러가 자동으로 생성하는 것 6가지:
1. `final` 필드 두 개 — 모두 불변
2. canonical constructor (모든 필드를 받는 생성자)
3. 접근자 메서드 `status()`, `server()` — **주의: `getStatus()`가 아니라 `status()`**
4. `equals()` — 필드 값 기반
5. `hashCode()` — 필드 값 기반 (HashMap 키로 사용 가능)
6. `toString()` — `"HealthResponse[status=ok, server=java-spring]"` 형식
7. (보너스) 클래스 자체가 암묵적으로 `final` — **상속 불가**

### Q: 그럼 FastAPI에서 자주 쓰는 Pydantic `BaseModel`하고는 뭐가 달라?

**가장 큰 차이는 런타임 검증 여부**. Pydantic은 단순 DTO가 아니라 "런타임 검증기"를 겸한다.

| 특성 | Java `record` | Python `@dataclass(frozen=True)` | **Pydantic `BaseModel`** |
|---|---|---|---|
| 불변성 | 항상 | 지정 | 옵션 |
| `__init__` 자동 | ✓ | ✓ | ✓ |
| 필드 기반 equals | ✓ | ✓ | ✓ |
| 필드 기반 hash | ✓ | ✓ | ✓ |
| **런타임 타입 검증** | **✗** | **✗** | **✓** |
| JSON 직렬화 내장 | Jackson이 지원 | 수동 | **내장** |
| 상속 | 불가 | 가능 | 가능 |

Pydantic은 `BaseModel` 상속한 클래스의 `__init__`이 **타입 + 제약을 전부 런타임에 체크**한다:

```python
class UserCreate(BaseModel):
    email: EmailStr
    age: int = Field(ge=0, le=150)

UserCreate(email="not-an-email", age=-5)  # 💥 ValidationError
```

Java record는 **정적 타입 시스템** 덕에 컴파일 타임에 `int`에 `String`을 넣는 건 잡지만, "유효한 이메일인가?", "0 이상인가?" 같은 **도메인 제약**은 record만으로는 검증하지 않는다.

### Q: 그럼 Java에서는 검증을 누가 해?

**Jakarta Validation** (구 Bean Validation, JSR 380)이 담당. `spring-boot-starter-validation` 의존성으로 포함되어 있다. record 필드에 어노테이션으로 선언:

```java
import jakarta.validation.constraints.*;

public record UserCreate(
    @Email String email,
    @Min(0) @Max(150) int age,
    @NotBlank String name
) {}
```

Controller에서 `@Valid`를 붙이면 Spring이 요청 바인딩 직후 자동으로 검증하고, 실패 시 `MethodArgumentNotValidException` → 400 Bad Request로 변환:

```java
@PostMapping("/users")
public User create(@Valid @RequestBody UserCreate request) {
    // 여기 도달했으면 이미 검증 통과 상태
}
```

**역할 분담 정리**:
- **record** = Pydantic의 "데이터 컨테이너" 부분
- **Jakarta Validation** = Pydantic의 "검증 엔진" 부분

Pydantic은 둘을 한 클래스에 합쳤고, Java는 관심사 분리 스타일로 나눴다.

### Q: record 안에서 검증 로직을 넣고 싶으면?

**Compact Constructor** 문법:

```java
public record UserCreate(String email, int age, String name) {
    public UserCreate {           // 파라미터 선언 없이 바디만
        if (age < 0 || age > 150) {
            throw new IllegalArgumentException("age out of range: " + age);
        }
    }
}
```

필드 할당(`this.age = age`)은 컴파일러가 붙여주고, 바디에는 검증·정규화만 작성. Python `@dataclass`의 `__post_init__`과 정확히 대응.

### Q: record는 왜 상속이 안 돼?

값 기반 동등성(equals)을 안전하게 유지하려는 설계 결정. 부모-자식 관계가 생기면 `equals()` 정의가 모호해지는 고전적 문제를 피하기 위해 **암묵적으로 `final`**.

대신 `sealed interface` + record 조합으로 합집합 타입(algebraic data type)을 만들 수 있다:

```java
sealed interface PaymentResult permits Success, Failure {}
public record Success(String transactionId) implements PaymentResult {}
public record Failure(String reason, int code) implements PaymentResult {}
```

TypeScript `type Result = Success | Failure`와 유사한 패턴. 함수형 스타일 도메인 모델에 유용.

### Q: Java 16 이전에는 DTO를 어떻게 만들었어?

**Lombok** 이라는 서드파티 라이브러리가 거의 표준이었다:

```java
@Value  // Lombok 어노테이션
public class HealthResponse {
    String status;
    String server;
}
```

Lombok이 컴파일 타임에 바이트코드를 조작해서 보일러플레이트를 생성했는데:
- IDE 플러그인 필요
- 빌드 툴 호환성 이슈
- "마법스럽다"는 반감

그래서 Java 16에 `record`가 언어 자체로 들어오면서 Lombok 의존도가 크게 줄었다. 이 프로젝트는 **Lombok 없이 record만으로** 진행한다. 의도적 선택 — "Lombok 없어도 된다"를 체감하는 것이 목표.

### Q: Kotlin `data class`와 같은 거야?

사실상 거의 같다. 개념적 발상 자체가 Kotlin/Scala가 먼저였고 Java가 따라간 것. 나중에 Kotlin Spring Boot 구현체를 추가할 때 동일한 DTO를 Kotlin `data class`로 다시 써보며 비교할 예정이다.

---

## 프레임워크 철학 비교

### Q: Spring Boot가 Ruby on Rails랑 굉장히 비슷해 보이는데 실제로 그래?

**짧은 답**: 표면적으로는 매우 비슷하다. 그리고 그게 우연이 아니다 — Spring Boot는 **Rails에서 직접 영감을 받아 만들어진 후배**다. 하지만 한 꺼풀 벗기면 철학·문맥·커뮤니티가 상당히 다르다.

**역사적 사실**:
- 2004 Rails 등장 → "Convention over Configuration" 대중화
- 2005~2013 Spring Framework → 강력하지만 **XML 설정 지옥**으로 악명
- 2014 Spring Boot 1.0 → "Java에도 Rails 같은 경험을 만들겠다"는 명시적 목표로 출시

즉 Rails는 선구자, Spring Boot는 Java의 엔터프라이즈 문맥에 맞춰 재해석한 후배다.

### Q: 구체적으로 뭐가 닮았어?

| 영역 | Rails | Spring Boot |
|---|---|---|
| MVC 아키텍처 | 표준 MVC | `@RestController` / `@Service` / `@Entity` |
| 컨벤션 우선 | `app/models/user.rb` 만들면 자동 | `@Entity` + `@Table` 어노테이션 |
| 내장 서버 | Puma | Tomcat |
| 기본 탑재 ORM | ActiveRecord | Spring Data JPA (Hibernate) |
| 설정 파일 | `config/database.yml`, `config/routes.rb` | `application.yml` |
| 환경별 프로파일 | `development.rb`, `production.rb` | `application-dev.yml`, `application-prod.yml` |
| 의존성 번들링 | Gemfile + bundler | starter 의존성 + BOM |
| 제너레이터 스캐폴딩 | `rails new`, `rails generate` | Spring Initializr + IDE 템플릿 |
| "자동으로 연결" | Rails magic (metaprogramming) | Auto-Configuration (조건부 Bean) |

### Q: 그럼 결정적으로 뭐가 다르지?

**1. Convention의 스펙트럼**

- **Rails**: "코드 자체가 암묵 규약을 따른다"
  ```ruby
  class User < ApplicationRecord; end
  ```
  이 한 줄만으로 `users` 테이블 연결 + `find_by_email` 같은 메서드가 **런타임 metaprogramming으로 동적 생성**. Ruby의 동적 특성 덕분.

- **Spring**: "자동이되 명시적"
  ```java
  @Entity
  @Table(name = "users")
  public class User {
      @Id @GeneratedValue private Long id;
      @Column(nullable = false) private String email;
  }
  ```
  어노테이션을 **명시적으로** 붙여야 하지만, 대신 정적 타입 검증 + IDE 추적이 가능.

**2. 타입 시스템**

| | Rails | Spring Boot |
|---|---|---|
| 타입 | 동적 (Ruby) | 정적 (Java) |
| 메서드 생성 | 런타임 metaprogramming (`method_missing`) | 컴파일/시작 시점 (어노테이션 프로세싱, 프록시) |
| 리팩터링 안전성 | 낮음 (문자열 참조 많음) | 높음 (IDE 추적 완벽) |
| 실행 속도 | 느림 (Ruby VM) | 빠름 (JVM + JIT) |

Spring Data JPA의 `findByEmailAndStatus`는 인터페이스 선언만으로 구현체를 자동 생성하지만, 이건 **컴파일 분석 + 런타임 프록시**로 구현된다. Rails의 `method_missing` 마법과 **같은 효과, 완전히 다른 메커니즘**.

**3. 의존성 주입(DI)의 지위**

- **Rails**: DI는 있지만 거의 안 쓴다. Ruby의 동적 특성 덕에 테스트 시 monkey-patching/mocking으로 충분. DI 컨테이너는 Rails 진영에서 오랫동안 "YAGNI" 취급.
- **Spring Boot**: **DI가 프레임워크의 심장**. 모든 Bean이 생성자 주입으로 연결. 테스트 시 Mock 교체, 환경별 다른 구현 선택이 설계의 중심. Java가 정적 타입이라 런타임 monkey-patching이 어려운 것이 DI 문화의 근본 원인.

**4. 문화와 시장**

| | Rails | Spring Boot |
|---|---|---|
| 타깃 | 스타트업, 빠른 MVP | 엔터프라이즈, 대규모 팀 |
| 대표 사용자 | Shopify, GitHub, Basecamp | 은행, 통신사, 정부, 대기업 |
| 문화 | "개발자 행복" | "예측 가능성, 강건성" |
| 모놀리스 vs MSA | 모놀리스 선호 ("Majestic Monolith") | MSA 주류 |
| 기대 팀 규모 | 1~20명 | 수십~수백 명 |

### Q: 장황함 차이는 어느 정도야?

- Rails: `class User < ApplicationRecord; end` (한 줄)
- Spring Boot: 어노테이션 3~5개 + 필드 + record/Lombok

이 장황함이 **정적 타입 + IDE 지원 + 리팩터링 안전성**으로 바뀐다. 대규모 팀에서 1000개 클래스를 5년간 유지할 때 이 트레이드오프의 가치가 역전될 수 있다. 스타트업 3개월 MVP에는 Rails가 절대 유리.

### Q: 이 둘 중 어느 쪽이 "더 좋다"고 말할 수 있나?

**맥락에 따라 다르다**:
- 1~3명이 3~12개월에 MVP를 만들어야 한다 → **Rails**
- 수십~수백 명 팀이 5년 이상 유지할 엔터프라이즈 시스템 → **Spring Boot**
- 대규모 트래픽 + 복잡한 분산 트랜잭션 → **Spring Boot** (JVM의 튜닝 가능성 + Spring Cloud 생태계)
- Cold start/메모리가 중요한 Serverless → **Rails 유리** (또는 Spring Boot + GraalVM Native Image)

### Q: 벤치마크 랩 관점에서 이 둘을 비교하면 뭐가 나올까?

| 시나리오 | 예상 |
|---|---|
| 01 lightweight | Spring Boot 유리 (JIT, 정적 타입 최적화) |
| 02 JSON payload | Spring Boot 유리 (Jackson이 매우 빠름) |
| 03 DB read | 박빙 — ActiveRecord와 Hibernate 둘 다 상당히 최적화됨 |
| 04 DB write | Spring Boot 약간 유리 |
| 05 external API | 비슷 (I/O 대기가 지배) |
| Cold start | **Rails 압도적 유리** — JVM 부팅 비용이 큼 |
| 메모리 | **Rails 유리** — JVM 힙 오버헤드 |

특히 Cold start와 메모리는 Serverless/K8s autoscaling 환경에서 실무적으로 매우 중요한 차이다. GraalVM Native Image로 Spring Boot의 cold start를 1초 이하로 줄이는 실험이 로드맵에 있다.

### Q: 한 문장 요약?

> Rails는 웹 프레임워크의 표준 공식을 세웠고, Spring Boot는 그 공식을 Java의 엔터프라이즈 문맥에서 재구현했다. 외형은 쌍둥이처럼 닮았지만, 타입 시스템·DI 철학·시장 문화가 다른 "같은 DNA, 다른 환경의 진화형"이다.

---

## 설정 파일

### Q: `application.properties` vs `application.yml` 중 뭘 쓰나?

둘 다 Spring Boot가 기본 인식한다. 내용만 동등하다면 선택은 취향이지만:
- `.properties` — Java 전통. 한 줄당 `key=value`. 중첩 구조 표현이 장황함.
- `.yml` — 계층 구조 표현이 깔끔. `spring.datasource.url`, `spring.jpa.hibernate.ddl-auto` 같은 중첩이 많은 Spring 설정에 잘 맞음.

이 프로젝트는 `.yml`을 채택한다. Rails의 `database.yml`과 톤을 맞추고, 환경별 프로파일(`application-docker.yml`) 분리도 YAML 쪽이 익숙하기 때문.
