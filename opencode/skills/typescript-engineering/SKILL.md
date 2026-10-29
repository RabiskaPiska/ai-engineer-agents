---
name: typescript-engineering
description: "Rule catalog, decision tables, config templates and verification gates for production TypeScript (TypeScript 7.0 / 6.0, Node.js 26 LTS, ESLint 10 + typescript-eslint 8, oxlint, Biome 2, Vitest 5, pnpm 12), current as of October 2026. Use when writing, reviewing, configuring, upgrading or testing TypeScript code, tsconfig.json, package.json exports, eslint.config.*, vitest.config.* or library builds."
---

# TypeScript engineering (October 2026)

This skill is the reference for the `typescript-engineer` agent. Rules carry IDs so reviews can cite them
(for example "violates TS-ASYNC-1"). Each rule says why it exists; when a case is not covered, apply the reason.

Load on demand:
- `references/configs.md`: tested templates for `tsconfig.json`, `eslint.config.mjs`, `vitest.config.ts`,
  `package.json` scripts and library `exports`. Every template was executed on 2026-10-29 (results in
  `sources/typescript.md`).
- `references/ts7-migration.md`: moving a repo from TypeScript 5.x to 6.0 to 7.0, including tools that still
  need the TypeScript 6 API.
- `references/recipes.md`: tested code for the race stress test, benchmark statistics (interleaved runs plus
  Mann-Whitney), symlink-safe path resolution, graceful shutdown, heap-growth checks and the release workflow.

## 1. Detect before you change

Run these first and let the answers pick the branch in every table below.

```bash
node --version                      # runtime floor; compare with package.json#engines
npx tsc --version                   # "Version 7.0.x" = native compiler; 6.x = JS compiler
ls pnpm-lock.yaml package-lock.json yarn.lock bun.lock bun.lockb deno.lock 2>/dev/null
node -p "require('./package.json').type"   # "module" = ESM
ls eslint.config.* biome.json* .oxlintrc.json oxlint.config.ts .prettierrc* 2>/dev/null
```

Use the package manager that owns the lockfile (`npm ci`, `pnpm install --frozen-lockfile`,
`yarn install --immutable`, `bun install --frozen-lockfile`). Never add a second lockfile.

## 2. Decision tables

### 2.1 Module settings by where the code runs

| Code is executed by | `module` | `moduleResolution` | Relative import style | Notes |
|---|---|---|---|---|
| Node.js directly (services, CLIs) | `nodenext` | `nodenext` | `./x.js`, or `./x.ts` with `rewriteRelativeImportExtensions` | `"type": "module"` in package.json |
| Node type stripping (no build step) | `nodenext` | `nodenext` | `./x.ts` | `erasableSyntaxOnly`, `verbatimModuleSyntax`, `noEmit` or `rewriteRelativeImportExtensions` |
| A bundler (Vite, Rolldown, esbuild, Next.js) | `preserve` or `esnext` | `bundler` | extensionless allowed | The bundler, not tsc, emits JS |
| Published library | `nodenext` | `nodenext` | `./x.js` | Build with tsdown or `tsc`, then `publint` + `attw --pack . --profile esm-only` (drop the profile only for dual CJS/ESM) |
| Bun / Deno | `preserve` / per runtime docs | `bundler` | `./x.ts` | Both run TS directly; still type-check with `tsc --noEmit` |

### 2.2 Linting with TypeScript 7

TypeScript 7.0 ships no programmatic API (it arrives in 7.1, beta on 2026-10-20), and typescript-eslint
8.72.1 declares `typescript: ">=4.8.4 <6.1.0"`. Pick one row:

| Situation | Setup | Gate |
|---|---|---|
| Want typescript-eslint typed rules (default for existing ESLint repos) | `"typescript": "npm:@typescript/typescript6@^6.0.2"` and `"@typescript/native": "npm:typescript@^7.0.2"` in devDependencies; `npx tsc` is TS 7, `npx tsc6` is TS 6 | `eslint . --max-warnings=0` and `tsc --noEmit` |
| Want speed, no ESLint plugins needed | `oxlint` + `oxlint-tsgolint` (typescript-go based, needs TS 7-clean tsconfig) | `oxlint --type-aware --deny-warnings` |
| One tool for format + lint | Biome 2 with the `types` domain rules (some still nursery) | `biome check .` |
| Vue, Svelte, Astro, MDX, Angular templates | Stay on TypeScript 6.0 for those projects; Volar-based tools need the TS 6 API | `vue-tsc --noEmit` / `svelte-check` |

