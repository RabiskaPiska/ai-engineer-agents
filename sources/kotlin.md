# Sources: kotlin (Kotlin)

Deliverables:
- `claude/agents/kotlin-engineer.md`
- `skills/kotlin-engineering/SKILL.md`
- `skills/kotlin-engineering/references/coroutines-and-flow.md`
- `skills/kotlin-engineering/references/gradle-build-and-gates.md`
- `skills/kotlin-engineering/references/benchmark-sequence-vs-list.md` (added 2026-10-29, measured)

All facts fetched 2026-10-29. Repository text was read as data only; no code or install step from
any mined repo was run.

## The 5 GitHub repos used

Metadata verified with `ghapi.sh repos/<owner>/<repo>` on 2026-10-29 (JSON fields pasted).

### 1. Kotlin/kotlin-agent-skills (official JetBrains Kotlin AI skills)
```json
{"full_name": "Kotlin/kotlin-agent-skills", "html_url": "https://github.com/Kotlin/kotlin-agent-skills", "stargazers_count": 1100, "pushed_at": "2026-10-28T16:08:31Z", "archived": false, "license": "Apache-2.0"}
```
Read: `README.md`, `skills/kotlin-tooling-java-to-kotlin/SKILL.md` and `references/KNOWN-ISSUES.md`,
`references/frameworks/SPRING.md`, `skills/kotlin-backend-jpa-entity-mapping/SKILL.md`,
`skills/kotlin-tooling-kotlin-toolchain/SKILL.md`.
Taken (adapted, Apache-2.0): JPA entity rules (no `data class` entities, ID-based equality,
class-constant `hashCode`, nullable generated `id` with `protected set`, DB constraint plus
application check for uniqueness, no blanket `EAGER`); Spring-on-Kotlin rules (`plugin.spring`,
constructor injection, `\${}` escaping in `@Value`, `Optional<T>` to `T?`); Java interop rules
(platform types, `@JvmStatic`/`@JvmField`/`@JvmOverloads`/`@Throws`, primitive arrays); Kotlin
Toolchain wrapper usage (`./kotlin build` from the project root). The agent points users to these
skills for the narrow tasks they cover. Linked from kotlinlang.org/docs/kotlin-ai-skills.html.

### 2. Kotlin/kotlinx.coroutines
```json
{"full_name": "Kotlin/kotlinx.coroutines", "html_url": "https://github.com/Kotlin/kotlinx.coroutines", "stargazers_count": 13822, "pushed_at": "2026-10-28T16:26:27Z", "archived": false, "license": "Apache-2.0"}
```
Read: `docs/topics/exception-handling.md`, `docs/topics/coroutines-cancellation.md`,
`docs/topics/shared-mutable-state-and-concurrency.md`, `kotlinx-coroutines-test/README.md`.
Taken: cancellation rules (rethrow `CancellationException`, `ensureActive`/`yield`,
`withContext(NonCancellable)` only with `withContext`, timeouts), exception propagation and
`CoroutineExceptionHandler` semantics, supervision, shared-state options in order (confinement,
atomics, `Mutex`), and `runTest` behavior (delay skipping, 60 s timeout, uncaught exceptions,
`return` on Kotlin/JS, test dispatchers, `Dispatchers.setMain`). Version 1.11.0 from its releases.

### 3. chrisbanes/skills
```json
{"full_name": "chrisbanes/skills", "html_url": "https://github.com/chrisbanes/skills", "stargazers_count": 1127, "pushed_at": "2026-10-27T21:35:28Z", "archived": false, "license": "Apache-2.0"}
```
Read: `skills/kotlin-api-design/SKILL.md`, `skills/kotlin-concurrency-and-flow/SKILL.md`,
`skills/kotlin-control-flow/SKILL.md`, `skills/release-kotlin-library/SKILL.md`,
`skills/gradle-run/SKILL.md`.
Taken (adapted, Apache-2.0): "explicit owner and lifetime" for coroutines; do not wrap an existing
suspend API in `launch`/callbacks; `Channel(Channel.BUFFERED).receiveAsFlow()` for single-consumer
events that must survive a collector gap vs `SharedFlow` for broadcast; exhaustive `when` without
catch-all `else` over sealed types, guarded branches first; smallest type for single-field domain
concepts; compact Gradle output handling (`--console=plain`, never paste full logs) which became
the "read the tail, grep the first error" gate practice.

