---
name: rust-engineering
description: "Rule catalog and gate commands for production Rust (Rust 1.99.1, edition 2024, October 2026). Use whenever writing, reviewing, refactoring, debugging, profiling or testing Rust: .rs files, Cargo.toml, build.rs, rust-toolchain.toml, clippy.toml, deny.toml, tokio/axum/sqlx/serde services, CLIs, libraries, unsafe or FFI code. Covers project layout, lint config, errors, ownership, async, unsafe, performance, supply-chain security, observability and the exact verification commands."
---

# Rust engineering (October 2026)

The reference behind the `rust-engineer` agent. Rules are grouped by area and given an ID so reviews
can cite them (`R-ERR-3`). Each rule says what to do and, where it is not obvious, why. Ready-to-copy
configuration and a compile-tested service skeleton live in `references/`:

- `references/project-templates.md`: workspace `Cargo.toml` with `[workspace.lints]`, release and
  profiling profiles, `rust-toolchain.toml`, `clippy.toml`, `rustfmt.toml`, `deny.toml`, and a
  GitHub Actions CI workflow.
- `references/service-skeleton.md`: an axum 0.8 + tokio 1.54 service with typed domain errors,
  body limits, timeouts, panic isolation, structured logging and graceful shutdown, verified with
  clippy pedantic, tests and a live run on Rust 1.99.1.

## 0. Baseline facts to rely on

- Stable is **1.99.1** (2026-10-15); 1.100.0 is scheduled for 2026-11-12. Latest edition is
  **2024**. rustup is **1.29.2**. Install the pinned toolchain from `rust-toolchain.toml` with
  `rustup toolchain install` (no arguments).
- The edition-2024 resolver is MSRV-aware: `cargo generate-lockfile` prints
  `Locking N packages to highest Rust <rust-version> compatible versions`. Keep `rust-version`
  honest and the resolver picks dependency versions that build on it.
- Recent std additions worth using within your MSRV: `LazyLock` (1.80), `#[expect]` lint reasons
  (1.81), async closures and `AsyncFn*` bounds (1.85), `if let` chains (1.88), `array_windows`
  (1.94), `cfg_select!` and `if let` match guards (1.95), `assert_matches!` (1.96, import it),
  `format_into` + `NumBuffer` (1.98), `Vec::into_parts`/`from_parts` and `Box::into_non_null`
  (1.99).

## 1. Project and packaging (R-PRJ)

1. New crates: `edition = "2024"`, explicit `rust-version`, `license`, and `publish = false` for
   private crates so nothing reaches crates.io by accident.
2. Workspaces: members under `crates/`, flat. Root defines `[workspace.package]`,
   `[workspace.dependencies]`, `[workspace.lints]`; members use `x.workspace = true`. Internal
   crates are workspace dependencies by path.
3. `Cargo.lock` is committed for binaries; CI uses `--locked`. `cargo new` tracks it for libraries
   too (Cargo FAQ); if a library commits it, add a CI job that runs `cargo update` first so the
   latest compatible versions are also tested.
4. Version requirements: caret (`"1.54"`). No `*`, no `=` pins except for proc-macro companion
   crates that must match exactly.
5. Features: additive, named for what they enable, never `no-std`/`use-x`. Test the feature
   matrix with `cargo hack check --feature-powerset --no-dev-deps`.
6. `main.rs` is wiring only; logic lives in a library crate so it can be unit- and
   integration-tested.
7. `build.rs` only when unavoidable; it must be deterministic, emit `cargo::rerun-if-changed`,
   and never touch the network. Build scripts and proc macros run on developer machines and CI with
   full privileges.
8. Pin applications to an exact toolchain in `rust-toolchain.toml`; upgrade deliberately (read the
   release post, run all gates) rather than on whatever CI image is current.
9. Edition-2024 members can now (Cargo 1.99) override an inherited dependency's
   `default-features = false`; earlier editions ignore it with a warning.

## 2. Lints and formatting (R-LINT)

1. Configure lints once in `[workspace.lints]` (template in `references/project-templates.md`):
   `clippy::all` and `clippy::pedantic` at `warn` with `priority = -1`, plus selected restriction
   lints (`unwrap_used`, `allow_attributes_without_reason`, `undocumented_unsafe_blocks`,
   `print_stdout`, `dbg_macro`, `as_conversions`).
