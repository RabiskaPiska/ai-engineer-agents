# Measured: Sequence vs List, boxed vs primitive arrays (JMH, JDK 25)

Run on 2026-10-29 to test the speed claims in the agent's Performance rules instead of repeating
folklore. The result changed one rule: the common claim "Sequence is slower than List on small
collections" did not hold for these pipelines.

## Setup

- Kotlin 2.4.21, kotlinx-benchmark 0.5.0 (JMH 1.37 default), Gradle 9.8.2.
- JDK: Eclipse Temurin 25.0.5+8 (`25.0.5+8-LTS`), SHA-256 checked against the Adoptium API.
- Host: shared VPS, AMD EPYC 9454, 16 vCPU, load average 5–10 from other work during the run.
  That noise is why the error bars are wide on some rows. Compare only results whose 99.9%
  intervals do not overlap.
- JMH: `avgt`, ns/op, 9 forks x (5 warmup + 5 measurement iterations of 1 s) = 45 samples per row.
  "Error" is JMH's 99.9% confidence half-width.

```kotlin
// build.gradle.kts (relevant part)
benchmark {
    targets { register("main") }
    configurations {
        named("main") {
            warmups = 5; iterations = 5; iterationTime = 1; iterationTimeUnit = "s"
            mode = "avgt"; outputTimeUnit = "ns"; advanced("jvmForks", 9)
        }
    }
}
```

```kotlin
@State(Scope.Benchmark)
class SequenceVsList {                       // terminal op: sum()
    @Param("3", "10", "100", "10000") var size: Int = 0
    private lateinit var data: List<Int>
    @Setup fun setup() { data = List(size) { it } }
    @Benchmark fun list(): Int = data.map { it * 3 }.filter { it % 2 == 0 }.sum()
    @Benchmark fun sequence(): Int = data.asSequence().map { it * 3 }.filter { it % 2 == 0 }.sum()
}

@State(Scope.Benchmark)
class SeqToList {                            // terminal op: a List result
    @Param("3", "10000") var size: Int = 0
    private lateinit var data: List<Int>
    @Setup fun setup() { data = List(size) { it } }
    @Benchmark fun list(): List<Int> = data.map { it * 3 }.filter { it % 2 == 0 }
    @Benchmark fun sequence(): List<Int> = data.asSequence().map { it * 3 }.filter { it % 2 == 0 }.toList()
}

@State(Scope.Benchmark)
class BoxedVsPrimitive {
    @Param("10000") var size: Int = 0
    private lateinit var boxed: Array<Int>
    private lateinit var primitive: IntArray
    @Setup fun setup() { boxed = Array(size) { it }; primitive = IntArray(size) { it } }
    @Benchmark fun boxedSum(): Long { var s = 0L; for (x in boxed) s += x; return s }
    @Benchmark fun primitiveSum(): Long { var s = 0L; for (x in primitive) s += x; return s }
}
```

## Results (JMH summary, pasted)

```text
Benchmark                      (size)  Mode  Cnt       Score       Error  Units
BoxedVsPrimitive.boxedSum       10000  avgt   45    4368.482 ±   397.712  ns/op
BoxedVsPrimitive.primitiveSum   10000  avgt   45     794.173 ±    49.918  ns/op
SequenceVsList.list                 3  avgt   45      56.566 ±     4.696  ns/op
SequenceVsList.list                10  avgt   45     144.194 ±    19.491  ns/op
SequenceVsList.list               100  avgt   45    1517.864 ±   430.631  ns/op
SequenceVsList.list             10000  avgt   45  149496.001 ± 17197.091  ns/op
SequenceVsList.sequence             3  avgt   45      11.801 ±     0.659  ns/op
SequenceVsList.sequence            10  avgt   45      37.759 ±     3.930  ns/op
SequenceVsList.sequence           100  avgt   45     449.799 ±    73.376  ns/op
SequenceVsList.sequence         10000  avgt   45   73520.615 ± 11161.283  ns/op

Benchmark           (size)  Mode  Cnt       Score        Error  Units
SeqToList.list           3  avgt   45      50.323 ±      3.637  ns/op
SeqToList.list       10000  avgt   45  266759.925 ± 373878.877  ns/op
SeqToList.sequence       3  avgt   45      40.588 ±     13.834  ns/op
SeqToList.sequence   10000  avgt   45   90506.133 ±   5939.533  ns/op
```

Medians from the raw samples (less sensitive to the noisy host): `SeqToList.list` size 10000
121,716 ns vs `sequence` 90,196 ns; size 3: 48.2 ns vs 33.1 ns.

## What the numbers support

| Claim | Verdict on this run |
|---|---|
| `Sequence` is slower than eager `List` operations on small collections | **Not supported.** With a `sum()` terminal, `Sequence` was faster at every size (3 elements: 11.8 ± 0.7 vs 56.6 ± 4.7 ns; the intervals do not overlap). With a `toList()` terminal at 3 elements, the intervals overlap (40.6 ± 13.8 vs 50.3 ± 3.6 ns): no measurable difference. The eager chain allocates one intermediate `ArrayList` per step, the likely reason (not profiled). |
| `Sequence` helps on long multi-step pipelines | Supported for `sum()` at 10,000 (73.5k ± 11.2k vs 149.5k ± 17.2k ns). For `toList()` at 10,000, the `list` row has a very wide interval (one outlier sample of 4.59 ms, probably GC or host noise), so only the medians favour `Sequence`. Treat it as indicative, not proven. |
| Primitive arrays avoid boxing cost | Supported: summing `IntArray` was 794 ± 50 ns vs 4,368 ± 398 ns for `Array<Int>` (about 5.5x). |
| `inline` higher-order functions are faster on hot paths | **Not measured** in this run. |

Limits: one JDK, one noisy machine, `Int` elements, two- and three-step pipelines. Other element
types, other operators (`sorted`, `distinct`, `flatMap`) or a JIT that inlines differently can
change the result. Rules built on this file say "choose by semantics, measure when it matters";
they do not claim a general winner.

Re-run: `./gradlew benchmark` (and `./gradlew tolistBenchmark` for a second profile that
`include("SeqToList")`); raw JSON lands in `build/reports/benchmarks/<profile>/<timestamp>/`.
