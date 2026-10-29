---
name: java-engineering
description: "Rule catalog and verification gates for production Java (JDK 17-27, Oct 2026 toolchain): modern idioms by release, JSpecify + NullAway nullness, exceptions, resources, concurrency and virtual threads, performance with JMH/JFR, secure coding, JPA/JDBC, Spring Boot 4, Maven/Gradle build hygiene, and testing with JUnit 6, AssertJ, Mockito and Testcontainers. Use when writing, reviewing, testing, profiling or upgrading Java code, pom.xml or build.gradle(.kts) files."
---

# Java engineering: rules and gates

This skill is the reference the `java-engineer` agent applies on every change. Rules have stable
IDs so reviews can cite them (`JV-CONC-03`). Each rule says what to do and, where it is not obvious,
why. Versions were checked on 2026-10-29; see the agent's toolchain table and `sources/java.md`.

Read the references when you need the detail:
- `references/build-recipes.md`: copy-ready Maven and Gradle fragments for `-Xlint`, Error Prone +
  NullAway, Spotless, Surefire/Failsafe, JaCoCo, PIT, JMH, jcstress, Mockito agent (Maven and
  Gradle), dependency checks, and packaging (reproducible builds, jlink/jpackage, Jib, Spring Boot
  images, Central Portal publishing).
- `references/jvm-diagnostics.md`: symptom-first JVM diagnosis with jcmd, JFR, async-profiler, NMT
  and heap dumps, with safety tiers.

## 0. Detect before you write

| Question | Where to look | Command |
|---|---|---|
| Target Java release | `maven.compiler.release`, `<release>`, Gradle `toolchain.languageVersion` / `options.release` | `./mvnw help:evaluate -Dexpression=maven.compiler.release -q -DforceStdout` |
| JDK running the build | wrapper output | `./mvnw -v` / `./gradlew --version` |
| Framework + version | parent POM, BOM import, Gradle plugin | `./mvnw dependency:tree -Dincludes=org.springframework.boot` |
| Test stack | `src/test/java` imports, BOMs | `grep -rl "org.junit.jupiter" src/test | head` |
| Static analysis present | compiler args, plugins | `grep -nE "errorprone|nullaway|spotless|checkstyle|spotbugs|pmd|jacoco" pom.xml build.gradle*` |
| Formatter style | `.editorconfig`, Spotless config | — |

Never use a language feature newer than the target release, and never raise the release, a build
tool major, or a framework major as a side effect of another task.

## 1. Language and API (JV-LANG)

- **JV-LANG-01** Data carriers are records; validate invariants in the compact constructor and copy
  mutable components (`items = List.copyOf(items)`), because records are only shallowly immutable.
- **JV-LANG-02** Closed hierarchies are `sealed`; consume them with an exhaustive `switch` with no
  `default`, so a new subtype is a compile error at every unhandled site.
- **JV-LANG-03** Use record patterns and guarded patterns (`case Point(var x, var y) when x > 0`)
  instead of `instanceof` chains (21+).
- **JV-LANG-04** Return unmodifiable collections (`List.copyOf`, `stream().toList()`); never return
  `null` for a collection or array.
- **JV-LANG-05** `java.time` only; inject `Clock`; store instants in UTC; convert to zones at the
  edges.
- **JV-LANG-06** `var` only when the type is evident from the initializer.
- **JV-LANG-07** Use `SequencedCollection` methods (`getFirst`, `getLast`, `reversed`) on 21+
  instead of index arithmetic; `getFirst()` on an empty list throws.
- **JV-LANG-08** Text blocks for multi-line literals; never use `.formatted()` to build SQL, JSON or
  HTML from untrusted input.
- **JV-LANG-09** Prefer composition and small interfaces over inheritance; make classes `final`
  unless designed for extension.
- **JV-LANG-10** Markdown doc comments (`///`, 23+) are fine in new code if the project targets 23+;
  otherwise classic Javadoc. Document every public API's nullness, exceptions and thread safety.
- **JV-LANG-11** Preview and incubator APIs (in 27: structured concurrency, lazy constants,
  primitive patterns, Vector API, PEM) are off-limits in production code unless the user opts in
  to `--enable-preview` for compile, test and run.

## 2. Nullness (JV-NULL)

- **JV-NULL-01** Add `@NullMarked` (`org.jspecify.annotations`) in `package-info.java` and mark the
  exceptions `@Nullable`. JSpecify 1.0.x is the standard; Spring Framework 7 uses it.
- **JV-NULL-02** Enforce with NullAway at `ERROR` severity: exactly one of
  `-XepOpt:NullAway:OnlyNullMarked=true` or `-XepOpt:NullAway:AnnotatedPackages=com.acme`
  (passing both or neither fails the build at load).
