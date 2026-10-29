# Sources: java (fetched 2026-10-29)

Provenance for `claude/agents/java-engineer.md` and `skills/java-engineering/` (SKILL.md plus
`references/build-recipes.md` and `references/jvm-diagnostics.md`). Repository text was read as
data only; no code or install step from any mined repository was executed.

## The 5 GitHub repositories used

Each verified with `ghapi.sh repos/<owner>/<repo>` on 2026-10-29; the JSON fields used are pasted
verbatim.

### 1. github/awesome-copilot
```json
{"full_name": "github/awesome-copilot", "html_url": "https://github.com/github/awesome-copilot", "stargazers_count": 40541, "pushed_at": "2026-10-29T00:07:04Z", "license": "MIT", "archived": false, "default_branch": "main"}
```
Read: `skills/java-development/SKILL.md` and its `references/` (modern-java, build-and-dependencies,
quality-and-packaging), `skills/java-junit/SKILL.md` and `references/assertj-and-mockito.md`,
`references/build-setup.md`, `skills/java-diagnostics/SKILL.md` with `references/jfr.md`,
`async-profiler.md`, `thread-dumps.md`, `skills/java-testcontainers/SKILL.md`,
`skills/java-hibernate-jpa/references/fetching-and-n-plus-one.md`,
`skills/java-upgrade/references/java-21-to-25.md`,
`skills/spring-boot-testing/references/sb4-migration.md`, `testcontainers-jdbc.md`,
`instructions/springboot-4-migration.instructions.md`.
Took (MIT, adapted with attribution): the "detect before you write / never upgrade implicitly"
stance; the JDK 23+ implicit-annotation-processing change; the Error Prone Maven fragment shape and
the JDK 21 `-XDaddTypeAnnotationsToSymbol=true` requirement (cross-checked with errorprone.info);
the Mockito 5.14+ `-javaagent` setup and the `@{argLine}` + JaCoCo interaction; the PIT run command
(`test-compile org.pitest:pitest-maven:mutationCoverage`); the JUnit 6 vs 5 table (Java 17 baseline,
Gradle 9 needs `junit-platform-launcher`); the diagnostics safety-tier model and JFR/async-profiler
commands (`references/jvm-diagnostics.md`); `Thread.dump_to_file -format=json` for virtual threads;
Spring Boot 4 migration points (modular starters, Jackson 3, JSpecify, Undertow removed,
`@MockitoBean`).

### 2. jabrena/plinth (formerly jabrena/cursor-rules-java; the old name returns HTTP 301)
```json
{"full_name": "jabrena/plinth", "html_url": "https://github.com/jabrena/plinth", "stargazers_count": 456, "pushed_at": "2026-10-29T05:13:20Z", "license": "Apache-2.0", "archived": false, "default_branch": "main"}
```
Read: `skills/125-java-concurrency/SKILL.md` and `references/125-java-concurrency.md` (principles
and safeguards), `skills/124-java-secure-coding/SKILL.md`, `skills/126-java-exception-handling/SKILL.md`,
`skills/141-java-refactoring-with-modern-features/SKILL.md`, `skills/112-java-maven-plugins/SKILL.md`,
and the skills index (110-183, 300-403).
Took (Apache-2.0, paraphrased): the concurrency rule set behind JV-CONC-01..11 (bounded queues with
`CallerRunsPolicy`, `Semaphore` to cap downstream concurrency, interruption discipline, lock
ordering and `tryLock`, `LongAdder`/`CopyOnWriteArrayList` fit-for-purpose primitives, no blocking
in ForkJoin, `ScopedValue` over `ThreadLocal`, JFR `VirtualThreadPinned`); the "structured
concurrency is preview in 27, requires `--enable-preview`" guard; the secure-coding and
exception-handling topic lists (JV-SEC, JV-ERR: chaining, `addSuppressed`, boundary translation,
bounded retries only for idempotent operations); the compile-before-and-verify-after loop.