### 4. maxrave-dev/kotlin-footguns
```json
{"full_name": "maxrave-dev/kotlin-footguns", "html_url": "https://github.com/maxrave-dev/kotlin-footguns", "stargazers_count": 1747, "pushed_at": "2026-10-29T04:27:53Z", "archived": false, "license": "GPL-3.0"}
```
Read: `README.md`, `skills/state-and-background-footguns/SKILL.md`,
`skills/remote-api-footguns/SKILL.md`, `skills/engineering-method-footguns/SKILL.md`,
`skills/data-layer-footguns/SKILL.md` (index entries).
Taken (paraphrased only; GPL-3.0 text is not copied): StateFlow conflation makes write order the
correctness question; cancel-before-relaunch for per-concern jobs; `stateIn(WhileSubscribed)` for
cold-to-hot sharing; `flatMapLatest` + `distinctUntilChanged` before expensive side effects;
combine condition flows into one idempotent gate; an empty `actual` means unimplemented, not
impossible; read build logs bottom-up for the verdict and at the first error for the cause.

### 5. android/skills (official Android agent skills)
```json
{"full_name": "android/skills", "html_url": "https://github.com/android/skills", "stargazers_count": 10008, "pushed_at": "2026-10-26T20:27:33Z", "archived": false, "license": "Apache-2.0"}
```
Read: `testing/testing-setup/SKILL.md`, `performance/r8-analyzer/SKILL.md`,
`jetpack-compose/jetpack-compose-performance/SKILL.md` (skimmed).
Taken (adapted): respect the project's existing test stack; prefer fakes and add MockK only when
clearly necessary; R8 full mode with narrow keep rules; release-build verification for Android
changes.

Read but not counted: `VoltAgent/awesome-claude-code-subagents`
`categories/02-language-specialists/kotlin-specialist.md` (MIT). Rejected as a source because it
targets "Kotlin 1.9+" and recommends context receivers, which Kotlin replaced with context
parameters (stable in 2.4). Its only influence is the anti-pattern note on context receivers.

## MCP servers declared in the agent (verified 2026-10-29)

| Server | Repo / endpoint | Evidence |
|---|---|---|
| github | by-name reference (pre-configured) | per SPEC |
| context7 | https://mcp.context7.com/mcp, repo upstash/context7 (MIT, 63,882 stars, pushed 2026-10-28) | README states the URL; `initialize` POST returned HTTP 200; `resolve-library-id kotlinx.coroutines` returned `/kotlin/kotlinx.coroutines` (versions 1.9.0, 1.10.1, 1.11.0) |
| gradle | rnett/gradle-mcp (Apache-2.0, 68 stars, pushed 2026-10-25, release 0.0.16 on 2026-10-05) | **Pinned** (2026-10-29): `jbang run --quiet --java 21 --runtime-option=--add-modules=jdk.incubator.vector dev.rnett.gradle-mcp:gradle-mcp:0.0.16`. The README's `jbang run --quiet --fresh gradle-mcp@rnett` was dropped: the alias in rnett/jbang-catalog `jbang-catalog.json` is `"script-ref": "dev.rnett.gradle-mcp:gradle-mcp:+"`, so with `--fresh` it re-resolves the newest artifact on every launch, which contradicts the agent's own rule against dynamic versions. The pinned args reproduce the alias settings (`"java": "21"`, `"runtime-options": ["--add-modules", "jdk.incubator.vector"]`). Maven Central `maven-metadata.xml`: `<release>0.0.16</release>`, lastUpdated 20261005000736; the 0.0.16 jar manifest has `Main-Class: dev.rnett.gradle.mcp.Application`. JBang flags `-j/--java`, `-R/--runtime-option`, `--[no-]quiet`, `--[no-]fresh` from jbangdev/jbang `docs/modules/cli/pages/jbang-run.adoc` (JBang v0.142.0, 2026-09-22). Launched this session with exactly those args (JBang 0.142.0, sha256-checked): MCP `initialize` answered `serverInfo {"name": "gradle-mcp", "version": "0.0.16"}`, protocol 2025-06-18, `tools/list` returned 10 tools; stderr showed `WARNING: Using incubator modules: jdk.incubator.vector` (runtime option applied) and JBang downloaded a JDK 21 because `--java 21` asks for that major version. Requires JDK 21+ and JBang. |
| maven-tools | arvindand/maven-tools-mcp (MIT, 35 stars, pushed 2026-10-26, release v3.2.3 on 2026-10-04) | README config: `docker run -i --rm arvindand/maven-tools-mcp:latest`, README recommends pinned `:3.2.3`; Docker Hub tag `3.2.3` status active (last_updated 2026-10-04). |