### 2.3 Test runner

| Situation | Choose |
|---|---|
| New project, any runtime | Vitest 5 (`vitest run`); needs Node >=22.12 and Vite >=6.4 as a peer |
| Existing Jest 30 suite that is green | Keep Jest; migrate only with a reason (speed, ESM pain) |
| Zero-dependency library or script | `node --test` (built in; run `.ts` directly under type stripping) |
| Browser/E2E | Playwright Test 1.64; Vitest Browser Mode for component tests |

## 3. Rule catalog

### Types (TS-TYPE)

- TS-TYPE-1. `strict: true` plus `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`,
  `noImplicitOverride`, `noImplicitReturns`, `noFallthroughCasesInSwitch`,
  `noPropertyAccessFromIndexSignature`. Strict alone lets `arr[i].x` crash at runtime when `i` is out of range.
- TS-TYPE-2. No `any` in new code. Use `unknown` and narrow. Enforced by `no-explicit-any` and the
  `no-unsafe-*` family in `strictTypeChecked`.
- TS-TYPE-3. Discriminated unions for state, with exhaustive handling:

  ```ts
  type Job =
    | { readonly status: "queued" }
    | { readonly status: "running"; readonly startedAt: Temporal.Instant }
    | { readonly status: "failed"; readonly error: string };

  function label(job: Job): string {
    switch (job.status) {
      case "queued": return "Queued";
      case "running": return `Running since ${job.startedAt.toString()}`;
      case "failed": return `Failed: ${job.error}`;
      default: { const unreachable: never = job; return unreachable; }
    }
  }
  ```
  `Temporal` is a runtime global in Node 26 (not in Node 22/24) and is typed only when `lib` includes
  `"esnext"` or `"esnext.temporal"` (TS 6.0+). Without it `tsc` reports `TS2304: Cannot find name 'Temporal'`
  (observed 2026-10-29). On older runtimes use a `Date`-based or polyfilled type instead.
- TS-TYPE-4. `satisfies` for tables and config: `const routes = { home: "/", user: "/u/:id" } as const satisfies Record<string, `/${string}`>;`
- TS-TYPE-5. Branded types come only from a parser:

  ```ts
  declare const brand: unique symbol;
  export type UserId = string & { readonly [brand]: "UserId" };
  export function parseUserId(raw: string): UserId | undefined {
    return /^[0-9a-f-]{36}$/.test(raw) ? (raw as UserId) : undefined; // the only cast, after the check
  }
  ```
- TS-TYPE-6. Explicit return types on exported functions and public methods. It fixes the contract,
  shortens error messages at call sites, and is required by `isolatedDeclarations`.
- TS-TYPE-7. `@ts-expect-error <reason>` instead of `@ts-ignore`: it fails once the error disappears.
- TS-TYPE-8. Type assertions only after a runtime check the compiler cannot follow, with a comment; never
  `as unknown as T`. Non-null `!` only directly after a check in the same scope.
- TS-TYPE-9. Keep type-level code readable: conditional types nested more than two levels, or recursive
  types over user input, belong in a tested utility with `expectTypeOf` tests, not inline in an API.
- TS-TYPE-10. `readonly` arrays and properties in public signatures (`readonly T[]`, `Readonly<T>`) so
  callers know you will not mutate their data.

### Runtime syntax (TS-SYN)

- TS-SYN-1. Write erasable TypeScript only: no `enum`, `const enum`, value-bearing `namespace`,
  parameter properties, `import x = require()`. Turn on `erasableSyntaxOnly`. Reason: Node 22.18+/24/26 run
  `.ts` by stripping types and reject these. `const enum` is not erasable either: it fails `erasableSyntaxOnly`
  (`TS1294`) and Node type stripping (`ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX`). Under `isolatedModules` only
  ambient const enums (declared in `.d.ts`) are errors (`TS2748`); a local `export const enum` still compiles
  there, but transpilers emit it as a normal enum instead of inlining it.
  Replacement for enums:

  ```ts
  export const Role = { Admin: "admin", Member: "member" } as const;
  export type Role = (typeof Role)[keyof typeof Role];
  ```
