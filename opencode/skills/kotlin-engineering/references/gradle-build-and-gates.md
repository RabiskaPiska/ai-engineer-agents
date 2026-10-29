# Gradle build setup and gate wiring (Kotlin 2.4.21, Gradle 9.8.2)

Snippets below were checked against official docs on 2026-10-29 (kotlinlang.org KGP pages, detekt.dev,
Spotless plugin README, Kover docs, Gradle user guide). Versions belong in
`gradle/libs.versions.toml`; inline versions here are for readability only. Add a gate only when
the project lacks it, and in its own change.

## Version catalog skeleton

```toml
[versions]
kotlin = "2.4.21"
coroutines = "1.11.0"
serialization = "1.12.0"
ktor = "3.6.0"
kotest = "6.2.6"
junit = "6.1.3"
mockk = "1.14.11"
turbine = "1.2.1"
kover = "0.9.11"
detekt = "2.0.0-alpha.6"
spotless = "8.10.4"
ktlint = "1.8.0"

[libraries]
kotlinx-coroutines-core = { module = "org.jetbrains.kotlinx:kotlinx-coroutines-core", version.ref = "coroutines" }
kotlinx-coroutines-test = { module = "org.jetbrains.kotlinx:kotlinx-coroutines-test", version.ref = "coroutines" }
kotlinx-serialization-json = { module = "org.jetbrains.kotlinx:kotlinx-serialization-json", version.ref = "serialization" }
turbine = { module = "app.cash.turbine:turbine", version.ref = "turbine" }
mockk = { module = "io.mockk:mockk", version.ref = "mockk" }

[plugins]
kotlin-jvm = { id = "org.jetbrains.kotlin.jvm", version.ref = "kotlin" }
kotlin-serialization = { id = "org.jetbrains.kotlin.plugin.serialization", version.ref = "kotlin" }
kover = { id = "org.jetbrains.kotlinx.kover", version.ref = "kover" }
detekt = { id = "dev.detekt", version.ref = "detekt" }
spotless = { id = "com.diffplug.spotless", version.ref = "spotless" }
```

## Compiler options (module or convention plugin)

```kotlin
kotlin {
    jvmToolchain(25)                       // JDK used to compile and test
    explicitApi()                          // libraries only
    compilerOptions {
        allWarningsAsErrors.set(true)      // CI-grade; document exceptions below
        extraWarnings.set(true)            // -Wextra: additional checks
        progressiveMode.set(true)          // optional: adopt fixes for unstable code immediately
        freeCompilerArgs.addAll(
            "-Xreturn-value-checker=check",          // unused return value checker (2.3+)
            // "-Xwarning-level=DIAGNOSTIC_NAME:warning", // targeted exception to -Werror, with a comment why
        )
    }
}
```

- `jvmTarget` defaults from the toolchain; set it lower only when the deployment JVM is older.
  Kotlin 2.4 accepts targets up to 26.
- Spring projects on Kotlin 2.2/2.3: add `-Xannotation-default-target=param-property`.
- Use `-Xrender-internal-diagnostic-names` once to discover a diagnostic's name for `-Xwarning-level`.

## Formatting: Spotless with ktlint (or ktfmt)

```kotlin
plugins { id("com.diffplug.spotless") version "8.10.4" }

spotless {
    kotlin {
        target("src/**/*.kt")
        ktlint("1.8.0")                    // reads .editorconfig (ktlint_code_style etc.)
        // or: ktfmt("0.65").googleStyle()
    }
    kotlinGradle {
        target("*.gradle.kts")
        ktlint("1.8.0")
    }
}
```

Gate: `./gradlew spotlessCheck`. Fix: `./gradlew spotlessApply`. Keep `kotlin.code.style=official`
in `gradle.properties` so the IDE formatter agrees.

Compiler alignment, same caveat as detekt: ktlint 1.8.0 is built on Kotlin 2.2.21 (its
`gradle/libs.versions.toml` at tag 1.8.0), ktfmt 0.65 on Kotlin 2.4.10. On 2026-10-29 both parsed
and formatted Kotlin 2.4 collection literals, explicit backing fields and context parameters in a
small sample without errors, but that is a sample, not a guarantee. When a codebase uses 2.4-only
syntax, run the formatter once over those files and read the result before trusting
`spotlessCheck`, or prefer ktfmt 0.65. Since 0.65, ktfmt is published as `org.jetbrains.kotlinx:ktfmt`
(was `com.facebook:ktfmt`); Spotless 8.10.4 picks the right coordinate from the version.

## Static analysis: detekt

Kotlin 2.4 projects: detekt 2.0.0-alpha.6 is built against Kotlin 2.4.10 (detekt compatibility
table); 1.23.8 is built against Kotlin 2.0.21. Pin whichever you choose exactly.

```kotlin
plugins { id("dev.detekt") version "2.0.0-alpha.6" }   // 1.x used id("io.gitlab.arturbosch.detekt")

detekt {
    buildUponDefaultConfig = true
    config.setFrom("$rootDir/config/detekt/detekt.yml")
    baseline = file("$rootDir/config/detekt/baseline.xml")  // existing debt only; never grow it
    parallel = true
}
```

Tasks: `detekt` (no type resolution, runs in `check`), `detektMain`/`detektTest` (type resolution,
more rules), `detektBaseline`, `detektGenerateConfig`. Reports land in `build/reports/detekt/`
(xml, html, md, sarif); upload the SARIF to code scanning in CI.

## Coverage: Kover

```kotlin
plugins { id("org.jetbrains.kotlinx.kover") version "0.9.11" }

kover {
    reports {
        verify {
            rule {
                minBound(80)               // start at the current measured value, ratchet up
            }
        }
    }
}
```