2. CI denies warnings: `cargo clippy ... -- -D warnings`, or on 1.97+ `CARGO_BUILD_WARNINGS=deny`
   which keeps the build cache valid. Never `#![deny(warnings)]` in source.
3. Suppress with `#[expect(clippy::lint_name, reason = "...")]` on the narrowest item. `expect`
   warns once the lint stops firing, so stale suppressions surface. Use lint names with
   underscores; Cargo 1.99 warns on hyphenated names in `[lints]`.
4. Libraries add `missing_docs`, `missing_errors_doc`, `missing_panics_doc`,
   `unreachable_pub`; applications may drop them.
5. `unsafe_code = "forbid"` in crates that need no unsafe; crates that do need it use
   `deny` at the crate level and `#[expect(unsafe_code, reason)]`/module-level allow in the one
   module that owns the unsafe.
6. rustfmt owns formatting: `cargo fmt --all`, `style_edition = "2024"` in `rustfmt.toml`. Do not
   hand-format or argue style in review.
7. Since 1.97 linker output appears as the `linker_messages` warning. Investigate it before
   allowing it in `[lints.rust]`.

## 3. Types and API design (R-API)

1. Encode invariants in types: enums for states, newtypes for IDs/units/validated strings, fallible
   constructors (`TryFrom`, `FromStr`, `try_new`). Validate once at the boundary, then pass the
   validated type everywhere.
2. Parameters: `&str`, `&[T]`, `impl AsRef<Path>`, `impl IntoIterator<Item = T>`; owned `T` only
   when stored or consumed. No `&String`/`&Vec<T>`/`&Box<T>`/`&Option<T>` (use `Option<&T>`).
3. No `bool` parameters in shared signatures (clippy `fn_params_excessive_bools` with
   `max-fn-params-bools = 0`).
4. Derive `Debug` on every public type, plus `Clone`, `PartialEq`/`Eq`, `Hash`, `Default`,
   `PartialOrd`/`Ord` where semantics fit; `Copy` only for small plain data. If `Ord` is
   hand-written, hand-write `PartialEq`, `PartialOrd` and `Hash` to agree with it.
5. `Display` for anything shown to people; `Debug` for diagnostics. Never swap them.
6. Implement `From`/`TryFrom`, `FromStr`, `FromIterator`/`Extend`, `IntoIterator` for owned and
   borrowed forms. No `Into` impls.
7. Naming: no `get_` prefix on getters; `as_` (free borrow), `to_` (costly), `into_` (consumes);
   `new`/`with_*`/`try_new`/`builder()`. Avoid `Manager`, `Service`, `Helper`, `Util` in type
   names.
8. Builders for more than two optional parameters; setters infallible, `build()` returns
   `Result` and does all validation.
9. Private by default; `pub(crate)` before `pub`. `#[non_exhaustive]` on public enums and
   public-field structs you may extend. Seal traits that downstream must not implement.
10. Keep third-party and smart-pointer types out of public signatures; services are cheap-`Clone`
    wrappers around `Arc<Inner>`.
11. `#[must_use]` on pure functions returning values and on types whose drop is a bug (guards,
    futures, builders).
12. Assert `Send`/`Sync` of public types at compile time:
    `const _: () = { const fn f<T: Send + Sync>() {} f::<MyType>(); };`
13. Libraries: run `cargo semver-checks` before every release; adding a variant to an exhaustive
    enum, a field to a constructible struct, or a trait bound is breaking.

## 4. Errors and panics (R-ERR)

1. Library errors: enum (or struct + private kind) with `#[derive(Debug, thiserror::Error)]`,
   `Send + Sync + 'static`, `#[source]`/`#[from]` for causes, lowercase messages without trailing
   punctuation. No `String`, `Box<dyn Error>` or `anyhow::Error` in a library's public API.
2. Do not build one crate-wide error enum listing every failure; scope errors to operations so
   callers match only what can happen.
3. Applications: one error type (`anyhow::Result`, or `eyre`/`color-eyre` for richer reports) with
   `.context()`/`.with_context(|| ...)` at every I/O or boundary call. Add the identifying value
   (path, id, URL) to the context.
