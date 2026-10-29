---
name: javascript-engineering
description: "Rule catalog, config templates and verification gates for production JavaScript on Node.js 22/24/26 and modern browsers (October 2026 toolchain: ESLint 10 flat config, Prettier 3.9, TypeScript 7 JSDoc checking, Vitest 5, node:test, Playwright 1.64, Vite 8, npm 12 / pnpm 12). Use when writing, reviewing, testing, profiling or packaging .js/.mjs/.cjs code, setting up lint/test/type-check for a JavaScript repo, hardening a Node service, or debugging async, stream, memory, hanging-test or browser-performance problems."
---

# JavaScript engineering (Node.js + browser), October 2026

This skill backs the `javascript-engineer` agent. It is a catalog of checkable rules plus the exact
commands that prove them. Config files to copy live in `references/configs.md`; they were run
end-to-end on 2026-10-29 (see `sources/javascript.md`, self-check section).

How to use it: find the section for the task, apply its rules, then run the gate block at the end.
When a rule and the repo's existing convention disagree, follow the repo and mention the gap.

## 1. Project setup decisions

| Decision | Default | Switch when |
|---|---|---|
| Runtime | Node 26 LTS (Active since 2026-10-28) | Platform pins 24/22 (both supported until 2028-04-30 / 2027-04-30) |
| Module system | ESM, `"type": "module"` | A legacy CJS app: keep CJS, add `exports`; Node 22.12+ can `require()` ESM |
| Package manager | the one in `packageManager` / the lockfile present | New project: pnpm 12 (strict; 1-day release-age delay is the default since pnpm 11) or npm 12 |
| Types | JSDoc + `tsc --noEmit` (TypeScript 7.0.2, `checkJs`) | Team wants `.ts`: hand to the typescript engineer |
| Format | Prettier 3.9 | Biome 2.6 if the repo already uses it (lint + format in one binary) |
| Lint | ESLint 10 flat config (+ optional oxlint 1.90 pre-pass) | Biome-only repos: `biome ci` |
| Unit tests | Vitest 5 for apps/browser code; `node:test` for small Node libs with zero deps | Existing Jest 30 suite: keep it, do not mix runners |
| E2E | Playwright 1.64 (`@playwright/test`) | |
| Bundling | Vite 8 for apps; tsdown 0.23 or plain ESM (no bundle) for libraries | |
| Validation | zod 4 / valibot 1.5 / Fastify JSON schema at boundaries | |
| HTTP server | Fastify 5 (schemas, hooks, perf) | Express 5 in existing Express apps; Hono 4 for edge/multi-runtime |

Corepack is no longer shipped with Node 25+. Pin the package manager with `"packageManager"` and
install it explicitly in CI (`npm i -g pnpm@12.16.1` or `corepack@0.36.0` from npm).

## 2. Modules and packages

- Use `node:` specifiers for built-ins. Relative imports carry the file extension
  (`./util.js`) because Node's ESM resolver does not guess.
- `import.meta.dirname` / `import.meta.filename` replace `__dirname` / `__filename` in ESM.
- JSON: `import data from './data.json' with { type: 'json' }` (import attributes, ES2025).
- Library `package.json` minimum: `name`, `version`, `type`, `exports`, `files`, `engines`,
  `license`, `sideEffects` (false when true), `repository`. No `main`-only libraries for new work.
- Dual ESM/CJS only when a real consumer needs it; otherwise ship ESM and let Node 22.12+ consumers
  `require()` it. Verify with `publint` and `attw --pack . --profile esm-only`.
- JSDoc-typed libraries ship emitted declarations: `tsc -p tsconfig.build.json` (`allowJs`,
  `declaration`, `emitDeclarationOnly`, `outDir: dist/types`) run from `prepack`, plus a `types`
  condition first in each `exports` entry. Without it consumers get `any` and attw only prints
  "This package does not contain types" with exit 0. Template: `references/configs.md`, library variant
  (TS 7.0.2 emitted the `.d.ts` in the smoke test).
- `"engines"` states the oldest supported Node; enforce it with `eslint-plugin-n`
  (`n/no-unsupported-features/*` reads `engines`).
- Dependencies: runtime deps in `dependencies`, tooling in `devDependencies`, plugin hosts in
  `peerDependencies`. Exact pins for apps (`save-exact=true`), caret ranges for libraries.