Optional (body only, not in frontmatter): IntelliJ IDEA 2026.2 built-in MCP server, documented at
https://www.jetbrains.com/help/idea/mcp-server.html (bundled since 2025.2; port and transport
are configured per IDE, so no fixed URL can be declared).

Rejected: IlyaGulya/gradle-mcp-server (archived), normaltusker/kotlin-mcp-server (last push
2025-09-05, AGPL-3.0).

## Official version sources (fetched 2026-10-29)

| Fact | Source |
|---|---|
| Kotlin 2.4.21 released 2026-10-08; 2.4.20 2026-09-07; 2.4.10 2026-07-14; 2.4 line 2026-06-03 to 2027-12-03; 2.5.0 planned Dec 2026 | https://kotlinlang.org/docs/releases.html and GitHub releases API `repos/JetBrains/kotlin/releases` |
| Kotlin 2.4.0 features (stable context parameters, explicit backing fields, UUID API, Java 26 bytecode, Gradle up to 9.5.0, AGP min 8.5.2, K1 removed, Compose flag deprecations, CMS GC default) | https://kotlinlang.org/docs/whatsnew24.html (page header says "Released: July 14, 2026" while the releases table and GitHub say 2.4.0 shipped 2026-06-03; the files use the GitHub date) |
| Kotlin 2.4.20 (Gradle up to 9.7.0, `StackTraceRecoverable`, indy `when` stable/default on JVM 21+, `kotlinr`, native image) | https://kotlinlang.org/docs/whatsnew2420.html |
| Kotlin 2.3.0 (unused return value checker, Java 25 bytecode, stable `kotlin.time.Clock`/`Instant`) | https://kotlinlang.org/docs/whatsnew23.html |
| KGP to Gradle/AGP compatibility table | https://kotlinlang.org/docs/gradle-configure-project.html |
| `-jvm-target`/`-Xjdk-release` values up to 26; `-Werror`, `-Wextra`, `-Xwarning-level` | https://kotlinlang.org/docs/compiler-reference.html |
| `allWarningsAsErrors`, `extraWarnings`, `progressiveMode`, `jvmDefault` DSL | https://kotlinlang.org/docs/gradle-compiler-options.html |
| `abiValidation()`, `checkKotlinAbi`, `updateKotlinAbi` | https://kotlinlang.org/docs/gradle-binary-compatibility-validation.html |
| `-Xreturn-value-checker`, `@MustUseReturnValues`, `val _ =` | https://kotlinlang.org/docs/unused-return-value-checker.html |
| Context parameters | https://kotlinlang.org/docs/context-parameters.html |
| Power-assert plugin id | https://kotlinlang.org/docs/power-assert.html |
| Kotlin AI skills list | https://kotlinlang.org/docs/kotlin-ai-skills.html |
| Kotlin Language Server (Alpha) | https://kotlinlang.org/docs/kotlin-lsp.html; releases `repos/Kotlin/kotlin-lsp/releases` (v263.7084.0, 2026-10-17) |
| JDK 27 GA 2026-09-15, 26 GA 2026-03-17, 25 GA 2025-09-16 | https://openjdk.org/projects/jdk/ |
| JDK 25 most recent LTS, 27 most recent feature release | https://api.adoptium.net/v3/info/available_releases |
| Gradle 9.8.2 current (build 2026-10-19) | https://services.gradle.org/versions/current and `repos/gradle/gradle/releases` |
| Gradle runs on JVM 17–27 | https://docs.gradle.org/current/userguide/compatibility.html |
| Configuration cache opt-in property; `updateDaemonJvm`; `--write-verification-metadata`; `--write-locks` | https://docs.gradle.org/current/userguide/configuration_cache_enabling.html, gradle_daemon.html, dependency_verification.html, dependency_locking.html |
| Spring Boot 4.1.2: Java 17+, up to Java 27, Spring Framework 7.0.10+, Gradle 8.14+/9.x | https://docs.spring.io/spring-boot/system-requirements.html |
| Spring Boot Kotlin: Kotlin 2.2.x minimum, `-Xannotation-default-target=param-property`, JSpecify | https://docs.spring.io/spring-boot/reference/features/kotlin.html |
| Ktor 3.6.0 | https://ktor.io/docs/releases.html; client `sanitizeHeader`: https://ktor.io/docs/client-logging.html |
| detekt versions, plugin id `dev.detekt`, tasks, DSL, compatibility table | https://detekt.dev/docs/gettingstarted/gradle, https://detekt.dev/docs/introduction/compatibility |
| JUnit 6: Java 17 / Kotlin 2.2 baseline, `suspend` test methods | https://docs.junit.org/6.0.0/release-notes/ |
| Kover plugin id, tasks, `verify { rule { } }` | https://kotlin.github.io/kotlinx-kover/gradle-plugin/ and Kover README |
| Spotless `ktlint()`/`ktfmt()` config | diffplug/spotless `plugin-gradle/README.md` |
| kotlinx-benchmark setup (`register("main")`, allopen, runtime artifact) | Kotlin/kotlinx-benchmark `README.md`, `docs/kotlin-jvm-project-setup.md` |
| OSV-Scanner CLI `scan source -r` | google/osv-scanner `README.md` |
| async-profiler `asprof` usage | async-profiler/async-profiler `README.md` |
| AGP 9.5.0 latest stable (Google Maven `maven-metadata.xml` lists 9.5.0 after 9.5.0-rc02; `gradle-9.5.0.pom` Last-Modified 2026-10-28); needs Gradle 9.6.0, JDK 17, max API 37 | https://developer.android.com/build/releases/agp-9-5-0-release-notes ("Android Gradle plugin 9.5.0 (October 2026)"); https://dl.google.com/dl/android/maven2/com/android/tools/build/gradle/maven-metadata.xml |
| Android Studio Rabbit 2 (2026.2.2) latest stable | https://developer.android.com/studio/releases (page last updated 2026-10-28) |
| Play target API: from 2026-08-31 new apps and updates target API 36 (Wear OS/AAOS 35, TV/XR 34), existing apps 35+, extension to 2026-11-01 | https://developer.android.com/google/play/requirements/target-sdk (last updated 2026-10-28) |
| JDK 25 GA 2025-09-16; Temurin 25.0.5+8 current (Adoptium assets API, checksum `68982529…d7fb`) | https://openjdk.org/projects/jdk/25/, https://api.adoptium.net/v3/assets/latest/25/hotspot |
| detekt 2.0.0-alpha.6 published 2026-08-04T22:38:20Z (prerelease) | `ghapi.sh repos/detekt/detekt/releases` |
| ktlint 1.8.0 built on Kotlin 2.2.21 (`kotlin = "2.2.21"`); ktfmt 0.65 built on Kotlin 2.4.10 (`kotlin = "2.4.10"`), new coordinate `org.jetbrains.kotlinx:ktfmt` | `ghapi.sh repos/ktlint/ktlint/contents/gradle/libs.versions.toml?ref=1.8.0`; `repos/Kotlin/ktfmt/contents/gradle/libs.versions.toml?ref=v0.65`; ktfmt v0.65 release notes; Maven Central `org/jetbrains/kotlinx/ktfmt/maven-metadata.xml` release 0.65; diffplug/spotless `KtfmtStep.java` at `gradle/8.10.4` (`MAVEN_COORDINATE = "org.jetbrains.kotlinx:ktfmt:"`) |
| Kover `minBound(Int)` | kotlinx-kover `kover-gradle-plugin/api/kover-gradle-plugin.api` line 324 `public abstract fun minBound (I)V` (in `KoverVerifyRule`); `kover-gradle-plugin/examples/jvm/single/build.gradle.kts` uses `minBound(50)`; also compiled this session (see self-check) |
| OSV-Scanner exit codes 0 / 1 / 127 / 128 ("No packages found") | https://google.github.io/osv-scanner/output/ (Return Codes table) |
| JEP 491: `synchronized` no longer pins virtual threads, delivered in JDK 24; native frames and class initializers still pin; JFR `jdk.VirtualThreadPinned` | https://openjdk.org/jeps/491 |
| `Executor.asCoroutineDispatcher()` | https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/as-coroutine-dispatcher.html |
| Heap dumps: `jcmd GC.heap_dump`, `-XX:+HeapDumpOnOutOfMemoryError` | https://docs.oracle.com/en/java/javase/25/troubleshoot/diagnostic-tools.html |
| LeakCanary 2.14 (2024-04-18) latest non-alpha; 3.0-alpha-9 (2026-06-25); setup `debugImplementation` | https://square.github.io/leakcanary/getting_started/; Maven Central `com/squareup/leakcanary/leakcanary-android/maven-metadata.xml`; `ghapi.sh repos/square/leakcanary/releases` |
| XXE settings for DocumentBuilderFactory, SAXParserFactory, XMLInputFactory | https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html |
| `android:exported` set explicitly | https://developer.android.com/privacy-and-security/risks/android-exported |
| WebView file access settings, `WebViewAssetLoader`, JavaScript and cleartext guidance | https://developer.android.com/privacy-and-security/risks/webview-unsafe-file-inclusion |
| Maven Central Portal: no official Gradle plugin; community plugins incl. vanniktech | https://central.sonatype.org/publish/publish-portal-gradle/ |
| vanniktech `publishToMavenCentral()`, `signAllPublications()`, `ORG_GRADLE_PROJECT_*` secrets; 0.37.0 (2026-06-21) on Maven Central | https://vanniktech.github.io/gradle-maven-publish-plugin/central/; Maven Central plugin marker `com/vanniktech/maven/publish/com.vanniktech.maven.publish.gradle.plugin` release 0.37.0 |
| KMP publication structure, single-host publishing, Apple host limits, `androidLibrary {}` | https://kotlinlang.org/docs/multiplatform/multiplatform-publish-lib-setup.html |
| Ktor `buildFatJar` / `runFatJar`, `io.ktor.plugin` | https://ktor.io/docs/server-fatjar.html |
| Spring Boot `bootJar`, `bootBuildImage` | https://docs.spring.io/spring-boot/gradle-plugin/packaging.html, https://docs.spring.io/spring-boot/gradle-plugin/packaging-oci-image.html |
| Jib Gradle plugin 3.5.4 (2026-07-14), `jib`, `jibDockerBuild` | GoogleContainerTools/jib `jib-gradle-plugin/README.md`; `ghapi.sh repos/GoogleContainerTools/jib/releases` |
| `jlink` / `jpackage` (`--name`, `--input`, `--main-jar` confirmed with `jpackage --help` on JDK 25.0.5) | https://docs.oracle.com/en/java/javase/25/jpackage/packaging-overview.html |
| GraalVM Native Build Tools 1.1.17 (2026-10-23), `nativeCompile`, `nativeTest` | https://graalvm.github.io/native-build-tools/latest/gradle-plugin.html; Gradle Plugin Portal marker release 1.1.17 |
| Android app signing, Play App Signing, `signingReport`; `bundle<Variant>` tasks | https://developer.android.com/studio/publish/app-signing, https://developer.android.com/build/building-cmdline |
| Library versions (coroutines 1.11.0, serialization 1.12.0, datetime 0.8.0, Ktor 3.6.0, Spring Boot 4.1.2/4.0.9, Compose MP 1.12.2, KSP 2.3.12, Exposed 1.6.0, Arrow 2.3.0.1, ktlint 1.8.0, ktfmt 0.65, Spotless 8.10.4, Kover 0.9.11, Kotest 6.2.6, JUnit 6.1.3, MockK 1.14.11, Turbine 1.2.1, Konsist 0.18.1, Lincheck 3.7, kotlinx-benchmark 0.5.0, Dokka 2.2.0, atomicfu 0.33.0, async-profiler 4.6, OSV-Scanner 2.7.0, Kotlin Toolchain 0.13.0) | GitHub releases API, latest non-prerelease per repo, 2026-10-29 |