4. Map domain errors to transport responses at the edge (axum `IntoResponse` for an `ApiError`
   wrapper) so domain crates stay HTTP-free. Never leak internal error text for 5xx responses;
   log it with the request id instead.
5. Panics are for bugs. Never panic on external input. `expect("invariant: ...")` over `unwrap()`
   in shipping code; tests may `unwrap()`.
6. `let ... else` and `if let` chains instead of check-then-unwrap.
7. Lock poisoning means another thread panicked mid-update: `.lock().expect("... poisoned")` is
   the usual policy, unless the data is rebuilt.
8. Destructors never fail or block; offer `fn close(self) -> Result<()>` for fallible teardown.
9. Docs: `# Errors`, `# Panics`, `# Safety` sections on public items where they apply.

## 5. Ownership, borrowing and memory (R-OWN)

1. Prefer unique ownership; shared (`Rc`/`Arc`) and interior mutability (`RefCell`/`Mutex`) only
   by design.
2. Borrow-checker conflicts: shorten borrows with blocks, bind temporaries, `mem::take`/`replace`,
   split structs for disjoint borrows, use indices into an owning `Vec`. Clone only small
   immutable data, deliberately.
3. Structs own their data (`String`, `Vec<u8>`) unless profiling shows a lifetime-carrying view is
   worth the API cost. Name lifetimes on types descriptively (`'src`).
4. `Cow<'_, str>` when a function usually borrows but sometimes must allocate.
5. Pre-size collections; reuse buffers in loops (`clear()` + refill); `Box<str>`/`Arc<str>`/
   `Box<[T]>` for long-lived immutable data; `shrink_to_fit` after building long-lived collections.
6. Box large enum variants (clippy `large_enum_variant`) and large futures (`large_futures`).
7. Do not round-trip `Box::leak` back into a `Box` (1.99 docs advise against it); use
   `Box::into_raw`/`into_non_null` when you need to give ownership away and take it back.
8. `let _guard = lock_or_span();` keeps a guard alive; `let _ = ...` drops it at once.

## 6. Async and concurrency (R-ASYNC)

1. tokio is the default runtime (1.54.1; MSRV 1.85; LTS 1.51.x to 2027-03 and 1.53.x to
   2027-09). Do not add `async-std` (deprecated in favour of `smol`).
2. `#[tokio::main]` multi-thread for services; `current_thread` for CLIs that only need light I/O.
   Libraries never create a runtime or spawn behind the caller's back; they take an executor or
   return futures.
3. No `std::sync::MutexGuard`, `RefCell` borrow or `Rc` held across `.await`. Keep critical
   sections synchronous and short; `tokio::sync::Mutex` only when the guard must span an await.
4. Blocking calls (`std::fs`, blocking HTTP, compression, password hashing, heavy CPU) go to
   `tokio::task::spawn_blocking` or a dedicated rayon pool.
5. Bounded `mpsc` channels; `oneshot` for replies; `watch` for latest value; `broadcast` for
   fan-out. Size bounds from expected burst, not "big enough".
6. Structured concurrency: `JoinSet` for dynamic groups, `tokio_util::task::TaskTracker` +
   `CancellationToken` for background work that must drain on shutdown. No detached
   `tokio::spawn` without an owner.
7. Timeouts on every outbound call (`tokio::time::timeout`, client-level timeouts) and on every
   inbound request (`tower_http::timeout::TimeoutLayer::with_status_code`).
8. `tokio::select!` in a loop: only cancellation-safe futures in branches (`mpsc::Receiver::recv`
   is; `AsyncReadExt::read_exact`, `write_all` and `tokio::sync::Mutex::lock` are not); pin long-lived futures outside the loop with
   `tokio::pin!`/`std::pin::pin!`.
9. Native `async fn` in traits for static dispatch; `async-trait` (0.1.92) only for `dyn Trait`.
   Prefer `F: AsyncFn(...)` bounds over `F: Fn() -> Fut, Fut: Future`.
10. Data parallelism: rayon `par_iter` or `std::thread::scope`; never block a tokio worker on
    rayon without `spawn_blocking` or a oneshot handoff.
11. Atomics: use the weakest correct `Ordering` and document why; custom lock-free code must pass
    loom.