- Monorepos: npm `"workspaces": ["packages/*"]` or pnpm `pnpm-workspace.yaml` (`packages:`). One
  lockfile at the root; install and run gates from the root (`npm run test --workspaces --if-present`,
  `pnpm -r test`); internal deps use `"workspace:*"` (pnpm) so a broken sibling fails the build
  instead of resolving an old published copy. Add a dependency to one package with
  `npm install <pkg> -w <name>` / `pnpm add <pkg> --filter <name>`.
- Releases follow semver against the public surface (`exports`, documented options, emitted
  types, `engines`): removing an export, raising `engines`, or narrowing accepted input is a major.
  Record each change with Changesets (`@changesets/cli` 3.0.3): `npx changeset` in the PR,
  `npx changeset version` to bump and write changelogs, `npx changeset publish` from CI with
  trusted publishing and provenance.

## 3. Types via JSDoc (TypeScript 7 checker)

- `tsconfig.json`: `allowJs`, `checkJs`, `noEmit`, `strict` (default in TS 7), `module`/`moduleResolution`
  `nodenext`, `skipLibCheck: true`, and `target`/`lib` matching the oldest runtime: `esnext` for Node
  26 (types Temporal, `Map#getOrInsert`, `Error.isError`, `Promise.try`, `RegExp.escape`,
  `Uint8Array.fromBase64`); `es2024` for libraries that still support Node 22, so `tsc` rejects
  APIs Node 22 lacks. `Iterator.concat` has no lib typing in TS 7.0.2 (TS2339 even with `esnext`):
  use a generator or a reasoned `// @ts-expect-error`. Template in `references/configs.md`.
- Annotate module boundaries: `@param`, `@returns`, `@throws` (documentation), `@typedef`,
  `@template`, `@satisfies`, `@import` (`/** @import { Server } from 'node:http' */`).
- TS 7 removed legacy JSDoc forms: use `typeof X` for values in type positions, named `@typedef`
  for aliases, arrow-style function types, no `@enum`, no Closure `function(a): b`, no postfix `!`.
- `// @ts-expect-error <reason>` over `// @ts-ignore`, and only with a reason.
- Type-aware ESLint (`typescript-eslint` 8.72.1) peers on `typescript >=4.8.4 <6.1.0`, so the package
  named `typescript` has to be the TS 6 API. Use the TypeScript 7 announcement recipe:
  `"typescript": "npm:@typescript/typescript6@^6.0.2"` plus `"@typescript/native": "npm:typescript@^7.0.2"`.
  `npx tsc` then runs 7.0.2 and `tsc6` runs 6.0. An alias under another name (`"typescript6": ...`)
  leaves `typescript` at 7.0.2 and `npm install` fails with ERESOLVE. Config fragment in
  `references/configs.md`.

## 4. Errors

- Throw `Error` (sub)classes with `code` and `cause`. One shared base:
  `class AppError extends Error { constructor(message, { code, cause, status } = {}) { super(message, { cause }); this.name = 'AppError'; this.code = code; this.status = status } }`.
- Operational vs programmer errors: operational errors (bad input, timeouts, 404 upstream) are
  handled and mapped; programmer errors (TypeError, invariant breaks) crash the process after
  logging, and the supervisor restarts it. A process in an unknown state should not keep serving.
- Central error handling: one handler per entry point (Fastify `setErrorHandler`, Express error
  middleware, a CLI `main().catch(...)`) that logs with context and returns a generic body.
- Never swallow: no empty `catch`, no `.catch(() => {})`. If ignoring is intended, comment why and
  narrow the condition (`if (err.code !== 'ENOENT') throw err`).
- `return await` inside `try` so the `catch` actually sees rejections.
- Subscribe to `'error'` on every EventEmitter/stream you create; an unhandled `'error'` event
  crashes the process.

## 5. Async, concurrency, cancellation

- No floating promises. `forEach(async ...)` is always a bug; use `for...of` with `await` (sequential)
  or `Promise.all(items.map(...))` (parallel) or `p-map` with `concurrency` (bounded).
- Timeouts on every I/O: `AbortSignal.timeout(ms)`; combine caller and timeout signals with
  `AbortSignal.any([signal, AbortSignal.timeout(ms)])`; pass `signal` to `fetch`, `setTimeout` from
  `node:timers/promises`, `events.once`, streams and your own functions.