### 3. google/error-prone
```json
{"full_name": "google/error-prone", "html_url": "https://github.com/google/error-prone", "stargazers_count": 7263, "pushed_at": "2026-10-29T01:01:58Z", "license": "Apache-2.0", "archived": false, "default_branch": "master"}
```
Read: `README.md`, `docs/installation.md` on the `gh-pages` branch (served as
https://errorprone.info/docs/installation), release `v2.51.0` notes (2026-10-22).
Took: Maven compiler flags (`-XDcompilePolicy=simple`, `--should-stop=ifError=FLOW`,
`-Xplugin:ErrorProne`), the `.mvn/jvm.config` `--add-exports`/`--add-opens` list and the `-J` form
for forked compilers, "Error Prone must be run on JDK 21 or newer", the JDK 21
`-XDaddTypeAnnotationsToSymbol=true` note, `annotationProcessorPaths` interaction with other
processors, and the `[BugPattern]` output format used in the gates.

### 4. uber/NullAway
```json
{"full_name": "uber/NullAway", "html_url": "https://github.com/uber/NullAway", "stargazers_count": 4126, "pushed_at": "2026-10-28T22:23:06Z", "license": "MIT", "archived": false, "default_branch": "master"}
```
Read: `README.md`, wiki pages `Configuration.md` and `JSpecify-Support.md`
(raw.githubusercontent.com/wiki/uber/NullAway/...).
Took: requirements (JDK 17+, Error Prone 2.36.0+), the rule that exactly one of
`AnnotatedPackages` / `OnlyNullMarked=true` must be passed, JSpecify as the recommended annotation
source, JSpecify mode needing JDK 22+ javac or `-XDaddTypeAnnotationsToSymbol=true` on OpenJDK
21.0.8+, generated-code exclusion, and Lombok caveats.

### 5. VoltAgent/awesome-claude-code-subagents
```json
{"full_name": "VoltAgent/awesome-claude-code-subagents", "html_url": "https://github.com/VoltAgent/awesome-claude-code-subagents", "stargazers_count": 26164, "pushed_at": "2026-10-11T08:20:37Z", "license": "MIT", "archived": false, "default_branch": "main"}
```
Read: `categories/02-language-specialists/java-architect.md` (287 lines).
Took: the breadth checklist of production concerns a Java agent must cover (Spring patterns,
persistence, security, messaging, observability, cloud-native). Deliberately not taken, as
counter-examples: its fixed `tools` allowlist and `model: sonnet` (this agent inherits both), the
Java 17+/Spring Boot 3.x baseline (stale for Oct 2026), the ">85% coverage" quota, and the
pre-written delivery message with invented metrics; the output contract here requires pasted
command output instead.

## MCP servers declared in the agent (verified 2026-10-29)

| Server | Repo / endpoint | Evidence |
|---|---|---|
| context7 | `https://mcp.context7.com/mcp` (http) | `initialize` POST returned `serverInfo.name=Context7`, `version 4.4.3`. |
| javadocs | `https://www.javadocs.dev/mcp` (http); source repo `jamesward/javadoccentral` (57 stars, pushed 2026-10-27T13:14:07Z, no license file) | `initialize` returned `serverInfo.name=javadocs.dev`; `tools/list` returned `get_latest_version`, `get_javadoc_index`, `list_javadoc_symbols`, `get_javadoc_symbol`, `get_source_file`, `list_source_files`, `search_artifacts`, `symbol_to_artifact`. Endpoint from the repo README ("Point your MCP client to https://www.javadocs.dev/mcp (Streamable HTTP)"). |
| maven-tools | `arvindand/maven-tools-mcp` (35 stars, pushed 2026-10-26T14:40:58Z, MIT) | README install: `docker run -i --rm arvindand/maven-tools-mcp:latest`; README documents `:3.2.3-noc7` (current release v3.2.3, no Context7 tools). Docker Hub tags `3.2.3-noc7` and `latest-noc7` updated 2026-10-04. Not executed here. |
| maven-decoder | `salitaba/maven-decoder-mcp` (20 stars, pushed 2026-09-16T15:25:28Z, MIT) | README config: `"command": "uvx", "args": ["maven-decoder-mcp"]`; declared here pinned as `["maven-decoder-mcp@1.3.2"]`. PyPI `maven-decoder-mcp` 1.3.2 is the latest (uploaded 2026-09-09, not yanked, MIT). Pin syntax: `uv help tool run` documents `<package>@<version>` ("e.g., `uv tool run ruff@0.3.0`"), and `uvx cowsay@6.1` ran here (uvx 0.13.1). `uv pip compile --no-build` resolves `maven-decoder-mcp==1.3.2` to 41 wheel-only packages on Python 3.10-3.13; on Python 3.15 it needs an sdist build of `cheetah3`, so pass `--python 3.13` to uvx if startup fails there. Transitive dependencies (for example `mcp`) are not pinned by this. The server itself was not started. |
| github | by-name reference to the already configured server | — |

Considered and not declared: `JetBrains/mcp-jetbrains` (963 stars, last push 2026-01-07; the IDE
now ships its own MCP server), `isaacphi/mcp-language-server` with jdtls (pushed 2026-03-01; needs a
local language-server setup), `bitfist/javadoc-mcp-server`, `jermeyyy/javadoc-mcp`,
`mustafagoksever/java-inspector`, `bhxch/jlens` (fewer than 5 stars each or overlapping with
javadocs.dev).

## Official version sources (fetched 2026-10-29)

| Fact | Source |
|---|---|
| JDK 25 GA 2025-09-16, LTS, JEP list | https://openjdk.org/projects/jdk/25/ |
| JDK 26 GA 2026-03-17, JEP list | https://openjdk.org/projects/jdk/26/ |
| JDK 27 GA 2026-09-15, JEP list (523, 527, 531-538) | https://openjdk.org/projects/jdk/27/ |
| JDK 28 proposed GA 2027-03-09 | https://openjdk.org/projects/jdk/28/ |
| JDK 22/23/24 JEP lists (491, 485, 490, 467, 456) | https://openjdk.org/projects/jdk/22/ , /23/ , /24/ |
| JEP 500 and JEP 514 text | https://openjdk.org/jeps/500 , https://openjdk.org/jeps/514 |
| Temurin 25.0.5+8 (2026-10-22), 27.0.1 (2026-10-24), 21.0.13+9 (2026-10-22), 26.0.2; most recent LTS 25 | https://api.adoptium.net/v3/info/available_releases and `/v3/assets/feature_releases/<v>/ga` |
| `ExecutorService.close()` since 19; `HttpClient` implements `AutoCloseable` since 21 | https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ExecutorService.html , https://docs.oracle.com/en/java/javase/25/docs/api/java.net.http/java/net/http/HttpClient.html |
| Maven 3.10.0 (2026-09-27), 4.0.0-rc-7 (2026-09-24), 3.9.16 | https://maven.apache.org/docs/history.html |
| Gradle 9.8.2 (2026-10-19); runs on JVM 17-27 | https://services.gradle.org/versions/current , https://docs.gradle.org/current/userguide/compatibility.html |
| Spring Boot 4.1.2 requires Java 17, compatible to 27, Framework 7.0.10+, GraalVM 25+ | https://docs.spring.io/spring-boot/system-requirements.html |
| Boot property defaults (`spring.jpa.open-in-view=true`, actuator exposure `[health]`, `spring.threads.virtual.enabled`, `logging.structured.format.console`) | https://docs.spring.io/spring-boot/appendix/application-properties/index.html |
| Spring Boot 4.0 changes (Jackson 3, Jakarta Servlet 6.1, Jackson 2 deprecated) | https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Release-Notes |
| Spring Boot releases v4.1.2 / v4.0.9 / v4.2.0-RC1 (2026-10-22), v4.1.0 (2026-06-10) | GitHub API `repos/spring-projects/spring-boot/releases` |
| JUnit r6.1.3 (2026-08-07), r5.14.4 (2026-04-26) | GitHub API `repos/junit-team/junit-framework/releases` |
| Testcontainers 2.0.5 (2026-04-20); 2.0.0 notes (module prefix, package relocation, JUnit 4 removed) | GitHub API `repos/testcontainers/testcontainers-java/releases` |
| JaCoCo 0.8.16 (2026-10-26): official Java 27 support | GitHub API `repos/jacoco/jacoco/releases/tags/v0.8.16` |
| SpotBugs 4.10.5 (2026-10-12) | GitHub API `repos/spotbugs/spotbugs/releases` |
| async-profiler 4.6 (2026-10-19) and its breaking changes | GitHub API `repos/async-profiler/async-profiler/releases/tags/v4.6` |
| OSV-Scanner v2.7.0 (2026-10-12); `osv-scanner scan source -r <dir>` | GitHub API `repos/google/osv-scanner/releases`, README |
| Error Prone min JDK per version (2.43+ needs 21); Gradle DSL `error()`, `option()` | https://errorprone.info/docs/installation , https://github.com/tbroyer/gradle-errorprone-plugin (README) |
| `UpgradeToJava25` recipe definition | https://github.com/openrewrite/rewrite-migrate-java (`src/main/resources/META-INF/rewrite/java-version-25.yml`) |
| palantir-java-format "120 character" formatter | https://github.com/palantir/palantir-java-format (README) |
| Subagent frontmatter, `mcpServers`, nested spawning (3 layers by default) | https://code.claude.com/docs/en/sub-agents.md |
| Library versions and upload dates (Last-Modified of the POM): spring-boot 4.1.2, spring-core 7.0.10, hibernate-core 7.4.14.Final, jackson-databind 2.22.4 (2026-10-17) and tools.jackson 3.2.4 (2026-10-18), quarkus-bom 3.40.1.1 (2026-10-19; 3.40.1 was 2026-09-30), micronaut-platform 5.2.4 (2026-10-26), archunit 1.5.1 (2026-09-25), jqwik 1.10.2 (2026-10-10), checkstyle 14.3.0 (2026-09-27), pmd-java 7.28.0 (2026-09-25), dependency-check-maven 13.0.0 (2026-08-03), cyclonedx-maven-plugin 2.9.3 (2026-07-30), jcstress-core and jcstress-java-test-archetype 0.16 (2023-02-27), jmh-generator-annprocess 1.37, jib-maven-plugin 3.5.2 (2026-07-14), central-publishing-maven-plugin 0.12.0 (2026-10-13), maven-gpg-plugin 3.2.8, maven-source-plugin 3.4.0, maven-javadoc-plugin 3.12.0, maven-artifact-plugin 3.7.0, mockito-core 5.24.0, assertj-core 3.27.7, testcontainers 2.0.5, archunit-junit5 1.5.1, error_prone_core 2.51.0, nullaway 0.14.3, jspecify 1.0.1, spotless-maven-plugin 3.10.4, spotless-plugin-gradle 8.10.4, google-java-format 1.37.0 (latest) and 1.36.1 (2026-07-30, Spotless default), palantir-java-format 2.103.0, spotbugs-maven-plugin 4.10.5.0, findsecbugs-plugin 1.14.0, jacoco-maven-plugin 0.8.16, pitest-maven 1.30.1, pitest-junit5-plugin 1.2.3, jmh-core 1.37, rewrite-maven-plugin 6.46.1, maven-compiler-plugin 3.16.0, maven-surefire/failsafe-plugin 3.6.1, maven-dependency-plugin 3.11.0, maven-checkstyle-plugin 3.6.0, maven-pmd-plugin 3.28.0, maven-wrapper 3.3.4, caffeine 3.3.1, slf4j-api 2.0.20, logback-classic 1.6.6 | https://repo1.maven.org/maven2/<group>/<artifact>/maven-metadata.xml |
| Gradle plugin versions: net.ltgt.errorprone 5.1.1, net.ltgt.nullaway 3.3.0, com.diffplug.spotless 8.10.4, com.github.spotbugs 6.5.13, info.solidsoft.pitest 1.19.0, me.champeau.jmh 0.7.3, com.google.cloud.tools.jib 3.5.4 (2026-07-14) | https://plugins.gradle.org/m2/<plugin path>/maven-metadata.xml |
| Spotless 3.10.3 / 8.10.3 made google-java-format 1.36.1 the default; GJF 1.37.0 released 2026-10-01 | GitHub API `repos/diffplug/spotless/contents/plugin-maven/CHANGES.md` and `plugin-gradle/CHANGES.md`; `repos/google/google-java-format/releases` |
| Mockito `-javaagent` wiring for Gradle (`mockitoAgent` configuration, `isTransitive = false`) and Maven | Mockito 5.24.0 Javadoc (`mockito-core-5.24.0-javadoc.jar` from repo1.maven.org, `org/mockito/Mockito.html`) |
| Maven 3.10.0: super POM sets `project.build.outputTimestamp` (reproducible by default) and UTF-8 encodings | https://maven.apache.org/docs/3.10.0/release-notes.html , https://maven.apache.org/guides/mini/guide-reproducible-builds.html |
| Gradle 9: archive tasks are reproducible by default | https://docs.gradle.org/9.0.0/release-notes.html , https://docs.gradle.org/current/userguide/working_with_files.html |
| jlink without JMOD files and its restrictions (JEP 493, JDK 24) | https://openjdk.org/jeps/493 |
| Spring Boot AOT cache training on the extracted layout; `-Djarmode=tools` `extract --layers`, `list-layers`; `build-image` / `bootBuildImage` need a Docker daemon | https://docs.spring.io/spring-boot/reference/packaging/aot-cache.html , https://docs.spring.io/spring-boot/reference/packaging/container-images/dockerfiles.html , https://docs.spring.io/spring-boot/maven-plugin/build-image.html , https://docs.spring.io/spring-boot/gradle-plugin/packaging-oci-image.html |
| Jib releases v3.5.2-maven / v3.5.4-gradle (2026-07-14); repo 14,451 stars, Apache-2.0, pushed 2026-10-16 | GitHub API `repos/GoogleContainerTools/jib/releases`, https://github.com/GoogleContainerTools/jib |
| Central Portal: plugin 0.12.0 (13 Oct 2026, adds `skipUpload`), `publishingServerId`, `autoPublish`, `waitUntil`; requirements (sources, javadoc, `.asc` signatures, checksums, POM name/description/url/licenses/developers/scm); no official Gradle plugin; OSSRH end of life 2025-06-30 | https://central.sonatype.org/publish/publish-portal-maven/ , https://central.sonatype.org/publish/requirements/ , https://central.sonatype.org/publish/publish-portal-gradle/ , https://central.sonatype.org/news/20250326_ossrh_sunset/ |
| Subagent tool limits live in the definition's `tools` / `disallowedTools` fields; built-in Explore denies Write and Edit | https://code.claude.com/docs/en/sub-agents.md |

## Verification runs (2026-10-29, fix pass)

Toolchain: Temurin 25.0.5+8, Apache Maven 3.10.0, Gradle 9.8.2, unpacked in the session
scratchpad (the system has no JDK on `PATH`). Projects were scratch copies; nothing from a mined
repository was executed.

| Recipe | Command | Result |
|---|---|---|
| Spotless, GJF 1.37.0 (old pin) | `mvn spotless:check` / `gradle spotlessCheck` | exit 1, `google-java-format(java.lang.reflect.InvocationTargetException)` in both |
| Spotless, GJF 1.36.1 / `<googleJavaFormat/>` | `mvn spotless:check` | exit 0; `mvn -X` shows the empty element resolves `google-java-format:jar:1.36.1` |
| Maven sections 1, 3, 4 together (Error Prone + NullAway, Spotless 1.36.1, JaCoCo, Surefire/Failsafe with Mockito agent) | `mvn -B -ntp spotless:check verify` | exit 0, `Tests run: 3, Failures: 0, Errors: 0, Skipped: 0` |
| PIT (section 5) | `mvn test-compile org.pitest:pitest-maven:mutationCoverage` | exit 0, `Generated 4 mutations Killed 3 (75%)` |
| Gradle block (section 2), pasted verbatim | `gradle build`, `gradle spotlessCheck` | exit 0 / 0; test XML has 0 matches for "self-attaching" or "loaded dynamically" (the same build without `mockitoAgent` had both) |
| JMH 1.37 archetype, unmodified | `mvn package` then `java -jar target/benchmarks.jar` | package exit 0, run exit 1: `Unable to find the resource: /META-INF/BenchmarkList` |
| JMH with `annotationProcessorPaths` or `-proc:full` | same | run exit 0, `ParseBench.parse avgt 2 756.312 ns/op` (processor path), `927.210 ns/op` (`-proc:full`) |
| jcstress 0.16 archetype, unmodified | `java -jar target/jcstress.jar -t ConcurrencyTest -m sanity` | exit 1, exception in `TestList.getTests` |
| jcstress with `-proc:full`, racy `int` counter | `java -jar target/jcstress.jar -t CounterTest -m quick` | exit 1, `[FAILED]`, `1, 1  23,670  1.45%  Forbidden  lost update` |
| jcstress, `AtomicInteger` counter | same with `-t AtomicCounterTest` | exit 0 |
| AOT cache training | `java -XX:AOTCacheOutput=dir.aot -cp classes Hi` / `-jar hi.jar` | exit 1 "Cannot have non-empty directory in paths" / exit 0, next run logs "Opened AOT cache app.aot." |
| Reproducible jar (section 10) | two `mvn clean package`, `sha256sum`; `artifact:check-buildplan` (3.7.0) | identical hashes with and without `outputTimestamp` (super POM default `1980-02-01T00:00:00Z`); "No known issue in 9 plugins" |
| module-info, jdeps, jlink, jpackage | see section 10 | `requires java.net.http transitive`, `qualified opens ... to java.logging`; image 57 MB with 3 modules; `jpackage --type app-image` launcher runs; `Automatic-Module-Name` jar described as `com.acme.lib@1.0 automatic` |
| Jib 3.5.2 | `mvn package jib:buildTar` | exit 0; image config user `1000:1000`, created `1970-01-01T00:00:00Z`, base `eclipse-temurin:25-jre` |
| Central Portal dry run | `mvn deploy` with `skipUpload`, throwaway GPG key in a scratch `GNUPGHOME` | exit 0; `central-bundle.zip` holds jar, sources, javadoc, POM, each with `.asc`, `.md5`, `.sha1`, `.sha256`, `.sha512` |

## [UNVERIFIED] items

- Not executed: Testcontainers (no Docker access for this user), `spring-boot:build-image` /
  `bootBuildImage` (needs a Docker daemon), the Gradle PIT and JMH plugins, the static-analysis
  table (build-recipes section 8), and the dependency and OpenRewrite commands (section 9). Those
  come from the official docs above.
- The two stdio MCP servers (maven-tools via Docker, maven-decoder via uvx) were not started, per
  the rule not to run code from mined repositories; only their README commands, Docker Hub tags and
  PyPI metadata (plus a wheel-only resolve of maven-decoder-mcp 1.3.2) were checked.
- A real upload to the Central Portal (needs a verified namespace and a Portal token).

## Self-check (re-run 2026-10-29 after the fix pass)

Scripts: a Python checker in the session scratchpad (`yaml.safe_load` from PyYAML 6.0.1, heading
order check, line counts, `ghapi.sh repos/<owner>/<repo>` for every GitHub repo linked in the
files, HTTP GET for every other URL) plus a second script for the MCP-server repos named without a
link and a JSON-RPC `initialize` POST to the two remote MCP endpoints. Output pasted verbatim:

```text
yaml.safe_load(agent): OK keys=['description', 'mcpServers', 'model', 'name', 'skills'] unknown_keys=[] mcpServers=['github', 'context7', 'javadocs', 'maven-tools', 'maven-decoder']
yaml.safe_load(skill): OK keys=['description', 'name'] unknown_keys=[]
headings: all 9 present=True in_order=True found=['## Role and scope', '## Operating loop', '## Toolchain baseline (October 2026)', '## Engineering rules', '## Verification gates', '## Delegation', '## MCP and skills usage', '## Anti-patterns', '## Output contract']
lines agent: 391
lines skill: 317
lines ref1: 482
lines ref2: 89
lines sources: 258
ghapi repos/GoogleContainerTools/jib: OK GoogleContainerTools/jib pushed 2026-10-16T16:30:55Z
ghapi repos/VoltAgent/awesome-claude-code-subagents: OK VoltAgent/awesome-claude-code-subagents pushed 2026-10-11T08:20:37Z
ghapi repos/async-profiler/async-profiler: OK async-profiler/async-profiler pushed 2026-10-27T01:32:15Z
ghapi repos/github/awesome-copilot: OK github/awesome-copilot pushed 2026-10-29T00:07:04Z
ghapi repos/google/error-prone: OK google/error-prone pushed 2026-10-29T01:01:58Z
ghapi repos/jabrena/plinth: OK jabrena/plinth pushed 2026-10-29T05:13:20Z
ghapi repos/openrewrite/rewrite-migrate-java: OK openrewrite/rewrite-migrate-java pushed 2026-10-29T07:14:42Z
ghapi repos/palantir/palantir-java-format: OK palantir/palantir-java-format pushed 2026-10-29T08:39:41Z
ghapi repos/spring-projects/spring-boot: OK spring-projects/spring-boot pushed 2026-10-29T09:59:44Z
ghapi repos/tbroyer/gradle-errorprone-plugin: OK tbroyer/gradle-errorprone-plugin pushed 2026-10-23T13:20:32Z
ghapi repos/uber/NullAway: OK uber/NullAway pushed 2026-10-28T22:23:06Z
GET https://api.adoptium.net/v3/info/available_releases: 200
GET https://central.sonatype.org/news/20250326_ossrh_sunset/: 200
GET https://central.sonatype.org/publish/publish-portal-gradle/: 200
GET https://central.sonatype.org/publish/publish-portal-maven/: 200
GET https://central.sonatype.org/publish/requirements/: 200
GET https://code.claude.com/docs/en/sub-agents.md: 200
GET https://docs.gradle.org/9.0.0/release-notes.html: 200
GET https://docs.gradle.org/current/userguide/compatibility.html: 200
GET https://docs.gradle.org/current/userguide/working_with_files.html: 200
GET https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ExecutorService.html: 200
GET https://docs.oracle.com/en/java/javase/25/docs/api/java.net.http/java/net/http/HttpClient.html: 200
GET https://docs.oracle.com/en/java/javase/25/docs/specs/man/jcmd.html: 200
GET https://docs.spring.io/spring-boot/appendix/application-properties/index.html: 200
GET https://docs.spring.io/spring-boot/gradle-plugin/packaging-oci-image.html: 200
GET https://docs.spring.io/spring-boot/maven-plugin/build-image.html: 200
GET https://docs.spring.io/spring-boot/reference/packaging/aot-cache.html: 200
GET https://docs.spring.io/spring-boot/reference/packaging/container-images/dockerfiles.html: 200
GET https://docs.spring.io/spring-boot/system-requirements.html: 200
GET https://errorprone.info/docs/installation: 200
GET https://maven.apache.org/docs/3.10.0/release-notes.html: 200
GET https://maven.apache.org/docs/history.html: 200
GET https://maven.apache.org/guides/mini/guide-reproducible-builds.html: 200
GET https://mcp.context7.com/mcp: skip-GET (MCP endpoint; verified via initialize POST)
GET https://openjdk.org/jeps/493: 200
GET https://openjdk.org/jeps/500: 200
GET https://openjdk.org/jeps/514: 200
GET https://openjdk.org/projects/jdk/22/: 200
GET https://openjdk.org/projects/jdk/25/: 200
GET https://openjdk.org/projects/jdk/26/: 200
GET https://openjdk.org/projects/jdk/27/: 200
GET https://openjdk.org/projects/jdk/28/: 200
GET https://plugins.gradle.org/m2/: 200
GET https://repo1.maven.org/maven2/: 200
GET https://services.gradle.org/versions/current: 200
GET https://www.javadocs.dev/mcp: skip-GET (MCP endpoint; verified via initialize POST)
ghapi repos/arvindand/maven-tools-mcp: OK arvindand/maven-tools-mcp pushed 2026-10-26T14:40:58Z
ghapi repos/salitaba/maven-decoder-mcp: OK salitaba/maven-decoder-mcp pushed 2026-09-16T15:25:28Z
ghapi repos/jamesward/javadoccentral: OK jamesward/javadoccentral pushed 2026-10-27T13:14:07Z
ghapi repos/JetBrains/mcp-jetbrains: OK JetBrains/mcp-jetbrains pushed 2026-01-07T16:21:45Z
ghapi repos/isaacphi/mcp-language-server: OK isaacphi/mcp-language-server pushed 2026-03-01T23:27:09Z
ghapi repos/bitfist/javadoc-mcp-server: OK bitfist/javadoc-mcp-server pushed 2026-08-29T04:01:32Z
ghapi repos/jermeyyy/javadoc-mcp: OK jermeyyy/javadoc-mcp pushed 2025-10-11T18:46:56Z
ghapi repos/mustafagoksever/java-inspector: OK mustafagoksever/java-inspector pushed 2026-08-22T09:57:18Z
ghapi repos/bhxch/jlens: OK bhxch/jlens pushed 2026-03-16T15:41:45Z
ghapi repos/jabrena/cursor-rules-java: FAIL Moved Permanently
ghapi repos/diffplug/spotless: OK diffplug/spotless pushed 2026-10-28T19:34:32Z
ghapi repos/google/google-java-format: OK google/google-java-format pushed 2026-10-29T10:19:58Z
POST initialize https://mcp.context7.com/mcp: "serverInfo":{"name":"Context7","title":
POST initialize https://www.javadocs.dev/mcp: "serverInfo":{"name":"javadocs.dev","ver
```

Notes: the agent is 391 lines (target 250-500); SKILL.md is 317 lines (target 150-400) plus two
reference files. The checker ran after this block was pasted, so `lines sources` is the final line
count of this file (confirm with `wc -l sources/java.md`). URLs containing `<placeholders>` were
excluded from the GET check by design. `jabrena/cursor-rules-java` answers 301 because the repo was
renamed to `jabrena/plinth`, which is checked above.