## [UNVERIFIED] items

- Behavior of Gradle 9.8.x with KGP 2.4.21 beyond "may print deprecations" (the official table
  stops at 9.7.0). The 2026-10-29 builds below ran KGP 2.4.21 on Gradle 9.8.2 with
  `BUILD SUCCESSFUL` and a "Deprecated Gradle features were used" notice, which is one data point.
- AGP 9.4/9.5 with KGP 2.4.21: outside the kotlinlang.org tested range (up to 9.3.1); not built
  this session (no Android SDK on the box).
- `inline` higher-order functions and value classes as speed-ups: not benchmarked; the files now
  say "measure" instead of claiming a gain.
- Android, Ktor fat-jar, Spring Boot, Jib, jpackage, GraalVM and Maven Central publishing commands
  were taken from the official pages listed above and not executed this session.
- Snippets in the skill other than those listed under "Executed this session" were not compiled.

Resolved 2026-10-29: Kover `minBound(Int)` (was unverified). Evidence: kotlinx-kover
`kover-gradle-plugin/api/kover-gradle-plugin.api` line 324 `public abstract fun minBound (I)V`,
`kover-gradle-plugin/examples/jvm/single/build.gradle.kts` `minBound(50)`, and the compile/run
below.

## Executed this session (2026-10-29)

