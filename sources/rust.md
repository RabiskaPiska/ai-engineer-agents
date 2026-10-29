# Sources: Rust (slug `rust`)

Provenance for `claude/agents/rust-engineer.md`, `skills/rust-engineering/SKILL.md` and
`skills/rust-engineering/references/*.md`. All facts fetched or executed on **2026-10-29**.
Mined repositories were read as text only; no code or install step from them was run.

## 1. GitHub repositories used (exactly 5)

Each verified with `ghapi.sh repos/<owner>/<repo>`; the JSON fields used are pasted verbatim.

### 1. morganlinton/BeautifulRust

```json
{"full_name": "morganlinton/BeautifulRust", "html_url": "https://github.com/morganlinton/BeautifulRust", "stargazers_count": 1383, "pushed_at": "2026-10-28T15:41:26Z", "license": "MIT", "archived": false, "default_branch": "main"}
```

Read: `skills/rust-best-practices/SKILL.md`, `lints/lints.toml`, `lints/clippy.toml`.
Took (MIT, adapted with attribution): the `[lints]` table shape (groups at `priority = -1`, then
`unwrap_used`, `allow_attributes_without_reason`, `undocumented_unsafe_blocks`, `print_stdout`,
`as_conversions`, `clone_on_ref_ptr` ...), the `clippy.toml` keys (`max-fn-params-bools = 0`,
`allow-unwrap-in-tests`), the "don't clone to satisfy the borrow checker" ladder, the no-bool-params
rule, the `Send` compile-time assertion idiom, and the refactoring guidance. Our lint table was then
re-verified by running clippy 0.1.99 on a scratch workspace.

### 2. microsoft/rust-guidelines (Pragmatic Rust Guidelines)

```json
{"full_name": "microsoft/rust-guidelines", "html_url": "https://github.com/microsoft/rust-guidelines", "stargazers_count": 221, "pushed_at": "2026-10-28T22:54:48Z", "license": "MIT", "archived": false, "default_branch": "main"}
```

Read: `src/guidelines/checklist/README.md`, `apps/M-APP-ERROR.md`, `apps/M-MIMALLOC-APPS.md`,
`ai/M-DESIGN-FOR-AI.md`, `ai/M-TAUTOLOGICAL-TESTS.md`, `correctness/M-PANIC-ON-BUG.md`,
`correctness/M-UNSAFE.md`, `libs/interop/M-TYPES-SEND.md`.
Took: panic-means-stop and panic-on-detected-bug policy; the three valid reasons for `unsafe` and
the "no ad-hoc transmute / unsafe impl Send" rule; apps-may-use-anyhow-but-only-one-app-error-type;
mimalloc for apps (we require a benchmark first); types-are-Send; services-are-Clone; no
tautological tests; design-for-AI (strong types, docs, testable APIs).

### 3. apollographql/rust-best-practices

```json
{"full_name": "apollographql/rust-best-practices", "html_url": "https://github.com/apollographql/rust-best-practices", "stargazers_count": 165, "pushed_at": "2026-10-15T17:36:18Z", "license": "Apache-2.0", "archived": false, "default_branch": "main"}
```

Read: `AGENTS.md`, `.codex/rules/rust_programming.md`, `book/chapter_05.md` (testing).
Took (Apache-2.0, paraphrased): the three-command minimum gate (`fmt --check`, clippy
`--all-targets --all-features --locked -D warnings`, `test --workspace --all-features`), test naming
as behaviour sentences with one behaviour per test, `_or_else` lazy defaults, static-vs-dynamic
dispatch guidance, type-state only when it pays, `TODO(issue #NNN)` policy, and the "measured
performance claims only" review trigger.

### 4. leonardomso/rust-skills

```json
{"full_name": "leonardomso/rust-skills", "html_url": "https://github.com/leonardomso/rust-skills", "stargazers_count": 654, "pushed_at": "2026-06-14T22:51:13Z", "license": "MIT", "archived": false, "default_branch": "master"}
```

Read: `SKILL.md` (265 rules in 26 categories, "current for Rust 1.96 (2024 edition)").
Took: category coverage used as a completeness checklist for our catalog (async channels by purpose,
`JoinSet`, `CancellationToken`, cancel safety in `select!`, `AsyncFn` bounds, edition-2024
`unsafe extern` / `#[unsafe(no_mangle)]`, `MaybeUninit`, numeric `checked_*`/`TryFrom`, serde
`deny_unknown_fields`/`try_from`, observability rules, `proj-msrv-declare`). Rejected its
`#![deny(clippy::correctness)]` source-attribute style (we configure lints in Cargo.toml) and
`proj-prelude-module` (conflicts with Microsoft M-NO-PRELUDE and BeautifulRust).

