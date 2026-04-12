# Java + Spring Boot 구현

## 개요

Java + Spring Boot(Servlet MVC) + Spring Data JPA + 내장 Tomcat을 사용한 벤치마크 API 구현.

> **구현 원칙**: Spring의 관용적 방식(Layered Architecture, Annotation-driven configuration, Auto-configuration)을 따른다. 다른 프레임워크의 패턴을 억지로 이식하지 않는다.

> **학습 맥락**: 토마토는 Java를 처음 다룬다. 이 문서는 "Django/FastAPI는 익숙한데 Java는 처음"인 관점에서 Spring Boot의 첫 뼈대를 **Django와의 대응**으로 풀어가는 것을 목표로 한다. 따라서 기술 스택 표·비교표 이전에 **개념 해설**을 앞에 두었다.

---

## 1. Django 뼈대와의 대응

Django에서 `django-admin startproject myproj` 한 줄로 나오는 뼈대와, Spring Initializr(`start.spring.io`)에서 내려받는 Spring Boot 뼈대는 거의 **1:1 대응**된다.

| 역할                              | Django                                    | Spring Boot (Java)                       |
|-----------------------------------|-------------------------------------------|-------------------------------------------|
| 프로젝트 생성 도구                 | `django-admin startproject`               | `start.spring.io` (Spring Initializr)     |
| 의존성 파일                        | `requirements.txt` / `pyproject.toml`     | `build.gradle.kts` (또는 `pom.xml`)       |
| 진입점 / 실행 방법                  | `manage.py runserver`                     | `./gradlew bootRun` 또는 `java -jar app.jar` |
| 프레임워크 메타 설정               | `settings.py`                             | `application.yml` / `application.properties` |
| 앱 등록                            | `INSTALLED_APPS` 리스트에 수동 추가       | `@ComponentScan`이 패키지 하위를 자동 스캔 |
| 라우팅                             | `urls.py`에 path 리스트                   | `@RestController` 클래스의 메서드마다 `@GetMapping` |
| ORM                                | Django ORM                                | Spring Data JPA (= Hibernate 위 추상화)   |
| 개발 서버 내장                     | `runserver` (개발 전용, WSGI)             | **내장 Tomcat** (프로덕션 그대로 사용 가능) |
| 설정과 코드의 위치                  | `myproj/settings.py` + 앱별 `models.py`   | `application.yml` + 패키지별 `@Service`/`@Entity` |

핵심 차이는 딱 두 가지만 기억하면 된다:

1. **Spring Boot는 "클래스패스에 뭐가 있는지"만 보고 자동으로 결정한다.** Django의 `INSTALLED_APPS`처럼 목록을 수동 관리하지 않는다. 의존성에 `spring-boot-starter-web`을 넣으면 Spring이 "아 웹 서버가 필요하구나" 하고 Tomcat을 자동으로 띄운다. 이게 바로 "자동 설정(Auto-Configuration)"이다.
2. **Java는 컴파일 언어라서 빌드 도구(Gradle/Maven)가 필수다.** Python은 스크립트를 바로 실행할 수 있지만, Java 코드는 `.class` 바이트코드로 먼저 컴파일되어야 JVM이 실행할 수 있다. Gradle이 그 컴파일+의존성 해결+JAR 패키징을 담당한다.

---

## 2. 기술 스택