- TS-SYN-2. `verbatimModuleSyntax: true`: type-only imports must be `import type { X }`. This makes
  elision predictable for every transpiler.
- TS-SYN-3. Decorators: use only TC39 standard decorators (no `experimentalDecorators`) unless a framework
  (NestJS, Angular, TypeORM) requires the legacy form; then keep it confined to that project.

### Modules and packages (TS-MOD)

- TS-MOD-1. ESM-first: `"type": "module"`. Use `.cts` only for files that must be CommonJS.
- TS-MOD-2. Aliases via `package.json#imports`, not `baseUrl` (a hard error in TS 7) or `paths` (Node never
  sees it). Pick the prefix by your runtime floor (`engines.node`):
  - Node >=24.14 or >=25.4 only: `"#/*"` works. Node added `#/` specifiers in v25.4.0 / v24.14.0 and TS
    resolves them from 6.0. Node 22 rejects them with `ERR_INVALID_MODULE_SPECIFIER`.
  - Node 22 floor (or any doubt): use a named prefix such as `"#src/*"`, which every supported Node accepts.
  - Published library or anything built to `dist/`: map to emitted JS (`"#src/*": "./dist/*"`, imported as
    `#src/x.js`). With `rootDir`/`outDir` set, `tsc` maps that back to `src/*.ts` for type-checking, so it
    type-checks before the first build. Never point a published package at `src/*.ts`.
  - Type-stripping app with no build (`noEmit`): `"#src/*": "./src/*"` imported as `#src/x.ts` needs
    `allowImportingTsExtensions`; `rewriteRelativeImportExtensions` reports `TS2877` for non-relative `.ts` imports.
- TS-MOD-3. Library `exports`: put `types` first in each condition, ship `declarationMap`, set `"files"`
  (exclude tests, type tests and benchmarks), and validate with `publint` and
  `attw --pack . --profile esm-only` before every release. Prefer ESM-only; ship dual builds only when a
  supported consumer needs `require` (Node 22.12+ can `require()` ESM), and then run `attw --pack .` with no
  profile so `node10` and `node16 (from CJS)` must pass too.
- TS-MOD-4. No barrel `index.ts` re-exporting subtrees. Several small entry points; enforce internal
  boundaries with dependency-cruiser rules (entry-point-only imports, no cycles) and prove the rule fails
  on a deliberate deep import.
- TS-MOD-5. `types` in tsconfig is explicit (`["node"]`, plus `"vitest/globals"` only if globals are on).
  TS 6/7 default it to `[]`; listing exactly what you use also speeds builds.
- TS-MOD-6. Monorepos: project references with `composite: true` and `tsc -b`; TS 7 can parallelize
  references with `--builders`. Workspace protocol (`workspace:*`) for internal deps.
- TS-MOD-7. Versioning and changelogs come from changesets (`@changesets/cli` 3.x): each PR that changes a
  published package adds a `.changeset/*.md` (`npx changeset`), the release PR runs `npx changeset version`,
  and publishing runs from CI (TS-SEC-9). Hand-edited version numbers drift from the changelog. Use the
  changeset bot or `npx changeset status --since=main` (exit 1 when packages changed without a changeset)
  to catch missing entries.

### Errors (TS-ERR)

- TS-ERR-1. Throw only `Error` instances (lint: `only-throw-error`). Subclass with a stable `code`, pass
  `{ cause }` when wrapping so the original stack survives.
- TS-ERR-2. Expected domain failures are values, not exceptions:

  ```ts
  export type Result<T, E extends string> =
    | { readonly ok: true; readonly value: T }
    | { readonly ok: false; readonly error: E };
  ```
- TS-ERR-3. Validate at trust boundaries with a schema and derive the type from it:

  ```ts
  import { z } from "zod";
  const Env = z.object({ DATABASE_URL: z.url(), PORT: z.coerce.number().int().min(1).max(65535) });
  export type Env = z.infer<typeof Env>;
  export const env: Env = Env.parse(process.env); // fail fast at startup
  ```
