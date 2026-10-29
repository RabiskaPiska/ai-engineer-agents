# Sources: Go (slug `go`)

Author run: 2026-10-29; fixer pass the same day (change log: `_work/fixes/go.md`). Deliverables:

- `claude/agents/go-engineer.md`
- `skills/go-engineering/SKILL.md` plus `references/golangci-v2.md`, `references/service-skeleton.md`,
  `references/concurrency-patterns.md`

All repository metadata below came from `ghapi.sh repos/<owner>/<repo>` (authenticated GitHub REST
GET) on 2026-10-29. Repo text was read as data only; no code or install step from these five repos
was executed.

## The 5 GitHub repos used

### 1. samber/cc-skills-golang

```json
{"full_name": "samber/cc-skills-golang", "html_url": "https://github.com/samber/cc-skills-golang", "stargazers_count": 3719, "pushed_at": "2026-10-23T07:50:53Z", "license": "MIT", "archived": false}
```

Read: `skills/golang-lint/SKILL.md`, `skills/golang-modernize/SKILL.md`,
`skills/golang-modernize/references/versions.md` (headings and the Go 1.24 to 1.27 sections),
`skills/golang-concurrency/SKILL.md`, the repo file tree (about 40 Go skills).
Took (MIT, adapted with attribution): the idea of a numbered, checkable rule catalog with a "why" per
rule; the `//nolint:<linter> // reason` discipline enforced by `nolintlint`; splitting a legacy lint
cleanup across parallel subagents by linter category; the WaitGroup-vs-errgroup decision table and the
"before you spawn a goroutine" checklist; the Go 1.27 version-bump risk list (removed GODEBUGs, json/v2
strictness, gofmt alignment), which I then re-verified line by line against go.dev/doc/go1.27.
Not taken: the 48-linter config (I built and executed a smaller one), the brew install path.

### 2. uber-go/guide

```json
{"full_name": "uber-go/guide", "html_url": "https://github.com/uber-go/guide", "stargazers_count": 17756, "pushed_at": "2026-04-15T15:10:48Z", "license": "Apache-2.0", "archived": false}
```

Read: `style.md` (4,107 lines; sections Errors/Handle Errors Once, Channel Size is One or None,
Don't fire-and-forget goroutines, Avoid init(), Exit in Main, Copy Slices and Maps at Boundaries,
Start Enums at One, Performance, Functional Options, Test Tables), and `LICENSE` (Apache-2.0).
Took (adapted with attribution): handle-errors-once (GO-ERR-3), channel size one or none (GO-CONC-3),
goroutine ownership and goleak (GO-CONC-1, GO-CONC-8), enums starting at one, copying slices/maps at
boundaries (GO-API-6), exit once from `main` via `run()` (GO-ERR-8), `strconv` over `fmt` and capacity
hints (GO-PERF-4). Rejected: `go.uber.org/atomic` (the stdlib typed atomics since Go 1.19 cover it).

### 3. google/styleguide (Go style guide: go/guide.md, go/decisions.md, go/best-practices.md)

```json
{"full_name": "google/styleguide", "html_url": "https://github.com/google/styleguide", "stargazers_count": 39774, "pushed_at": "2026-10-29T03:08:02Z", "license": "NOASSERTION", "archived": false}
```

License file is Creative Commons Attribution 3.0 (GitHub reports NOASSERTION), so this was
paraphrased only, no text copied. Read: `go/best-practices.md` headings, "Placement of %w in errors",
"Interfaces" (avoid unnecessary interfaces, consumer owns the interface, no exported test doubles),
"Use real transports", "Don't call t.Fatal from separate goroutines".
Took: `%w` at the end of the message (GO-ERR-1), interface ownership rules (GO-API-1), preferring real
implementations and transports over mocks (GO-TEST-5), the `t.Fatal`-from-goroutine rule (GO-TEST-4).

### 4. wshobson/agents

```json
{"full_name": "wshobson/agents", "html_url": "https://github.com/wshobson/agents", "stargazers_count": 41969, "pushed_at": "2026-10-26T01:08:14Z", "license": "MIT", "archived": false}
```