| 항목         | 선택                    | 이유                                              |
|--------------|-------------------------|---------------------------------------------------|
| 언어         | Java 21 (LTS)           | 최신 LTS, Virtual Threads 지원, Homebrew Temurin  |
| 프레임워크   | Spring Boot 3.5.13      | 3.x 라인 최신 stable. 4.x는 출시 직후라 생태계 미숙 |
| 빌드 도구    | **Gradle 8.x (Kotlin DSL)** | Maven XML보다 간결, Kotlin 후속 추가 시 일관성       |
| HTTP 서버    | 내장 **Tomcat** (Servlet API, Blocking) | Spring MVC 기본값. WebFlux/Netty는 후속 Variant   |
| ORM          | Spring Data JPA (Hibernate) | JVM 진영 사실상의 표준. ActiveRecord/Django ORM 대응 |
| JDBC 드라이버 | `org.postgresql:postgresql` | PostgreSQL 공식 JDBC 드라이버                        |
| 커넥션 풀    | **HikariCP** (Spring Boot 기본 내장)      | 가장 빠른 JVM 커넥션 풀. `DataSource`를 자동 주입 |
| 검증         | Jakarta Validation (Hibernate Validator) | `@NotNull`, `@Email` 같은 표준 어노테이션        |
| 헬스체크/메트릭 | Spring Boot Actuator                      | `/actuator/health`, `/actuator/metrics` 자동 제공  |
| 테스트       | JUnit 5 + Spring Boot Test + AssertJ     | Starter Test에 모두 포함                           |

---

## 3. Spring Initializr — 프로젝트 스캐폴딩

Java 생태계는 "프로젝트를 맨손으로 세팅하는 것"이 상당히 고통스럽다. 버전 호환성 매트릭스가 복잡하기 때문. 그래서 Spring 팀이 **웹 UI + API**로 스캐폴딩 도구를 제공한다: `start.spring.io`.

이 프로젝트에서 사용한 `curl` 명령 (고정값):

```bash
curl -fsSL -o starter.zip \
  -d type=gradle-project-kotlin \
  -d language=java \
  -d bootVersion=3.5.13 \
  -d groupId=com.benchmark \
  -d artifactId=java-spring \
  -d name=java-spring \
  --data-urlencode "description=Java Spring Boot implementation for Backend Benchmark Lab" \
  -d packageName=com.benchmark.javaspring \
  -d packaging=jar \
  -d javaVersion=21 \
  -d dependencies=web,data-jpa,validation,actuator,postgresql \
  https://start.spring.io/starter.zip
```

### 주요 파라미터 의미

| 파라미터         | 값                               | 의미                                                |
|------------------|----------------------------------|-----------------------------------------------------|
| `type`           | `gradle-project-kotlin`          | Gradle + Kotlin DSL (`build.gradle.kts`)            |
| `language`       | `java`                           | Java 코드 (Kotlin 소스 원하면 `kotlin`)             |
| `bootVersion`    | `3.5.13` (주의: `.RELEASE` 접미사 X) | Spring Boot 버전. metadata id와 API param은 다름  |
| `groupId`        | `com.benchmark`                  | Maven coordinate의 그룹 (조직/도메인 역순)           |
| `artifactId`     | `java-spring`                    | Maven coordinate의 아티팩트 (프로젝트명)             |
| `packageName`    | `com.benchmark.javaspring`       | 실제 Java 패키지 경로 (디렉토리 구조 됨)             |
| `packaging`      | `jar`                            | 실행 가능한 uber-JAR. WAR은 외부 컨테이너 배포용     |
| `javaVersion`    | `21`                             | Java 21 toolchain                                    |
| `dependencies`   | 쉼표 구분                         | Initializr가 아는 starter 식별자                     |

> **삽질 노트**: 처음 시도 시 `bootVersion=3.5.13.RELEASE`로 보내면 500 에러가 난다. metadata JSON에는 id가 `3.5.13.RELEASE`로 표시되지만, 실제 API가 받는 값은 순수 버전 문자열 `3.5.13`이어야 한다. Spring Initializr의 문서화되지 않은 관용.

---

## 4. 다운로드된 스켈레톤 구조