Toolchain fetched into the scratchpad and checksum-verified: Temurin JDK 25.0.5+8 (Adoptium
SHA-256 `68982529869257d0ee6b824ec5aa270ff8b118bb438670da0b97ebdab178d7fb: OK`), Gradle 9.8.2
(services.gradle.org `.sha256: OK`), ktlint 1.8.0 and ktfmt 0.65 (GitHub release asset digests: OK),
JBang 0.142.0 (asset digest: OK).

```text
# kotlinx-benchmark 0.5.0, Kotlin 2.4.21, 9 forks x 5+5 x 1 s; full table in references/benchmark-sequence-vs-list.md
SequenceVsList.list         3  avgt 45     56.566 ±  4.696 ns/op
SequenceVsList.sequence     3  avgt 45     11.801 ±  0.659 ns/op
BoxedVsPrimitive.boxedSum     10000 avgt 45 4368.482 ± 397.712 ns/op
BoxedVsPrimitive.primitiveSum 10000 avgt 45  794.173 ±  49.918 ns/op
BUILD SUCCESSFUL in 16m 13s

# gates sample: Kover 0.9.11 minBound(80) + Spotless 8.10.4 ktfmt("0.65") + -Xcollection-literals
$ gradle spotlessCheck test koverVerify koverXmlReport  -> BUILD SUCCESSFUL in 20s (exit=0)
$ (add an uncovered function) gradle koverVerify        -> exit=1
  > Rule violated: lines covered percentage is 25.000000, but expected minimum is 80
  Spotless resolved caches/modules-2/files-2.1/org.jetbrains.kotlinx/ktfmt/0.65/.../ktfmt-0.65.jar

# ktlint 1.8.0 (built on Kotlin 2.2.21) on Kotlin 2.4 syntax
collection literals, clean file      -> exit=0
collection literals, badly formatted -> exit=1, 4 findings (indent, square-brackets-spacing x2, comma-spacing)
explicit backing field + context parameter -> exit=0
ktfmt 0.65 on the same files -> formats them, exit=0

# OSV-Scanner 2.5.0 (local binary) on Gradle fixtures
build.gradle.kts only                         -> exit=128 "No package sources found"
verification-metadata.xml, jackson-databind 2.9.8 -> exit=1 "60 known vulnerabilities"
gradle.lockfile, jackson-databind 2.9.8       -> exit=1
gradle.lockfile, kotlin-stdlib 2.4.21         -> exit=0 "No issues found"

# target-detection grep (SKILL section 1) on 4 fixtures
old grep: hits kotlin("jvm") and com.android.library only (misses alias(libs.plugins.*), id("org.jetbrains.kotlin.jvm"), libs.versions.toml)
new grep: 7 hits covering all four forms

# gradle MCP server, pinned args
initialize -> serverInfo gradle-mcp 0.0.16; tools/list -> 10 tools
```