12. Graceful shutdown: listen for SIGINT/SIGTERM, stop accepting
    (`axum::serve(...).with_graceful_shutdown(fut)`), cancel the token, `tracker.close()`, then
    `tracker.wait().await` with an outer deadline.

## 7. Unsafe and FFI (R-UNSAFE)

1. Justify every `unsafe`: FFI, a novel abstraction, or a benchmarked hot path. Look for a std or
   well-audited crate first.
2. `// SAFETY:` before every `unsafe` block, `# Safety` on every `unsafe fn`, one unsafe operation
   per block (`multiple_unsafe_ops_per_block`), `unsafe_op_in_unsafe_fn` on (default in 2024).
3. The module is the soundness boundary: private fields + safe API. Assume user `Clone`, `Drop`,
   `Deref`, `Hash` and closures misbehave or panic.
4. Edition 2024 syntax: `unsafe extern "C" { safe fn ...; unsafe fn ...; }`,
   `#[unsafe(no_mangle)]`, `#[unsafe(export_name = "...")]`; `&raw const`/`&raw mut` instead of
   references to `static mut`.
5. `MaybeUninit<T>` for uninitialised memory; never `mem::zeroed()` for types with validity
   invariants.
6. FFI: `#[repr(C)]` types, `CStr`/`CString`, explicit ownership of every pointer, RAII wrapper
   that frees in `Drop`, null checks returning `Result`, `catch_unwind` at `extern "C"` entry
   points (`extern "C-unwind"` only when unwinding across is intended). Bindings via `bindgen` in a
   `*-sys` crate; logic in a safe crate.
7. Variadic `extern "C"` functions can be defined in Rust since 1.99 (`args: ...` is a `VaList`);
   reads are `unsafe` and must match the caller's contract.
8. Verify with Miri, AddressSanitizer for FFI, and adversarial tests (see gates).

## 8. Performance (R-PERF)

1. Measure first. Benchmarks: criterion 0.8 or divan with `std::hint::black_box`; with criterion, save a baseline
   before the change and compare after. Profiles: `samply record` or `cargo flamegraph` on a
   `--profile profiling` build.
2. Release profile: `lto = "thin"` (or `"fat"` for small binaries where build time allows),
   `codegen-units = 1`, `debug = "line-tables-only"`; decide `panic = "abort"` per binary.
3. Allocation: `with_capacity`, buffer reuse, `write!` into an existing `String` instead of
   `format!` in hot loops, `itoa`-style formatting via `{integer}::format_into` (1.98).
4. Hashing: default SipHash for attacker-controlled keys; `foldhash`/`rustc-hash` (`FxHashMap`)
   for trusted keys only.
5. Global allocator (`mimalloc`, `tikv-jemallocator`) in applications after a benchmark shows the
   win.
6. Iterators over indexing in hot loops so bounds checks can be elided; `array_windows`/
   `chunks_exact` for fixed-size windows.
7. `#[inline]` only on small cross-crate hot functions; `#[cold]`/`core::hint::cold_path()` for
   error branches. Verify with a benchmark, not intuition.
8. `target-cpu` above the baseline only when you control the deployment hardware.
9. `cargo build --timings` and `cargo llvm-lines` (third-party, 0.4.48) when compile time is the problem;
   split crates and trim features before reaching for exotic linkers (LLD is already the default on
   x86_64 Linux since 1.90).

## 9. Security and supply chain (R-SEC)

1. Review every new dependency: maintainers, downloads, last release, `build.rs`, proc macros,
   transitive count (`cargo tree -e normal -i <crate>`), license. Prefer fewer, well-known crates.
2. Gates: `cargo deny check` (advisories, bans, licenses, sources) and `cargo audit` in CI;
   `cargo auditable build --release` for shipped binaries; `cargo vet` where the org requires
   audited dependencies.
3. 2026 incidents to remember: malicious republish of `arrayref` 0.3.10, `internment` 0.8.7 and
   `append-only-vec` 0.1.9 via a `proc-macro1` build-script payload (2026-08-20); targeted social
   engineering of crate owners (2026-09-17); `cargo miri` writing the environment into `target/`
   where CI caches could leak secrets (2026-09-21); `tar` crate CVE-2026-33056 fixed in Cargo 1.94.1;
   CVE-2026-5222/5223 for third-party registries fixed in 1.96.