```
implementations/java-spring-boot/
├── build.gradle.kts                     # 빌드 스크립트 (의존성·컴파일·플러그인)
├── settings.gradle.kts                  # 프로젝트 이름 선언 (멀티모듈 아닐 때 거의 이거뿐)
├── gradlew                              # Gradle Wrapper 실행 스크립트 (Unix)
├── gradlew.bat                          # Gradle Wrapper 실행 스크립트 (Windows)
├── gradle/wrapper/
│   ├── gradle-wrapper.jar               # Wrapper 부트스트랩 JAR
│   └── gradle-wrapper.properties        # Gradle 버전·배포 URL
└── src/
    ├── main/
    │   ├── java/com/benchmark/javaspring/
    │   │   └── JavaSpringApplication.java   # 메인 클래스 (@SpringBootApplication)
    │   └── resources/
    │       └── application.properties       # 설정 (이후 .yml로 전환)
    └── test/
        └── java/com/benchmark/javaspring/
            └── JavaSpringApplicationTests.java  # 컨텍스트 로딩 확인 기본 테스트
```

Django와 비교해서 놀라는 두 가지:

1. **`src/main/java/` 경로가 왜 이렇게 깊은가?** Maven이 정한 디렉토리 규약(Standard Directory Layout). `src/main/java`는 프로덕션 코드, `src/main/resources`는 리소스(설정·템플릿·정적 파일), `src/test/java`는 테스트 코드. **약속 기반**이라 거의 모든 Java 프로젝트가 같은 모양이다. Gradle도 이 규약을 그대로 따른다.
2. **`com/benchmark/javaspring/` 같은 길고 역순인 디렉토리는 뭔가?** Java의 **패키지 경로**. `com.benchmark.javaspring`이 논리적 이름이고 디렉토리 구조는 그걸 그대로 반영. `com.` 접두사는 과거 "조직 도메인의 역순"을 쓰는 관례(`apache.org` → `org.apache`) — 전 세계적으로 unique한 이름 충돌 방지 목적. 필수는 아니지만 관용이다.

---

## 5. 파일별 해설

### 5-1. `build.gradle.kts` — "뭘 어떻게 빌드할지" 선언

```kotlin
plugins {
    java
    id("org.springframework.boot") version "3.5.13"
    id("io.spring.dependency-management") version "1.1.7"
}

group = "com.benchmark"
version = "0.0.1-SNAPSHOT"
description = "Java Spring Boot implementation for Backend Benchmark Lab"

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(21)
    }
}

repositories {
    mavenCentral()
}

dependencies {
    implementation("org.springframework.boot:spring-boot-starter-actuator")
    implementation("org.springframework.boot:spring-boot-starter-data-jpa")
    implementation("org.springframework.boot:spring-boot-starter-validation")
    implementation("org.springframework.boot:spring-boot-starter-web")
    runtimeOnly("org.postgresql:postgresql")
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

tasks.withType<Test> {
    useJUnitPlatform()
}
```

**Django 비유**: `pyproject.toml` + `settings.py`의 앱 등록을 합친 느낌이지만, 더 중요하게는 **여기가 Make/Rake 같은 빌드 태스크 정의 파일**이라는 점이다. `./gradlew build`, `./gradlew test`, `./gradlew bootRun` 같은 명령은 전부 이 파일에서 정의한 플러그인·태스크를 호출한다.

#### `plugins` 블록

- `java` — 표준 Java 플러그인. `compileJava`, `jar` 태스크 등을 추가한다.
- `org.springframework.boot` — Boot 빌드 플러그인. `bootRun`(개발 서버 실행), `bootJar`(uber-JAR 패키징) 등을 추가.
- `io.spring.dependency-management` — Maven BOM 지원. 이게 뭔지가 다음 포인트.

#### BOM — "버전은 알아서 맞춰줘" 시스템

Java 생태계에서 **수십 개 라이브러리를 동시에 쓸 때 생기는 악명 높은 버전 충돌**을 해결하는 메커니즘이 **BOM(Bill of Materials)**이다. Spring Boot가 "이 Spring Boot 버전에서 검증된 모든 서드파티 라이브러리 버전 조합"을 하나의 BOM으로 관리한다.

그래서 아래처럼 의존성에 **버전 숫자가 전혀 없어도** 된다:

```kotlin
implementation("org.springframework.boot:spring-boot-starter-web")
runtimeOnly("org.postgresql:postgresql")
```

Python의 `requirements.txt`에는 `django>=4.2,<5.0` 같은 버전 범위를 일일이 적어야 하지만, Spring Boot 환경에서는 **Boot 버전 하나만 결정하면 나머지는 자동**이다. 학습 초반엔 낯설지만 익숙해지면 굉장히 편하다.

#### `implementation` vs `runtimeOnly` vs `testImplementation` — 의존성 범위

Gradle은 의존성을 "언제 필요한가"로 분류한다:

| 범위                    | 컴파일 클래스패스 포함? | 런타임 포함? | 테스트 포함? | 예                                               |
|-------------------------|-------------------------|--------------|--------------|--------------------------------------------------|
| `implementation`        | ✅                      | ✅           | ✅           | 대부분의 라이브러리 (Spring MVC, Jackson 등)      |
| `runtimeOnly`           | ❌                      | ✅           | ✅           | JDBC 드라이버 — 코드는 `java.sql.*`만 쓰므로      |
| `testImplementation`    | ❌                      | ❌           | ✅           | JUnit, Mockito — 테스트에서만 쓰는 것             |
| `testRuntimeOnly`       | ❌                      | ❌           | 런타임만      | JUnit Platform Launcher                          |

**왜 PostgreSQL 드라이버가 `runtimeOnly`인가?** JDBC는 표준 API(`java.sql.Connection`, `java.sql.Statement`)로 되어 있어 컴파일 타임엔 드라이버 클래스 이름을 직접 참조하지 않는다. 런타임에 JDBC URL(`jdbc:postgresql://...`)을 보고 드라이버를 동적으로 로드하므로 **컴파일러가 볼 필요가 없다**. `runtimeOnly`로 지정하면 IDE 자동완성에서 드라이버 내부 클래스가 튀어나오지 않아 깔끔하고, 컴파일 클래스패스도 가벼워진다.

Django로 치면 `psycopg2`가 `requirements.txt`에는 있지만 코드에서 `import psycopg2`를 직접 안 쓰는 것과 같다(Django ORM이 알아서 로드).

#### `java { toolchain { ... } }` — JDK 자동 관리

Gradle 6.7+부터 지원하는 기능. `./gradlew build`를 실행하면 **시스템에 설치된 Java 버전과 무관하게** Gradle이 JDK 21을 찾아 쓰거나, 없으면 다운로드한다. 이 프로젝트는 Homebrew로 이미 JDK 21이 깔려 있으므로 그걸 그대로 사용.

팀/CI/개인 PC 간에 JDK 버전 미스매치로 생기는 "내 컴에선 되는데" 문제를 원천 차단하는 장치.

#### `repositories { mavenCentral() }`

Java 진영의 PyPI에 해당. `mavenCentral()`이 공식 중앙 저장소(모든 오픈소스 JAR이 올라가는 곳). Spring 팀의 milestone 빌드 등은 별도 저장소를 추가하기도 한다.

---

### 5-2. `JavaSpringApplication.java` — 진입점

```java
package com.benchmark.javaspring;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class JavaSpringApplication {
    public static void main(String[] args) {
        SpringApplication.run(JavaSpringApplication.class, args);
    }
}
```

총 14줄짜리 파일이지만 여기에 Spring Boot의 모든 마법이 응축되어 있다.

#### `public static void main(String[] args)` — Java 실행의 진입점

모든 Java 프로그램은 `main` 메서드에서 시작한다. Python의 `if __name__ == "__main__":`과 같은 역할. JVM이 클래스 파일을 로드한 뒤 `main`을 호출한다.

- `public` — JVM이 바깥에서 호출할 수 있도록
- `static` — 인스턴스 없이 클래스 수준에서 호출 가능하도록
- `void` — 반환값 없음
- `String[] args` — 커맨드라인 인자 배열