## Self-check results (2026-10-29, re-run after the fix pass)

```text
$ python3 -I selfcheck.py
claude/agents/kotlin-engineer.md yaml.safe_load OK keys= ['name', 'description', 'model', 'skills', 'mcpServers'] lines= 439
  invalid fields: none | tools omitted: True
  mcpServers: ['github', 'context7', 'gradle', 'maven-tools']
  heading check: PASS
  ALL-CAPS MUST count: 0
skills/kotlin-engineering/SKILL.md yaml.safe_load OK keys= ['name', 'description'] lines= 303
references: benchmark-sequence-vs-list.md 100 lines, coroutines-and-flow.md 144 lines, gradle-build-and-gates.md 251 lines
  link references/coroutines-and-flow.md exists
  link references/gradle-build-and-gates.md exists
  link references/benchmark-sequence-vs-list.md exists
  link references/benchmark-sequence-vs-list.md exists
  link references/gradle-build-and-gates.md exists
```

Link check (2026-10-29). GitHub repos via `ghapi.sh repos/<owner>/<repo>`, every other URL via
`curl -sL -o /dev/null -w '%{http_code}'`. Four regex hits on `gradle/<file>` were project file paths,
not repos, and are excluded. `mcp.context7.com/mcp` answers 405 to GET by design (MCP is POST); a
POST `initialize` returned 200.

