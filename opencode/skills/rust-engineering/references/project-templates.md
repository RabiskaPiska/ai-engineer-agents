# Project templates (verified 2026-10-29 on Rust 1.99.1)

These files were written into a scratch workspace and checked with the real toolchain:
`cargo generate-lockfile` (MSRV-aware resolution to Rust 1.94), `cargo fmt --all --check`,
`cargo clippy --workspace --all-targets --all-features --locked -- -D warnings` (clean with
`clippy::pedantic`), `cargo nextest run` (5 passed), `RUSTDOCFLAGS="-D warnings" cargo doc`, and
`cargo deny check` with cargo-deny 0.20.2 (`advisories ok, bans ok, licenses ok, sources ok`).
`CARGO_BUILD_WARNINGS=deny` was confirmed to fail the build on a warning
(`error: warnings are denied by build.warnings configuration`). The CI workflow was parsed with
`yaml.safe_load` but not executed on GitHub Actions `[UNVERIFIED as a run]`.

Adjust versions to the newest compatible releases when you start a project; these were current on
2026-10-29.

## Workspace `Cargo.toml`

Lint table adapted from BeautifulRust `lints/lints.toml` (MIT) and Microsoft Pragmatic Rust
Guidelines (MIT). `unsafe_code = "forbid"` suits crates without unsafe; switch to `"deny"` plus a
scoped `#[expect(unsafe_code, reason = "...")]` where unsafe is required.

```toml
[workspace]
resolver = "3"
members = ["crates/*"]

[workspace.package]
edition = "2024"
rust-version = "1.94"
license = "MIT OR Apache-2.0"
publish = false

[workspace.dependencies]
anyhow = "1.0.104"
axum = "0.8.9"
serde = { version = "1.0.229", features = ["derive"] }
serde_json = "1.0.154"
thiserror = "2.0.21"
tokio = { version = "1.54.1", features = ["macros", "rt-multi-thread", "net", "signal", "time"] }
tokio-util = { version = "0.7.20", features = ["rt"] }
tower-http = { version = "0.7.1", features = ["catch-panic", "limit", "timeout", "trace"] }
tracing = "0.1.44"
tracing-subscriber = { version = "0.3.23", features = ["env-filter", "json"] }
proptest = "1.12.0"
orders = { path = "crates/orders" }

[workspace.lints.rust]
unsafe_code = "forbid"
unsafe_op_in_unsafe_fn = "warn"
missing_debug_implementations = "warn"
unreachable_pub = "warn"
rust_2018_idioms = { level = "warn", priority = -1 }
# Declare custom cfgs used by loom/tokio tooling so clippy -D warnings does not fail on unexpected_cfgs.
unexpected_cfgs = { level = "warn", check-cfg = ['cfg(loom)', 'cfg(tokio_unstable)'] }

[workspace.lints.clippy]
all = { level = "warn", priority = -1 }
pedantic = { level = "warn", priority = -1 }
unwrap_used = "warn"
panic_in_result_fn = "warn"
allow_attributes = "warn"
allow_attributes_without_reason = "warn"
undocumented_unsafe_blocks = "warn"
dbg_macro = "warn"
todo = "warn"
print_stdout = "warn"
print_stderr = "warn"
as_conversions = "warn"
clone_on_ref_ptr = "warn"
redundant_clone = "warn"
large_futures = "warn"
module_name_repetitions = "allow"
must_use_candidate = "allow"
missing_errors_doc = "allow"

[profile.release]
lto = "thin"
codegen-units = 1
debug = "line-tables-only"

[profile.profiling]
inherits = "release"
debug = true
```

Member crate:

```toml
[package]
name = "orders"
version = "0.1.0"
edition.workspace = true
rust-version.workspace = true
license.workspace = true
publish.workspace = true

[dependencies]
serde.workspace = true
thiserror.workspace = true

[dev-dependencies]
proptest.workspace = true

[lints]
workspace = true
```

## `rust-toolchain.toml` (applications)

```toml
[toolchain]
channel = "1.99.1"
components = ["rustfmt", "clippy"]
profile = "minimal"
```

## `clippy.toml`

```toml
allow-unwrap-in-tests = true
allow-expect-in-tests = true
allow-print-in-tests = true
max-fn-params-bools = 0
```

## `rustfmt.toml`

```toml
style_edition = "2024"
```

## `deny.toml` (cargo-deny 0.20)

`cargo deny check` warns `license-not-encountered` for allowed licenses no dependency uses; trim
the list to what you need or accept the warnings.

```toml
# cargo-deny 0.20 policy. Run: cargo deny check
[graph]
all-features = true

[advisories]
# RustSec database; vulnerable and unmaintained crates fail the check.
unmaintained = "workspace"
yanked = "deny"
ignore = [
    # { id = "RUSTSEC-YYYY-NNNN", reason = "no fix yet; not reachable because ...; revisit by YYYY-MM-DD" },
]

[licenses]
allow = [
    "MIT",
    "Apache-2.0",
    "Apache-2.0 WITH LLVM-exception",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "Unicode-3.0",
    "Zlib",
]
confidence-threshold = 0.9

[bans]
multiple-versions = "warn"
wildcards = "deny"
allow-wildcard-paths = true
deny = [
    { crate = "openssl", reason = "use rustls" },
]

[sources]
unknown-registry = "deny"
unknown-git = "deny"
allow-registry = ["https://github.com/rust-lang/crates.io-index"]
```

## `.github/workflows/ci.yml`

Action majors checked on 2026-10-29: actions/checkout v7.0.1, Swatinem/rust-cache v2.9.3,
taiki-e/install-action v2.88.0. In high-assurance repositories pin each action to a full commit SHA.
`rustup toolchain install` with no arguments installs the toolchain named in
`rust-toolchain.toml` (rustup >= 1.28).

```yaml
name: ci
on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

env:
  CARGO_TERM_COLOR: always
  CARGO_BUILD_WARNINGS: deny   # Rust 1.97+: deny warnings without invalidating the cache

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - run: rustup toolchain install          # installs the channel pinned in rust-toolchain.toml
      - uses: Swatinem/rust-cache@v2            # no secrets in this job, so caching target/ is safe
      - uses: taiki-e/install-action@v2
        with:
          tool: cargo-nextest,cargo-deny,cargo-llvm-cov,cargo-hack
      - run: cargo fmt --all --check
      - run: cargo clippy --workspace --all-targets --all-features --locked
      - run: cargo nextest run --workspace --all-features --locked
      - run: cargo test --workspace --all-features --doc --locked
      - run: cargo deny check
      - run: cargo hack check --workspace --feature-powerset --no-dev-deps --locked
      - run: cargo llvm-cov nextest --workspace --all-features --locked --fail-under-lines 80

  miri:
    # Only for crates that contain unsafe code (list them with -p). No secrets and no cache: see the
    # Rust Security Response advisory of 2026-09-21 on Miri persisting the environment.
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - run: rustup toolchain install nightly --component miri
      # proptest calls getcwd, which Miri isolation rejects: disable isolation and cap cases.
      - run: cargo +nightly miri test -p <unsafe-crate>
        env:
          MIRIFLAGS: -Zmiri-disable-isolation
          PROPTEST_CASES: "8"
```

## Optional additions

- `.cargo/config.toml` with `[build] rustflags = ["--cfg", "tokio_unstable"]` only in a dev-only
  profile or local config when using tokio-console; never ship it in release builds.
- `[profile.release] panic = "abort"` for CLIs and workers that do not isolate panics; keep unwind
  for servers using tower-http `CatchPanicLayer`.
- `[profile.release] overflow-checks = true` where integer wrap-around would be a security bug.