- **JV-NULL-03** JSpecify mode (`-XepOpt:NullAway:JSpecifyMode=true`) needs javac from JDK 22+, or
  `-XDaddTypeAnnotationsToSymbol=true` on an OpenJDK 21.0.8+ build; build with the newest JDK and
  target older releases with `--release`.
- **JV-NULL-04** `Optional` only as a return type; never fields, parameters, or `Optional<List<>>`.
  Use `orElseThrow()`, `map`, `orElse`; never bare `get()`.
- **JV-NULL-05** Public entry points validate with `Objects.requireNonNull(arg, "arg")` or Bean
  Validation at framework boundaries.

## 3. Errors (JV-ERR)

- **JV-ERR-01** Throw specific exceptions; unchecked for programming errors and invariant
  violations, checked only when the caller can reasonably recover.
- **JV-ERR-02** Chain the cause (`new PaymentException("charge failed for " + orderId, e)`); include
  identifiers, never secrets or personal data, in messages.
- **JV-ERR-03** No empty `catch`; no `catch (Throwable)` or `catch (Error)` outside top-level task
  boundaries; no `e.printStackTrace()`.
- **JV-ERR-04** `InterruptedException`: restore with `Thread.currentThread().interrupt()` and exit
  or rethrow. Swallowing it breaks cancellation and shutdown.
- **JV-ERR-05** Log or rethrow, not both; the handler logs once with the exception as the last
  SLF4J argument.
- **JV-ERR-06** Translate at boundaries: HTTP via `@RestControllerAdvice` returning `ProblemDetail`
  (RFC 9457); messaging via dead-letter handling; never expose stack traces to clients.
- **JV-ERR-07** Secondary failures during cleanup go into `addSuppressed`, which try-with-resources
  does for you.

## 4. Resources and memory (JV-RES)

- **JV-RES-01** Every `AutoCloseable` lives in try-with-resources: JDBC `Connection`/`Statement`/
  `ResultSet`, streams, `Files.lines/list/walk`, `ExecutorService` (`close()` since 19),
  `HttpClient` (`close()` since 21).
- **JV-RES-02** Caches and queues are bounded (Caffeine `maximumSize`, `ArrayBlockingQueue`); an
  unbounded `HashMap` cache keyed by request data is a memory leak.
- **JV-RES-03** `ThreadLocal.remove()` in `finally`; on 25+ prefer `ScopedValue` for
  request context, which cannot leak across pooled threads.
- **JV-RES-04** Containers: `-XX:MaxRAMPercentage` (typically 70-80) instead of a fixed `-Xmx`;
  leave headroom for metaspace, thread stacks, direct buffers and code cache.
- **JV-RES-05** GC: G1 is the default everywhere from JDK 27 (JEP 523). Choose ZGC (generational
  only since 24) for large heaps with strict pause targets, after measuring.
- **JV-RES-06** Do not use `finalize`, `Runtime.runFinalization`, or `System.gc()` as control flow;
  use `Cleaner` for native resource backstops.

## 5. Concurrency (JV-CONC)

- **JV-CONC-01** Order of preference: immutability, confinement, concurrent collections and
  atomics, then locks. Annotate every mutable shared field with its guarding lock.
- **JV-CONC-02** Virtual threads for blocking I/O: `Executors.newVirtualThreadPerTaskExecutor()` or
  `spring.threads.virtual.enabled=true`. One virtual thread per task, never pooled.
- **JV-CONC-03** Limit concurrency to a downstream (DB pool, rate-limited API) with a `Semaphore`
  sized to that resource, not with a thread-pool size.
- **JV-CONC-04** JDK 21-23 with virtual threads: no `synchronized` around blocking calls (carrier
  pinning); use `ReentrantLock`. JDK 24+ (JEP 491) removed nearly all such pinning; verify with JFR
  `jdk.VirtualThreadPinned`.
- **JV-CONC-05** Platform pools: bounded queue, named threads, explicit `RejectedExecutionHandler`
  (`CallerRunsPolicy` gives backpressure), and orderly shutdown.
- **JV-CONC-06** No blocking I/O in the common `ForkJoinPool`, parallel streams or
  `CompletableFuture.*Async` without an executor argument.
- **JV-CONC-07** Every remote call has connect and request timeouts; retries are bounded, jittered,
  and limited to idempotent operations.
- **JV-CONC-08** Avoid lock-order deadlocks with a global ordering or `tryLock(timeout)`; never call
  alien code (callbacks, listeners) while holding a lock.