- TS-ERR-4. `catch (error: unknown)` (the default with `useUnknownInCatchVariables` under strict); narrow
  before use; never swallow. Log once at the boundary that handles the error, not at every layer.
- TS-ERR-5. Process-level: let unhandled rejections crash the process and restart via the supervisor;
  register `uncaughtException` only to log and exit. Node's default mode has been `throw` since v15: it emits
  `unhandledRejection` and crashes only if no listener exists, so a stray listener silently keeps the process
  alive. `--unhandled-rejections=strict` raises the uncaught exception even when such a listener exists; use it
  when you cannot audit every library's listeners.

### Async and concurrency (TS-ASYNC)

- TS-ASYNC-1. No floating promises (`no-floating-promises`, `no-misused-promises`, `await-thenable`,
  `return-await` in try/catch). A floating promise loses its rejection and its ordering.
- TS-ASYNC-2. Independent awaits run concurrently (`Promise.all`); bounded concurrency for fan-out over
  external resources; `Promise.allSettled` when partial failure is acceptable and reported.
- TS-ASYNC-3. Every network/DB/child-process call takes an `AbortSignal` and a timeout
  (`AbortSignal.timeout(ms)`, `AbortSignal.any([...])`).
- TS-ASYNC-4. Resources are released with `using`/`await using` (`Symbol.dispose`/`Symbol.asyncDispose`) or
  `try/finally`. The TS 7.1 API itself relies on `using` to free Go-side memory.
- TS-ASYNC-5. No read-modify-write of shared state across an `await`; serialize with a queue/mutex or
  move the state into the database with a transaction or conditional update. Prove it with a stress test,
  not a shuffle: run the operation 1000+ times concurrently through a store whose reads and writes yield a
  random 0-3 event-loop turns (seeded PRNG, seed in the test name), then assert the invariant (for example,
  total = number of deposits). Recipe in `references/recipes.md`; it fails on the unserialized version
  (observed `expected 117 to be 2000`) and passes with a per-key lock.
- TS-ASYNC-6. CPU-bound work in `worker_threads`; keep event-loop delay p99 under your latency budget
  (`perf_hooks.monitorEventLoopDelay`).
- TS-ASYNC-7. Tests: always `await expect(p).resolves/rejects` (Vitest 5 fails unawaited async assertions);
  use fake timers (`vi.useFakeTimers()`, which also fakes `Temporal` in Vitest 5) instead of real sleeps.

### Performance (TS-PERF)

- TS-PERF-1. Profile before optimizing: `node --cpu-prof app.js` (open the `.cpuprofile` in Chrome
  DevTools), `node --heap-prof`, `--heapsnapshot-near-heap-limit=2` for OOMs.
- TS-PERF-2. Benchmarks live in `*.bench.ts` and run with `vitest bench`; never benchmark inside unit tests.
  For quick local checks use `bench.compare()` and `toBeFasterThan(other, { delta })`. To accept or reject a
  change, one run is not evidence. The acceptance rule:
  - Run baseline and candidate at least 10 times each, interleaved (alternate the order every round), on the
    same machine, the same pinned Node version, and an otherwise idle CPU. Record `node --version` and the
    CPU model with the result.
  - Each run writes its result with `writeResult` (one JSON file per run; the path must be inside the
    project). The per-run statistic is `latency.mean`; `latency.p50` is quantized by timer resolution for
    sub-microsecond functions.
  - Compare the medians of the per-run means and run a two-sided Mann-Whitney U test. It is a regression only
    when the median slows by more than the agreed threshold (default 5%) and p < 0.05. Smaller or
    non-significant differences are noise, not wins.
  - Commit the baseline result files so reviewers and CI compare against the same reference.
  `scripts/bench-stats.mjs` in `references/recipes.md` implements this; its p-values match
  `scipy.stats.mannwhitneyu` to 5 decimals.
- TS-PERF-3. Hot paths: monomorphic object shapes (initialize all fields in the constructor), no `delete`,
  `Map` for dynamic keys, avoid megamorphic callbacks, stream instead of buffering large bodies.
- TS-PERF-4. Compiler time: explicit `types`, project references, `isolatedDeclarations` for parallel
  `.d.ts` emit, `tsc --extendedDiagnostics` to find regressions; in TS 7 tune `--checkers N` (default 4)
  and keep it fixed across CI machines, since varying it can rarely change order-dependent results.