4. CI hygiene: secrets only in the steps that need them; jobs that write caches get no secrets;
   `--locked` everywhere; pin third-party actions to a full commit SHA in high-assurance repos.
5. Input: parameterized SQL only (`sqlx::query!`/`query_as!` checked at build time with
   `DATABASE_URL` or offline `.sqlx` data from `cargo sqlx prepare`); request body limits;
   `serde(deny_unknown_fields)` on external input where strictness matters; size and depth limits
   on recursive formats.
6. Secrets: `secrecy::SecretString` (0.10.3) or `zeroize` (1.9.1); custom `Debug` that redacts;
   never log tokens, passwords or full request bodies with PII.
7. TLS: rustls (0.23.46) unless the platform mandates native TLS; never disable certificate
   verification outside tests.
8. Config from the environment is read once at startup into a typed struct; `env::set_var` is
   `unsafe` in edition 2024 because it races with concurrent reads.
9. Integer handling at trust boundaries: `checked_*`/`TryFrom`; `overflow-checks = true` in the
   release profile for code where wrap-around would be a security bug.

## 10. Observability (R-OBS)

1. `tracing` 0.1.44 everywhere; libraries never install a subscriber.
2. Binaries: `tracing-subscriber` 0.3.23 with `EnvFilter` from `RUST_LOG`, `.json()` in
   production; `tracing-opentelemetry` 0.34 + `opentelemetry-otlp` 0.33 when a collector exists.
3. Structured fields (`info!(order_id = %id, "accepted")`), `#[instrument(skip(secret_args))]` on
   request-scoped async functions, request ids propagated via tower-http.
4. Log an error once where it is handled, with its chain (`error = ?err`; anyhow's `Debug` prints
   the `Caused by` list).
5. `tokio-console` (`console-subscriber` 0.5) for diagnosing stuck tasks in development; it needs
   tokio's `tracing` feature and `--cfg tokio_unstable`, so keep it out of release builds.

## 11. Testing (R-TEST)

1. Failing test first for every bug and feature.
2. Unit tests in `#[cfg(test)] mod tests` for internals; integration tests in `tests/` for public
   behaviour; doctests for examples (they compile, so they stay true).
3. Names read as behaviour (`parse_rejects_zero_quantity`); one behaviour per test; assertion
   messages carry the input (`assert_eq!(got, want, "input {input:?}")`).
4. Property tests (`proptest` 1.12) for parsers, round-trips and invariants; snapshot tests
   (`insta` 1.49) for large structured output; `rstest` for tables of cases.
5. Fuzz untrusted-input parsers with `cargo fuzz` (nightly) or `bolero`.
6. I/O, time and randomness behind traits or injectable clients so tests are deterministic;
   integration tests against real dependencies with `testcontainers` (0.28) where mocks would lie.
7. Test runner: `cargo nextest run` (0.9.150) for speed and isolation; it does not run doctests,
   so also run `cargo test --doc`.
8. Coverage: `cargo llvm-cov nextest` with `--fail-under-lines`; mutation testing with
   `cargo mutants --in-diff` on changed code to check that tests actually assert.
9. Do not write tautological tests that restate constants or mirror the implementation.

## 12. Verification gates

Run from the workspace root and paste real output. A gate counts only if it ran in this session.

```bash
# Gate 1: every change
cargo fmt --all --check
cargo clippy --workspace --all-targets --all-features --locked -- -D warnings
cargo nextest run --workspace --all-features --locked
cargo test --workspace --all-features --doc --locked

# Gate 2: before merge
RUSTDOCFLAGS="-D warnings" cargo doc --workspace --no-deps --all-features --locked
cargo deny check
cargo audit
cargo hack check --workspace --feature-powerset --no-dev-deps
cargo hack check --workspace --rust-version
cargo shear
cargo llvm-cov nextest --workspace --all-features --fail-under-lines 80

# Gate 3: by risk
cargo +nightly miri nextest run                       # unsafe code (or: cargo +nightly miri test)
rustup +nightly component add rust-src                # prerequisite for -Zbuild-std
RUSTFLAGS=-Zsanitizer=address RUSTDOCFLAGS=-Zsanitizer=address \
  cargo +nightly test -Zbuild-std --target x86_64-unknown-linux-gnu   # FFI memory errors
RUSTFLAGS="--cfg loom" cargo test --release --test loom_*             # custom sync primitives
cargo +nightly fuzz run <target> -- -max_total_time=300               # untrusted-input parsers
git diff origin/main... > /tmp/changes.diff && cargo mutants --in-diff /tmp/changes.diff   # empty diff = not run, not a pass
cargo semver-checks                                                    # library releases
cargo bench --bench <name> -- --save-baseline before                   # then --baseline before
```

