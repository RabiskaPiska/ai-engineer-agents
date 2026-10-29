# JVM diagnostics playbook

Symptom-first diagnosis with JDK tools. The tier model and several commands are adapted from
`github/awesome-copilot` `skills/java-diagnostics` (MIT, see `sources/java.md`). Prefer the official
tool docs for the JDK in use: `https://docs.oracle.com/en/java/javase/25/docs/specs/man/jcmd.html`
and `.../jfr.html`.

## Safety tiers

| Tier | Tools | Rule |
|---|---|---|
| 1 Read-only | `jcmd <pid> VM.version`, `VM.flags`, `Thread.print`, `jstat -gcutil <pid> 1s 10`, logs | Run after stating the command. |
| 2 Recording | JFR, async-profiler, NMT, class histograms (`GC.class_histogram` pauses at a safepoint) | Needs consent; state duration and overhead first. |
| 3 Intrusive | Heap dumps, `VM.system_properties`, `VM.command_line`, `jinfo`, anything on production | Needs explicit consent, a target path, a disk-space check. Heap dumps and property listings contain secrets: analyze locally, never upload, delete afterwards. |

Never run Tier 2 or 3 against production unless the user explicitly asks. Attach as the same OS
user as the target JVM. Reproduce on dev or staging when you can.

## Symptom table

| Symptom | First step | Then |
|---|---|---|
| High CPU | 3 thread dumps 5 s apart (`jcmd <pid> Thread.print`) plus `top -H -p <pid>`; map the hot native thread id (hex) to `nid=` | JFR `settings=profile` or `asprof -e cpu` flame graph |
| Memory growth / OOM | `jstat -gcutil`, then `GC.class_histogram` twice minutes apart | Heap dump + Eclipse MAT, or JFR with `path-to-gc-roots=true` |
| RSS grows, heap does not | Start with `-XX:NativeMemoryTracking=summary`, then `jcmd <pid> VM.native_memory baseline` and `summary.diff` | `asprof -e nativemem` (async-profiler 4.0+) |
| Deadlock / stuck threads | `jcmd <pid> Thread.print` (reports Java-level deadlocks) | For virtual threads: `jcmd <pid> Thread.dump_to_file -format=json /tmp/threads.json` |
| GC pauses | `-Xlog:gc*:file=gc.log:time,uptime,level,tags` | JFR `jdk.GarbageCollection`, `jdk.GCPhasePause`; revisit heap size and collector |
| Slow requests | Tracing and metrics first (Micrometer/OpenTelemetry), then logs | JFR socket/file/lock events; `asprof -e wall -t` |
| Virtual-thread stalls | JFR `jdk.VirtualThreadPinned` (JDK 21+) | Remove `synchronized` around blocking calls on 21-23; upgrade to 24+ |
| Slow startup | `-Xlog:class+load`, framework startup report | JFR from start; AOT cache (`-XX:AOTCacheOutput`) on 25+ |

## JFR

```bash
# at startup
java -XX:StartFlightRecording=filename=/secure/rec.jfr,duration=120s,settings=profile -jar app.jar
# on a running JVM
jcmd <pid> JFR.start name=diag duration=120s settings=profile filename=/secure/rec.jfr
jcmd <pid> JFR.dump name=diag filename=/secure/rec.jfr
jcmd <pid> JFR.stop name=diag
# analysis
jfr summary /secure/rec.jfr
jfr print --events jdk.ExecutionSample /secure/rec.jfr | head -50
jfr print --events jdk.VirtualThreadPinned,jdk.JavaMonitorEnter /secure/rec.jfr
jfr print --events jdk.ObjectAllocationSample /secure/rec.jfr | head -50
```

- `settings=default` is the low-overhead profile for always-on recording (`maxage=30m maxsize=250m`);
  `settings=profile` collects more for a bounded window.
- JDK 25 added JFR CPU-time profiling (experimental, JEP 509), cooperative sampling (518) and method
  timing and tracing (520); JDK 27 added in-process data redaction (536). Check `jfr` help on the
  running JDK before relying on them.
- Open recordings in JDK Mission Control for the automated analysis page.

## async-profiler (4.6, 2026-10-19)

Download a pinned release from `https://github.com/async-profiler/async-profiler/releases` and
verify its checksum; do not pipe install scripts into a shell.

```bash
asprof -d 30 -e cpu   -f /secure/cpu.html   <pid>   # CPU flame graph
asprof -d 30 -e wall -t -f /secure/wall.html <pid>  # latency, per thread
asprof -d 30 -e alloc -f /secure/alloc.html <pid>   # allocation
asprof -d 30 -e lock  -f /secure/lock.html  <pid>   # contention
```

If `-e cpu` fails because of `perf_event_paranoid` or container seccomp, use `-e ctimer` or
`-e itimer` rather than relaxing host security; changing sysctls or adding `SYS_ADMIN` is a host
decision for the user. Version 4.6 removed the embedded HTTP server and changed the `filter`
option; read the release notes of the version you run.

## Heap and GC

```bash
jstat -gcutil <pid> 1s 10                          # occupancy and GC counts
jcmd <pid> GC.class_histogram -all=true | head -30 # Tier 2: safepoint pause
jcmd <pid> GC.heap_dump /secure/heap.hprof         # Tier 3: pause + secrets in file
```

Compare two histograms taken minutes apart; a class whose instance count only grows is the leak
candidate. In MAT, use the dominator tree and "path to GC roots excluding weak references".

## Containers

- The JVM reads cgroup limits; size with `-XX:MaxRAMPercentage` and `-XX:InitialRAMPercentage`.
- `jcmd` inside the container needs the same user and a shared `/tmp`; with distroless images use
  an ephemeral debug container that shares the process namespace.
- Leave non-heap headroom: metaspace, code cache, thread stacks (virtual threads use heap for their
  stacks), direct buffers, and native libraries.