### Security (TS-SEC)

- TS-SEC-1. Parameterized queries only (tagged-template query builders count; string concatenation does not).
- TS-SEC-2. `execFile`/`spawn` with an argument array; never `exec` or `shell: true` with input.
- TS-SEC-3. Paths from input: resolve with `fs.realpath` on both the root and the target (for a file that
  does not exist yet, the real path of its parent plus the basename), then accept only `real === realRoot` or
  `real.startsWith(realRoot + path.sep)`. A string prefix check alone is fooled by a symlink under the root,
  and `root + path.sep` alone wrongly rejects the root itself. `resolveInside()` in `references/recipes.md`
  is tested against `link/secret.txt`, `link/new.txt`, `../x`, absolute paths, `.` and `""`.
- TS-SEC-4. Prototype pollution: schema-validate before merging; `Map` or `Object.create(null)` for
  input-keyed dictionaries; reject `__proto__`, `constructor`, `prototype` keys.
- TS-SEC-5. SSRF: allow-list outbound hosts for user-supplied URLs; resolve and block private ranges.
- TS-SEC-6. Supply chain: lockfile committed, frozen installs in CI, pnpm 11+ safe defaults
  (`minimumReleaseAge` 1440 minutes, `strictDepBuilds`, `blockExoticSubdeps`), `npm audit --audit-level=high`
  in CI, review install scripts before allowing builds (`pnpm approve-builds` / `allowBuilds`).
- TS-SEC-7. Untrusted-input CLIs and workers can run under the stable Node Permission Model:
  `node --permission --allow-fs-read=./data app.js` (use `--permission-audit` first to see what it needs).
- TS-SEC-8. Never log secrets or full request bodies; redact at the logger (pino `redact`).
- TS-SEC-9. Publishing: publish only from CI through npm trusted publishing (OIDC). It needs npm >=11.5.1 and
  Node >=22.14 (Node 22 bundles npm 10, so use Node 24/26 in the release job), a GitHub-hosted runner, and
  `permissions: id-token: write`. Provenance is then generated automatically for public packages from
  public repos. After the first trusted publish, set the package to "Require two-factor authentication and
  disallow tokens", revoke old automation tokens, and keep 2FA on every maintainer account. Consumers and
  CI verify with `npm audit signatures` (registry signatures plus provenance attestations).
- TS-SEC-10. XSS: render untrusted data only through auto-escaping templates or framework bindings; no
  `innerHTML`, `dangerouslySetInnerHTML` or `v-html` with input unless it passed a sanitizer (DOMPurify).
  Encode for the output context (HTML text, attribute, URL, JS). Ship a Content-Security-Policy without
  `'unsafe-inline'`/`'unsafe-eval'` for scripts (nonces or hashes), set with `helmet` or the framework.
- TS-SEC-11. No dynamic code: no `eval`, `new Function`, or string arguments to `setTimeout`/`setInterval`.
  Enforced by `no-eval`, `no-new-func` and `@typescript-eslint/no-implied-eval` (in `strictTypeChecked`).
- TS-SEC-12. ReDoS: regexes that run on input must not backtrack super-linearly. Lint with
  `eslint-plugin-regexp` (`regexp/no-super-linear-backtracking` is in its recommended config; add
  `regexp/no-super-linear-move` for input-facing code) and cap input length before matching. For
  user-supplied patterns use a linear-time engine (`re2js`, pure JS; `re2` is faster but needs a native
  install script).
- TS-SEC-13. Sessions and auth: session cookies are `HttpOnly`, `Secure`, `SameSite=Lax` (or `Strict`),
  `Path=/`, preferably `__Host-` prefixed, with server-side expiry and rotation on login and privilege change.
  State-changing requests need CSRF protection beyond SameSite: a synchronizer or signed double-submit token,
  or rejecting `Sec-Fetch-Site: cross-site`. JWTs: verify signature, `alg` allow-list, `exp`, `iss`, `aud`;
  never accept `alg: none`; do not keep long-lived JWTs in `localStorage`.
- TS-SEC-14. Abuse controls: rate-limit and size-limit every public endpoint (per IP and per account, stricter
  on login, signup, password reset and expensive queries), set body-size limits on parsers, and return 429
  with `Retry-After`. CORS: an explicit origin allow-list; never reflect `Origin` and never combine `*` with
  credentials.
