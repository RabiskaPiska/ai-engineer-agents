---
name: kotlin-engineering
description: "Kotlin production-engineering rule catalog and gate commands (Kotlin 2.4.21, Gradle 9.8, JDK 25 LTS, Oct 2026). Use when writing, reviewing, debugging, testing or building Kotlin code: JVM services (Ktor, Spring Boot 4), Android, Kotlin Multiplatform, coroutines/Flow, Gradle Kotlin DSL, detekt/ktlint/Kover/ABI validation, benchmarks. Load before planning any non-trivial Kotlin change."
---

# Kotlin engineering

A rule catalog for shipping Kotlin that is correct, cancellable, binary-stable and verified.
Rules are written so a reviewer can check them in a diff. Versions were verified on 2026-10-29;
the project's own pins always win over this file.

Reference files (read only the one that matches the task):
- [references/coroutines-and-flow.md](references/coroutines-and-flow.md): ownership, cancellation,
  exceptions, Flow state/events, testing with `runTest` and Turbine.
- [references/gradle-build-and-gates.md](references/gradle-build-and-gates.md): build setup snippets
  for every gate (Spotless, detekt, Kover, ABI validation, warnings-as-errors, dependency
  verification, benchmarks), Maven and Kotlin Toolchain equivalents.
- [references/benchmark-sequence-vs-list.md](references/benchmark-sequence-vs-list.md): a JMH run
  (9 forks, JDK 25) of `Sequence` vs `List` and `IntArray` vs `Array<Int>`, with the code to re-run it.

## 1. Detect before you change

Run these reads first; they decide every later choice.

```bash
cat settings.gradle.kts build.gradle.kts gradle/libs.versions.toml gradle.properties 2>/dev/null
cat gradle/wrapper/gradle-wrapper.properties gradle/gradle-daemon-jvm.properties 2>/dev/null
ls build-logic buildSrc 2>/dev/null          # convention plugins
ls pom.xml project.yaml 2>/dev/null           # Maven or Kotlin Toolchain instead of Gradle
# targets: kotlin("jvm") form, id("org.jetbrains.kotlin.*") form, version-catalog aliases, AGP ids
grep -rnE 'kotlin\("(jvm|multiplatform|android)"\)|org\.jetbrains\.kotlin\.(jvm|multiplatform|android)|libs\.plugins\.(kotlin|android)|com\.android\.' \
  --include=*.kts --include=*.toml . | head -20
```

Record: Kotlin version, `jvmToolchain`/`jvmTarget`, targets, test framework (kotlin.test,
JUnit 5/6, Kotest), existing gates (Spotless/ktlint, detekt + baseline, Kover bounds,
`abiValidation`, `explicitApi`, `allWarningsAsErrors`), DI framework, serialization library.

Compatibility facts that commonly bite (kotlinlang.org KGP table, checked 2026-10-29):

| KGP | Gradle fully supported | AGP |
|---|---|---|
| 2.4.20 – 2.4.21 | 7.6.3 – 9.7.0 | 8.5.2 – 9.3.1 |
| 2.4.0 – 2.4.10 | 7.6.3 – 9.5.0 | 8.5.2 – 9.1.0 |
| 2.3.20 – 2.3.21 | 7.6.3 – 9.3.0 | 8.2.2 – 9.0.0 |

Newer Gradle (9.8.x) generally works with deprecation warnings. Kotlin 2.4 emits JVM bytecode up
to 26; Gradle 9.8 runs on JVM 17–27. Kotlin 2.4 removed K1 (`-language-version=1.9`).

Android baseline (developer.android.com, checked 2026-10-29): latest stable AGP is 9.5.0
(2026-10-28; Gradle 9.6.0+, JDK 17+, up to API 37), which is newer than the 9.3.1 ceiling tested
with KGP 2.4.21; Android Studio stable is Rabbit 2 (2026.2.2). Google Play has required
`targetSdk = 36` for new apps and updates since 2026-08-31 (Wear OS and Automotive 35, TV and XR
34); `compileSdk` is at least `targetSdk`.

## 2. Language rules (Kotlin 2.4)