- **JV-CONC-09** High-contention counters use `LongAdder`; read-mostly listener lists use
  `CopyOnWriteArrayList`.
- **JV-CONC-10** Test concurrent code with deterministic coordination (`CountDownLatch`,
  Awaitility), never `Thread.sleep`; JMM-sensitive lock-free code gets a `jcstress` test
  (build-recipes section 7: `java -jar target/jcstress.jar -t <Test> -m quick`; any count in a
  `Forbidden` row fails the test).
- **JV-CONC-11** `StructuredTaskScope` is still preview in JDK 27 (seventh preview, JEP 533); its
  API changed between previews. Do not ship it without explicit opt-in.

## 6. Performance (JV-PERF)

- **JV-PERF-01** No optimization without a measurement: JMH for code-level, JFR or async-profiler
  for system-level. State baseline and result with error margins, same JDK and flags.
- **JV-PERF-02** JMH rules: return or `Blackhole.consume` results, use `@State` for inputs, fork at
  least twice, warm up, and run `-prof gc` to see allocation per operation. On JDK 23+ the 1.37
  archetype POM needs `jmh-generator-annprocess` in `annotationProcessorPaths` (or `-proc:full`);
  without it `mvn package` still passes but the jar fails with
  `Unable to find the resource: /META-INF/BenchmarkList` (JV-BUILD-04).
- **JV-PERF-03** Avoid boxing in hot paths (primitive streams, primitive arrays), presize
  collections, reuse immutable objects, avoid regex compilation in loops (`Pattern` as a constant).
- **JV-PERF-04** Database first: most latency in business apps is queries. Kill N+1 (fetch joins,
  `@EntityGraph`, `hibernate.default_batch_fetch_size`), paginate, and index what you filter on.
- **JV-PERF-05** Startup: JDK 25+ AOT cache (`java -XX:AOTCacheOutput=app.aot -jar app.jar`
  training run, then `-XX:AOTCache=app.aot`) is the first lever; GraalVM native image (Spring
  Boot 4 needs GraalVM 25+) is the second, with its reflection and testing costs. Train and run
  from jars only: a non-empty directory on the class path (`-cp target/classes`) makes the
  training run fail with "Cannot have non-empty directory in paths". For Spring Boot, extract
  first (`java -Djarmode=tools -jar app.jar extract --destination application`) and train with
  `-Dspring.context.exit=onRefresh -jar application/app.jar`.
- **JV-PERF-06** Compact object headers (`-XX:+UseCompactObjectHeaders`, product in 25, default in
  27) reduce heap use; measure before and after on 25.

## 7. Security (JV-SEC)

- **JV-SEC-01** Bind parameters for SQL/JPQL/HQL/LDAP; no string concatenation of untrusted input
  into queries, commands, paths, or log patterns.
- **JV-SEC-02** No `ObjectInputStream` on untrusted data; if legacy code needs it, add a
  `jdk.serialFilter` allow-list. Jackson: no default typing, no polymorphic `@JsonTypeInfo` on
  untrusted input with class-name ids.
- **JV-SEC-03** XML: disable DTDs/external entities on `DocumentBuilderFactory`, `SAXParserFactory`,
  `XMLInputFactory`, `TransformerFactory`.
- **JV-SEC-04** Crypto: Argon2id/BCrypt for passwords, AES-GCM with a random 12-byte IV,
  `SecureRandom` for tokens, TLS 1.2+ only; no MD5/SHA-1/DES/ECB for security.
- **JV-SEC-05** Secrets from env or a secret manager; never in code, tests, `application.yml`
  defaults, or logs. Mask them in `toString()` of config records.
- **JV-SEC-06** Spring Security: deny by default, method security for domain rules, CSRF on for
  cookie sessions, CORS allow-list. Actuator: only `health` (the default) on the public port.
- **JV-SEC-07** Paths from users: `base.resolve(input).normalize()` then `startsWith(base)` check.
- **JV-SEC-08** Every new or upgraded dependency is checked (OSV-Scanner, dependency-check, or the
  maven-tools MCP CVE lookup) and its license noted.

## 8. Data and I/O (JV-DATA)

- **JV-DATA-01** JPA entities: no Lombok `@Data`, `equals/hashCode` on the id with null-safe
  handling (or business key), associations `LAZY`, `toString` without associations.
- **JV-DATA-02** Transactions at the service layer (`@Transactional` on public methods called from
  outside the bean); read-only transactions for queries; no remote calls inside a DB transaction.
- **JV-DATA-03** Disable `spring.jpa.open-in-view` (Boot default is `true`) and load what the view
  needs in the service.
