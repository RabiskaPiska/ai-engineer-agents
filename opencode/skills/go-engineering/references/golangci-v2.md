# golangci-lint v2 configuration (vetted 2026-10-29)

Validated with `golangci-lint config verify` (exit 0) and run with golangci-lint 2.14.0 on a sample
module built with go1.27.3; the latest release is v2.15.0 (2026-10-16). Against a file seeded with
defects it reported: `bodyclose` (unclosed response body), `noctx` (`http.Get` without context),
`errorlint` (`err == io.EOF`), `gosec` G107/G114 (variable URL, server without timeouts), and
`modernize`/`intrange` (`interface{}`, 3-clause loop). On clean code it printed `0 issues.`.

The v2 schema differs from v1: `version: "2"` is required, formatters live under `formatters:`,
`linters.default` replaces `disable-all`/`enable-all`, and exclusions live under
`linters.exclusions`. Convert an old file with `golangci-lint migrate`.

Replace `example.com/sample` with your module path.

```yaml
version: "2"

run:
  timeout: 5m
  tests: true

linters:
  default: standard        # errcheck, govet, ineffassign, staticcheck, unused
  enable:
    - bodyclose
    - contextcheck
    - copyloopvar
    - errorlint
    - errname
    - exhaustive
    - fatcontext
    - forcetypeassert
    - gocritic
    - gosec
    - intrange
    - modernize
    - nilerr
    - nilnesserr
    - noctx
    - nolintlint
    - perfsprint
    - recvcheck
    - revive
    - rowserrcheck
    - sloglint
    - sqlclosecheck
    - testifylint
    - thelper
    - unconvert
    - unparam
    - usestdlibvars
    - usetesting
    - wastedassign
  settings:
    govet:
      enable-all: true
      disable:
        - fieldalignment   # noisy; enable only for hot structs
    nolintlint:
      require-explanation: true
      require-specific: true
    revive:
      rules:
        - name: exported
        - name: context-as-argument
        - name: error-return
        - name: error-strings
        - name: receiver-naming
        - name: var-naming
  exclusions:
    generated: strict
    presets:
      - std-error-handling
    rules:
      - path: _test\.go
        linters:
          - gosec
          - forcetypeassert

formatters:
  enable:
    - gofumpt
    - goimports
  settings:
    goimports:
      local-prefixes:
        - example.com/sample

issues:
  max-issues-per-linter: 0
  max-same-issues: 0
  uniq-by-line: false
```

Why these linters (beyond the `standard` set of errcheck, govet, ineffassign, staticcheck, unused):

| Linter | Catches | Rule |
|---|---|---|
| bodyclose, sqlclosecheck, rowserrcheck | leaked HTTP bodies, SQL rows/statements, unchecked `rows.Err()` | GO-DATA-2, GO-SEC-5 |
| noctx, contextcheck, fatcontext | requests without context, broken context chains, contexts growing in loops | GO-CTX-1..2 |
| errorlint, nilerr, nilnesserr, errname | `==` on wrapped errors, returning nil after an error check, naming | GO-ERR-2, GO-ERR-4 |
| gosec | injection, weak crypto, missing server timeouts, file permissions | GO-SEC |
| modernize, intrange, copyloopvar, usestdlibvars | pre-1.22 idioms, constants already in the stdlib | GO-MOD-6 |
| exhaustive, forcetypeassert, recvcheck | missing enum cases, unchecked type assertions, mixed receivers | GO-API-10 |
| perfsprint, unconvert, wastedassign | needless `fmt`, conversions and assignments | GO-PERF-4 |
| testifylint, thelper, usetesting | testify misuse, helpers without `t.Helper()`, `os.MkdirTemp` instead of `t.TempDir()` | GO-TEST |
| sloglint | inconsistent slog key/value style, `slog.DiscardHandler` hints | logging |
| nolintlint | bare `//nolint` or a missing reason | process |
| revive, gocritic, unparam | doc comments on exports, error strings, receiver names, unused params | GO-API-7 |

Settings worth knowing:

- `issues.uniq-by-line: false` is deliberate: the default (`true`) printed only the `gosec` finding
  on a line that also had `bodyclose` and `noctx` findings.
- `max-issues-per-linter: 0` and `max-same-issues: 0` stop the default caps (50 and 3) from hiding
  findings.
- On a legacy codebase add `issues.new-from-merge-base: main` so only new code is gated, then burn
  down the backlog separately.
- `linters.exclusions.generated: strict` only skips files with the standard
  `// Code generated ... DO NOT EDIT.` header.
- Install the pinned binary, not via `go install`:
  `curl -sSfL https://golangci-lint.run/install.sh | sh -s -- -b $(go env GOPATH)/bin v2.15.0`.