- Race conditions: protect read-modify-write on shared state (single-flight a key with a `Map` of
  in-flight promises, or `async-cache-dedupe`). Use database transactions/constraints for
  correctness, not in-process locks across instances.
- Event loop health: track `perf_hooks.monitorEventLoopDelay()`; p99 delay above ~100 ms on an API
  is a defect to investigate. CPU work goes to `worker_threads` (piscina pool).
- `queueMicrotask` and `process.nextTick` are not scheduling tools for heavy work; they starve I/O.
- Request context: `AsyncLocalStorage` from `node:async_hooks` (Stability 2) carries a request id,
  tenant or trace context through `await` chains: `als.run({ reqId }, () => handle(req))`, read with
  `als.getStore()`. Prefer `run()` over `enterWith()` (Stability 1), never store mutable shared
  objects in it, and promisify callback APIs that lose the context.
- Worker data: `postMessage(value, transferList)` copies by structured clone unless an
  `ArrayBuffer`/`MessagePort` is listed in `transferList`, which moves it (unusable on the sender
  afterwards). Use a `MessageChannel` for a dedicated worker-to-worker or request/response channel.
- Shared memory: `SharedArrayBuffer` + `Atomics` (`Atomics.add`, `Atomics.wait` / `Atomics.notify`)
  only for hot counters or ring buffers where copying costs too much; every access goes through
  `Atomics`. `Atomics.wait` blocks, so it is for workers only; the browser main thread uses
  `Atomics.waitAsync`. SharedArrayBuffer cannot go in `transferList`; it is shared as-is.
- Browsers expose `SharedArrayBuffer` only when the page is cross-origin isolated: serve
  `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: require-corp` (or
  `credentialless`) over HTTPS and check `self.crossOriginIsolated` before use. COEP blocks
  cross-origin subresources that do not send CORS/CORP headers, so audit embeds first.
- Explicit resource management: `using` / `await using` with `Symbol.dispose` /
  `Symbol.asyncDispose` (Node 24+, Chrome 134+, Firefox 141+; Safari preview only per MDN BCD
  8.1.7). In Safari-targeted code, transpile or use `try/finally`.

## 6. Streams and large data

- `await pipeline(source, ...transforms, sink)` from `node:stream/promises`; transforms as
  `async function*`. This gives backpressure and error propagation in one call.
- Line processing: `readline.createInterface({ input, crlfDelay: Infinity })` with `for await`.
- Writing manually: `if (!w.write(chunk)) await once(w, 'drain')`.
- Collect small streams with `node:stream/consumers` (`text`, `json`, `buffer`); cap sizes for
  untrusted input.
- Web Streams (`ReadableStream`, `CompressionStream`) for code shared with browsers; convert with
  `Readable.fromWeb` / `Readable.toWeb`.

## 7. Language idioms (ES2026 era)

- `const`/`let`, never `var`; `===`; optional chaining and `??` (not `||` for defaults that may be 0/'').
- Non-mutating array methods: `toSorted`, `toReversed`, `toSpliced`, `with`; `Object.groupBy`,
  `Map.groupBy`; `structuredClone` for deep copies; `Array.fromAsync` for async iterables.
- ES2025 (TC39 finished proposals): iterator helpers (`.map/.filter/.take/.toArray` on iterators),
  `Promise.try` (Node 23+), `RegExp.escape` (Node 24+), Set methods, import attributes / JSON modules,
  `Float16Array`.
- ES2026 additions usable on Node 26 and current Chromium/Firefox: `Map.prototype.getOrInsert` /
  `getOrInsertComputed`, `Iterator.concat`, `Uint8Array.fromBase64` / `.toBase64` (Node 25+),
  `Error.isError` (Node 24.3+; Safari preview only), `Array.fromAsync`. `Math.sumPrecise` is not in
  Node 26 per MDN BCD. Check `Map#getOrInsert` (Safari 26.2+) and `Iterator.concat` (Safari 26.4+)
  against your browser targets.
- Temporal (ES2027, on by default in Node 26, Chrome 144+, Firefox 139+): use for date/time math
  and time zones; for Safari, load a polyfill behind feature detection (`temporal-polyfill` 1.0.6,
  MIT, 2026-10-13, is the actively published one; `@js-temporal/polyfill` last shipped 0.5.1 in
  2025-03). Score it with the supply-chain gate before adding it.