What failure looks like and what to do:

| Signal | Meaning | Action |
|---|---|---|
| `Diff in <file>` from fmt | unformatted code | `cargo fmt --all`, re-run |
| `error: ...` from clippy with `-D warnings` | a lint fired | fix the code; `#[expect(..., reason)]` only if the lint is wrong here |
| nextest `FAIL [..]` / `N failed` | behaviour regression | read the first failure; fix code, not the test, unless the test is wrong and you say why |
| `error[advisory]` from cargo-deny / `Vulnerable crates found!` from cargo-audit | known vulnerable dependency | upgrade; if no fix exists, document the risk and an `ignore` with an expiry date |
| `error[license]` / `error[banned]` | policy violation | replace the dependency or get an explicit exception |
| `Undefined Behavior:` from Miri | unsound code | fix before merge; never suppress |
| `MISSED` mutants in the diff | tests do not observe that code | add an assertion that kills the mutant |
| semver-checks `FAIL` | breaking API change | bump the major version or restore compatibility |

Install the tools with `cargo install --locked cargo-nextest cargo-deny cargo-audit
cargo-llvm-cov cargo-hack cargo-shear cargo-mutants cargo-semver-checks` (or `cargo binstall` for
prebuilt binaries); Miri via `rustup +nightly component add miri`.

## 13. Review checklist

Before returning code, confirm:

- [ ] Gate 1 is clean, with output pasted; Gate 2/3 items run where the change warrants them.
- [ ] No `unwrap()` on fallible runtime paths; every `expect`/`assert!` names its invariant.
- [ ] Public API takes borrowed general types, derives the right traits, and has docs with
      `# Errors`/`# Panics`/`# Safety` where relevant.
- [ ] Error types are typed in libraries and contextual in applications.
- [ ] No guard or `!Send` value held across `.await`; no blocking calls on async workers; every
      spawned task owned and every network call bounded by a timeout.
- [ ] Every `unsafe` block has a `// SAFETY:` proof and Miri coverage.
- [ ] New dependencies reviewed and justified; `cargo deny check` passes.
- [ ] Performance claims come with before/after numbers.
- [ ] Anything not verified in this session is marked `[UNVERIFIED]`.

## Addenda (orchestrator fixes from the blind score, 2026-10-29)

- **Async tests.** Use `#[tokio::test]` (add `flavor = "multi_thread"` only when the code under test needs
  it). For timeouts and retries use `#[tokio::test(start_paused = true)]` or `tokio::time::pause()`, so time is
  deterministic and the test never sleeps for real. Cover graceful shutdown with a test that fires the
  `CancellationToken` and asserts in-flight requests drain.
- **Concurrency evidence.** loom covers custom sync primitives (declare `cfg(loom)` in `[workspace.lints.rust]`
  `unexpected_cfgs`, as the template does). ThreadSanitizer covers unsafe/FFI code (see the agent's Gate 3).
  TSan reports that come only from tokio/mio internals are inconclusive, not a pass. Suppress them explicitly
  and record the run.
- **Shipping applications.** Build container images in multiple stages: cache dependencies (for example with
  cargo-chef), then copy only the release binary into a slim runtime image. Use the `x86_64-unknown-linux-musl`
  target for static binaries. Cross-compile with `cross` or `cargo-zigbuild`. Automate releases (release-plz or
  cargo-dist). Check each tool's current version on crates.io before pinning it.
- **Service skeleton notes.** Background jobs must `select!` on `token.cancelled()`, or the token does nothing.
  A handler timeout is a server-side condition: answer 503 or 504, not 408.
- **MCP servers.** `rust-analyzer-mcp` and `rust-mcp-server` start only after `cargo install` (see the agent's
  MCP section). Neither has been handshake-tested in this pack, so treat them as optional until you have run
  one MCP `initialize` against the installed binary.