Read: `plugins/systems-programming/agents/golang-pro.md` and
`plugins/systems-programming/skills/go-concurrency-patterns/SKILL.md`.
Took: the agent-plus-skill pairing (a short agent prompt with a preloaded skill holding the depth) and
the capability scope list (services, gRPC, DB, observability) used to shape "Role and scope".
Rejected: its Go 1.21 baseline and generic "master X" phrasing; its "prefer channels over mutexes"
advice (replaced by the ownership-based channel-vs-mutex rule); buffered-by-default channel examples.

### 5. VoltAgent/awesome-claude-code-subagents

```json
{"full_name": "VoltAgent/awesome-claude-code-subagents", "html_url": "https://github.com/VoltAgent/awesome-claude-code-subagents", "stargazers_count": 26164, "pushed_at": "2026-10-11T08:20:37Z", "license": "MIT", "archived": false}
```

Read: `categories/02-language-specialists/golang-pro.md`.
Took: the "development checklist" framing (context propagation in all APIs, table-driven tests,
benchmarks for critical paths, docs for exported items), which became the review checklist in the
skill. Rejected: the `tools:` allowlist (the spec wants inherited tools, including MCP), the Go 1.21
baseline, and checklist items with no command behind them.

## MCP servers declared in the agent (verified 2026-10-29)

| Server | Verification |
|---|---|
| `github` | by-name reference to the already-configured server (spec). `github/github-mcp-server`: 34,054 stars, pushed 2026-10-29, MIT. |
| `context7` (`https://mcp.context7.com/mcp`) | `upstash/context7`: 63,879 stars, pushed 2026-10-28, MIT. HTTP `initialize` POST returned 200. |
| `gopls` (stdio `gopls mcp`) | Official, in `golang/tools` (8,011 stars, pushed 2026-10-28, BSD-3-Clause). Doc: `gopls/doc/features/mcp.md` (line 5: "Gopls includes an experimental built-in server for the Model Context Protocol", so the agent flags it as experimental; "`gopls mcp` ... speaks MCP over stdin/stdout"; Claude Code: `claude mcp add gopls -- gopls mcp`; requires gopls v0.20+). Installed gopls v0.24.0 with go1.27.3 and ran a stdio handshake: serverInfo `gopls v1.0.0`, tools `go_diagnostics, go_file_context, go_package_api, go_rename_symbol, go_search, go_symbol_references, go_vulncheck, go_workspace`. |
| `pkg-go-dev` (stdio `godig mcp`, pinned `go install github.com/samber/godig/cmd/godig@v0.2.0`) | `samber/godig`: 21 stars, pushed 2026-10-18, MIT, owner type `User` (single maintainer); latest tag `v0.2.0` (release 2026-07-02). Because of that trust profile the agent now defaults to the local stdio server, pinned to the tag, and treats the hosted `https://godig.samber.dev/mcp` (README: "A public instance is hosted on Clever Cloud") as opt-in only. Install command from the README (`go install github.com/samber/godig/cmd/godig@latest`, "Requires Go >= 1.25"), pinned to `@v0.2.0`. Data flow, from `cmd/godig/root.go` at v0.2.0: `--base-url` defaults to `pkggodev.DefaultBaseURL` ("the production pkg.go.dev API base URL", `samber/go-pkggodev-client` v0.5.0 `client.go`) and `--vuln-base-url` to `https://vuln.go.dev`; README: "All operations are read-only and need no authentication". Fixer run: installed v0.2.0 with go1.27.3 into a scratch GOBIN and ran a stdio `initialize` + `tools/list`: serverInfo `{'name': 'godig', 'version': 'dev'}`, 19 tools. The author's earlier HTTP handshake against the hosted URL returned the same serverInfo and 19 tools: `dependencies, imported-by, major-versions, module-info, module-licenses, module-readme, overview, package-doc, package-examples, package-imports, package-info, package-licenses, packages, search, symbol-doc, symbol-examples, symbols, versions, vulns`. Low star count: it is new; chosen because no other pkg.go.dev server combines search, versions, importers, licenses and vulns. Alternative considered: `mrjoshuak/godoc-mcp` (126 stars, pushed 2026-03-06, MIT), redundant with gopls `go_package_api`. |