- **JV-DATA-04** Schema changes through Flyway or Liquibase migrations, never `ddl-auto=update`
  outside throwaway local runs.
- **JV-DATA-05** `HttpClient`/`RestClient`: explicit timeouts, status-code handling, and response
  size limits; JSON mapped to records.
- **JV-DATA-06** Jackson 3 (`tools.jackson.*`) is the Spring Boot 4 default; annotations still live
  in `com.fasterxml.jackson.annotation`. Do not mix Jackson 2 and 3 mappers without reason.

## 9. Spring Boot 4 (JV-SPRING), only when the project uses Spring

- **JV-SPRING-01** Constructor injection, `final` fields, no field `@Autowired`.
- **JV-SPRING-02** Typed configuration with `@ConfigurationProperties` records plus validation;
  no `@Value` sprawl.
- **JV-SPRING-03** Boot 4 uses modular starters and Jakarta EE 11 (Servlet 6.1); `javax.*` imports
  are a migration bug. Undertow support is removed.
- **JV-SPRING-04** Tests: slices (`@WebMvcTest`, `@DataJpaTest`, `@JdbcTest`) before
  `@SpringBootTest`; use Spring Framework's `@MockitoBean`/`@MockitoSpyBean` instead of Boot's
  legacy `@MockBean` (the Boot 4 migration guides replace it); Testcontainers with
  `@ServiceConnection` for real databases; keep the context cache warm by reusing configurations.
- **JV-SPRING-05** Observability: Micrometer metrics and tracing via Actuator; structured logging
  (`logging.structured.format.console`) where the platform ingests JSON.
- **JV-SPRING-06** Check property names against the docs for the Boot version in use (context7 or
  the application-properties appendix) before adding them.

## 10. Build and dependencies (JV-BUILD)

- **JV-BUILD-01** Maven: `maven.compiler.release` set, UTF-8 encoding, every plugin version pinned,
  `maven-enforcer-plugin` with `requireMavenVersion`, `requireJavaVersion` and
  `dependencyConvergence` where the project allows.
- **JV-BUILD-02** Gradle: toolchains plus `options.release`, version catalog
  (`gradle/libs.versions.toml`) when present, `testRuntimeOnly("org.junit.platform:junit-platform-launcher")`
  (required with Gradle 9), configuration cache friendly tasks.
- **JV-BUILD-03** BOMs for version alignment; one version per library across modules; override
  transitives through `dependencyManagement`/`constraints` with a comment.
- **JV-BUILD-04** Annotation processors (Lombok, MapStruct, Error Prone, Hibernate metamodel) are
  declared explicitly: JDK 23+ does not run classpath processors implicitly.
- **JV-BUILD-05** Compiler: `-Xlint:all` with zero new warnings; `-Werror` only when the codebase is
  already clean.
- **JV-BUILD-06** Report updates with `versions:display-dependency-updates`
  (`-Dmaven.version.ignore='(?i).*(alpha|beta|rc|-m)[-.0-9]*'`); apply majors only as their own
  task, ideally with OpenRewrite recipes (`rewrite-migrate-java`, `rewrite-spring`).
- **JV-BUILD-07** Produce an SBOM for deployables (`cyclonedx-maven-plugin` `makeAggregateBom`).
- **JV-BUILD-08** Pin formatter engines only to versions the Spotless release supports: Spotless
  3.10.4 / 8.10.4 with google-java-format 1.36.1 (its default). 1.37.0 fails every file with
  `InvocationTargetException` there.

## 11. Packaging and distribution (JV-PKG)

Commands and verified runs are in `references/build-recipes.md` section 10.

- **JV-PKG-01** Libraries and CLIs that other modular code consumes ship a `module-info.java` that
  `exports` only API packages, `requires transitive` only types that appear in the exported API,
  and `opens` packages only to the framework that reflects on them (`opens com.acme.x to
  com.fasterxml.jackson.databind`). If a library cannot be modular yet, set
  `Automatic-Module-Name` in the manifest so the module name is stable.
- **JV-PKG-02** Self-contained CLIs and desktop tools: compute modules with
  `jdeps --print-module-deps`, link with `jlink --strip-debug --no-header-files --no-man-pages`,
  and wrap with `jpackage` when users need a native launcher or installer. Build on the target
  OS/architecture; JDKs without `jmods/` (Temurin 25, JEP 493) link only their own platform.
- **JV-PKG-03** Container images: Jib (`jib:build`, `jib:buildTar` without Docker) or
  `spring-boot:build-image` / `bootBuildImage` (buildpacks, Docker needed) instead of a
  hand-written fat-jar Dockerfile. With a Dockerfile, use the Boot layered jar
  (`java -Djarmode=tools -jar app.jar extract --layers`) so dependencies stay in a cached layer.
  Run as a non-root user and pin the base image by digest for releases.
