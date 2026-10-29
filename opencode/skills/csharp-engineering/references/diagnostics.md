# Diagnostics, async pitfalls, and performance measurement

Read when a task involves a hang, deadlock, slowdown, memory growth, flaky test, or a performance
claim. Tool versions as of 2026-10-29: dotnet-trace/-counters/-dump/-gcdump 10.0.750501,
BenchmarkDotNet 0.15.8. On SDK 10+ you can run any of them without installing via `dnx`
(for example `dnx dotnet-counters monitor --process-id 1234`).

## 1. Async and concurrency pitfalls (symptom, cause, fix)

The async guidance here is paraphrased from David Fowler's AspNetCoreDiagnosticScenarios notes
(no license on that repository, so nothing is copied) and cross-checked against the
dotnet/skills performance references (MIT).

| Symptom | Likely cause | Fix |
|---|---|---|
| Throughput collapses under load, thread count climbs, CPU low | Sync-over-async (`.Result`, `.Wait()`) or blocking I/O starving the thread pool | Make the call chain async; `dotnet-counters` shows `dotnet.thread_pool.queue.length` growing |
| Deadlock in UI or legacy ASP.NET | Blocking on a task that needs the captured synchronization context | Async all the way; `ConfigureAwait(false)` in library code |
| Process crashes with no catch | Exception escaped an `async void` method or an unobserved fire-and-forget task | Return `Task`; queue background work through `Channel<T>` + hosted service |
| Continuations run inline and stall the caller | `TaskCompletionSource` created without `RunContinuationsAsynchronously` | Pass `TaskCreationOptions.RunContinuationsAsynchronously` |
| Timer leaks, memory slowly grows | `CancellationTokenSource` with timeout never disposed; event handlers never removed | `using var cts = ...; cts.CancelAfter(...)`; unsubscribe or use weak patterns |
| Data written to a stream is truncated | Writer disposed without flushing, or flush forced synchronous during `Dispose` | `await writer.FlushAsync(ct)` before disposal; `await using` |
| `ObjectDisposedException` on `HttpContext` | Context captured in a background task after the request ended | Copy needed values first; resolve services from a new scope (`IServiceScopeFactory`) |
| Request work keeps running after the client disconnects | `CancellationToken` not forwarded | Add a `CancellationToken` handler parameter and pass it down (CA2016) |
| Value created twice / side effect duplicated | `ConcurrentDictionary.GetOrAdd` factory runs concurrently | Store `Lazy<T>` values, or use `AsyncLazy`-style caching (`HybridCache` for cache-aside) |
| `AsyncLocal` value leaks into unrelated work | Value set outside an async method or captured by a timer/thread-pool callback | Set it inside the async flow; suppress flow (`ExecutionContext.SuppressFlow()`) when starting long-lived timers |
| Corruption or exceptions from `ValueTask` | Awaited twice or after completion was consumed | Await once, or call `.AsTask()` once and reuse that |

## 2. Live process: counters, traces, dumps

```bash
dotnet-counters ps                                                   # find the PID
dotnet-counters monitor -p <pid> --counters System.Runtime,Microsoft.AspNetCore.Hosting
dotnet-counters collect -p <pid> --format csv -o counters.csv         # record for the report

# CPU / wall-clock trace (default profiles dotnet-common + dotnet-sampled-thread-time).
# The old `cpu-sampling` profile was removed in current dotnet-trace.
dotnet-trace collect -p <pid> --duration 00:00:00:30 --format Speedscope
# GC / allocation investigation
dotnet-trace collect -p <pid> --profile gc-verbose --duration 00:00:00:30
# Linux only, glibc >= 2.27: kernel + managed stacks via perf_events
dotnet-trace collect-linux -p <pid>

# Heap snapshot (lighter than a full dump), open in Visual Studio or PerfView
dotnet-gcdump collect -p <pid>

# Full dump + SOS analysis for hangs and deadlocks
dotnet-dump collect -p <pid>
dotnet-dump analyze <dump-file>
#   > clrstack -all        managed stacks of every thread
#   > dumpasync            async state machines and what they await
#   > syncblk              monitors held / waited on (lock deadlocks)
#   > threadpool           queue length, worker counts
#   > dumpheap -stat       types by count/size (memory growth)
#   > gcroot <address>     why an object is still alive
```

In containers, the tools need the same `/tmp` (diagnostic port) as the app; run them as a sidecar
sharing the volume, or use `dotnet-monitor`. A test-run hang is easier: use
`--blame-hang`/`--hangdump` (see `test-commands.md`) to get a dump automatically.

## 3. Microbenchmarks with BenchmarkDotNet

```csharp
// bench/App.Benchmarks/ParserBenchmarks.cs  (console project, OutputType Exe, Release only)
using BenchmarkDotNet.Attributes;
using BenchmarkDotNet.Running;

[MemoryDiagnoser]
public class ParserBenchmarks
{
    private string _input = "";

    [GlobalSetup]
    public void Setup() => _input = File.ReadAllText("sample.txt");

    [Benchmark(Baseline = true)]
    public int Current() => LegacyParser.Count(_input);

    [Benchmark]
    public int Candidate() => SpanParser.Count(_input);
}

public static class Program
{
    public static void Main(string[] args) =>
        BenchmarkSwitcher.FromAssembly(typeof(Program).Assembly).Run(args);
}
```

```bash
dotnet run -c Release --project bench/App.Benchmarks -- --filter '*ParserBenchmarks*'
dotnet run -c Release --project bench/App.Benchmarks -- --filter '*' --memory --join
```

Rules: Release build, no debugger, return results so the JIT cannot eliminate the work, keep setup
out of the measured method, compare against a `Baseline = true` method, and report Mean, Error,
Allocated, and Ratio. Changes within the Error interval are noise.

## 4. Build problems

```bash
dotnet build -bl:artifacts/build.binlog       # binary log of the full build
dotnet build -v:diag > artifacts/build.log     # text fallback, very large
```

Open the binlog with MSBuild Structured Log Viewer, or (if installed) the dotnet/skills
`dotnet-msbuild` plugin's binlog MCP server. Look for: which `Directory.Build.props` set a property,
which package version CPM resolved, why a target was skipped, and double-writes in `bin/obj`.

## 5. EF Core query diagnosis

```csharp
// Development/test only: see the SQL and parameters EF generates
optionsBuilder
    .LogTo(Console.WriteLine, [DbLoggerCategory.Database.Command.Name], LogLevel.Information)
    .EnableSensitiveDataLogging(); // never in production: logs parameter values
```

- `query.ToQueryString()` shows the SQL for one LINQ query without executing it.
- Many near-identical SELECTs in the log for one request means N+1; fix with `Include` or
  projection.
- "Cartesian explosion" warning or huge row counts with several `Include` collections: add
  `AsSplitQuery()`.
- Client evaluation errors mean the expression cannot be translated; rewrite it, do not call
  `AsEnumerable()` early on a large set.
- Slow but correct SQL: get the plan from the database (`EXPLAIN ANALYZE` on PostgreSQL, actual
  execution plan on SQL Server) and add or adjust indexes in a migration.