- Classes: `#private` fields, static blocks; composition over inheritance; no prototype patching of
  built-ins.
- Prefer `Map`/`Set` for dynamic keys; `Object.create(null)` when a plain dictionary is needed.
- `crypto.randomUUID()` and `crypto.getRandomValues()` for ids/tokens; `Math.random` is not for
  security.

## 8. Node.js services

- Config: read env once at startup into a validated, frozen object (zod schema); fail fast on
  missing values. `node --env-file=.env` or `process.loadEnvFile()` for local dev only.
- HTTP: set server timeouts (`requestTimeout`, `headersTimeout`, `keepAliveTimeout` behind a load
  balancer), body size limits, and a health/readiness pair that flips to 503 during shutdown.
- Outbound HTTP: built-in `fetch` (undici 8 in Node 26) with timeouts; reuse a dispatcher/agent for
  connection pooling; never disable TLS verification.
- Logging: pino JSON to stdout with `req.id`; redact `authorization`, cookies, tokens
  (`redact` option). No `console.log` in services.
- Stack traces from bundled or transpiled output: run with `node --enable-source-maps` (stable
  since v14.18/v15.11) and ship the `.map` files next to the bundle; an override of
  `Error.prepareStackTrace` must call the original or source maps stop applying.
- Tracing and metrics: OpenTelemetry (`@opentelemetry/sdk-node` 0.300.0 +
  `@opentelemetry/auto-instrumentations-node` 0.82.0, Apache-2.0). Start the `NodeSDK` in a separate
  `instrumentation.js` and load it before the app with `node --import ./instrumentation.js app.js`
  so http/undici/pg are patched before they are imported; do not also set
  `--require @opentelemetry/auto-instrumentations-node/register` in `NODE_OPTIONS`. Export via OTLP
  to a collector, and put the trace id in pino logs to correlate them.
- Shutdown: on SIGTERM/SIGINT stop accepting, drain, close pools, then exit; force-exit timer
  shorter than the orchestrator's grace period. `close-with-grace` or Fastify `onClose` hooks.
- Containers: `node` as PID-1-aware entry (`--init` or `tini`), non-root user, `NODE_ENV=production`,
  `npm ci --omit=dev`, memory limit plus `--max-old-space-size` (or `--max-old-space-size-percentage`).
- Cluster/scale: one process per container and scale horizontally; `node:cluster` only on bare VMs.

## 9. Browser code

- Ship native ESM, let Vite 8 bundle and code-split. Set targets via `browserslist`
  (`baseline widely available` is a sound default) and check features with MDN BCD before use.
- Main-thread budget: tasks under 50 ms; break loops with `await scheduler.yield()` where available
  (Chrome 129+, Firefox 142+, not Safari) with a `setTimeout(0)` fallback; move CPU work to a Worker.
- DOM: batch reads before writes; event delegation for large lists; `{ passive: true }` for
  scroll/touch; `AbortController` signals to remove listeners (`addEventListener(type, fn, { signal })`).
- Security: `textContent` for text; `Element.setHTML()` (Chrome 146+, Firefox 148+) or a vetted
  sanitizer for HTML; CSP with nonces/hashes; Trusted Types where supported; `rel="noopener"` on
  `target=_blank`; never put secrets in client bundles (anything in `import.meta.env.VITE_*` is public).
- Storage: no tokens in `localStorage`; prefer `HttpOnly; Secure; SameSite` cookies set by the
  server. Cookie sessions need CSRF protection (security item 7).
- Performance evidence comes from a trace or Lighthouse run (lab) or RUM/CrUX (field); label which.

## 10. Security checklist (review every diff against it)

1. Injection: SQL/NoSQL via parameterized queries only; shell via `execFile(cmd, args)`; paths via
   `path.resolve(base, input)` plus a `startsWith(base + path.sep)` check.
2. Code execution: no `eval`, `new Function`, `vm` for untrusted code, string timers, dynamic
   `import()`/`require()` of user-controlled specifiers.
3. Prototype pollution: reject `__proto__`, `constructor`, `prototype` keys in merges; schema-validate
   JSON; use `Map`.