**Immutability and visibility**
- `val` over `var`; read-only collection interfaces in signatures; mutable state private.
- Kotlin 2.4 stable explicit backing fields replace the `_state`/`state` pair:
  ```kotlin
  class CartViewModel {
      val items: StateFlow<List<Item>>
          field = MutableStateFlow(emptyList())

      fun add(item: Item) = items.update { it + item }   // smart-cast to MutableStateFlow inside the class
  }
  ```
  On 2.3 this needs `-Xexplicit-backing-fields`; on older versions keep the private-backing pattern.
- Libraries: `kotlin { explicitApi() }`. Public API declares visibility and return types; internal
  helpers are `internal`.

**Nullability**
- No `!!` outside tests. `requireNotNull(x) { "order $id has no customer" }` states the invariant.
- Platform types from Java get an explicit Kotlin type at the boundary. JSpecify-annotated Java
  (Spring 7, JUnit 6) is enforced strictly by Kotlin since 2.1, so trust its annotations.
- `lateinit` only for framework-injected fields or test setup, never for values a constructor
  could take.

**Modeling**
- Closed domains: `sealed interface` + exhaustive `when` expression without `else`. Guard
  conditions (`is Event.Message if event.isUnread ->`) are stable since 2.2; put the guarded branch
  before the unguarded one for the same subtype.
- Single-field domain values: `@JvmInline value class OrderId(val raw: Long)`. Validate in `init`
  when the type has invariants.
- `data class` for DTOs and value carriers only; never for JPA entities (ID-based `equals`,
  `hashCode() = javaClass.hashCode()`, `toString` without lazy relations, `var id: Long? = null`
  with `protected set`).
- `object` for stateless singletons; avoid hidden mutable state in `object`/`companion object`.
- Context parameters (stable in 2.4) for cross-cutting capabilities passed through many calls
  (`context(tx: Transaction) fun save(...)`). Do not use them to hide ordinary dependencies a
  constructor should take. Context receivers are gone; migrate them to context parameters.

**Functions and APIs**
- Expression bodies for single expressions; named arguments for booleans and same-typed params.
- Scope functions: one level deep, `let` for null-handling or mapping, `apply` for configuration,
  `also` for side effects; no nested `it`.
- Extension functions when the receiver is the natural subject and the function needs only its
  public API; member functions when it is core behavior of the type.
- Use the unused-return-value checker in new code (`-Xreturn-value-checker=check`, mark own APIs
  with `@MustUseReturnValues`); use `val _ = call()` to discard deliberately.

**Experimental in 2.4 (opt-in, flag in review):** collection literals (`-Xcollection-literals`),
explicit context arguments (`-Xexplicit-context-arguments`), improved const evaluation
(`-Xintrinsic-const-evaluation`), `returnsResultOf` contract (`-Xallow-returns-result-of`, produces
pre-release binaries), `@IntroducedAt` (`@OptIn(ExperimentalVersionOverloading::class)`), UUID v4/v7
generators. Applications may adopt them deliberately; published libraries should not.

**Stdlib picks:** `kotlin.uuid.Uuid` (stable API in 2.4), `kotlin.time.Clock`/`Instant`
(stable since 2.3), `isSorted()` family (2.4), `buildList`/`buildMap`, `Duration` over raw millis,
`use {}` for every `Closeable`.

## 3. Errors

- Recoverable domain outcomes go in the return type (sealed result or nullable). Exceptions for
  programmer errors (`require`/`check`/`error`) and infrastructure failures.
- Never `runCatching` around suspend calls and never `catch (e: Exception)`/`Throwable` in
  coroutine code without rethrowing `CancellationException` first:
  ```kotlin
  try { repo.save(order) }
  catch (e: CancellationException) { throw e }
  catch (e: SQLException) { return SaveResult.StorageUnavailable(e) }
  ```
- Map exceptions to HTTP at one place (Ktor `StatusPages`, Spring `@ControllerAdvice`), not per
  handler.
- Log once, at the boundary that handles the error, with structured context; never log and
  rethrow the same exception.

## 4. Concurrency (summary; details in references/coroutines-and-flow.md)

1. Every coroutine has an owner with a lifecycle; no `GlobalScope`.
2. Suspend functions are main-safe and switch dispatchers themselves (`withContext(io)`).
3. Dispatchers are injected for tests.
4. `StateFlow` for state, `Channel(BUFFERED).receiveAsFlow()` for must-deliver single-consumer
   events, `SharedFlow` for broadcast events, `stateIn(scope, WhileSubscribed(5_000), initial)`
   to share cold flows.