Django의 `manage.py`와 유사하지만, `manage.py`는 파이썬 스크립트라 런타임에 해석되는 반면 Java의 `main`은 **JAR에 패키징된 바이트코드**에서 실행된다.

#### `SpringApplication.run(JavaSpringApplication.class, args)` — Boot 기동 시퀀스

이 한 줄이 내부적으로 하는 일:

1. Spring **Application Context** (IoC 컨테이너) 생성
2. 클래스패스를 스캔해서 `@Component`, `@Service`, `@Repository`, `@Controller`가 붙은 클래스를 모두 찾음
3. 찾은 클래스들을 **Bean**으로 등록 (IoC 컨테이너가 생명주기를 관리하는 객체)
4. Bean 사이의 의존성(`@Autowired` / 생성자 주입)을 자동으로 연결 (Dependency Injection)
5. **Auto-Configuration 체인**을 실행 — 클래스패스에 `spring-boot-starter-web`이 있으므로 `EmbeddedTomcatConfiguration`이 자동 활성화되고, 내장 Tomcat이 포트 8080에서 기동
6. `DispatcherServlet`이 Tomcat에 등록 (HTTP 요청 → Controller 매핑의 중심)
7. 요청 수락 시작

**Django 비유**: `manage.py runserver`가 내부적으로 `wsgi.py`의 `get_wsgi_application()`을 호출해 URL conf를 로드하고 WSGI 서버를 띄우는 것과 비슷하지만, **모든 단계가 런타임에 클래스패스 기반으로 자동화**되어 있다는 점이 다르다.

#### `@SpringBootApplication` — 3개의 어노테이션 합성

이 한 어노테이션은 사실 세 개가 합쳐진 것이다:

| 합성된 어노테이션           | 역할                                                                                  |
|-----------------------------|---------------------------------------------------------------------------------------|
| `@Configuration`            | "이 클래스는 Bean 정의의 원천" — Java-based config. 필요하면 이 클래스 안에 `@Bean` 메서드로 수동 Bean 등록도 가능 |
| `@EnableAutoConfiguration`  | **Spring Boot의 핵심 마법**. 클래스패스에 뭐가 있는지 보고 자동으로 설정 클래스를 골라 적용 |
| `@ComponentScan`            | 이 클래스의 패키지(`com.benchmark.javaspring`)와 **하위 패키지** 전체를 스캔해 `@Component/@Service/@Repository/@Controller`를 자동 발견 |

**중요한 제약**: `@ComponentScan`이 스캔하는 루트는 **메인 클래스가 있는 패키지 기준**이다. 앞으로 작성할 Controller/Service/Repository는 반드시 `com.benchmark.javaspring.*` 하위에 두어야 자동 발견된다. 만약 `com.benchmark.other.UserController`에 두면 스캔이 안 되어 HTTP 요청이 404가 된다.

Django의 `INSTALLED_APPS`처럼 명시적으로 앱을 등록하지 않고, **컨벤션으로 해결**하는 방식.

#### `@EnableAutoConfiguration`이 실제로 어떻게 동작하나 (심화)

Spring Boot JAR 안에는 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` 파일이 있고, 여기에 수백 개의 Configuration 클래스가 나열되어 있다. 각 클래스에는 `@ConditionalOnClass`, `@ConditionalOnMissingBean` 같은 조건 어노테이션이 붙어 있어서 "클래스패스에 Tomcat이 있을 때만 활성화", "사용자가 수동으로 Bean을 등록하지 않았을 때만 활성화" 같은 규칙으로 걸러진다.

즉, 자동 설정 = **조건부 Bean 등록의 거대한 체인**. 이 구조 덕분에 의존성 하나만 추가해도 필요한 Bean들이 자동으로 조립된다.

---

### 5-3. `settings.gradle.kts`

```kotlin
rootProject.name = "java-spring"
```

단일 모듈 프로젝트에서는 사실상 프로젝트명 선언만 한다. 멀티모듈(`include(":api", ":core")`)이 될 때 의미가 커진다. 당장은 신경 쓸 필요 없음.

---

### 5-4. `gradlew` / `gradlew.bat` / `gradle-wrapper.jar` — Gradle Wrapper

Gradle CLI를 시스템에 별도 설치하지 않아도 **`./gradlew <태스크>`** 명령으로 프로젝트에 지정된 정확한 버전의 Gradle을 실행할 수 있게 해주는 부트스트랩 스크립트. 프로젝트마다 사용하는 Gradle 버전이 달라도 서로 충돌하지 않는다.

`gradle/wrapper/gradle-wrapper.properties`에 `distributionUrl=https\://services.gradle.org/distributions/gradle-8.14.3-bin.zip` 같은 줄이 있어서, 최초 실행 시 해당 URL에서 Gradle을 받아 `~/.gradle/wrapper/dists/`에 캐시한다.

