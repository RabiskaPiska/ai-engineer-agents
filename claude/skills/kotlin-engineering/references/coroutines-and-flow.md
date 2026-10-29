# Coroutines and Flow (kotlinx.coroutines 1.11.0)

Grounded in the kotlinx.coroutines guide (`docs/topics/` in Kotlin/kotlinx.coroutines: cancellation,
exception handling, shared mutable state) and the `kotlinx-coroutines-test` README, read on
2026-10-29, plus ownership/event patterns adapted from chrisbanes/skills (Apache-2.0).

## 1. Ownership

Every coroutine needs an owner whose lifecycle ends it. Decide the owner before writing `launch`.

| Situation | Owner |
|---|---|
| Work whose result the caller needs | the caller: make it a `suspend fun`, use `coroutineScope { }` inside |
| Parallel children, all-or-nothing | `coroutineScope { val a = async { }; val b = async { }; a.await() to b.await() }` |
| Parallel children that fail independently | `supervisorScope { }` and handle each child's failure |
| Android screen state | `viewModelScope` |
| App-lifetime background work (server) | an injected `CoroutineScope(SupervisorJob() + dispatcher)` created at startup and cancelled at shutdown |
| Ktor request | the call's coroutine (handlers are already `suspend`) |

Rules:
- No `GlobalScope`. No stored `CoroutineScope` without a `cancel()` on the owner's teardown.
- A non-suspending function that calls `launch` hides work from its caller. Only do it when the
  function's owner is explicit (e.g. a ViewModel action), and keep the `Job` if it must be
  cancelled or replaced: cancel the previous job before relaunching.
- If an existing `suspend` API already gives the caller result, failure and cancellation, leave it
  suspend; do not wrap it in `launch` plus a callback.

## 2. Dispatchers

```kotlin
class ReportRepository(
    private val api: ReportApi,
    private val io: CoroutineDispatcher = Dispatchers.IO,
) {
    suspend fun load(id: ReportId): Report = withContext(io) { api.fetch(id) }   // main-safe
}
```

- Inject dispatchers; tests pass `StandardTestDispatcher(testScheduler)`.
- `Dispatchers.Default` for CPU work, `Dispatchers.IO` for blocking IO,
  `Dispatchers.IO.limitedParallelism(n)` to cap a blocking resource (e.g. a JDBC pool of n).
- `runBlocking` only at entry points. Never inside a coroutine, request handler, Android main
  thread, or test (use `runTest`).
- Blocking calls that support interruption: `runInterruptible(io) { blockingCall() }` so
  cancellation interrupts the thread.

## 3. Cancellation

Cancellation is cooperative: a coroutine stops at the next suspension point or explicit check,
by throwing `CancellationException`.

- CPU loops: call `ensureActive()` (throws if cancelled) or `yield()` (also lets others run).
- Catching `CancellationException` breaks propagation unless you rethrow it. `runCatching` and
  `catch (e: Exception)` both catch it; in coroutine code use specific exception types or rethrow:
  ```kotlin
  catch (e: CancellationException) { throw e }
  catch (e: IOException) { ... }
  ```
- Suspending cleanup in `finally` needs `withContext(NonCancellable) { ... }`; without it the
  first suspension in `finally` throws immediately. Use `NonCancellable` only with `withContext`,
  never with `launch`/`async` (that breaks the parent-child relation).
- Timeouts: `withTimeout` throws `TimeoutCancellationException`; `withTimeoutOrNull` returns null.
  Resources acquired inside a timeout block must be released in `finally`.
- A value already produced is lost if the consumer is cancelled while resuming; transfer ownership
  of closeable resources with care (close in `finally` on the producer side or use `onUndeliveredElement`
  for channels).

## 4. Exceptions

- An uncaught exception in a child cancels its parent and siblings (except under `SupervisorJob`/
  `supervisorScope`).
- `launch` propagates uncaught exceptions to the parent/handler; `async` stores them until
  `await()`. A root `async` whose result is never awaited loses its exception.