4. ReDoS: `eslint-plugin-regexp` + review of any regex applied to user input; cap input length.
5. SSRF: allowlist hosts for server-side fetches of user URLs. A hostname allowlist alone is not
   enough: resolve the name (`dns.promises.lookup(host, { all: true })`), reject every private,
   loopback, link-local and metadata address, then connect only to the validated IP (a custom
   `lookup` in the undici `Agent` `connect` options) so DNS rebinding cannot swap it, and fetch
   with `redirect: 'error'` (or `'manual'` and re-validate each hop).
6. XSS: no `innerHTML`/`outerHTML`/`insertAdjacentHTML`/`document.write` with untrusted data.
7. AuthN/Z: authorization on every route; constant-time compare (`crypto.timingSafeEqual`) for
   secrets; passwords with `crypto.scrypt` or argon2; rate-limit login. CSRF for cookie sessions:
   `SameSite=Lax` or `Strict` on the session cookie, state changes only on non-GET methods, and on
   each state-changing request either verify `Origin` (or `Sec-Fetch-Site: same-origin`) against
   an allowlist or require a synchronizer / signed double-submit token (`@fastify/csrf-protection`
   in Fastify). Bearer-token APIs without cookies do not need it.
8. Secrets: env/secret manager only; `.env*` in `.gitignore` and `.npmignore`/`files`; `npm pack
   --dry-run` before publishing to see what ships.
9. Supply chain: lockfile committed; npm 12 `allowScripts` / pnpm `allowBuilds` reviewed per
   package; `min-release-age` (npm) or `minimumReleaseAge` (pnpm, default 1 day in v11+);
   `npm audit signatures`; Socket score for new deps; trusted publishing + provenance for releases.
10. Runtime hardening for tools that touch untrusted input: `node --permission --allow-fs-read=<dir>`
    (the Permission Model is stable since 22.13/23.5); try `--permission-audit` first to discover
    what is needed. `--allow-net` (Node 25+) is Stability 1.1 (active development): treat network
    restriction through it as experimental and keep the SSRF checks in code.

## 11. Testing

- Pyramid for services: component/API tests through HTTP (Fastify `inject`, supertest) are the
  backbone; unit tests for pure logic; a few Playwright E2E for critical journeys.
- Test names state unit, scenario, and expectation; arrange/act/assert layout.
- Cover the five outcomes of an entry point: response, state change, outbound calls, messages
  emitted, observability (logs/metrics) where they matter.
- Network: MSW 3 (`msw/node` `setupServer`) or undici `MockAgent`; fail on unhandled requests
  (`onUnhandledRequest: 'error'`).
- Time: `vi.useFakeTimers()` / `mock.timers.enable()` only where time is under test; restore after.
- Isolation: per-test data, random ports, `t.after()` / `afterEach` cleanup in the same scope that
  created the resource. Shuffle runs to prove order independence: Vitest needs both
  `--sequence.shuffle.files` (file order) and `--sequence.shuffle.tests` (order inside a file).
- Flaky test protocol: reproduce in isolation (`--test-name-pattern` / `-t`), repeat (loop 50 runs),
  inspect shared state and timers, find the handle with `--reporter=hanging-process` (Vitest) or
  `why-is-node-running`, fix in the creating scope, re-run isolated then full suite. Retries are a
  diagnostic, not a fix.
- Hang check, per runner. Vitest with `--reporter=hanging-process`: passes when the process exits
  on its own and the reporter prints no open handles. `node --test --test-timeout=30000`: passes
  with exit 0; a leaked handle shows up as the file-level test failing with
  `failureType: 'testTimeoutFailure'` ("test timed out after 30000ms") and no handle list, so use
  `why-is-node-running` to find it. Never add `--test-force-exit` to make the gate green: it exits
  past the leak (a leaked `setInterval` file reports `pass 1`).
- Tests that prove a timeout or abort assert elapsed time (or use fake timers) and set a short
  per-test timeout, so a wait that ignores the signal fails on its own instead of only through the
  runner's 5 s default.
- Coverage is a floor, not a goal: thresholds in config so the gate fails on regressions.

## 12. Performance and profiling

- Baseline first, same machine, same data; report command and numbers.
- CPU: `node --cpu-prof --cpu-prof-dir=prof app.js` then open the `.cpuprofile` in DevTools, or
  `npx @platformatic/flame@1.7.0 run app.js`, which writes CPU and heap flame graphs (`.html`) plus
  markdown summaries in the working directory (`flame app.js` without `run` fails with
  "Unknown command").