**Wrapper를 왜 쓰는가?**
- 팀/CI/로컬이 전부 동일한 Gradle 버전을 사용해 재현성 보장
- Gradle 자체를 별도 설치하지 않아도 되어 진입장벽 낮춤
- 프로젝트별로 다른 Gradle 버전 독립 관리

관례상 `gradle`, `gradlew`, `gradlew.bat`, `gradle-wrapper.jar` 모두 **git에 커밋**한다 (wrapper JAR까지 포함). 이 프로젝트 루트 `.gitignore`에도 `!gradle/wrapper/gradle-wrapper.jar`로 예외 처리되어 있다(건너뛰지 않도록).

---

### 5-5. `src/main/resources/application.properties`

기본값은 빈 파일. 이 프로젝트에서는 곧 `application.yml`로 바꾸고 DB 연결·Tomcat 포트·JPA 설정을 채워 넣을 예정이다 (Step 2).

**Django 비유**: `settings.py` 역할. 단, Java는 코드가 아니라 **외부 설정 파일**로 분리한다. 코드 재컴파일 없이 환경별로 바꿀 수 있는 장점이 있고, `application-{profile}.yml` 형태로 환경(dev/prod/docker)별 분리도 가능하다.

---

### 5-6. `src/test/java/com/benchmark/javaspring/JavaSpringApplicationTests.java`

Initializr 기본 제공 테스트:

```java
@SpringBootTest
class JavaSpringApplicationTests {
    @Test
    void contextLoads() { }
}
```

아무것도 검증하지 않는 것처럼 보이지만, `@SpringBootTest`가 붙어 있어 **실제로 전체 애플리케이션 컨텍스트를 기동**하는 테스트다. Bean 등록·의존성 주입·Auto-Configuration에 실패가 있으면 이 테스트 하나만으로도 잡힌다. "smoke test" 역할.

---

## 6. 다음 단계 (Step 2~)

| Step | 작업 | 담당                                        |
|------|------|---------------------------------------------|
| 2    | `application.properties` → `application.yml` 전환 + DB/Tomcat/JPA 설정 | Claude (설정 파일)                          |
| 3    | `/health` 엔드포인트 구현                       | 토마토 (스니펫 + 설명 → 직접 타이핑)        |
| 4    | `Dockerfile` (multi-stage: JDK build → JRE run)  | Claude                                       |
| 5    | `docker-compose.yml`에 `java-spring` 서비스 추가 | Claude                                       |
| 6    | 로컬 빌드·실행 검증 (`./gradlew bootRun`, curl)  | 공동                                         |
| 7    | k6 `scenario 01-lightweight` 실행                 | 공동                                         |
| 8    | 이 문서에 벤치마크 결과 추가 + 회고를 `learnings/`에 기록 | 공동                                         |

---

## 7. 자주 나오는 Q (학습 로그)

토마토가 진행 중 떠올린 질문은 `learnings/qna/scenario28.md`에 쌓는다. 이 문서에는 **스펙/구현에 해당하는 개념 해설**만 두고, 토마토의 즉흥적 사고 흐름은 learnings 쪽으로 분리.