- `CoroutineExceptionHandler` runs only for uncaught exceptions in root coroutines (or direct
  children of a supervisor). It cannot recover the coroutine; use it for last-resort logging.
- Multiple failures aggregate: the first exception wins, later ones are attached as suppressed.
- Stack-trace recovery (JVM, debug mode) copies exceptions to add coroutine frames. Exceptions with
  extra required constructor args can implement `kotlin.coroutines.debug.StackTraceRecoverable`
  (Kotlin 2.4.20, `@OptIn(ExperimentalStdlibCoroutineSupportApi::class)`).

## 5. Shared mutable state

In order of preference:
1. Don't share: confine state to one coroutine/actor-like loop reading a `Channel`.
2. `MutableStateFlow.update { it.copy(...) }` for state objects (atomic CAS loop).
3. Atomics (`AtomicInteger`, `AtomicReference`, or atomicfu 0.33.0 in multiplatform code) for counters.
4. `Mutex.withLock { }` for suspending critical sections (does not block a thread).
5. Thread confinement with `limitedParallelism(1)` for coarse-grained confinement.

Never hold a `synchronized` lock or `ReentrantLock` across a suspension point.
Concurrent data structures on the JVM get a Lincheck test (model checking + stress).

## 6. Flow: state vs events

| Need | Primitive | Why |
|---|---|---|
| Current renderable state | `StateFlow<UiState>` | conflated; new collectors get the latest value |
| Event to exactly one consumer, must survive a collector gap | `Channel<Event>(Channel.BUFFERED)` exposed as `receiveAsFlow()` | buffered; each element delivered once |
| Broadcast to all active collectors | `MutableSharedFlow(extraBufferCapacity = n)` | events emitted while nobody collects are dropped |
| Share an expensive cold flow | `stateIn(scope, SharingStarted.WhileSubscribed(5_000), initial)` | stops upstream 5 s after the last collector, survives configuration changes |

- Conflation means intermediate values can be skipped: never use `StateFlow` to count or log every
  change, and order writes so the last write is the correct state.
- Expose read-only types (`StateFlow`, `Flow`); on Kotlin 2.4 use explicit backing fields.
- `flatMapLatest` to restart work when a key changes; `distinctUntilChanged` (or
  `distinctUntilChangedBy { it.id }`) before expensive side effects.
- `combine` several condition flows into one gate; make start and stop idempotent.
- `catch { }` only upstream errors; put it before `stateIn`/`collect`. `retryWhen` with backoff for
  transient IO errors.
- `flowOn(io)` changes the upstream context only; never `withContext` inside `flow { }` emission.
- Concurrency over many items: `flatMapMerge(concurrency = n)` or a `Semaphore`, not unbounded
  `async` per element.

## 7. Testing coroutine code

```kotlin
class ReportViewModelTest {
    @Test
    fun `emits loaded state`() = runTest {
        val dispatcher = StandardTestDispatcher(testScheduler)
        val vm = ReportViewModel(FakeRepo(), io = dispatcher)

        vm.state.test {                                   // Turbine
            assertEquals(UiState.Loading, awaitItem())
            advanceUntilIdle()
            assertEquals(UiState.Loaded(sample), awaitItem())
            cancelAndIgnoreRemainingEvents()
        }
    }
}
```

- `runTest` skips `delay`, times out after 60 s by default (`runTest(timeout = 30.seconds)` to
  change), and rethrows uncaught child exceptions at the end.
- On Kotlin/JS the `runTest` result must be returned from the test function (expression body).
- `StandardTestDispatcher` queues work until you advance (`runCurrent`, `advanceTimeBy`,
  `advanceUntilIdle`); `UnconfinedTestDispatcher` runs eagerly, useful for collectors started
  in `backgroundScope`.
- Start never-ending collectors in `backgroundScope` so the test can finish.
- Android/Compose: `Dispatchers.setMain(StandardTestDispatcher())` in setup,
  `Dispatchers.resetMain()` in teardown. `kotlinx-coroutines-test` belongs in test configurations
  only.
- Delays inside `withContext(Dispatchers.Default)` are real time, not virtual; inject the
  dispatcher to keep tests fast.