5. `MutableStateFlow.update {}` for read-modify-write; `Mutex` for suspending critical sections;
   never `synchronized` around a suspension point.
6. Cancellation is cooperative: `ensureActive()`/`yield()` in CPU loops, `runInterruptible` for
   blocking calls, `withContext(NonCancellable)` for suspending cleanup only.
7. JVM-only shared data structures get a Lincheck test.
8. Blocking Java APIs (JDBC, legacy SDKs) can run on virtual threads through
   `Executors.newVirtualThreadPerTaskExecutor().asCoroutineDispatcher()`; one owner creates it and
   calls `close()` on shutdown. CPU work stays on `Dispatchers.Default`. JDK 24+ (JEP 491) no
   longer pins a virtual thread blocked in `synchronized`; native frames and class initializers
   still pin. Check with JFR: `jfr print --events jdk.VirtualThreadPinned rec.jfr`.

## 5. Frameworks

**Ktor 3.6**: plugins installed in modules, `ContentNegotiation` with kotlinx.serialization,
`StatusPages` for error mapping, `RequestValidation` for input, `Authentication` with route
scoping, client `Logging` with `sanitizeHeader { it == HttpHeaders.Authorization }`. Test routes
with `testApplication { }`. One `HttpClient` per configuration, closed on shutdown.

**Spring Boot 4.1** (Java 17+, Kotlin 2.2+, Spring Framework 7): `kotlin("plugin.spring")`,
`kotlin("plugin.jpa")` for entities, constructor injection, `runApplication<App>(*args)`,
`@ConfigurationProperties` on immutable classes (constructor binding), coroutine controllers
(`suspend fun`) or `Flow` returns where WebFlux is used. Spring Data repositories return `T?`
instead of `Optional<T>`.

**Persistence**: Exposed 1.x or Spring Data/JPA as the project already uses. Uniqueness enforced by
a database constraint, with an application check only for a clean error message. Diagnose N+1 with
SQL logs or query counts, fix with `@EntityGraph`/`JOIN FETCH`/DTO projections, never with
global `EAGER`.

**Serialization**: kotlinx.serialization 1.12 (`@Serializable`, explicit `Json { }` instance
shared and reused, polymorphism only through a closed `SerializersModule`). Jackson 3 via Spring's
`spring-boot-jackson` plus the Kotlin module when the stack is Jackson.

**Android / Compose**: state hoisted to a ViewModel exposing `StateFlow<UiState>`, collected with
`collectAsStateWithLifecycle()`; side effects in `LaunchedEffect` keyed correctly; stable
parameter types for composables; R8 full mode with narrow keep rules. Compose compiler flags
`StrongSkipping`/`IntrinsicRemember` are at `DeprecationLevel.ERROR` in 2.4 (always on); remove
them from builds.

**Kotlin Multiplatform**: keep `commonMain` semantic; platform services behind interfaces or narrow
`expect`/`actual`. An empty `actual` means "not implemented", not "impossible on this platform".
Kotlin/Native uses the concurrent-mark GC by default since 2.4 (`kotlin.native.binary.gc=pmcs`
reverts). Swift export is Alpha; prefer it only for new iOS integrations that accept that status.

## 6. Testing rules

- Tests are named for behavior (`` `rejects order without lines` ``), one reason to fail each.
- Suspend code: `runTest { }` (virtual time, 60 s default timeout, uncaught child exceptions
  rethrown). Inject `StandardTestDispatcher(testScheduler)`; `advanceUntilIdle()` to drain.
  JUnit 6 also accepts `suspend` test methods, but `runTest` is still needed for virtual time.
- `Dispatchers.setMain(StandardTestDispatcher())` in Android/Compose ViewModel tests, reset in
  `@AfterTest`.
- Flow: Turbine `flow.test { assertEquals(x, awaitItem()); cancelAndIgnoreRemainingEvents() }`.
- Prefer fakes over mocks; MockK (`coEvery`/`coVerify` for suspend) only at true external seams.
- Property-based tests (Kotest property module) for parsers, codecs, and math.
- Architecture rules (layer dependencies, naming) with Konsist where the project has them.
- Coverage is a floor, not a goal: Kover bound per module (start from the current value, ratchet
  up), and new code covered by meaningful assertions.