```text
ghapi repos/Kotlin/kotlin-agent-skills -> OK Kotlin/kotlin-agent-skills False
ghapi repos/Kotlin/kotlinx.coroutines -> OK Kotlin/kotlinx.coroutines False
ghapi repos/Kotlin/ktfmt -> OK Kotlin/ktfmt False
ghapi repos/VoltAgent/awesome-claude-code-subagents -> OK VoltAgent/awesome-claude-code-subagents False
ghapi repos/android/skills -> OK android/skills False
ghapi repos/chrisbanes/skills -> OK chrisbanes/skills False
ghapi repos/ktlint/ktlint -> OK ktlint/ktlint False
ghapi repos/maxrave-dev/kotlin-footguns -> OK maxrave-dev/kotlin-footguns False
curl https://api.adoptium.net/v3/info/available_releases -> 200
curl https://detekt.dev/docs/gettingstarted/gradle -> 200
curl https://detekt.dev/docs/introduction/compatibility -> 200
curl https://docs.gradle.org/current/userguide/compatibility.html -> 200
curl https://docs.gradle.org/current/userguide/configuration_cache_enabling.html -> 200
curl https://docs.junit.org/6.0.0/release-notes/ -> 200
curl https://docs.spring.io/spring-boot/reference/features/kotlin.html -> 200
curl https://docs.spring.io/spring-boot/system-requirements.html -> 200
curl https://github.com/Kotlin/kotlin-agent-skills -> 200
curl https://github.com/Kotlin/kotlinx.coroutines -> 200
curl https://github.com/android/skills -> 200
curl https://github.com/chrisbanes/skills -> 200
curl https://github.com/maxrave-dev/kotlin-footguns -> 200
curl https://kotlin.github.io/kotlinx-kover/gradle-plugin/ -> 200
curl https://kotlinlang.org/docs/compiler-reference.html -> 200
curl https://kotlinlang.org/docs/context-parameters.html -> 200
curl https://kotlinlang.org/docs/gradle-binary-compatibility-validation.html -> 200
curl https://kotlinlang.org/docs/gradle-compiler-options.html -> 200
curl https://kotlinlang.org/docs/gradle-configure-project.html -> 200
curl https://kotlinlang.org/docs/kotlin-ai-skills.html -> 200
curl https://kotlinlang.org/docs/kotlin-lsp.html -> 200
curl https://kotlinlang.org/docs/power-assert.html -> 200
curl https://kotlinlang.org/docs/releases.html -> 200
curl https://kotlinlang.org/docs/unused-return-value-checker.html -> 200
curl https://kotlinlang.org/docs/whatsnew23.html -> 200
curl https://kotlinlang.org/docs/whatsnew24.html -> 200
curl https://kotlinlang.org/docs/whatsnew2420.html -> 200
curl https://ktor.io/docs/client-logging.html -> 200
curl https://ktor.io/docs/releases.html -> 200
curl https://mcp.context7.com/mcp -> 405
curl https://openjdk.org/projects/jdk/ -> 200
curl https://services.gradle.org/versions/current -> 200
curl https://www.jetbrains.com/help/idea/mcp-server.html -> 200
ghapi repos/rnett/gradle-mcp -> OK rnett/gradle-mcp archived=False 2026-10-25T17:38:04Z
ghapi repos/rnett/jbang-catalog -> OK rnett/jbang-catalog archived=False 2026-03-19T00:05:43Z
ghapi repos/arvindand/maven-tools-mcp -> OK arvindand/maven-tools-mcp archived=False 2026-10-26T14:40:58Z
ghapi repos/upstash/context7 -> OK upstash/context7 archived=False 2026-10-28T20:26:24Z
ghapi repos/google/osv-scanner -> OK google/osv-scanner archived=False 2026-10-28T23:13:41Z
ghapi repos/diffplug/spotless -> OK diffplug/spotless archived=False 2026-10-28T19:34:32Z
ghapi repos/async-profiler/async-profiler -> OK async-profiler/async-profiler archived=False 2026-10-27T01:32:15Z
ghapi repos/Kotlin/kotlinx-benchmark -> OK Kotlin/kotlinx-benchmark archived=False 2026-10-06T19:59:45Z
ghapi repos/Kotlin/kotlinx-kover -> OK Kotlin/kotlinx-kover archived=False 2026-10-26T11:05:42Z
ghapi repos/Kotlin/kotlin-lsp -> OK Kotlin/kotlin-lsp archived=False 2026-10-29T04:33:54Z
ghapi repos/JetBrains/kotlin -> OK JetBrains/kotlin archived=False 2026-10-29T09:40:05Z
ghapi repos/JetBrains/kotlin-toolchain -> OK JetBrains/kotlin-toolchain archived=False 2026-10-29T01:17:01Z
ghapi repos/IlyaGulya/gradle-mcp-server -> OK IlyaGulya/gradle-mcp-server archived=True 2026-03-14T04:25:14Z
ghapi repos/normaltusker/kotlin-mcp-server -> OK normaltusker/kotlin-mcp-server archived=False 2025-09-05T07:37:10Z
ghapi repos/Kotlin/binary-compatibility-validator -> OK Kotlin/binary-compatibility-validator archived=False 2026-09-02T17:12:20Z
```

