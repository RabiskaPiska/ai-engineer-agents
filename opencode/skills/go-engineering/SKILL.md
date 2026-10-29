---
name: go-engineering
description: "Go (Golang) engineering rule catalog and verification gates for the Go 1.27 / October 2026 toolchain. Use when writing, reviewing, refactoring, testing, profiling or upgrading Go code (*.go, go.mod, go.work, .golangci.yml), setting up golangci-lint v2, govulncheck or CI for a Go module, or deciding which modern Go API (errors.AsType, wg.Go, synctest, os.Root, json/v2, std uuid) to use."
---

# Go engineering: rules and gates (October 2026)

This skill is the detailed companion to the `go-engineer` agent. It is a catalog of checkable rules,
each with the reason it exists, followed by the exact gate commands and a CI recipe. Rules are
numbered so reviews can cite them (`GO-ERR-2`). The gate commands, the release build line and the
reference code were run against a sample module with go1.27.3, golangci-lint 2.14.0, staticcheck
2026.2.2, govulncheck v1.9.0, actionlint v1.7.12 and hadolint v2.15.1 on 2026-10-29. Two things
could not be executed here and are marked `[UNVERIFIED]` where they appear: the container image
build (no Docker daemon access) and the CI workflow on GitHub's runners (actionlint-validated only).

Deeper material lives in `references/`:

- `references/golangci-v2.md`: the vetted `.golangci.yml` (v2 schema) and why each linter is on.
- `references/service-skeleton.md`: a tested HTTP service (`run()` pattern, timeouts, graceful
  shutdown that drains in-flight requests, body limits, CSRF protection), its tests, and the
  multi-stage Dockerfile for it (GO-MOD-7).
- `references/concurrency-patterns.md`: bounded fan-out with `errgroup`, a debouncer, and
  deterministic `testing/synctest` tests for both, including their edge cases.

## 0. Before you write code

1. Read the `go` and `toolchain` lines in `go.mod`. They bound which features you may use: generic
   methods need `go 1.27`; `new(expr)` and `errors.AsType` need `go 1.26`; `sync.WaitGroup.Go`,
   `testing/synctest` and `http.CrossOriginProtection` need `go 1.25`; `os.Root`, `t.Context()`,
   `b.Loop()`, `omitzero` and `tool` directives need `go 1.24`. The compiler rejects a too-new
   stdlib symbol with "requires go1.N or later (file is go1.M)", and `go test` runs the `stdversion`
   vet check too.
2. Read `.golangci.yml` and the CI workflow; the repo's gates are the contract.
3. Run `go test ./...` once and note pre-existing failures.
4. Use `go doc <pkg>.<Symbol>` for the installed toolchain's exact API rather than memory.

## 1. Rule catalog

### Errors (GO-ERR)

- **GO-ERR-1 Wrap with context, `%w` last.** `return fmt.Errorf("load config %s: %w", path, err)`.
  The chain then reads outer-to-inner like a stack, and `errors.Is/As` still work.
- **GO-ERR-2 Match, never compare.** `errors.Is(err, fs.ErrNotExist)`; `if pe, ok :=
  errors.AsType[*fs.PathError](err); ok { ... }` (Go 1.26+, type-safe and faster than `errors.As`).
  `err == io.EOF` is only correct when the API documents an unwrapped sentinel; `errorlint` enforces
  this.
- **GO-ERR-3 Handle once.** Log or return, not both. Logging at every layer multiplies noise and
  hides the real call site; log at the boundary that decides the outcome.
- **GO-ERR-4 Naming.** Sentinels `ErrNotFound` (`var ErrNotFound = errors.New("store: not found")`),
  types `NotFoundError`. Messages lower-case, no trailing punctuation (`revive` error-strings).
- **GO-ERR-5 Decide what is API.** Wrapping with `%w` makes the inner error part of your contract;
  use `%v` when callers should not depend on it.
- **GO-ERR-6 Multiple errors.** `errors.Join(errs...)`; no third-party multi-error library needed.
- **GO-ERR-7 Panics.** Only for invariants a caller cannot recover from. Never let a panic cross a
  package API; recover only at goroutine or request boundaries and convert to an error.
- **GO-ERR-8 Exit once.** `main` calls `run(ctx context.Context, getenv func(string) string,
  stdout io.Writer) error` (add `args []string` when the binary takes flags) and calls `os.Exit` in
  one place. `log.Fatal` elsewhere skips deferred cleanup. Interfaces such as `io.Writer`, not
  `*os.File`, are what let a test call `run` with a buffer and assert on it.