## Official version sources (fetched 2026-10-29)

- https://go.dev/doc/devel/release : go1.27.0 released 2026-08-19; go1.27.1 2026-09-01; go1.27.2
  2026-10-08; go1.27.3 2026-10-19 (security fixes to crypto/x509); go1.26.0 2026-02-10 through
  go1.26.10, "go1.26.10 (released 2026-10-19)" (re-read by the fixer); release policy "supported
  until there are two newer major releases".
- https://go.dev/dl/?mode=json : stable `go1.27.3`, `go1.26.10`; sha256 of go1.27.3.linux-amd64.tar.gz
  `65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40` matched the download.
- https://go.dev/doc/go1.27 : generic methods, struct-literal field selectors, encoding/json/v2 +
  jsontext, `uuid`, `crypto/mldsa`, experimental `simd`, goroutineleak profile GA, `go test` runs
  stdversion, `go fix` new modernizers, gofmt alignment fix, removed GODEBUGs, HTTP/1 body drain on
  close, `httptest.NewTestServer`, `synctest.Sleep`, `strings/bytes.CutLast`, macOS 13 minimum.
- https://go.dev/doc/go1.26 : `new(expr)`, self-referential generic constraints, rewritten `go fix`,
  Green Tea GC default, `errors.AsType`, `slog.NewMultiHandler`, `T.ArtifactDir`, `b.Loop` inlining
  fix, `ReverseProxy.Director` deprecated, post-quantum hybrid TLS by default, `crypto/hpke`.
- https://go.dev/doc/go1.25 : container-aware GOMAXPROCS, `testing/synctest`, `WaitGroup.Go`,
  `CrossOriginProtection`, `runtime/trace.FlightRecorder`, vet `waitgroup`/`hostport`, `-asan` leak
  detection, go.mod `ignore`.
- https://go.dev/doc/go1.24 : `tool` directives and `go get -tool`, `os.Root`, `omitzero`,
  `testing.B.Loop`, `T.Context`, `runtime.AddCleanup`, `weak`.
- https://pkg.go.dev/uuid@go1.27.3 : `New, NewV4, NewV7, Parse, MustParse, Nil, Max`.
- https://proxy.golang.org/<module>/@latest : gopls v0.24.0 (2026-10-14), golang.org/x/vuln v1.9.0
  (2026-10-11), golang.org/x/tools v0.52.0, golang.org/x/sync v0.24.0 (2026-09-23),
  golangci-lint/v2 v2.15.0, honnef.co/go/tools v0.8.2, mvdan.cc/gofumpt v0.12.0, testify v1.12.1,
  go-cmp v0.7.0, pgx/v5 v5.11.0, chi/v5 v5.5.0, otel v1.47.0, grpc v1.85.0, goose/v3 v3.29.0,
  goleak v1.3.0, gotestsum v1.13.0, delve v1.27.2, modelcontextprotocol/go-sdk v1.8.0.
- GitHub releases API (`repos/<r>/releases/latest`): golangci-lint v2.15.0 (2026-10-16), go-tools
  2026.2.2 (2026-10-12), gofumpt v0.12.0 (2026-09-07), delve v1.27.2 (2026-09-09), gotestsum v1.13.0
  (2025-09-11), goreleaser v2.19.0 (2026-10-22), sqlc v1.31.1 (2026-04-22), gosec v2.30.0
  (2026-10-23), uber-go/mock v0.6.0 (2025-08-18), mockery v3.9.0 (2026-10-28), buf v1.75.0
  (2026-10-22), ko v0.19.1 (2026-06-29), actions/checkout v7.0.1, actions/setup-go v7.0.0,
  golangci-lint-action v9.3.0.
- https://raw.githubusercontent.com/golangci/golangci-lint/main/.golangci.reference.yml and
  `docs/content/docs/welcome/install/local.md` : v2 schema; binary install recommended, `go install` /
  `go tool` "aren't guaranteed to work".
- https://raw.githubusercontent.com/golang/vuln/master/cmd/govulncheck/doc.go and
  `internal/scan/errors.go` : exit code 3 on findings; JSON/SARIF/OpenVEX modes exit 0.