- Power-assert compiler plugin (`kotlin("plugin.power-assert")`) gives readable `assert`/`require`
  failure diagrams; 2.4 adds a runtime library and `@PowerAssert` for custom assertion functions.

## 7. Performance rules

- Benchmark before and after with kotlinx-benchmark 0.5.0 (JMH on JVM; `allopen` for `@State`
  classes). Report mean and error, same JDK and flags.
- Profile services with async-profiler 4.6 (`asprof -d 30 -e cpu -f flame.html <pid>`) or JFR
  (`jcmd <pid> JFR.start duration=60s filename=rec.jfr`).
- Hot paths: primitive arrays (measured about 5.5x faster than `Array<Int>` for a 10,000-element
  sum on JDK 25), preallocated collection capacity, no regex construction or reflection per call.
  Value classes and `inline` lambdas can remove boxing and allocation; not measured here, so
  benchmark before claiming a gain.
- `Sequence` vs `List`: pick by semantics (lazy, short-circuiting, single pass). Measured on
  JDK 25, `Sequence` was faster, or not measurably different, from 3 to 10,000 elements for
  `map`/`filter` chains, so do not repeat "Sequence is slower on small collections" as a rule.
  Setup, code and numbers:
  [references/benchmark-sequence-vs-list.md](references/benchmark-sequence-vs-list.md).
- Coroutines are cheap but not free: do not `async` per element over large lists without bounding
  concurrency (`Semaphore`, `limitedParallelism`, or `flatMapMerge(concurrency = n)`).
- On JVM 21+, `when` over sealed types compiles via `invokedynamic` by default since 2.4.20.

**Memory and leaks**
- Android debug builds: `debugImplementation("com.squareup.leakcanary:leakcanary-android:2.14")`
  (2.14 is the latest non-alpha). A leak trace is fixed at the retaining reference.
- No `Activity`/`View`/`Fragment` or non-application `Context` in singletons, `companion object`s,
  ViewModels, static caches, or coroutines launched in a scope that outlives the screen. Long-lived
  code takes `applicationContext`.
- Services: `-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/var/dumps`; for slow growth take
  two `jcmd <pid> GC.heap_dump /tmp/h1.hprof` dumps some time apart and compare retained sizes.
  Usual causes: unbounded maps used as caches, listeners never unregistered, `ThreadLocal` on
  pooled threads, `CoroutineScope`s never cancelled.

## 8. Security checklist

- Input validated at the boundary into typed values; size limits on bodies and collections.
- Parameterized SQL only; no string templates in queries, shell commands or file paths from users.
- No polymorphic deserialization of untrusted data without a closed type set.
- XML (XXE, per OWASP): DOM and SAX factories set
  `http://apache.org/xml/features/disallow-doctype-decl = true` and
  `XMLConstants.FEATURE_SECURE_PROCESSING = true`; StAX sets
  `XMLInputFactory.SUPPORT_DTD = false` and `IS_SUPPORTING_EXTERNAL_ENTITIES = false`.
  ```kotlin
  val dbf = DocumentBuilderFactory.newDefaultInstance().apply {
      setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)
      setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true)
  }
  ```
- Android: explicit `android:exported` on every component (`false` by default choice); exported
  components guarded by a `signature` permission where possible; `Intent` extras and deep-link
  parameters validated. `WebView`: JavaScript off unless needed, all four file/content access
  settings `false`, local pages through `WebViewAssetLoader`, no `addJavascriptInterface` for
  untrusted content, no cleartext traffic.
- Secrets from env/secret manager; redacted in logs; never in `gradle.properties` under VCS.
- Authn/authz at route level with deny-by-default; CSRF/CORS configured explicitly for browser APIs.
- Dependency hygiene: version catalog, Gradle dependency verification and/or locking, OSV-Scanner
  in CI, repositories limited to `mavenCentral()`, `google()`, `gradlePluginPortal()`.

## 9. Packaging and publishing

Keep whatever the project already uses; these are the defaults for a new setup.