### Context (GO-CTX)

- **GO-CTX-1** `ctx context.Context` is the first parameter of every function that does I/O, blocks,
  or calls something that does.
- **GO-CTX-2** Never store a context in a struct, never pass `nil`, never use `context.Background()`
  inside a request path (`contextcheck`).
- **GO-CTX-3** Work that must outlive cancellation (audit write, cleanup on shutdown) uses
  `context.WithoutCancel(ctx)`, which keeps values but drops the deadline.
- **GO-CTX-4** Call the `cancel` returned by `WithCancel/WithTimeout` on every path (`defer cancel()`;
  vet `lostcancel`).
- **GO-CTX-5** Context values are for request-scoped data crossing APIs (trace IDs, auth principal),
  keyed by an unexported type. Not for optional parameters.

### Concurrency (GO-CONC)

- **GO-CONC-1 Ownership.** Every goroutine has a stop signal (context or closed channel) and someone
  who waits for it. Fire-and-forget goroutines leak memory and run after shutdown.
- **GO-CONC-2 Groups.** `wg.Go(func(){...})` (Go 1.25+) for fire-and-wait work that cannot fail;
  `errgroup.WithContext` + `g.SetLimit(n)` (golang.org/x/sync v0.24.0) when work can fail, must be
  bounded, or should cancel siblings. Never `wg.Add(1)` inside the goroutine (vet `waitgroup`).
- **GO-CONC-3 Channels.** Sender closes; receivers range. Unbuffered or size one by default. Use
  directional types (`<-chan T`, `chan<- T`) in signatures.
- **GO-CONC-4 Select.** Long-lived loops select on `<-ctx.Done()`. Reuse a `time.Timer` with `Reset`
  in hot loops instead of allocating with `time.After` on every iteration.
- **GO-CONC-5 Shared state.** A mutex lives next to the fields it guards, documented. Keep critical
  sections free of I/O. Do not copy lock-holding structs (vet `copylocks`). Use typed atomics
  (`atomic.Int64`, `atomic.Pointer[T]`); `go fix` (`atomictypes`) rewrites the old forms.
- **GO-CONC-6 Maps.** Concurrent map write is a fatal runtime error, not a recoverable panic. Guard
  with a mutex; reach for `sync.Map` only for read-mostly, disjoint-key workloads.
- **GO-CONC-7 Deduplicate.** `singleflight` for cache stampedes; `sync.OnceValue(s)` for lazy init.
- **GO-CONC-8 Test it.** `-race` always; `testing/synctest` for anything with timers, tickers or
  timeouts (fake clock, deterministic, no sleeps). `synctest.Sleep(d)` (1.27) advances the bubble
  clock and waits. Detect leaks with `go.uber.org/goleak` (`goleak.VerifyTestMain(m)`) or the
  `goroutineleak` pprof profile (GA in 1.27).

### API and package design (GO-API)

- **GO-API-1** Accept interfaces, return structs. The consumer owns the interface and keeps it small;
  no interface until there are two implementations or a real test seam.
- **GO-API-2** Package by responsibility (`billing`, `httpapi`, `postgres`), not by layer-type
  (`models`, `utils`). `internal/` for anything not intended for import.
- **GO-API-3** Useful zero values; constructors (`NewX`) only when invariants need them.
- **GO-API-4** Functional options or an options struct for more than three optional settings.
- **GO-API-5** Generic methods (1.27) for helpers scoped to one type; generics in general only when
  two or more concrete types share the algorithm. Interface methods cannot have type parameters.
- **GO-API-6** Copy caller-owned slices and maps that you retain (`slices.Clone`, `maps.Clone`).
- **GO-API-7** Document every exported identifier with a sentence starting with its name; document
  concurrency safety and zero-value behavior.
- **GO-API-8** Deprecate with a `// Deprecated:` paragraph, and add `//go:fix inline` to a wrapper
  that forwards to its replacement so `go fix` migrates callers automatically.
