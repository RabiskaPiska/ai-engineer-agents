# Build recipes (Maven and Gradle), checked 2026-10-29

Versions are the current stable releases on Maven Central / the Gradle Plugin Portal on
2026-10-29. Keep the project's existing versions unless the task is an upgrade, and add a tool the
project lacks only when the task asks for it. The Maven fragments in sections 1-7 and 10 and the
Gradle block in section 2 were executed on 2026-10-29 with Temurin 25.0.5+8, Maven 3.10.0 and
Gradle 9.8.2 (`sources/java.md` lists the runs). Not executed: Testcontainers (section 4), the
Gradle PIT/JMH plugins, `spring-boot:build-image`/`bootBuildImage`, and sections 8-9, which come
from the official docs. Still run `./mvnw -B verify` / `./gradlew build` after pasting and fix what
the build reports.

A formatter or plugin version only works with the plugin releases that support it, so pin versions
that were released together (or leave the version out and take the plugin's default) rather than
picking the newest of each.

## 1. Compiler: release, encoding, -Xlint, Error Prone + NullAway (Maven)

```xml
<properties>
  <maven.compiler.release>25</maven.compiler.release>
  <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
  <error-prone.version>2.51.0</error-prone.version>
  <nullaway.version>0.14.3</nullaway.version>
</properties>

<dependencies>
  <dependency>
    <groupId>org.jspecify</groupId>
    <artifactId>jspecify</artifactId>
    <version>1.0.1</version>
  </dependency>
</dependencies>

<build>
  <plugins>
    <plugin>
      <groupId>org.apache.maven.plugins</groupId>
      <artifactId>maven-compiler-plugin</artifactId>
      <version>3.16.0</version>
      <configuration>
        <compilerArgs>
          <arg>-Xlint:all</arg>
          <arg>-XDcompilePolicy=simple</arg>
          <arg>--should-stop=ifError=FLOW</arg>
          <!-- only when the build JDK is 21: -->
          <!-- <arg>-XDaddTypeAnnotationsToSymbol=true</arg> -->
          <arg>-Xplugin:ErrorProne -XepDisableWarningsInGeneratedCode -Xep:NullAway:ERROR -XepOpt:NullAway:OnlyNullMarked=true</arg>
        </compilerArgs>
        <annotationProcessorPaths>
          <path>
            <groupId>com.google.errorprone</groupId>
            <artifactId>error_prone_core</artifactId>
            <version>${error-prone.version}</version>
          </path>
          <path>
            <groupId>com.uber.nullaway</groupId>
            <artifactId>nullaway</artifactId>
            <version>${nullaway.version}</version>
          </path>
          <!-- other processors (MapStruct, Lombok, Hibernate jpamodelgen) must be listed here too -->
        </annotationProcessorPaths>
      </configuration>
    </plugin>
  </plugins>
</build>
```

`.mvn/jvm.config` (Error Prone needs these because JDK 16+ strongly encapsulates javac internals;
one flag per line). If the compiler is forked (`<fork>true</fork>` or toolchains), pass them as
`-J--add-exports=...` compiler args instead:

```
--add-exports jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED
--add-exports jdk.compiler/com.sun.tools.javac.file=ALL-UNNAMED
--add-exports jdk.compiler/com.sun.tools.javac.main=ALL-UNNAMED
--add-exports jdk.compiler/com.sun.tools.javac.model=ALL-UNNAMED
--add-exports jdk.compiler/com.sun.tools.javac.parser=ALL-UNNAMED
--add-exports jdk.compiler/com.sun.tools.javac.processing=ALL-UNNAMED
--add-exports jdk.compiler/com.sun.tools.javac.tree=ALL-UNNAMED
--add-exports jdk.compiler/com.sun.tools.javac.util=ALL-UNNAMED
--add-opens jdk.compiler/com.sun.tools.javac.code=ALL-UNNAMED
--add-opens jdk.compiler/com.sun.tools.javac.comp=ALL-UNNAMED
```

Facts behind the fragment:
- Error Prone 2.43+ must run on JDK 21 or newer; target older bytecode with `--release`.
- On a JDK 21 build, Error Prone requires `-XDaddTypeAnnotationsToSymbol=true`.
- NullAway needs Error Prone 2.36.0+ and exactly one of `OnlyNullMarked=true` or
  `AnnotatedPackages=<prefix>`; both or neither fails at load.
- All Error Prone flags (`-Xep...`) go inside the single `-Xplugin:ErrorProne ...` argument.
- `package-info.java`: `@NullMarked package com.acme.orders;` with
  `import org.jspecify.annotations.NullMarked;`.

## 2. Same in Gradle (Kotlin DSL)

```kotlin
import net.ltgt.gradle.errorprone.errorprone

plugins {
    java
    id("net.ltgt.errorprone") version "5.1.1"
    id("com.diffplug.spotless") version "8.10.4"
    jacoco
}

repositories { mavenCentral() }   // omit if settings.gradle.kts declares repositories

java { toolchain { languageVersion = JavaLanguageVersion.of(25) } }

// Mockito as a -javaagent (JV-TEST-04): no self-attach / dynamic-agent warnings on JDK 21+
val mockitoAgent = configurations.create("mockitoAgent")

dependencies {
    implementation("org.jspecify:jspecify:1.0.1")
    errorprone("com.google.errorprone:error_prone_core:2.51.0")
    errorprone("com.uber.nullaway:nullaway:0.14.3")

    testImplementation(platform("org.junit:junit-bom:6.1.3"))
    testImplementation("org.junit.jupiter:junit-jupiter")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")   // required with Gradle 9
    testImplementation("org.assertj:assertj-core:3.27.7")
    testImplementation("org.mockito:mockito-core:5.24.0")
    mockitoAgent("org.mockito:mockito-core:5.24.0") { isTransitive = false }
}

tasks.withType<JavaCompile>().configureEach {
    options.release = 25
    options.encoding = "UTF-8"
    options.compilerArgs.add("-Xlint:all")
    options.errorprone {
        disableWarningsInGeneratedCode = true
        error("NullAway")
        option("NullAway:OnlyNullMarked", true)
    }
}

tasks.test {
    useJUnitPlatform()
    jvmArgs("-javaagent:${mockitoAgent.asPath}")
}

// 1.36.1 is Spotless 8.10.4's default; google-java-format 1.37.0 fails under it (see section 3)
spotless { java { googleJavaFormat("1.36.1"); removeUnusedImports() } }
```

The Gradle plugin adds the `--add-exports`/`--add-opens` JVM flags itself. The
`net.ltgt.nullaway` plugin (3.3.0) is an optional shortcut for NullAway options. Without the
`mockitoAgent` wiring, the test XML under `build/test-results/test/` contains "Mockito is currently
self-attaching" and "WARNING: A Java agent has been loaded dynamically"; with it, neither appears.
Mockito's Javadoc also shows a `CommandLineArgumentProvider` form of the same wiring, which keeps
the test task relocatable for the build cache.

## 3. Formatting with Spotless (Maven)

```xml
<plugin>
  <groupId>com.diffplug.spotless</groupId>
  <artifactId>spotless-maven-plugin</artifactId>
  <version>3.10.4</version>
  <configuration>
    <java>
      <googleJavaFormat><version>1.36.1</version></googleJavaFormat>  <!-- or <palantirJavaFormat><version>2.103.0</version></palantirJavaFormat> -->
      <removeUnusedImports/>
    </java>
  </configuration>
</plugin>
```

`./mvnw spotless:check` fails on violations; `spotless:apply` fixes them. Spotless 3.10.3 / 8.10.3
made google-java-format 1.36.1 the default, and an empty `<googleJavaFormat/>` resolves to it. Do
not pin google-java-format 1.37.0 with Spotless 3.10.4 / 8.10.4: every file fails with
`google-java-format(java.lang.reflect.InvocationTargetException)`, although 1.37.0 itself runs fine
standalone. Raise the formatter version only after a Spotless release adopts it. google-java-format uses
2-space indentation; palantir-java-format describes itself as a lambda-friendly 120-character
formatter. Match what the team already uses and never reformat untouched files in a feature change.

## 4. Unit vs integration tests, JaCoCo, Mockito agent (Maven)

```xml
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-dependency-plugin</artifactId>
  <version>3.11.0</version>
  <executions><execution><goals><goal>properties</goal></goals></execution></executions>
</plugin>
<plugin>
  <groupId>org.jacoco</groupId>
  <artifactId>jacoco-maven-plugin</artifactId>
  <version>0.8.16</version>
  <executions>
    <execution><goals><goal>prepare-agent</goal></goals></execution>
    <execution><id>report</id><phase>verify</phase><goals><goal>report</goal></goals></execution>
  </executions>
</plugin>
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-surefire-plugin</artifactId>
  <version>3.6.1</version>
  <configuration>
    <argLine>@{argLine} -javaagent:${org.mockito:mockito-core:jar}</argLine>
  </configuration>
</plugin>
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-failsafe-plugin</artifactId>
  <version>3.6.1</version>
  <configuration>
    <argLine>@{argLine} -javaagent:${org.mockito:mockito-core:jar}</argLine>
  </configuration>
  <executions>
    <execution><goals><goal>integration-test</goal><goal>verify</goal></goals></execution>
  </executions>
</plugin>
```

- `@{argLine}` keeps the JaCoCo agent; without a `prepare-agent` execution a literal `@{argLine}`
  breaks the forked JVM, so drop it when JaCoCo is absent.
- The Mockito agent form needs `mockito-core` 5.14.0+ (earlier jars have no `Premain-Class`).
- Surefire runs `*Test`, `Test*`, `*Tests`, `*TestCase`; Failsafe runs `*IT`, `IT*`, `*ITCase` during
  `verify`. Run one IT with `./mvnw -Dit.test=OrderRepositoryIT verify`.
- JaCoCo report: `target/site/jacoco/index.html`. Add a `check` execution only if the project
  already enforces a threshold.

Testcontainers 2.x (`org.testcontainers:testcontainers-bom:2.0.5` imported in
`dependencyManagement`):

```xml
<dependency>
  <groupId>org.testcontainers</groupId>
  <artifactId>testcontainers-postgresql</artifactId>
  <scope>test</scope>
</dependency>
<dependency>
  <groupId>org.testcontainers</groupId>
  <artifactId>testcontainers-junit-jupiter</artifactId>
  <scope>test</scope>
</dependency>
```

Container classes moved to `org.testcontainers.<module>` (for example
`org.testcontainers.postgresql.PostgreSQLContainer`); pin image tags (`postgres:17.6`), never
`latest`.

## 5. Mutation testing with PIT

```xml
<plugin>
  <groupId>org.pitest</groupId>
  <artifactId>pitest-maven</artifactId>
  <version>1.30.1</version>
  <dependencies>
    <dependency>
      <groupId>org.pitest</groupId>
      <artifactId>pitest-junit5-plugin</artifactId>
      <version>1.2.3</version>
    </dependency>
  </dependencies>
  <configuration>
    <targetClasses><param>com.acme.orders.*</param></targetClasses>
  </configuration>
</plugin>
```

Run `./mvnw test-compile org.pitest:pitest-maven:mutationCoverage`; reports land in
`target/pit-reports`. Gradle: plugin `info.solidsoft.pitest` 1.19.0, task `pitest`. Run on changed
packages only; full-repo runs are slow.

## 6. Benchmarks with JMH 1.37

Maven: generate a separate benchmark module from the archetype, fix its compiler configuration,
then build the uber-jar:

```bash
mvn archetype:generate -DinteractiveMode=false \
  -DarchetypeGroupId=org.openjdk.jmh -DarchetypeArtifactId=jmh-java-benchmark-archetype \
  -DarchetypeVersion=1.37 -DgroupId=com.acme -DartifactId=benchmarks -Dversion=1.0
# edit benchmarks/pom.xml as shown below, then:
(cd benchmarks && mvn -B package && java -jar target/benchmarks.jar -f 2 -wi 5 -i 10 -prof gc)
```

The 1.37 archetype POM uses `maven-compiler-plugin` 3.8.0, `source`/`target` 1.8 and no processor
path, so it relies on implicit annotation processing, which JDK 23+ no longer does. The build
still succeeds, but the jar then fails with
`RuntimeException: ERROR: Unable to find the resource: /META-INF/BenchmarkList`. Replace the
generated compiler plugin with:

```xml
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-compiler-plugin</artifactId>
  <version>3.16.0</version>
  <configuration>
    <release>25</release>   <!-- the project's target release -->
    <annotationProcessorPaths>
      <path>
        <groupId>org.openjdk.jmh</groupId>
        <artifactId>jmh-generator-annprocess</artifactId>
        <version>${jmh.version}</version>
      </path>
    </annotationProcessorPaths>
    <!-- alternative: <compilerArgs><arg>-proc:full</arg></compilerArgs> -->
  </configuration>
</plugin>
```

Both variants were run on Temurin 25.0.5: before the edit the jar fails as above, after it prints
`ParseBench.parse  avgt ... ns/op`. JMH takes a lock at `${java.io.tmpdir}/jmh.lock`; on a shared
host where another user holds `/tmp/jmh.lock`, run with `java -Djava.io.tmpdir=<private dir> -jar ...`.

Gradle: plugin `me.champeau.jmh` 0.7.3, sources in `src/jmh/java`, run `./gradlew jmh`.

```java
@State(Scope.Benchmark)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
public class ParseBench {
  String input;
  @Setup public void setup() { input = "2026-10-29T10:15:30Z"; }
  @Benchmark public Instant parse() { return Instant.parse(input); }   // return the result: no dead-code elimination
}
```

## 7. Concurrency stress tests with jcstress 0.16

For lock-free or JMM-sensitive code (JV-CONC-10). Generate a separate module, apply the same
compiler fix as JMH (the 0.16 archetype also ships `maven-compiler-plugin` 3.8.0 with target 1.8;
without the fix the jar fails in `TestList.getTests` because the generated test list is missing):

```bash
mvn archetype:generate -DinteractiveMode=false \
  -DarchetypeGroupId=org.openjdk.jcstress -DarchetypeArtifactId=jcstress-java-test-archetype \
  -DarchetypeVersion=0.16 -DgroupId=com.acme -DartifactId=stress -Dversion=1.0
# in stress/pom.xml: maven-compiler-plugin 3.16.0, <release>25</release>,
#   <compilerArgs><arg>-proc:full</arg></compilerArgs>
(cd stress && mvn -B package && java -jar target/jcstress.jar -t CounterTest -m quick)
```

```java
@JCStressTest
@Outcome(id = {"1, 2", "2, 1"}, expect = Expect.ACCEPTABLE, desc = "each increment seen")
@Outcome(id = "1, 1", expect = Expect.FORBIDDEN, desc = "lost update")
@State
public class CounterTest {
  int v;                                   // the code under test; AtomicInteger makes it pass
  @Actor public void a1(II_Result r) { r.r1 = ++v; }
  @Actor public void a2(II_Result r) { r.r2 = ++v; }
}
```

Reading the result: each test prints a table of observed outcomes with `SAMPLES`, `FREQ` and
`EXPECT`. Any non-zero count in a `Forbidden` row marks the test `[FAILED]` and the run exits 1;
`Acceptable` rows are allowed results, and `Acceptable interesting` rows are allowed but worth a
comment. Run on 2026-10-29 (16 CPUs, `-m quick`, about 15 s): the plain `int` counter failed with
`1, 1  23,670  1.45%  Forbidden  lost update`; the `AtomicInteger` version exited 0. A pass only
means no forbidden outcome was observed on this hardware and JIT mode; use `-m default` or
`-m tough` before relying on it. The HTML report is written to `results/index.html`.

## 8. Optional static analysis (only if configured or requested)

| Tool | Maven coordinates (version) | Run |
|---|---|---|
| Checkstyle | `maven-checkstyle-plugin` 3.6.0 with a `com.puppycrawl.tools:checkstyle:14.3.0` plugin dependency | `./mvnw checkstyle:check` |
| PMD | `maven-pmd-plugin` 3.28.0 (PMD 7 engine; current PMD is 7.28.0) | `./mvnw pmd:check` |
| SpotBugs + FindSecBugs | `com.github.spotbugs:spotbugs-maven-plugin` 4.10.5.0 with plugin `com.h3xstream.findsecbugs:findsecbugs-plugin` 1.14.0 | `./mvnw spotbugs:check` |
| ArchUnit | `com.tngtech.archunit:archunit-junit5` 1.5.1 (test scope) | runs with the tests |

Error Prone overlaps with much of Checkstyle/PMD/SpotBugs; adding all of them to a project that has
none is rarely worth the noise. Start with `-Xlint:all`, a formatter, then Error Prone + NullAway.

## 9. Dependencies, updates, supply chain

```bash
./mvnw dependency:tree -Dincludes=com.fasterxml.jackson.core     # who brings it in
./mvnw dependency:analyze                                         # used-undeclared / unused-declared (review by hand)
./mvnw versions:display-dependency-updates -Dmaven.version.ignore='(?i).*(alpha|beta|rc|-m)[-.0-9]*'
./mvnw org.owasp:dependency-check-maven:13.0.0:check -DnvdApiKeyEnvironmentVariable=NVD_API_KEY
./mvnw org.cyclonedx:cyclonedx-maven-plugin:2.9.3:makeAggregateBom
osv-scanner scan source -r .
./mvnw -U org.openrewrite.maven:rewrite-maven-plugin:6.46.1:dryRun \
  -Drewrite.recipeArtifactCoordinates=org.openrewrite.recipe:rewrite-migrate-java:RELEASE \
  -Drewrite.activeRecipes=org.openrewrite.java.migrate.UpgradeToJava25
```

The OpenRewrite `dryRun` writes a patch under `target/rewrite/` for review instead of editing
files. The recipe `org.openrewrite.java.migrate.UpgradeToJava25` is defined in
`rewrite-migrate-java` (`META-INF/rewrite/java-version-25.yml`); that recipe module is under the
Moderne Source Available License, so check it is acceptable for your organisation. The NVD feed
needs an API key read from the environment; never put it on the command line or in the POM.

## 10. Packaging and distribution (JV-PKG)

Reproducible archives. Maven 3.10.0+ and Gradle 9+ already produce them; older Maven needs the
property (the Maven guide also suggests a fixed value updated by the release plugin):

```xml
<properties>
  <!-- Maven 3.10 super POM default: 1980-02-01T00:00:00Z -->
  <project.build.outputTimestamp>2026-10-29T00:00:00Z</project.build.outputTimestamp>
</properties>
```

```bash
./mvnw -B help:evaluate -Dexpression=project.build.outputTimestamp -q -DforceStdout   # what applies
./mvnw -B org.apache.maven.plugins:maven-artifact-plugin:3.7.0:check-buildplan       # plugins known to break reproducibility
./mvnw -B clean package && sha256sum target/*.jar   # run twice; the hashes must match
```

Run on 2026-10-29 with Maven 3.10.0: two clean builds gave the same jar hash both with and without
the property, because the super POM supplies it; `check-buildplan` printed "No known issue in 9
plugins".

Modular CLI to a trimmed runtime (jlink) and a native launcher (jpackage):

```bash
jdeps --print-module-deps --ignore-missing-deps target/app.jar   # modules a non-modular jar needs
jlink --module-path target/mods --add-modules com.acme.cli \
  --launcher cli=com.acme.cli/com.acme.cli.Main \
  --strip-debug --no-header-files --no-man-pages --output target/image
target/image/bin/cli
jpackage --type app-image --name acme-cli --module-path target/mods \
  --module com.acme.cli/com.acme.cli.Main --dest target/pkg   # deb/rpm/msi/dmg need the OS packager
```

Run on 2026-10-29: a module that `requires java.net.http` produced a 57 MB image (the full JDK is
303 MB) whose `java --list-modules` shows only `com.acme.cli`, `java.base` and `java.net.http`.
Temurin 25 ships without `jmods/` (JEP 493), so jlink links from the running JDK: build the image
on the target OS and architecture, and it cannot include `jdk.jlink` itself.

Container images without a Dockerfile:

```xml
<plugin>
  <groupId>com.google.cloud.tools</groupId>
  <artifactId>jib-maven-plugin</artifactId>
  <version>3.5.2</version>   <!-- Gradle: id("com.google.cloud.tools.jib") version "3.5.4" -->
  <configuration>
    <from><image>eclipse-temurin:25-jre</image></from>   <!-- pin by digest for releases -->
    <to><image>registry.example.com/acme/orders:${project.version}</image></to>
    <container><user>1000:1000</user></container>
  </configuration>
</plugin>
```

```bash
./mvnw -B package jib:buildTar      # image tarball, no Docker daemon needed
./mvnw -B package jib:build         # push to the registry in <to>
./mvnw -B spring-boot:build-image   # Spring Boot: Cloud Native Buildpacks, needs a Docker daemon
./gradlew bootBuildImage            # same for Gradle
java -Djarmode=tools -jar target/app.jar list-layers                                  # Boot layered jar
java -Djarmode=tools -jar target/app.jar extract --layers --destination extracted     # for a Dockerfile
```

`jib:buildTar` was run on 2026-10-29: it split the app into dependency, resource and class layers
on top of `eclipse-temurin:25-jre`, set user `1000:1000`, and stamped `created` as
`1970-01-01T00:00:00Z` (reproducible). `spring-boot:build-image` was not run (no Docker access on
the verification host); the command is from the Spring Boot plugin docs.

Publishing a library to Maven Central (Central Portal; OSSRH reached end of life on 2025-06-30):

```xml
<plugin>
  <groupId>org.sonatype.central</groupId>
  <artifactId>central-publishing-maven-plugin</artifactId>
  <version>0.12.0</version>
  <extensions>true</extensions>
  <configuration>
    <publishingServerId>central</publishingServerId>   <!-- <server> with a Portal user token in settings.xml -->
    <!-- <autoPublish>true</autoPublish> <waitUntil>published</waitUntil> once the flow is proven -->
  </configuration>
</plugin>
<!-- plus maven-source-plugin 3.4.0 (jar-no-fork), maven-javadoc-plugin 3.12.0 (jar),
     maven-gpg-plugin 3.2.8 (sign, phase verify) -->
```

Checklist before `./mvnw -B deploy`: the POM has `name`, `description`, `url`, `licenses`,
`developers` and `scm`; the build attaches `-sources.jar` and `-javadoc.jar`; every file gets a
`.asc` signature; the namespace is verified in the Portal; credentials and the GPG passphrase come
from `settings.xml` or the environment, never the POM. Dry run: add `<skipUpload>true</skipUpload>`
(0.12.0+) and inspect `target/central-publishing/central-bundle.zip`. Run on 2026-10-29 with a
throwaway GPG key: the bundle held the jar, sources, javadoc and POM, each with `.asc`, `.md5`,
`.sha1`, `.sha256` and `.sha512`. Sonatype publishes no official Gradle plugin; its Gradle page
points to JReleaser and community plugins.