| Artifact | Tooling (versions checked 2026-10-29) | Command / check |
|---|---|---|
| JVM library on Maven Central | Central Publisher Portal. Sonatype has no official Gradle plugin; `com.vanniktech.maven.publish` 0.37.0 (resolved from Maven Central) is one of the options it lists. Javadoc jar from Dokka when applied. | `mavenPublishing { publishToMavenCentral(); signAllPublications() }`; dry run `./gradlew publishToMavenLocal`; upload `./gradlew publishToMavenCentral` |
| KMP library | Same plugin or `maven-publish`; one root `kotlinMultiplatform` publication plus one per target. Publish everything from one host (Maven Central rejects duplicates). Any host cross-compiles Apple klibs; cinterop, CocoaPods and final Apple binaries need a Mac. Android target needs the `androidLibrary {}` block. | `./gradlew publishToMavenLocal`, then inspect `~/.m2/repository/<group>/` for every target |
| Ktor server | Ktor Gradle plugin `io.ktor.plugin` 3.6.0 with `application { mainClass.set(...) }` | `./gradlew buildFatJar` gives `build/libs/*-all.jar` (fat jar is disabled when the KMP plugin is applied in the same module) |
| Spring Boot | Spring Boot Gradle plugin | `./gradlew bootJar`; OCI image `./gradlew bootBuildImage` |
| Container without Dockerfile | Jib `com.google.cloud.tools.jib` 3.5.4 | `./gradlew jibDockerBuild` locally, `./gradlew jib --image=<registry/image>` in CI |
| Desktop app | JDK `jlink` (trimmed runtime) and `jpackage` (installer) | `jpackage --name <App> --input build/libs --main-jar <app>.jar ...` |
| Native image | GraalVM Native Build Tools `org.graalvm.buildtools.native` 1.1.17 | `./gradlew nativeCompile`; run `./gradlew nativeTest` because reflection and resources can be missing from the image |
| Android app | AGP; Play App Signing holds the app key, you hold the upload key | `./gradlew :app:bundleRelease` (AAB, runs R8); `./gradlew :app:signingReport` to check which key signs which variant |

Signing material (GPG key, keystore, passwords, Portal token) comes from environment variables
(`ORG_GRADLE_PROJECT_signingInMemoryKey`, `ORG_GRADLE_PROJECT_mavenCentralUsername`/`Password`)
or a git-ignored `keystore.properties`, never from a committed file.

## 10. Verification gates (quick list)

```bash
./gradlew spotlessCheck detekt --console=plain
./gradlew compileKotlin compileTestKotlin --console=plain     # with allWarningsAsErrors
./gradlew test koverVerify --console=plain                    # KMP: allTests; Android: testDebugUnitTest
./gradlew checkKotlinAbi --console=plain                      # libraries
./gradlew check --console=plain                               # everything wired into check
```

Capture output to a file (`> build.log 2>&1`), read `tail -40 build.log` for the verdict and
`grep -n -m1 -E '^e: |FAILED|What went wrong' build.log` for the cause. Paste the relevant lines in
the report. Setup snippets for each gate are in
[references/gradle-build-and-gates.md](references/gradle-build-and-gates.md).

Pass: `BUILD SUCCESSFUL`, no new detekt findings, baseline unchanged, Kover bound met, ABI dump
clean or intentionally updated with an explanation. Anything else is a fail to fix at the root.

Dependency scan: `osv-scanner scan source -r .` only sees Gradle dependencies through
`gradle.lockfile` or `gradle/verification-metadata.xml`. Exit `0` = clean, `1` = vulnerabilities,
`128` = "No package sources found" (nothing scanned: report as NOT RUN, not as a pass).

## 11. Review checklist (use on your own diff)

- [ ] No `!!`, no unowned coroutine, no swallowed `CancellationException`.
- [ ] Every `when` over a sealed type is exhaustive without `else`.
- [ ] Public API changes intended, typed, documented (KDoc), ABI dump updated if a library.
- [ ] Mutable state private; `StateFlow` updates via `update {}`.
- [ ] Blocking calls off the main/event-loop threads; dispatchers injected.
- [ ] New dependencies in the version catalog, checked for latest stable and CVEs.
- [ ] Tests fail without the change and pass with it; flaky tests fixed, not retried.
- [ ] Gates run in this session, output pasted; anything not run marked NOT RUN with the command.