- **GO-API-9 Iterators (Go 1.23+).** Expose `iter.Seq[T]` / `iter.Seq2[K, V]` (method names `All`,
  `Backward`, `Keys`, `Values` per the `iter` docs) when the sequence is lazy, large, streamed
  (pages, rows, tree walks) or the caller may stop early; return a slice when callers need `len`,
  indexing or several passes, or the data is already in memory (or return `slices.Values(s.items)`).
  The yield contract: stop calling `yield` as soon as it returns `false`; ignoring it panics with
  "range function continued iteration after function for loop body returned false". For fallible
  sequences yield `(T, error)` pairs and stop after the error. Consumers that pull values use
  `next, stop := iter.Pull(seq)` and `defer stop()`. Collect with `slices.Collect`,
  `maps.Collect`. The `go fix` modernizers `stringsseq` (`strings.SplitSeq`/`FieldsSeq` in `range`)
  and `stditerators` (`x.All()` instead of `Len`/`At` loops) apply these rewrites for you.
- **GO-API-10 Types.** Enums are typed constants from `iota + 1` so the zero value means "unset", and
  `switch` over them is exhaustive (`exhaustive`); type assertions use the two-value form
  (`forcetypeassert`); a type's methods use one receiver kind, all pointer or all value
  (`recvcheck`).

### Data and encoding (GO-DATA)

- **GO-DATA-1 JSON.** `encoding/json` is backed by the v2 engine in 1.27 with v1 behavior kept;
  new code may use `encoding/json/v2` (rejects duplicate keys and invalid UTF-8 by default; the
  `inline` option is spelled `embed`). Use `omitzero` instead of `omitempty` for structs and
  `time.Time`. Re-run integration tests against real payloads after the 1.27 upgrade; error message
  text may differ.
- **GO-DATA-2 SQL.** Parameterized queries only; `defer rows.Close()` and check `rows.Err()`;
  pass `ctx` (`QueryContext`); set `SetMaxOpenConns`, `SetMaxIdleConns`, `SetConnMaxLifetime`.
  For Postgres, `pgx/v5` (v5.11.0) with `pgxpool`; generate typed queries with sqlc (v1.31.1) when the
  repo uses it. Wrap multi-statement writes in a transaction with `defer tx.Rollback()` (a no-op
  after `Commit`).
- **GO-DATA-3 IDs and time.** Std `uuid.NewV7()` (Go 1.27) for sortable IDs; store `time.Time` in UTC;
  never parse with the `2006-02-01` layout (vet `timeformat`).
- **GO-DATA-4 Optional fields.** `new(expr)` (1.26) builds pointer fields inline:
  `Age: new(yearsSince(born))`.

### Security (GO-SEC)

- **GO-SEC-1** `http.Server` with `ReadHeaderTimeout` at minimum (gosec G112/G114 flag its absence)
  plus `ReadTimeout`, `WriteTimeout`, `IdleTimeout`. Slowloris is otherwise a one-line DoS.
- **GO-SEC-2** `http.MaxBytesReader` on every request body; reject unknown JSON fields on strict APIs.
- **GO-SEC-3** `http.NewCrossOriginProtection().Handler(mux)` (Go 1.25+) for browser-facing
  state-changing endpoints.
- **GO-SEC-4** File paths from users go through `os.OpenRoot(dir)` / `os.OpenInRoot(dir, name)`,
  which refuse `..` and symlink escapes.
- **GO-SEC-5** Outbound requests: `http.NewRequestWithContext`, a shared client with `Timeout`, URL
  allowlist for user-provided targets (SSRF), always close the body. In 1.27 closing an HTTP/1 body
  drains a bounded remainder for connection reuse.
- **GO-SEC-6** `html/template` (contextual escaping) for HTML, never `text/template`. `exec.Command`
  with separate args, never `sh -c` with interpolated input.
- **GO-SEC-7** Randomness: `crypto/rand` (`rand.Text()` for tokens); compare secrets with
  `subtle.ConstantTimeCompare`. TLS: leave `MinVersion` at the default (TLS 1.2) or raise it; never set
  `InsecureSkipVerify` outside tests. Post-quantum hybrid key exchange is on by default since 1.26.
- **GO-SEC-8** Reverse proxies use `httputil.ReverseProxy.Rewrite`, not the deprecated `Director`
  (a client can strip Director-added headers via hop-by-hop designation).
- **GO-SEC-9** Secrets never reach logs: implement `slog.LogValuer` on secret-bearing types to
  redact. Goroutine labels now appear in 1.27 tracebacks; keep secrets out of pprof labels or set
  `GODEBUG=tracebacklabels=0`.