- TS-SEC-15. Secret scanning: `gitleaks git --redact .` in CI and as a pre-commit hook (gitleaks 8.30.1;
  exit 0 = no leaks, 1 = leaks). Treat a hit as a leaked credential: rotate it, then remove it from history.

### Operations (TS-OPS)

- TS-OPS-1. Graceful shutdown: on `SIGTERM`/`SIGINT` stop accepting connections (`server.close()`), finish
  in-flight requests, close pools and flush telemetry, then exit 0; force-close and exit 1 after a deadline
  shorter than the orchestrator's kill timeout. `server.close()` only drops sockets that are idle at that
  moment, so keep calling `server.closeIdleConnections()` until it completes, or keep-alive clients hold the
  process open (observed: without the sweep the test hit the deadline and exited 1). Tested recipe in
  `references/recipes.md`.
- TS-OPS-2. Logging: structured JSON with pino, one logger per process, child loggers for request context,
  `redact` for secrets, log levels from config. Log once where an error is handled.
- TS-OPS-3. Tracing and metrics: OpenTelemetry. Zero-code start (documented form):
  `NODE_OPTIONS="--require @opentelemetry/auto-instrumentations-node/register"` with `OTEL_SERVICE_NAME`,
  `OTEL_TRACES_EXPORTER=otlp` and `OTEL_EXPORTER_OTLP_ENDPOINT`. Its pino instrumentation adds `trace_id` and
  `span_id` to log records. The 2026-10 SDK line (`@opentelemetry/sdk-node` 0.300.0) needs Node >=22.15.
  For ESM-only apps, confirm spans actually appear; ESM instrumentation is not covered by that doc page.
- TS-OPS-4. Bounded memory: every cache has a bound (`new LRUCache({ max, ttl })` from `lru-cache` 11, never a
  bare `Map` keyed by input), every queue has a maximum length, and every listener has an owner. Remove
  listeners with an `AbortSignal` (`addEventListener(type, fn, { signal })`, `events.on(emitter, name,
  { signal })`, `addAbortListener`) and treat `MaxListenersExceededWarning` as a leak.
- TS-OPS-5. Leak hunting: run the suspect operation in rounds, force GC (`node --expose-gc`, `globalThis.gc()`),
  and compare `process.memoryUsage().heapUsed` after warm-up; steady growth is a leak (observed: an unbounded
  `Map` grew 60.9 MB over 5 rounds, a bounded one 0 MB). Then take two heap snapshots
  (`node --heapsnapshot-signal=SIGUSR2`, or `v8.writeHeapSnapshot()`) before and after the rounds and open the
  second in Chrome DevTools Memory with the "Comparison" view to see which constructors grew.

## 4. Verification gates

Run in this order; stop and fix at the first failure. Capture exit codes without pipes:
`npm run lint > lint.log 2>&1; echo "EXIT=$?"`.

```bash
npx prettier --check .                    # or: npx biome check .
npx eslint . --max-warnings=0             # typed + security rules; or: npx oxlint --type-aware --deny-warnings
npx tsc --noEmit                          # monorepo: npx tsc -b ; low-memory CI: add --singleThreaded or --checkers 1
npx vitest run --coverage                 # thresholds live in vitest.config.ts; includes the race stress tests
npx vitest run --typecheck.only           # *.test-d.ts type tests (if present)
npx vitest run --sequence.shuffle         # order-dependence check (not a race detector); repeat 3x
npx publint && npx attw --pack . --profile esm-only   # libraries only; no --profile for dual CJS/ESM
npx knip                                  # unused files, exports, deps; needs knip.json entries for *.test-d.ts / *.bench.ts
npm audit --audit-level=high              # or: pnpm audit --audit-level high
npm audit signatures                      # registry signatures + provenance of installed packages
gitleaks git --redact .                   # secret scan of the git history
npx playwright test                       # apps with E2E
npx vitest bench                          # performance work: 10+ interleaved runs + scripts/bench-stats.mjs
npx stryker run                           # mutation testing for critical modules (slow; on demand)
```