Link check re-run after the fix pass (2026-10-29): every non-GitHub URL cited in the agent, skill,
references and this file (51 URLs) returned HTTP 200 with `curl -sSL`; `mcp.context7.com/mcp` as
above. Repos newly referenced in this pass, via `ghapi.sh repos/<owner>/<repo>`:

```text
ghapi repos/rnett/jbang-catalog -> OK archived=False 2026-03-19T00:05:43Z
ghapi repos/jbangdev/jbang -> OK archived=False 2026-10-26T01:11:48Z
ghapi repos/detekt/detekt -> OK archived=False 2026-10-28T23:05:48Z
ghapi repos/ktlint/ktlint -> OK archived=False 2026-10-25T17:34:10Z
ghapi repos/Kotlin/ktfmt -> OK archived=False 2026-10-28T11:18:08Z
ghapi repos/square/leakcanary -> OK archived=False 2026-10-21T15:42:05Z
ghapi repos/GoogleContainerTools/jib -> OK archived=False 2026-10-16T16:30:55Z
ghapi repos/graalvm/native-build-tools -> OK archived=False 2026-10-28T16:09:49Z
ghapi repos/vanniktech/gradle-maven-publish-plugin -> OK archived=False 2026-10-28T18:27:23Z
ghapi repos/adoptium/temurin25-binaries -> OK archived=False 2026-10-22T23:44:27Z
```

These are tool and doc sources for version facts, not additional mined repos; the mined set is
still the 5 repos above.