- https://raw.githubusercontent.com/golang/tools/master/gopls/doc/features/mcp.md and
  `gopls/internal/mcp/instructions.md` : gopls MCP modes and workflows; "experimental built-in server".

Added by the fixer pass (fetched 2026-10-29):

- https://raw.githubusercontent.com/golang/perf/master/cmd/benchstat/main.go : "Each benchmark should
  be run at least 10 times"; "Pick a number of benchmark runs (at least 10, ideally 20) and stick to
  it"; "The best way to do this is to interleave before and after runs"; `go test -c` to pre-compile.
  Basis of GO-PERF-2 and the interleaved gate.
- https://go.dev/doc/go1.23 : "The “range” clause in a “for-range” loop now accepts iterator functions".
  `go doc iter` (go1.27.3): `All`/`Backward` naming conventions, `Pull` and "they must call stop".
- https://raw.githubusercontent.com/golang/tools/master/go/analysis/passes/modernize/doc.go :
  analyzers `stditerators` ("use iterators instead of Len/At-style APIs") and `stringsseq`;
  `go tool fix help` with go1.27.3 lists both.
- https://go.dev/doc/toolchain : "default GOTOOLCHAIN setting is auto"; "When GOTOOLCHAIN is set to
  local, the go command always runs the bundled Go toolchain"; `go get toolchain@go1.22.9` updates
  only the toolchain line.
- https://go.dev/ref/mod : "Since Go 1.16, the go command acts as if -mod=readonly were set";
  "GOPRIVATE is a default value for GONOPROXY and GONOSUMDB".
- https://raw.githubusercontent.com/actions/setup-go/v7.0.0/docs/advanced-usage.md : go-version-file
  "Uses the toolchain directive if present, otherwise the action falls back to the go directive";
  "If a patch version is specified, that specific patch version will be used" (why GO-MOD-8 tells
  apps to add a `toolchain` line).
- GitHub API `repos/<r>/git/ref/tags/<tag>` (annotated tags dereferenced via `git/tags/<sha>`):
  actions/checkout v7.0.1 = `3d3c42e5aac5ba805825da76410c181273ba90b1`, actions/setup-go v7.0.0 =
  `b7ad1dad31e06c5925ef5d2fc7ad053ef454303e`, golangci/golangci-lint-action v9.3.0 = commit
  `ba0d7d2ec06a0ea1cb5fa41b2e4a3ab91d21278a` (tag object `d583c34f…`). rhysd/actionlint latest
  v1.7.12 (2026-03-30); hadolint/hadolint latest v2.15.1 (2026-07-31).
- https://hub.docker.com/v2/repositories/library/golang/tags/1.27.3-trixie : 200, last_updated
  2026-10-28. `gcr.io/v2/distroless/static-debian13/manifests/nonroot` : 200; the amd64 image config
  has `User: 65532`, `WorkingDir: /home/nonroot`.
- https://raw.githubusercontent.com/GoogleContainerTools/distroless/main/base/README.md : static
  contains "ca-certificates", "A /etc/passwd entry for a root user", "A /tmp directory", "tzdata";
  distroless README lists `gcr.io/distroless/static-debian13` with tags `latest, nonroot, debug,
  debug-nonroot`.