- **JV-PKG-04** Builds are reproducible: Maven 3.10+ and Gradle 9+ do it by default; on older Maven
  set `project.build.outputTimestamp`. Check with `artifact:check-buildplan` and by comparing
  `sha256sum` of two clean builds.
- **JV-PKG-05** Publishing to Maven Central goes through the Central Portal
  (`central-publishing-maven-plugin` 0.12.0; OSSRH is shut down): POM `name`, `description`,
  `url`, `licenses`, `developers`, `scm`; sources and javadoc jars; `.asc` signatures on every
  file; credentials and the GPG passphrase from `settings.xml` or the environment. Dry-run with
  `skipUpload` and inspect the bundle before the first real deploy.
- **JV-PKG-06** A release is immutable: never re-publish the same version, and bump the version
  instead of overwriting a tag or an image tag that someone may already have pulled.

## 12. Testing (JV-TEST)

- **JV-TEST-01** Unit tests `*Test` (Surefire/`test`), integration tests `*IT` (Failsafe/separate
  suite). Unit tests do no I/O and run in milliseconds.
- **JV-TEST-02** JUnit 6 (Java 17 baseline) and 5.14 share the `org.junit.jupiter.api` packages;
  import `junit-bom`; do not mix JUnit 4 `org.junit.Test` into Jupiter classes.
- **JV-TEST-03** AssertJ for fluent assertions (`assertThat(..).containsExactly(..)`,
  `assertThatThrownBy`); assert outcomes, not internal call counts.
- **JV-TEST-04** Mock only collaborators across a boundary; strict stubs (`MockitoExtension`)
  stay on. On JDK 21+, register Mockito 5.14+ as `-javaagent` to avoid dynamic-agent warnings:
  Surefire/Failsafe `argLine` in Maven, a `mockitoAgent` configuration plus
  `tasks.test { jvmArgs("-javaagent:${mockitoAgent.asPath}") }` in Gradle (build-recipes 2 and 4).
- **JV-TEST-05** Testcontainers 2.x: `org.testcontainers:testcontainers-<module>` artifacts and
  `org.testcontainers.<module>` packages; JUnit 4 support is gone.
- **JV-TEST-06** Determinism: fixed `Clock`, seeded randomness, explicit locale and time zone,
  Awaitility for async; flaky tests get the nondeterminism removed, not retries.
- **JV-TEST-07** Property-based tests (jqwik) for parsers, codecs and invariants; ArchUnit for
  layering rules that reviews keep catching.
- **JV-TEST-08** Never skip, disable, delete or weaken a failing test to go green; decide which side
  is wrong and say so.

## 13. Logging and observability (JV-LOG)

- **JV-LOG-01** SLF4J 2 API with placeholders (`log.info("order {} placed", id)`); no string
  concatenation; exception as the last argument.
- **JV-LOG-02** Levels: ERROR needs action, WARN unexpected but handled, INFO business events,
  DEBUG diagnostics. No `System.out` in application code.
- **JV-LOG-03** Correlation via MDC or tracing context, cleared in `finally`; never log tokens,
  passwords, full request bodies or personal data.

## 14. Gates (run in this order)

```bash
# Maven
./mvnw -v
./mvnw -B -ntp spotless:check
./mvnw -B -ntp -q -Dtest='FooTest' test
./mvnw -B -ntp verify
./mvnw -B -ntp checkstyle:check pmd:check spotbugs:check      # if configured
./mvnw -B -ntp test-compile org.pitest:pitest-maven:mutationCoverage -DtargetClasses='com.acme.foo.*'
osv-scanner scan source -r .

# Gradle
./gradlew spotlessCheck
./gradlew test --tests 'com.acme.FooTest'
./gradlew build
./gradlew jacocoTestReport pitest     # if plugins applied

# Benchmarks (JMH uber-jar from the jmh archetype, or ./gradlew jmh)
java -jar target/benchmarks.jar FooBench -f 2 -wi 5 -i 10 -prof gc

# JMM-sensitive code (jcstress uber-jar from the jcstress archetype)
java -jar target/jcstress.jar -t FooStressTest -m quick
```

Pass means: `BUILD SUCCESS`, `Failures: 0, Errors: 0`, no new `Skipped`, no new `-Xlint`/Error Prone/
NullAway warnings, coverage reported for changed classes, surviving mutants explained, benchmark
deltas outside the error margin before calling something faster. Any gate not run is reported as
`NOT RUN` with the reason and the exact command.