Release gate (libraries, in the CI publish job): `npm ci`, `npm audit signatures`, `npm run check`,
`npm run build && npm run check:package`, then `npm publish` through trusted publishing (TS-SEC-9); versions
come from `npx changeset version` (TS-MOD-7). Workflow in `references/recipes.md`.

Pass criteria: exit 0 for each; no new warnings; coverage thresholds met (start at lines 80 / branches 75
for an existing codebase and ratchet up; 90+ for new libraries); no type errors in type tests. For
`npm audit --audit-level=high`, exit 0 means no high or critical advisories; the report can still list
lower-severity ones (the flag sets the failure threshold, it does not filter output). For benchmarks, pass
means `bench-stats.mjs` exits 0 (TS-PERF-2).

Prove new gates bite. After adding or changing lint/type config, seed one defect per gate, confirm failure,
then remove it. Expected failures (observed 2026-10-29 with the templates in `references/configs.md`):

| Seeded defect | Gate | Expected failure |
|---|---|---|
| `save();` (unawaited async call) | `eslint` | `@typescript-eslint/no-floating-promises`, exit 1 |
| same | `oxlint --type-aware` | `typescript(no-floating-promises)`, exit 1 |
| `const first = xs[0]; first.length` | `tsc --noEmit` | `TS18048: 'first' is possibly 'undefined'`, exit 1 |
| `export enum Color { Red }` | `tsc --noEmit` | `TS1294 ... not allowed when 'erasableSyntaxOnly' is enabled`, exit 1 |
| `expectTypeOf(fn).returns.toEqualTypeOf<string>()` (wrong) | `vitest run --typecheck.only` | `TypeCheckError`, exit 1 |
| `/^(a+)+$/.test(input)`, `eval(x)`, `new Function(...)`, `setTimeout("code")` | `eslint` | `regexp/no-super-linear-backtracking`, `no-eval`, `no-new-func`, `@typescript-eslint/no-implied-eval`, exit 1 |
| an unreferenced `src/orphan.ts` | `knip` | `Unused files (1) src/orphan.ts`, exit 1 |
| a `ghp_...` token committed in `src/cfg.ts` | `gitleaks git --redact .` | `leaks found: 1`, exit 1 |
| deposits without the per-key lock | race stress test | `expected 117 to be 2000`, exit 1 |
| candidate 3x slower than baseline | `bench-stats.mjs` (10 interleaved runs) | `"verdict":"REGRESSION"`, p = 0.00018, exit 1 |

## 5. Testing patterns

- Co-locate tests (`foo.test.ts` next to `foo.ts`) or mirror under `tests/`; follow the repo.
- Table-driven cases with `test.each`; one behavior per test; name by behavior, not by method.
- Property-based tests (fast-check 4) for parsers, serializers and anything with an inverse
  (`decode(encode(x)) === x`).
- Mock at the process boundary (HTTP with MSW or an injected client, DB with a test container or an
  in-memory adapter), not internal modules. Vitest 5 clears mock call history between tests by default
  (`clearMocks: true`); `vi.when` sets per-argument return values.
- Type tests (`*.test-d.ts`, `expectTypeOf`) for exported generic utilities and public API shapes.
- Mutation testing (Stryker 10) on the modules where a silent bug is expensive (money, auth, permissions).

## 6. Review checklist (use before reporting done)

- [ ] No new `any`, `as` casts without a check, `!`, `@ts-ignore`, or disabled lint rules.
- [ ] Every external input validated with a schema; types derived from schemas.
- [ ] Every promise awaited/returned/voided; timeouts and `AbortSignal` on I/O.
- [ ] Union switches exhaustive; new variants produce compile errors where they must be handled.
- [ ] Public API: explicit return types, `readonly` inputs, docs on thrown errors.
- [ ] Imports: `import type` for types, extensions correct for the module mode, no new barrels or deep imports.
- [ ] Gates run, exit codes read directly, outputs pasted; failing-first test shown.
- [ ] `package.json` changes: lockfile updated by the package manager, `engines` still accurate.
- [ ] No `eval`/`new Function`/string timers; input-facing regexes pass `regexp/no-super-linear-backtracking`.
- [ ] Shared state changed across `await` has a lock or a DB-level guard and a stress test.
- [ ] Services: shutdown drains with a deadline; caches and listeners are bounded.