- **GO-SEC-10** `govulncheck ./...` on every dependency change and in CI; it reports only
  vulnerabilities whose symbols your code reaches. Rebuild with the latest patch release (go1.27.3
  fixes a crypto/x509 issue).

### Performance (GO-PERF)

- **GO-PERF-1** No optimization without a profile or benchmark. `go test -cpuprofile cpu.out
  -memprofile mem.out -bench=. ./pkg` then `go tool pprof -http=localhost:6060 cpu.out` (flame graph
  is the default view since 1.26).
- **GO-PERF-2** Benchmarks use `for b.Loop() { ... }` (1.24+; since 1.26 it no longer blocks
  inlining). Compare with `benchstat old.txt new.txt` over at least 10 runs per side (`-count=10`;
  benchstat's docs say "at least 10, ideally 20"), pick the count before you look, and do not rerun
  until it turns significant. Collect old and new on the same idle machine, interleaved (see the
  targeted gates below), so drift and thermal noise hit both sides equally. Quote the delta and
  p-value; `~` means no significant change.
- **GO-PERF-3** Escape analysis: `go build -gcflags='-m' ./pkg 2>&1 | grep escapes` to see why a
  value moves to the heap.
- **GO-PERF-4** Size hints for maps and slices with known sizes; `strings.Builder` with `Grow`;
  `strconv` instead of `fmt.Sprint` for single values (`perfsprint`).
- **GO-PERF-5** `sync.Pool` only for measured hot allocations, and reset objects before `Put`.
- **GO-PERF-6** PGO: save a production CPU profile as `default.pgo` next to `main.go`; `-pgo=auto`
  is the default, so `go build` applies it. Refresh it when hot paths change.
- **GO-PERF-7** Runtime knobs: `GOMAXPROCS` is container-aware since 1.25; set `GOMEMLIMIT` for
  memory-capped containers. Use `runtime/trace.FlightRecorder` to capture the last seconds of trace
  data on an anomaly instead of tracing continuously.

### Testing (GO-TEST)

- **GO-TEST-1** Table-driven tests with `t.Run(tt.name, ...)`; `t.Parallel()` where tests are
  independent (Go 1.22+ loop variables are per-iteration, so no `tt := tt`).
- **GO-TEST-2** Failure messages say `Func(input) = got, want want`. Use `cmp.Diff(want, got)` from
  `github.com/google/go-cmp` (v0.7.0) for structs. Follow the repo if it uses testify (v1.12.1).
- **GO-TEST-3** `t.Context()` instead of `context.Background()` (1.24); `t.TempDir()`, `t.Setenv()`,
  `t.Chdir()` instead of manual cleanup (`usetesting`); `t.ArtifactDir()` (1.26) for files worth
  keeping with `-artifacts`.
- **GO-TEST-4** `t.Fatal` only from the test goroutine (vet `testinggoroutine`). Helpers call
  `t.Helper()` (`thelper`).
- **GO-TEST-5** Prefer real implementations and fakes over mocks; for HTTP use `httptest`
  (`httptest.NewTestServer` in 1.27 runs on an in-memory network inside `synctest`). Generate mocks
  (mockery v3.9.0 or go.uber.org/mock v0.6.0) only for interfaces you own.
- **GO-TEST-6** Fuzz parsers, decoders and anything handling untrusted bytes:
  `func FuzzX(f *testing.F)`; seed with `f.Add`, commit crashers found under `testdata/fuzz/`.
- **GO-TEST-7** Integration tests behind a build tag (`//go:build integration`) or `testing.Short()`;
  databases via containers in CI, never shared state.
- **GO-TEST-8** Golden files under `testdata/`, updated with an `-update` flag, reviewed in diffs.

### Modules, build and release (GO-MOD)

- **GO-MOD-1** Libraries keep the `go` directive at the oldest supported line they need; apps can
  track the newest. After `go mod init`, check the generated `go` line and set it deliberately with
  `go mod edit -go=1.26.0` (or `go get go@1.26.0`).
- **GO-MOD-2** Dev tools via `tool` directives: `go get -tool golang.org/x/vuln/cmd/govulncheck@v1.9.0`,
  then `go tool govulncheck ./...`. golangci-lint is the exception: install the pinned release binary
  (`curl -sSfL https://golangci-lint.run/install.sh | sh -s -- -b $(go env GOPATH)/bin v2.15.0`),
  because its maintainers do not support `go install`/`go tool` builds. Run `go mod tidy` after
  `go get -tool`: in the verification run it left `go.sum` incomplete and the tidy gate failed.
- **GO-MOD-3** `go mod tidy` must leave no diff; commit `go.sum`; `go mod verify` in CI.
- **GO-MOD-4** No local-path `replace` in released modules; use `go.work` for multi-module local dev
  and do not commit `go.work` for libraries.
- **GO-MOD-5** Release builds: `CGO_ENABLED=0 go build -trimpath -ldflags="-s -w -X
  main.version=$(git describe --tags --always)" -o bin/app ./cmd/app`, with `var version = "dev"`
  in package `main`. The double quotes matter: inside single quotes the shell never expands
  `$(...)`, go splits the literal `$(git describe --tags)` into stray linker arguments, and the
  link fails with `usage: link [options] main.o` (exit 1, no binary). `--always` falls back to
  the commit hash when no tag exists. Check with `go version -m bin/app`. GoReleaser (v2.19.0) or ko
  (v0.19.1) for multi-platform artifacts and images.
- **GO-MOD-6** Upgrading Go: bump `toolchain`, run `go fix -diff ./...` and review, run the full
  gates, grep for removed GODEBUGs (`grep -n godebug go.mod; grep -rn --include='*.go' '//go:debug' .`), and
  expect a small `gofmt` whitespace diff with 1.27.
- **GO-MOD-7 Containers.** Multi-stage build: compile in `golang:1.27.3-trixie` with `CGO_ENABLED=0`,
  `-trimpath` and the GO-MOD-5 flags, then copy only the binary into
  `gcr.io/distroless/static-debian13:nonroot` (CA certificates, tzdata, `/tmp`; no shell or package
  manager; runs as UID 65532). Set `USER 65532:65532` numerically so Kubernetes `runAsNonRoot` can
  verify it, pass the version with `--build-arg VERSION=$(git describe --tags --always)`, use
  BuildKit cache mounts for `/go/pkg/mod` and `/root/.cache/go-build`, and pin both base images by
  digest in real repos. Use `base-debian13` only when cgo needs glibc. The full Dockerfile is in
  `references/service-skeleton.md`; lint it with `hadolint Dockerfile`.
- **GO-MOD-8 Toolchain and module fetching.** `GOTOOLCHAIN` defaults to `auto`, which downloads a
  newer toolchain whenever `go.mod` asks for one. Applications record the patched release with
  `go get toolchain@go1.27.3` (writes `toolchain go1.27.3`), because `actions/setup-go` installs the
  `toolchain` version and otherwise the exact `go` line, so `go 1.27.0` alone means CI builds with an
  unpatched 1.27.0. In CI and Docker set `GOTOOLCHAIN=local`, so a mismatch fails ("go.mod requires
  go >= 1.28.0 (running go 1.27.3; GOTOOLCHAIN=local)") instead of silently downloading. Private
  modules: `GOPRIVATE=github.com/yourorg/*`, which is the default for both `GONOPROXY` and
  `GONOSUMDB`, so their paths go neither to proxy.golang.org nor to sum.golang.org. Build commands
  have defaulted to `-mod=readonly` since Go 1.16 (a needed `go.mod` change is an error); set
  `GOFLAGS=-mod=readonly` in CI so an inherited `-mod=mod` cannot quietly add requirements, and use
  `-mod=vendor` only with a committed `vendor/`.

## 2. Gates

Run from the module root, in this order (cheap to expensive). Pass criteria in comments.

```bash
set -o pipefail
test -z "$(gofmt -l .)"                         # no files listed
go build ./...                                  # exit 0
go vet ./...                                    # exit 0, silent
go fix -diff ./...                              # exit 0 and empty; exit 1 prints pending modernizations
golangci-lint config verify && golangci-lint run ./...   # "0 issues."
go test -race -shuffle=on -count=1 ./...        # all "ok" (needs CGO_ENABLED=1 and a C toolchain)
go test -covermode=atomic -coverprofile=cover.out ./... && go tool cover -func=cover.out | tail -1
govulncheck ./...                               # "No vulnerabilities found."; exit 3 when found
go mod tidy && git diff --exit-code go.mod go.sum
```

Targeted gates when relevant:

```bash
go test -run='^$' -fuzz='^FuzzParse$' -fuzztime=30s ./internal/parse   # one package per fuzz run
# Interleaved A/B benchmark: build both test binaries once, alternate runs, 10 per side.
go test -c -o old.test ./pkg   # on the base commit (git stash or a worktree)
go test -c -o new.test ./pkg   # on the change
for i in $(seq 10); do
  ./old.test -test.run='^$' -test.bench='^BenchmarkX$' -test.benchmem >> old.txt
  ./new.test -test.run='^$' -test.bench='^BenchmarkX$' -test.benchmem >> new.txt
done
benchstat old.txt new.txt                       # delta with p-value and n=10 per side
staticcheck ./...                               # when the repo does not use golangci-lint; silent = pass
gopls check path/to/file.go                     # quick diagnostics for one file
go test -asan ./...                             # cgo code only: AddressSanitizer (leak detection on since 1.25)
```

Known false-pass traps (each was hit or checked during verification):

- `golangci-lint` shows one issue per line by default; set `issues.uniq-by-line: false` or a
  `gosec` hit hides a `bodyclose`/`noctx` hit on the same call.
- `govulncheck` with `-json`, `-format sarif` or `-format openvex` exits 0 regardless of findings.
- `go test ... | tail -1` exit status is tail's. Use `set -o pipefail`.
- `CGO_ENABLED=0 go test -race` fails with "-race requires cgo"; it is a setup problem, not a pass.
- Cached results: `-count=1` forces a re-run when the code under test reads files or env vars that the
  cache does not track.

## 3. CI recipe (GitHub Actions)

Actions are pinned to full commit SHAs (a tag can be moved; a SHA cannot), with the release in a
comment so Dependabot/Renovate can bump both. SHAs resolved on 2026-10-29 through the GitHub API
(`git/ref/tags/<tag>`, annotated tags dereferenced to their commit): actions/checkout v7.0.1,
actions/setup-go v7.0.0 (installs the `toolchain` version, else the `go` line; see GO-MOD-8),
golangci/golangci-lint-action v9.3.0. The workflow token is read-only and checkout does not keep it.

```yaml
name: ci

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

env:
  GOFLAGS: -mod=readonly
  GOTOOLCHAIN: local

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: actions/setup-go@b7ad1dad31e06c5925ef5d2fc7ad053ef454303e # v7.0.0
        with:
          go-version-file: go.mod
      - run: go mod verify
      - run: go mod tidy && git diff --exit-code go.mod go.sum
      - run: test -z "$(gofmt -l .)"
      - run: go vet ./...
      - run: go test -race -shuffle=on -count=1 -covermode=atomic -coverprofile=cover.out ./...
      - uses: golangci/golangci-lint-action@ba0d7d2ec06a0ea1cb5fa41b2e4a3ab91d21278a # v9.3.0
        with:
          version: v2.15.0
      - run: go run golang.org/x/vuln/cmd/govulncheck@v1.9.0 ./...
```

`actionlint` v1.7.12 reports no errors on this file, and every `run:` line was executed locally
against the sample module. It has not run on GitHub's runners: `[UNVERIFIED]` as a live workflow.

## 4. Review checklist

Use this when reviewing a Go diff; each line maps to a rule above.

- [ ] Errors wrapped with context, matched with `Is`/`AsType`, handled once (GO-ERR-1..3)
- [ ] `ctx` first, propagated, cancel called (GO-CTX-1..4)
- [ ] Each new goroutine has stop + wait; bounded fan-out; sender closes (GO-CONC-1..4)
- [ ] No data race under `-race`; timers tested with `synctest` (GO-CONC-8)
- [ ] Interfaces owned by consumers, minimal; no new `utils` package (GO-API-1..2)
- [ ] Iterators honor `yield`'s `false`; slices returned only when callers need them (GO-API-9)
- [ ] Resources closed; `rows.Err()` checked; SQL parameterized (GO-DATA-2)
- [ ] Server timeouts, body limits, path confinement, SSRF guard (GO-SEC-1..5)
- [ ] New APIs allowed by the `go` directive; no removed GODEBUG pinned (GO-MOD-1, GO-MOD-6)
- [ ] Dockerfile multi-stage, static, nonroot; CI pins SHAs, verifies modules (GO-MOD-3, GO-MOD-7..8)
- [ ] Tests: table-driven, fail before fix, `t.Context()`, fuzz for parsers (GO-TEST-1..6)
- [ ] Performance claims backed by `benchstat` output (GO-PERF-1..2)
- [ ] Gates pasted with real output
