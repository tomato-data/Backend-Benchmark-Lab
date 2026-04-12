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

## 설정 파일

### Q: `application.properties` vs `application.yml` 중 뭘 쓰나?

둘 다 Spring Boot가 기본 인식한다. 내용만 동등하다면 선택은 취향이지만:
- `.properties` — Java 전통. 한 줄당 `key=value`. 중첩 구조 표현이 장황함.
- `.yml` — 계층 구조 표현이 깔끔. `spring.datasource.url`, `spring.jpa.hibernate.ddl-auto` 같은 중첩이 많은 Spring 설정에 잘 맞음.

이 프로젝트는 `.yml`을 채택한다. Rails의 `database.yml`과 톤을 맞추고, 환경별 프로파일(`application-docker.yml`) 분리도 YAML 쪽이 익숙하기 때문.