### 5. rust-lang/rust-clippy

```json
{"full_name": "rust-lang/rust-clippy", "html_url": "https://github.com/rust-lang/rust-clippy", "stargazers_count": 13599, "pushed_at": "2026-10-28T19:44:03Z", "license": "Apache-2.0", "archived": false, "default_branch": "main"}
```

Read: `CHANGELOG.md` sections "Rust 1.95" to "Rust 1.99".
Took: confirmation that the lints we enable exist in 0.1.99 and recent additions/moves (e.g.
`for_unbounded_range`, `by_ref_peekable_peek` in `suspicious`; `from_iter_instead_of_collect`
deprecated; `empty_enums` moved to `nursery`), which shaped the lint table and the "don't silence,
fix" guidance.

**Read but not counted:** VoltAgent/awesome-claude-code-subagents `rust-engineer.md` (MIT, 26,164
stars) and wshobson/agents `rust-async-patterns` skill (MIT): both used as a baseline to beat.
VoltAgent's targets Rust 2021 edition and lists async-std, which is deprecated (crates.io
description "Deprecated in favor of `smol`"). actionbook/rust-skills (1,553 stars) has no license,
so it was not mined.

## 2. MCP servers declared in the agent (verified)

| Server | Repo JSON (ghapi) | crates.io | Install (from README) | Status |
|---|---|---|---|---|
| github | already configured on this box (`claude mcp list`: `github: https://api.githubcopilot.com/mcp/ (HTTP) - Connected`) | n/a | by name | connected |
| context7 | n/a | n/a | `type: http`, `url: https://mcp.context7.com/mcp` | live `initialize` POST returned `serverInfo.name = "Context7"`, version 4.4.3 |
| rust-analyzer-mcp (https://github.com/zeenix/rust-analyzer-mcp) | `{"full_name": "zeenix/rust-analyzer-mcp", "stargazers_count": 86, "pushed_at": "2026-09-15T17:14:45Z", "license": "MIT", "archived": false}` | 0.4.0 (updated 2026-08-22) | `cargo install rust-analyzer-mcp`; needs `rustup component add rust-analyzer`; `.mcp.json` `{"command": "rust-analyzer-mcp"}` | README read; not executed `[UNVERIFIED as a run]` |
| rust-mcp-server (https://github.com/Vaiz/rust-mcp-server) | `{"full_name": "Vaiz/rust-mcp-server", "stargazers_count": 37, "pushed_at": "2026-09-06T10:22:27Z", "license": "Unlicense", "archived": false}` | 0.4.1 (updated 2026-08-01) | `cargo install rust-mcp-server`; stdio by default, `--workspace <path>` optional | README read; not executed `[UNVERIFIED as a run]` |

Considered and not declared: Govcraft/rust-docs-mcp-server (300 stars, last push 2025-11-24, not
pushed in 2026); mmgeorge/docs-mcp (docs.rs rustdoc JSON, MIT, pushed 2026-09-27, but 5 stars and
106 crates.io downloads, too immature); KingingWang/crates-docs (14 stars). context7 covers crate
docs instead.

## 3. Official version sources (fetched 2026-10-29)

| Fact | Source |
|---|---|
| Rust 1.99.1, 2026-10-15; 1.99.0, 2026-10-01 | https://blog.rust-lang.org/2026/10/15/Rust-1.99.1/ , https://blog.rust-lang.org/2026/10/01/Rust-1.99.0/ |
| Channel manifest: rust 1.99.1 (58cf8f9c3 2026-10-13), cargo 0.100.0, clippy 0.1.99, rustfmt 1.10.0 | https://static.rust-lang.org/dist/channel-rust-stable.toml (date = "2026-10-15") |
| 1.98.0 (2026-08-20), 1.97.0 (2026-07-09), 1.96.0 (2026-05-28), 1.95.0 (2026-04-16), 1.94.0 (2026-03-05), 1.93.0, 1.92.0, 1.91.0, 1.90.0 feature notes | https://blog.rust-lang.org/releases/ and each linked post |
| 1.80 LazyLock, 1.81 lint reasons, 1.85 edition 2024 + async closures, 1.88 let chains | https://blog.rust-lang.org/2024/07/25/Rust-1.80.0/ , /2024/09/05/Rust-1.81.0/ , /2025/02/20/Rust-1.85.0/ , /2025/06/26/Rust-1.88.0/ |
| `OnceLock` since 1.70.0, `LazyLock` since 1.80.0 | https://doc.rust-lang.org/std/sync/struct.OnceLock.html , https://doc.rust-lang.org/std/sync/struct.LazyLock.html |
| Edition 2024 is the latest edition (chapters incl. newly unsafe functions, MSRV-aware resolver) | https://github.com/rust-lang/edition-guide/blob/master/src/SUMMARY.md , https://doc.rust-lang.org/edition-guide/ |
| Cargo 1.95-1.99 changes (build.warnings, CI disables incremental, debug profile, default-features override); Cargo 1.100 dated 2026-11-12 | https://doc.rust-lang.org/nightly/cargo/CHANGELOG.html |
| rustup 1.29.2, 2026-10-20 | https://blog.rust-lang.org/2026/10/20/Rustup-1.29.2/ |
| `rustup toolchain install` with no args installs the active toolchain | https://github.com/rust-lang/rustup/blob/main/CHANGELOG.md |
| i686 Windows demotion in 1.100 | https://blog.rust-lang.org/2026/10/02/demoting-i686-windows-targets-to-std-only/ |
| Security: arrayref compromise, targeted attacks, Miri env leak, CVE-2026-33056 | https://blog.rust-lang.org/2026/08/20/supply-chain-attack-on-arrayref/ , /2026/09/17/targeted-attacks/ , /2026/09/21/github-actions-leaking-secrets-when-miri-output-is-cached/ , /2026/03/21/cve-2026-33056/ |
| Sanitizer invocation | https://doc.rust-lang.org/beta/unstable-book/compiler-flags/sanitizer.html |
| `debug = "line-tables-only"` profile value | https://doc.rust-lang.org/cargo/reference/profiles.html |
| Cargo.lock guidance | https://doc.rust-lang.org/cargo/faq.html |
| nextest: doctests unsupported, run `cargo test --doc`; `cargo miri nextest run` | https://nexte.st/ , https://nexte.st/docs/integrations/miri/ |
| tokio 1.54.1, MSRV 1.85, LTS 1.51.x (to 2027-03) and 1.53.x (to 2027-09) | https://crates.io/api/v1/crates/tokio , https://github.com/tokio-rs/tokio/blob/master/README.md |
| tokio `select!` cancellation-safety list | https://docs.rs/tokio/1.54.1/tokio/macro.select.html |
| tower-http 0.7.1 `TimeoutLayer::with_status_code`, `CatchPanicLayer`; axum 0.8.9 `/{key}` captures, `DefaultBodyLimit`, `Serve::with_graceful_shutdown`; tokio-util `TaskTracker` | https://docs.rs/tower-http/0.7.1/tower_http/timeout/index.html , https://docs.rs/axum/0.8.9/axum/routing/struct.Router.html , https://docs.rs/axum/0.8.9/axum/serve/struct.Serve.html , https://docs.rs/tokio-util/0.7.20/tokio_util/task/task_tracker/struct.TaskTracker.html |
| sqlx `query!` needs `DATABASE_URL` or `.sqlx` offline data; sqlx 0.9.0 features | https://docs.rs/sqlx/0.9.0/sqlx/macro.query.html , https://crates.io/api/v1/crates/sqlx/0.9.0 |
| console-subscriber needs `tokio_unstable` | https://docs.rs/console-subscriber/0.5.0/console_subscriber/ |
| Tool CLI flags (llvm-cov `--fail-under-lines`, hack `--rust-version`/`--feature-powerset`, mutants `--in-diff`, deny `check`) | READMEs of taiki-e/cargo-llvm-cov, taiki-e/cargo-hack, sourcefrog/cargo-mutants (https://mutants.rs/in-diff.html), EmbarkStudios/cargo-deny |
| Crate versions in the baseline table | crates.io API `https://crates.io/api/v1/crates/<name>` (queried 2026-10-29) and GitHub releases API for serde, thiserror, anyhow, clap, rust-analyzer, dist |
| Claude Code subagent frontmatter, nested subagents (3 levels) | https://code.claude.com/docs/en/sub-agents.md |

## 4. Executed verification (this session)

Toolchain installed from the official, checksum-verified `rustup-init`
(`5be191e8...ec24f4`, matched `rustup-init.sha256`) into the scratchpad:

```
rustc 1.99.1 (58cf8f9c3 2026-10-13)
cargo 1.99.1 (5f94df478 2026-08-27)
clippy 0.1.99 (58cf8f9c35 2026-10-13)
rustup 1.29.2 (d8c92c676 2026-10-21)
cargo-nextest 0.9.150 (d225b1daf 2026-10-26)
cargo-deny 0.20.2
```

Scratch workspace = exactly the files in `references/project-templates.md` and
`references/service-skeleton.md`:

```
cargo generate-lockfile        -> Locking 109 packages to highest Rust 1.94 compatible versions
cargo fmt --all --check        -> exit 0 (after one cargo fmt; the first run correctly failed with "Diff in ...")
cargo clippy --workspace --all-targets --all-features --locked -- -D warnings
                               -> Finished `dev` profile ... (0 warnings, clippy::pedantic on)
cargo nextest run --workspace --all-features --locked
                               -> Summary [0.079s] 5 tests run: 5 passed, 0 skipped
cargo test --doc               -> test result: ok. 0 passed; 0 failed
RUSTDOCFLAGS="-D warnings" cargo doc --workspace --no-deps --all-features --locked -> Generated .../doc/api/index.html
cargo deny check               -> advisories ok, bans ok, licenses ok, sources ok (exit 0)
CARGO_BUILD_WARNINGS=deny cargo clippy (with an injected unused variable)
                               -> error: warnings are denied by `build.warnings` configuration (exit 101); clean: exit 0
live run: GET /healthz 204; POST /orders/ABC-1 {"quantity":3} 201; {"quantity":0} 422;
          SKU "bad" 422; 70 KB body 413; SIGINT exit 0; SIGTERM exit 0, "shutdown complete" logged
.github/workflows/ci.yml       -> yaml.safe_load OK, jobs: ['check', 'miri'] (not run on GitHub)
```

Not executed: Miri, sanitizers, loom, fuzzing, cargo-mutants, cargo-semver-checks, cargo-hack,
cargo-llvm-cov, cargo-audit, samply (commands taken from official docs/READMEs) `[UNVERIFIED as runs]`.

## 5. Self-check block

```
$ python3 -I selfcheck.py
agent yaml.safe_load: OK keys= ['name', 'description', 'model', 'skills', 'mcpServers'] invalid= []
agent mcpServers = ['github', {'context7': {'type': 'http', 'url': 'https://mcp.context7.com/mcp'}}, {'rust-analyzer': {'type': 'stdio', 'command': 'rust-analyzer-mcp'}}, {'rust-mcp-server': {'type': 'stdio', 'command': 'rust-mcp-server'}}]
skill yaml.safe_load: OK name= rust-engineering desc_len= 481
headings present: 9 / 9 missing= [] in_order= True
agent lines= 433 skill lines= 340
tools field omitted: True | shouting MUST count: 0
```

## 6. Link check (2026-10-29)

Every `https://` URL in the four deliverable files was extracted (`grep -ohE`) and checked: GitHub
repo URLs with `ghapi.sh repos/<owner>/<repo>`, everything else with `curl -L -w '%{http_code}'`.

```
ghapi-ok  github.com/morganlinton/BeautifulRust, microsoft/rust-guidelines, apollographql/rust-best-practices,
          leonardomso/rust-skills, rust-lang/rust-clippy, rust-lang/crates.io-index,
          zeenix/rust-analyzer-mcp, Vaiz/rust-mcp-server
200       blog.rust-lang.org: releases/, 2026/10/15/Rust-1.99.1, 2026/10/01/Rust-1.99.0, 2026/10/20/Rustup-1.29.2,
          2026/10/02/demoting-i686..., 2026/08/20/supply-chain-attack-on-arrayref, 2026/09/17/targeted-attacks,
          2026/09/21/github-actions-leaking-secrets-..., 2026/03/21/cve-2026-33056, 2024/07/25/Rust-1.80.0,
          2024/09/05/Rust-1.81.0, 2025/02/20/Rust-1.85.0, 2025/06/26/Rust-1.88.0
200       static.rust-lang.org/dist/channel-rust-stable.toml
200       doc.rust-lang.org: edition-guide/, nightly/cargo/CHANGELOG.html, cargo/faq.html, cargo/reference/profiles.html,
          std/sync/struct.LazyLock.html, std/sync/struct.OnceLock.html, beta/unstable-book/compiler-flags/sanitizer.html
200       github.com/rust-lang/edition-guide/blob/master/src/SUMMARY.md, rust-lang/rustup/blob/main/CHANGELOG.md,
          tokio-rs/tokio/blob/master/README.md
200       docs.rs: axum 0.8.9 Router + Serve, tower-http 0.7.1 timeout, tokio 1.54.1 select!, tokio-util 0.7.20 TaskTracker,
          sqlx 0.9.0 query!, console-subscriber 0.5.0
200       crates.io/api/v1/crates/tokio (needs a User-Agent), crates.io/api/v1/crates/sqlx/0.9.0
200       nexte.st/, nexte.st/docs/integrations/miri/, mutants.rs/in-diff.html, code.claude.com/docs/en/sub-agents.md
MCP       mcp.context7.com/mcp: JSON-RPC initialize -> serverInfo.name "Context7" 4.4.3
401       api.githubcopilot.com/mcp/ (expected: requires auth; the configured server reports Connected)
n/a       https://crates.io/api/v1/crates/<name> is a URL pattern, not a link
```

Result: 0 broken links.