Tasks: `koverHtmlReport`, `koverXmlReport` (JaCoCo-compatible XML for CI), `koverVerify`. In
multi-module builds aggregate in one merging module and call tasks by full path
(`:app:koverXmlReport`); short names run every project's tests. Android variants:
`:app:koverVerifyDebug`.

## Binary compatibility (libraries)

```kotlin
kotlin {
    @OptIn(org.jetbrains.kotlin.gradle.dsl.abi.ExperimentalAbiValidation::class)
    abiValidation()
}
```

`./gradlew checkKotlinAbi` compares against the checked-in dump (also runs as part of `check`);
`./gradlew updateKotlinAbi` regenerates it after an intended change. Review the dump diff in the PR.
Kotlin 2.4 deprecated parts of the earlier DSL; the separate `binary-compatibility-validator`
plugin is superseded by this built-in support for new setups.

## Tests

```kotlin
dependencies {
    testImplementation(kotlin("test"))                      // kotlin.test, JUnit platform on JVM
    testImplementation(libs.kotlinx.coroutines.test)
    testImplementation(libs.turbine)
    testImplementation(libs.mockk)
}
tasks.test { useJUnitPlatform() }
```

Kotest: `testImplementation("io.kotest:kotest-runner-junit5:6.2.6")` plus assertions module,
`useJUnitPlatform()`. KMP: tests in `commonTest` with kotlin.test; run `./gradlew allTests`.
Filter: `./gradlew :core:test --tests 'com.acme.OrderServiceTest'`.

## Reproducibility and supply chain

```properties
# gradle.properties
org.gradle.configuration-cache=true
org.gradle.caching=true
org.gradle.parallel=true
kotlin.code.style=official
```

- Daemon JVM pin: `./gradlew updateDaemonJvm --jvm-version=25` writes
  `gradle/gradle-daemon-jvm.properties`.
- Dependency verification: `./gradlew --write-verification-metadata sha256 help` creates
  `gradle/verification-metadata.xml`; commit it and review changes to it like code.
- Dependency locking (applications): `dependencyLocking { lockAllConfigurations() }`, then
  `./gradlew dependencies --write-locks`.
- Vulnerabilities: `osv-scanner scan source -r .` (OSV-Scanner 2.7.0) in CI. It reads
  `gradle.lockfile` or `gradle/verification-metadata.xml`, not `build.gradle.kts`, so one of those
  must exist first. Exit codes (OSV-Scanner docs, and measured with 2.5.0 on 2026-10-29): `0` =
  packages found, none vulnerable; `1` = vulnerabilities found; `128` = "No package sources found",
  nothing scanned. Treat `128` as NOT RUN, never as a pass:
  ```bash
  osv-scanner scan source -r . > osv.log 2>&1; rc=$?
  case $rc in 0) echo PASS;; 1) echo "FAIL: vulnerabilities"; grep -m1 'known vulnerabilit' osv.log;;
    128) echo "NOT RUN: no lockfile or verification-metadata.xml";; *) echo "ERROR rc=$rc";; esac
  ```
- Wrapper upgrades: `./gradlew wrapper --gradle-version 9.8.2` and verify the distribution checksum.

## Benchmarks: kotlinx-benchmark

```kotlin
plugins {
    id("org.jetbrains.kotlinx.benchmark") version "0.5.0"
    kotlin("plugin.allopen") version "2.4.21"
}
allOpen { annotation("org.openjdk.jmh.annotations.State") }
dependencies { implementation("org.jetbrains.kotlinx:kotlinx-benchmark-runtime:0.5.0") }
benchmark {
    targets { register("main") }             // Kotlin/JVM project; in KMP register the target name, e.g. "jvm"
    configurations {
        named("main") {
            warmups = 5; iterations = 5
            iterationTime = 1; iterationTimeUnit = "s"
            mode = "avgt"; outputTimeUnit = "ns"
            advanced("jvmForks", 9)          // several forks so the error bar covers JIT variance
        }
    }
}
```

Run `./gradlew benchmark`; keep JMH results as JSON artifacts and compare against the previous run
on the same machine and JDK. This exact setup (Kotlin 2.4.21, kotlinx-benchmark 0.5.0, Gradle
9.8.2, JDK 25.0.5) was built and run on 2026-10-29; the measured results are in
[benchmark-sequence-vs-list.md](benchmark-sequence-vs-list.md).

## Maven equivalent

```xml
<properties>
  <maven.compiler.release>25</maven.compiler.release>
  <kotlin.version>2.4.21</kotlin.version>
</properties>
<plugin>
  <groupId>org.jetbrains.kotlin</groupId>
  <artifactId>kotlin-maven-plugin</artifactId>
  <version>${kotlin.version}</version>
  <extensions>true</extensions>   <!-- 2.4: jvmTarget derived from maven.compiler.release -->
</plugin>
```

Kotlin 2.4 also honors `maven-toolchains-plugin` for the compile JDK. Gate: `mvn -q verify`.

## Kotlin Toolchain (ex-Amper, Alpha, 0.13.0)

Projects with `project.yaml`/`module.yaml` and a `./kotlin` wrapper: run `./kotlin build`,
`./kotlin test` from the project root so the wrapper's pinned version is used. Do not add Gradle
files to such a project. Kotlin 2.4.20 renamed the standalone script runner to `kotlinr` to avoid
clashing with the Toolchain's `kotlin` command.

## Reading Gradle output without flooding context

```bash
./gradlew check --console=plain > build.log 2>&1; echo "exit=$?"
tail -40 build.log
grep -n -m5 -E '^e: |FAILED|What went wrong|Could not resolve' build.log
```

The exit code comes from Gradle directly (no pipe), the verdict is at the bottom, and the cause is
usually the first `e:` or `What went wrong` line.