- https://code.claude.com/docs/en/sub-agents.md : `skills` preloads full skill content; subagents may
  spawn subagents up to three layers by default (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`).

## Executed verification of the gate commands

Toolchain: official go1.27.3 (checksum-verified), golangci-lint 2.14.0 (pre-installed on the box;
latest is 2.15.0), staticcheck 2026.2.2, govulncheck v1.9.0, gofumpt v0.12.0, gopls v0.24.0, benchstat,
installed with `go install <official module>@<version>`. Sample module in the scratchpad with the three
reference code files plus deliberately defective files.

```
gofmt -l .                       -> (empty)
go vet ./...                     -> vet-ok
go fix -diff ./... (clean code)  -> exit 0 ; (old.go with interface{} + 3-clause loop) -> diff, exit 1
golangci-lint config verify      -> config-ok
golangci-lint run (clean)        -> 0 issues.
golangci-lint run (defects)      -> bodyclose, errorlint, gosec G107, gosec G114, intrange, modernize any,
                                    modernize rangeint, noctx   (bodyclose/noctx only after uniq-by-line: false)
go test -race -shuffle=on -count=1 ./...   -> ok example.com/sample/internal/kv 1.026s
CGO_ENABLED=0 go test -race ./...          -> go: -race requires cgo; enable cgo by setting CGO_ENABLED=1
go test -covermode=atomic -coverprofile=cover.out ./... -> coverage: 100.0% of statements (kv)
go test -run='^$' -fuzz='^FuzzParsePair$' -fuzztime=10s -> elapsed: 10s, execs: 2855730 ... PASS
go test -bench=. -benchmem -count=6 + benchstat           -> table printed (author run; superseded below by -count=10 interleaved)
staticcheck ./...                -> sc-ok (silent)
govulncheck ./...                -> No vulnerabilities found. exit=0
go get -tool golang.org/x/vuln/cmd/govulncheck@v1.9.0; go tool govulncheck ./... -> No vulnerabilities found.
go mod edit -go=1.26.0 ; go test ./...     -> strings.CutLast requires go1.27 or later (file is go1.26)
go build ./...                             -> build-ok
go mod tidy && git diff --exit-code go.mod go.sum -> diff in go.sum after `go get -tool` (gate fails as intended)
CGO_ENABLED=0 go build -trimpath -ldflags='-s -w -X main.version=v0.0.1' -o bin/api ./cmd/api ; go version -m bin/api -> bin/api: go1.27.3 (author run, literal version only)
go build -gcflags='-m' ./internal/kv 2>&1 | grep -c escapes -> 5
cmd/api + internal/fanout: go vet ok, go test -race ok (3 runs for TestDebounce, 0.00s each), golangci-lint 0 issues
```

Fixer pass, 2026-10-29, go1.27.3, golangci-lint 2.14.0, staticcheck 2026.2.2, govulncheck v1.9.0,
actionlint v1.7.12 (`go install github.com/rhysd/actionlint/cmd/actionlint@v1.7.12`), hadolint v2.15.1
(release binary; its `.sha256` asset URL returned "Not Found", so the binary was only run in the
scratchpad, never installed). Fresh sample module with the reference files, then a second module
rebuilt from the code blocks extracted out of the markdown (byte-identical, `cmp` silent):

```
# GO-MOD-5, old single-quoted line                       -> exit=1, no binary
CGO_ENABLED=0 go build -trimpath -ldflags="-s -w -X main.version=$(git describe --tags --always)" -o bin/app ./cmd/api
                                                          -> exit=0; go version -m: "mod example.com/sample v0.3.0"
ADDR=127.0.0.1:0 ./bin/app (SIGTERM after 1s)            -> {"msg":"listening",...,"version":"v0.3.0"}, {"msg":"shutting down"}, exit 0
git describe --tags --always (no tags)                   -> 7812e30 (commit fallback)
gofmt -l . / go vet / go fix -diff / staticcheck         -> empty / ok / empty / silent
golangci-lint config verify && golangci-lint run ./...   -> 0 issues.
go test -race -shuffle=on -count=1 -cover ./...          -> cmd/api ok 87.3% (was 38.3%); internal/fanout ok 100.0%
go test -race -count=1 ./cmd/api (x5)                    -> ok x5
TestServeDrainsInFlightRequestOnShutdown on old BaseContext(ctx) -> FAIL: in-flight request = (503, "request ctx canceled\n", <nil>), want (200, "completed", nil)
TestFetchAllRejectsBadLimit on old FetchAll              -> FAIL: FetchAll(limit=0) is blocked; synctest "deadlock: main bubble goroutine has exited but blocked goroutines remain"
TestDebounceClosedInput on old Debounce (-timeout 15s)   -> panic: test timed out after 15s
iterator: break out of a range over a seq that ignores yield's false -> "runtime error: range function continued iteration after function for loop body returned false"
interleaved benchmark recipe (go test -c, 10 alternating runs, benchstat) -> n=10 per side, "~ (p=0.912 n=10)"
GOTOOLCHAIN=local with go 1.28.0 in go.mod               -> go: go.mod requires go >= 1.28.0 (running go 1.27.3; GOTOOLCHAIN=local)
default build with an unlisted import                    -> "no required module provides package github.com/google/uuid; to add it" exit=1
GOFLAGS=-mod=mod go build with the same import           -> exit=0 and go.mod silently gains github.com/google/uuid
go get toolchain@go1.27.3                                -> go: added toolchain go1.27.3
actionlint .github/workflows/ci.yml                      -> no output, exit=0
every run: line of that workflow, with GOFLAGS=-mod=readonly GOTOOLCHAIN=local -> all exit=0 ("all modules verified", "No vulnerabilities found.")
hadolint Dockerfile                                      -> no output, exit=0
Dockerfile build-stage commands outside Docker           -> "all modules verified", exit=0, binary "statically linked"
docker version                                           -> permission denied on /var/run/docker.sock (image build not run)
```

Observed and recorded rather than assumed: `go mod init` with go1.27.3 wrote `go 1.27.3` in this
environment, which does not match the Go 1.26 release-note description of a lower default; the skill
therefore tells the agent to check and set the `go` line explicitly instead of relying on either.

## Unverified items

- The GitHub Actions workflow in SKILL.md section 3 was not executed on GitHub's runners; it passes
  actionlint and each of its `run:` lines was executed locally. Marked `[UNVERIFIED]` in the skill.
- The Dockerfile in `references/service-skeleton.md` was linted and its build-stage commands were
  replayed outside Docker, but no image was built (no Docker daemon access). Marked `[UNVERIFIED]`.
- None of the rule IDs: `gosec` G112 was confirmed in `securego/gosec` `rules/rulelist.go` ("Detect
  ReadHeaderTimeout not configured as a potential risk"); G107 and G114 were observed in the run.

## Self-check

Produced by a Python script (`yaml.safe_load` on both frontmatters, required-heading check in spec
order, and a link check: every GitHub repo mentioned verified with `ghapi.sh repos/<owner>/<repo>`,
every other URL fetched with curl, MCP endpoints probed with an MCP `initialize` POST). Re-run after
the fixer pass on 2026-10-29, output pasted verbatim. Also checked by hand with `ghapi.sh` in that
pass: `hadolint/hadolint` 12502 stars, pushed 2026-10-19, GPL-3.0 (used as a lint binary only);
`GoogleContainerTools/distroless` 23178 stars, pushed 2026-10-29, Apache-2.0.

```
yaml.safe_load(agent frontmatter): OK, keys=['description', 'mcpServers', 'model', 'name', 'skills']
  invalid keys: none; name=go-engineer; model=inherit; skills=['go-engineering']; tools omitted=True
  mcpServers: ['github', 'context7:http', 'gopls:stdio', 'pkg-go-dev:stdio']
yaml.safe_load(skill frontmatter): OK, keys=['description', 'name'], name=go-engineering
heading check: 9/9 required headings present, missing=none, in spec order=True
line counts: agent=394 (target 250-500), skill=366 (target 150-400)
ALL-CAPS MUST/NEVER/ALWAYS occurrences: 0
ghapi repos/GoogleContainerTools/distroless: OK stars=23178 pushed_at=2026-10-29T09:43:31Z archived=False
ghapi repos/VoltAgent/awesome-claude-code-subagents: OK stars=26164 pushed_at=2026-10-11T08:20:37Z archived=False
ghapi repos/actions/setup-go: OK stars=1767 pushed_at=2026-10-17T10:15:43Z archived=False
ghapi repos/bufbuild/buf: OK stars=11508 pushed_at=2026-10-27T05:31:35Z archived=False
ghapi repos/dominikh/go-tools: OK stars=6920 pushed_at=2026-10-24T22:50:01Z archived=False
ghapi repos/github/github-mcp-server: OK stars=34054 pushed_at=2026-10-29T05:42:25Z archived=False
ghapi repos/go-delve/delve: OK stars=24955 pushed_at=2026-10-21T21:16:26Z archived=False
ghapi repos/golang/tools: OK stars=8011 pushed_at=2026-10-28T18:27:01Z archived=False
ghapi repos/golangci/golangci-lint: OK stars=19475 pushed_at=2026-10-27T20:39:39Z archived=False
ghapi repos/google/go-cmp: OK stars=4682 pushed_at=2026-10-29T01:02:50Z archived=False
ghapi repos/google/styleguide: OK stars=39773 pushed_at=2026-10-29T03:08:02Z archived=False
ghapi repos/google/uuid: OK stars=6152 pushed_at=2024-11-14T17:05:06Z archived=False
ghapi repos/goreleaser/goreleaser: OK stars=16127 pushed_at=2026-10-28T06:22:24Z archived=False
ghapi repos/gotestyourself/gotestsum: OK stars=2735 pushed_at=2026-04-15T00:47:43Z archived=False
ghapi repos/hadolint/hadolint: OK stars=12502 pushed_at=2026-10-19T12:12:51Z archived=False
ghapi repos/mrjoshuak/godoc-mcp: OK stars=126 pushed_at=2026-03-06T17:15:24Z archived=False
ghapi repos/mvdan/gofumpt: OK stars=4103 pushed_at=2026-10-12T13:04:15Z archived=False
ghapi repos/rhysd/actionlint: OK stars=4365 pushed_at=2026-07-16T06:05:57Z archived=False
ghapi repos/samber/cc-skills-golang: OK stars=3720 pushed_at=2026-10-23T07:50:53Z archived=False
ghapi repos/samber/go-pkggodev-client: OK stars=3 pushed_at=2026-08-08T01:02:59Z archived=False
ghapi repos/samber/godig: OK stars=21 pushed_at=2026-10-18T22:42:40Z archived=False
ghapi repos/securego/gosec: OK stars=8990 pushed_at=2026-10-28T12:41:31Z archived=False
ghapi repos/sqlc-dev/sqlc: OK stars=18419 pushed_at=2026-10-26T10:14:20Z archived=False
ghapi repos/uber-go/guide: OK stars=17756 pushed_at=2026-04-15T15:10:48Z archived=False
ghapi repos/upstash/context7: OK stars=63883 pushed_at=2026-10-28T20:26:24Z archived=False
ghapi repos/vektra/mockery: OK stars=7171 pushed_at=2026-10-28T21:35:20Z archived=False
ghapi repos/wshobson/agents: OK stars=41969 pushed_at=2026-10-26T01:08:14Z archived=False
GET https://code.claude.com/docs/en/sub-agents.md: 200
GET https://go.dev/dl/?mode=json: 200
GET https://go.dev/doc/devel/release: 200
GET https://go.dev/doc/go1.23: 200
GET https://go.dev/doc/go1.24: 200
GET https://go.dev/doc/go1.25: 200
GET https://go.dev/doc/go1.26: 200
GET https://go.dev/doc/go1.27: 200
GET https://go.dev/doc/toolchain: 200
GET https://go.dev/ref/mod: 200
POST initialize https://godig.samber.dev/mcp: 200
GET https://golangci-lint.run/install.sh: 200
GET https://hub.docker.com/v2/repositories/library/golang/tags/1.27.3-trixie: 200
POST initialize https://mcp.context7.com/mcp: 200
GET https://pkg.go.dev/uuid@go1.27.3: 200
GET https://raw.githubusercontent.com/GoogleContainerTools/distroless/main/base/README.md: 200
GET https://raw.githubusercontent.com/actions/setup-go/v7.0.0/docs/advanced-usage.md: 200
GET https://raw.githubusercontent.com/golang/perf/master/cmd/benchstat/main.go: 200
GET https://raw.githubusercontent.com/golang/tools/master/go/analysis/passes/modernize/doc.go: 200
GET https://raw.githubusercontent.com/golang/tools/master/gopls/doc/features/mcp.md: 200
GET https://raw.githubusercontent.com/golang/vuln/master/cmd/govulncheck/doc.go: 200
GET https://raw.githubusercontent.com/golangci/golangci-lint/main/.golangci.reference.yml: 200
GET https://vuln.go.dev: 200
```