- Memory: `node --heap-prof`, `--heapsnapshot-signal=SIGUSR2`, or Chrome DevTools MCP
  `take_heapsnapshot` / `compare_heapsnapshots`; look for growing `Map`s, listeners and closures.
- HTTP load: `npx autocannon -c 100 -d 30 http://127.0.0.1:3000/route` (autocannon 8.0.0).
- Micro-benchmarks in Vitest 5: `bench` is a test-context fixture, no longer an export of
  `vitest`. In a `*.bench.js` file write `test('x', async ({ bench }) => { const r = await
  bench.compare(bench('a', fa), bench('b', fb)); expect(r.get('a')).toBeFasterThan(r.get('b'), { delta: 0.1 }) })`
  and run `npx vitest bench --run --reporter=verbose` (the default reporter hides the table).
  `bench.compare` interleaves iterations; consume results so they are not dead code.
- Statistical rule for any speed claim: at least 10 interleaved runs (or samples) per variant on the
  same machine, and a spread or significance check before calling it a win.
  - tinybench/Vitest: the difference between means must exceed the combined `rme` (both printed),
    or assert it with `toBeFasterThan(..., { delta })`.
  - CLI/startup: `hyperfine --warmup 3 --runs 10 --export-json r.json 'node a.js' 'node b.js'`
    (hyperfine 2.0.0), then Welch's t-test with
    `uvx --from 'git+https://github.com/sharkdp/hyperfine' welch_ttest r.json`.
  - HTTP: 3 autocannon runs per variant, alternating A/B; claim a p99 or req/s change only when it
    is larger than the run-to-run spread of each variant.
- Common wins: avoid repeated `JSON.stringify` (Fastify response schemas serialize faster), batch
  DB calls, stream instead of buffering, cache with bounds, keep objects monomorphic in hot loops.

## 13. Gate block (copy into the report)

```bash
set -u
npm ci                                              ; echo "install exit=$?"
npx prettier --check .                              ; echo "format exit=$?"
npx eslint . --max-warnings=0                       ; echo "lint exit=$?"
npx tsc --noEmit                                    ; echo "types exit=$?"
npx vitest run --coverage                           ; echo "test exit=$?"
npx vitest run --sequence.shuffle.files --sequence.shuffle.tests ; echo "shuffle exit=$?"
npx knip                                            ; echo "knip exit=$?"
npm audit --audit-level=high                        ; echo "audit exit=$?"
npm audit signatures                                ; echo "signatures exit=$?"
# libraries:  npm run build:types ; npx publint ; npx @arethetypeswrong/cli --pack . --profile esm-only
#             (fail if attw prints "This package does not contain types")
# browser:    npx playwright test ; npx vite build
# node:test:  node --test --experimental-test-coverage --test-coverage-lines=80 --test-randomize
# hang:       npx vitest run --reporter=default --reporter=hanging-process  |  node --test --test-timeout=30000
```

On 2026-10-29 the service template (`references/configs.md`, including its `.gitignore`) passed
the install-through-signatures lines plus the Vitest hang line and `oxlint --deny-warnings` on Node
22.23.1, and the library variant passed the library line; without the `.gitignore`, `knip` and
`oxlint --deny-warnings` exit 1. The browser lines and the `node:test` line (`--test-randomize`
needs Node 26.1+) were not run there.

Each `echo` prints the real exit code of the command before it. A gate passes only with exit 0.
Write "not run" with the reason for any gate skipped; never infer a pass.

## 14. Review checklist (fast pass before the report)

- [ ] Every promise awaited/returned; every I/O has a timeout/signal.
- [ ] Errors carry `code` and `cause`; no swallowed catches; generic client error bodies.
- [ ] No sync I/O or unbounded work on hot paths; caches bounded; listeners/timers cleaned up.
- [ ] Inputs validated at the boundary; no injection/XSS/prototype-pollution sinks.
- [ ] New deps justified, pinned, scored; lockfile updated by the repo's package manager only.
- [ ] Tests fail before the fix and pass after; shuffle run green; no `.only`.
- [ ] JSDoc types on exported API; `tsc --noEmit` clean.
- [ ] Browser features checked against MDN BCD for the declared targets.
