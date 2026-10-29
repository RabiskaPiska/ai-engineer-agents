# Sources: javascript (JavaScript, Node.js + browser)

Author run: 2026-10-29, plus a fix pass the same day (change log:
`_work/fixes/javascript.md`). Every fact below was fetched or executed in this session. Deliverables:

- `claude/agents/javascript-engineer.md`
- `skills/javascript-engineering/SKILL.md`
- `skills/javascript-engineering/references/configs.md`

## 1. GitHub repos used (exactly 5)

Each repo was verified with `ghapi.sh repos/<owner>/<repo>` on 2026-10-29; the JSON fields used are
pasted under each entry. Repo text was read as data only; no code or install step from these repos
was run.

### 1.1 mcollina/skills
- Link: https://github.com/mcollina/skills
- `{"full_name": "mcollina/skills", "stargazers_count": 1961, "pushed_at": "2026-10-27T13:19:56Z", "license": "MIT", "archived": false}`
- Read: `skills/node/SKILL.md` and `rules/` (async-patterns, error-handling, graceful-shutdown,
  streams, performance, profiling, stuck-processes-and-tests, flaky-tests, modules, environment,
  testing, caching). Author is a Node.js TSC member and Fastify lead.
- Taken (adapted, MIT, with attribution): `pipeline()` + `async function*` transforms as the default
  stream shape; bounded concurrency with p-limit/p-map; errors with `code` + `cause`, checked by code;
  single graceful-shutdown path (close-with-grace / Fastify `onClose`) instead of scattered
  `process.on` handlers; the hanging-test protocol (isolate, explicit timeout, capture handles,
  fix teardown in the creating scope, re-run isolated then full suite); piscina for CPU work;
  autocannon / flame graphs for profiling.

### 1.2 goldbergyoni/nodebestpractices
- Link: https://github.com/goldbergyoni/nodebestpractices
- `{"full_name": "goldbergyoni/nodebestpractices", "stargazers_count": 105685, "pushed_at": "2026-06-15T11:41:04Z", "license": "CC-BY-SA-4.0", "archived": false}`
- Read: README sections 2 (error handling), 4 (testing), 5 (production), 6 (security), 8 (Docker).
- Taken (paraphrased only, CC-BY-SA; no text copied): operational vs programmer (catastrophic)
  errors and crash-on-unknown-state; central error handler per entry point; `return await` for full
  stack traces; validate input with a schema library; `execFile` over shell `exec`; no dynamic module
  paths from input; ReDoS awareness; hide error details from clients; run as non-root, start with
  `node` not `npm start`, log to stdout, `npm ci`; test the five outcomes of an entry point.

### 1.3 antfu/skills
- Link: https://github.com/antfu/skills
- `{"full_name": "antfu/skills", "stargazers_count": 6022, "pushed_at": "2026-10-23T02:36:51Z", "license": "MIT", "archived": false}`
- Read: `skills/antfu/SKILL.md`, `references/library-development.md`, `references/setting-up.md`,
  `skills/vitest/SKILL.md` (generated against Vitest 5.1.0-beta.1 on 2026-10-23),
  `skills/pnpm/references/best-practices-ci.md`.
- Taken (adapted, MIT): ESM-only libraries with an `exports` map, `publint` on every build, tsdown for
  bundled libraries, npm trusted publishing (OIDC) from CI; a single `check`/`ci` script chaining
  lint, typecheck, knip and tests; Vitest feature map (shuffle, coverage thresholds, bench, browser
  mode) used to decide which Vitest options the gates call.

### 1.4 addyosmani/agent-skills
- Link: https://github.com/addyosmani/agent-skills
- `{"full_name": "addyosmani/agent-skills", "stargazers_count": 111567, "pushed_at": "2026-10-29T05:06:58Z", "license": "MIT", "archived": false}`
- Read: `agents/web-performance-auditor.md`, `agents/security-auditor.md`, `agents/test-engineer.md`.
- Taken (adapted, MIT): the metric-honesty rule (label lab vs field data, never report unmeasured
  Core Web Vitals); Chrome DevTools MCP tools for traces, Lighthouse and heap snapshots; browser
  rules (long tasks, `scheduler.yield()`, passive listeners, layout thrash); the security review
  scope (input handling, authZ on every route, SSRF allowlists, secrets) used for the
  security-auditor delegation brief.

### 1.5 wshobson/agents
- Link: https://github.com/wshobson/agents
- `{"full_name": "wshobson/agents", "stargazers_count": 41969, "pushed_at": "2026-10-26T01:08:14Z", "license": "MIT", "archived": false}`
- Read: `plugins/javascript-typescript/agents/javascript-pro.md`,
  `plugins/javascript-typescript/skills/modern-javascript-patterns/SKILL.md`,
  `plugins/javascript-typescript/skills/nodejs-backend-patterns/SKILL.md`,
  `plugins/javascript-typescript/skills/javascript-testing-patterns/SKILL.md` (paths re-checked with
  `ghapi.sh repos/wshobson/agents/contents/<path>`; the earlier `skills/...` paths return Not Found).
- Taken (adapted, MIT): dependency injection as the primary test seam (over module mocking), async
  test patterns, the Node + browser dual scope of a JavaScript agent. Also used as a negative
  example: its 35-line agent has no versions, gates or output contract, which this agent adds.

## 2. Official version sources (fetched 2026-10-29)

| Fact | Value | Source |
|---|---|---|
| Node.js releases per line | v26.13.0 (2026-10-28, LTS "Lithium", npm 11.20.0, V8 14.6.202.34); v24.22.2 (2026-10-27, "Krypton"); v22.23.4 (2026-10-20, "Jod"); v20.20.2 (2026-03-24); v25.9.0 (2026-03-31) | https://nodejs.org/dist/index.json |
| Node.js schedule | v26 LTS 2026-10-28, maintenance 2027-10-20, end 2029-04-30; v24 maintenance 2026-10-20, end 2028-04-30; v22 end 2027-04-30; v20 end 2026-04-30; v25 end 2026-06-01; v27 alpha 2026-10-28, start 2027-04-22 | https://raw.githubusercontent.com/nodejs/Release/main/schedule.json |
| Node 26.13.0 = LTS transition only | "This release marks the transition of Node.js 26.x into Long Term Support (LTS) with the codename 'Lithium'" | https://nodejs.org/en/blog/release/v26.13.0 |
| Node 26.0.0 notable changes | Temporal on by default; V8 14.6 (upsert, `Iterator.concat`); Undici 8; `module.register()` runtime-deprecated; `--experimental-transform-types` removed | https://nodejs.org/en/blog/release/v26.0.0 |
| Corepack | "build: stop distributing Corepack" (semver-major in v25.0.0) | https://nodejs.org/en/blog/release/v25.0.0 |
| Node CLI flags used in gates | `--permission` stable since v23.5.0/v22.13.0; `--permission-audit` added v25.8.0; `--allow-net` added v25.0.0; `--test-randomize` added v26.1.0; `--test-coverage-lines`; `--no-strip-types` (type stripping stable v25.2.0/v24.12.0); `--unhandled-rejections` default `throw`; `--heapsnapshot-signal`; `--max-old-space-size-percentage` | https://raw.githubusercontent.com/nodejs/node/v26.13.0/doc/api/cli.md |
| `require(esm)` | unflagged v22.12.0/v23.0.0; no longer experimental v25.4.0 | https://raw.githubusercontent.com/nodejs/node/v26.13.0/doc/api/modules.md |
| `node:test` | Stability 2 (Stable); coverage still Stability 1 | https://raw.githubusercontent.com/nodejs/node/v26.13.0/doc/api/test.md |
| ECMAScript 2025 / 2026 / 2027 | ES2025: `Promise.try`, `RegExp.escape`, sync iterator helpers, Set methods, JSON modules, import attributes, RegExp modifiers, duplicate named groups, Float16. ES2026: Upsert, JSON.parse source text access, Iterator Sequencing, Uint8Array base64, `Math.sumPrecise`, `Error.isError`, `Array.fromAsync`. ES2027 (stage 4 so far): Temporal, Explicit Resource Management, Joint Iteration, `Atomics.pause`, iterator chunking/includes/join | https://raw.githubusercontent.com/tc39/proposals/main/finished-proposals.md (year column) ; https://tc39.es/ecma262/2026/ (HTTP 200) |
| Feature support per engine | `using`: Node 24.0.0, Chrome 134, Firefox 141, Safari preview. Temporal: Node 26.0.0, Chrome 144, Firefox 139, Safari preview. `Map.getOrInsert`: Node 26, Safari 26.2. `Math.sumPrecise`: not in Node. `Element.setHTML`: Chrome 146, Firefox 148, no Safari. `scheduler.yield`: Chrome 129, Firefox 142, no Safari | MDN browser-compat-data 8.1.7 (2026-10-22), https://unpkg.com/@mdn/browser-compat-data/data.json |
| Browsers | Chrome 157.0.8103.27 stable (2026-10-28 UTC); Firefox 159.0 (2026-10-27); Safari 27.2 "Released October 26, 2026 — 27.2 (20625.2.8)" (27.0 2026-09-14, 27.1 2026-10-23). MDN BCD 8.1.7 already lists Safari 27.2 and still marks Temporal and `using` as `preview` | https://chromiumdash.appspot.com/fetch_releases?channel=Stable&platform=Windows&num=1 ; https://product-details.mozilla.org/1.0/firefox_versions.json ; https://developer.apple.com/tutorials/data/documentation/safari-release-notes.json (JSON behind https://developer.apple.com/documentation/safari-release-notes) |
| npm 12 | 12.0.0 (2026-07-08): dependency lifecycle scripts blocked unless allowed by `allowScripts`; `allow-git`/`allow-remote` default `none`; shrinkwrap removed; supports node `^22.22.2 \|\| ^24.15.0 \|\| >=26.0.0`. Latest 12.2.1 (2026-10-15). `min-release-age` config | https://github.com/npm/cli/releases/tag/v12.0.0 ; https://raw.githubusercontent.com/npm/cli/v12.2.1/workspaces/config/lib/definitions/definitions.js ; https://raw.githubusercontent.com/npm/cli/v12.2.1/docs/lib/content/commands/npm-install-scripts.md |
| pnpm | 11.0.0 (2026-04-28): Node 22+, `minimumReleaseAge` default 1440 min, `allowBuilds`, `.npmrc` auth/registry only. 12.0.0 (2026-08-26). Latest 12.16.1 (2026-10-27) | https://github.com/pnpm/pnpm/releases/tag/v11.0.0 ; https://github.com/pnpm/pnpm/releases/tag/v12.0.0 |
| TypeScript 7 | 7.0.2 (2026-07-08) native compiler; JSDoc changes (`typeof` for values, no `@enum`/Closure function types/postfix `!`); no programmatic API, use `@typescript/typescript6` 6.0.2 (2026-07-06). Side-by-side recipe quoted from the post: `"@typescript/native": "npm:typescript@^7.0.2", "typescript": "npm:@typescript/typescript6@^6.0.2"` ("npx tsc will just work with 7.0") | https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/ ; registry `typescript` and `@typescript/typescript6` time fields |
| ESLint 10 | 10.0.0 (2026-02-06): eslintrc removed, `eslint-env` comments reported as errors. Latest 10.13.0 (2026-10-16) | https://github.com/eslint/eslint/releases/tag/v10.0.0 ; https://raw.githubusercontent.com/eslint/eslint/v10.13.0/docs/src/use/configure/configuration-files.md |
| Vitest 5 | 5.0.0 (2026-09-03): requires Node 22 and Vite 6.4; `sequential` option removed; pluggable benchmark provider. Latest 5.0.5 (2026-10-15). CLI `--sequence.shuffle.files` ("Run files in a random order") and `--sequence.shuffle.tests` ("Run tests in a random order"), `--testTimeout`, `coverage.thresholds`, `hanging-process` reporter. Benchmarks: `bench` is a test-context fixture in `*.bench.*` files; `bench.compare()` "runs them using interleaved iterations"; `toBeFasterThan(other, { delta })` | https://github.com/vitest-dev/vitest/releases/tag/v5.0.0 ; https://raw.githubusercontent.com/vitest-dev/vitest/v5.0.5/docs/guide/cli-generated.md ; https://raw.githubusercontent.com/vitest-dev/vitest/v5.0.5/docs/guide/benchmarking.md |
| Vite 8 | 8.0.0 (2026-03-12); latest 8.3.5 (2026-10-21) | https://github.com/vitejs/vite/releases/tag/v8.0.0 |
| Bun / Deno | bun-v1.4.4 (2026-10-22); Deno v2.9.8 (2026-10-21) | https://github.com/oven-sh/bun/releases ; https://github.com/denoland/deno/releases |
| Playwright | v1.64.1 (2026-10-14) | https://github.com/microsoft/playwright/releases |
| Other package versions | Read from `https://registry.npmjs.org/<pkg>` (`dist-tags.latest` + `time`): prettier 3.9.10, @biomejs/biome 2.6.4, oxlint 1.90.0, oxfmt 0.75.0, @eslint/js 10.0.1, globals 17.13.0, eslint-plugin-n 18.5.0, eslint-plugin-security 4.2.0, eslint-plugin-regexp 3.3.2, eslint-plugin-unicorn 79.0.0, typescript-eslint 8.72.1 (peer `typescript >=4.8.4 <6.1.0`), jest 30.5.2, msw 3.0.3, rolldown 1.2.15, esbuild 0.28.2, tsdown 0.23.3, @rspack/core 2.3.0, knip 6.43.0, publint 0.3.25, @arethetypeswrong/cli 0.18.5, fastify 5.12.7, express 5.3.0, hono 4.13.14, undici 8.12.3, pino 10.4.0, zod 4.6.7, @yarnpkg/cli-dist 4.18.1, corepack 0.36.0, temporal-polyfill 1.0.6, @types/node 22.20.5 (22.x line) | https://registry.npmjs.org/ |
| GitHub Actions | actions/checkout v7.0.1 (2026-07-20); actions/setup-node v7.1.0 (2026-10-08) | `ghapi.sh repos/actions/<name>/releases/latest` |
| Registry dates added in the fix pass | eslint-plugin-n 18.5.0 2026-10-18; eslint-plugin-security 4.2.0 2026-10-01; eslint-plugin-regexp 3.3.2 2026-10-29; eslint-plugin-unicorn 79.0.0 2026-10-23; oxfmt 0.75.0 2026-10-27; rolldown 1.2.15 2026-10-21; esbuild 0.28.2 2026-08-08; tsdown 0.23.3 2026-10-28; @rspack/core 2.3.0 2026-10-29; knip 6.43.0 2026-10-24; publint 0.3.25 2026-10-01; @arethetypeswrong/cli 0.18.5 2026-07-09; fastify 5.12.7 2026-10-13; express 5.3.0 2026-10-09; hono 4.13.14 2026-10-25; undici 8.12.3 2026-10-19; pino 10.4.0 2026-10-02; zod 4.6.7 2026-10-12; @eslint/js 10.0.1 2026-02-06; globals 17.13.0 2026-10-01; pnpm 11.28.9 2026-10-27; @changesets/cli 3.0.3 2026-09-14; @opentelemetry/sdk-node 0.300.0, auto-instrumentations-node 0.82.0, api 1.10.0 all 2026-10-20; @platformatic/flame 1.7.0 2026-07-09; autocannon 8.0.0 2024-10-14 (still `latest`); tinybench 6.2.2 2026-10-10; @types/node 26.6.6 2026-10-28; @fastify/csrf-protection 8.0.2 2026-10-09; typescript-eslint 8.72.1 2026-10-26 | `https://registry.npmjs.org/<pkg>` (`dist-tags.latest` + `time`) |
| Node APIs added in the fix pass | `AsyncLocalStorage` Stability 2 (`enterWith`, `withScope` Stability 1); `transferList` moves `ArrayBuffer`/`MessagePort`, `SharedArrayBuffer` "cannot be listed in `transferList`"; `--allow-net` added v25.0.0, "Stability: 1.1 - Active development"; `--enable-source-maps` no longer experimental v15.11.0/v14.18.0; `--test-timeout` default Infinity; `--test-force-exit` exits "even if the event loop would otherwise remain active"; `net` connect `lookup` option | https://raw.githubusercontent.com/nodejs/node/v26.13.0/doc/api/async_context.md ; https://raw.githubusercontent.com/nodejs/node/v26.13.0/doc/api/worker_threads.md ; https://raw.githubusercontent.com/nodejs/node/v26.13.0/doc/api/cli.md ; https://raw.githubusercontent.com/nodejs/node/v26.13.0/doc/api/net.md ; undici Connector docs (accepts `tls.connect()` options) https://raw.githubusercontent.com/nodejs/undici/main/docs/docs/api/Connector.md |
| Browser shared memory | SharedArrayBuffer needs a secure context and cross-origin isolation; isolation = `Cross-Origin-Opener-Policy: same-origin` + `Cross-Origin-Embedder-Policy: require-corp` or `credentialless`; `Atomics.wait` "cannot be used in the main thread", use `Atomics.waitAsync` | https://raw.githubusercontent.com/mdn/content/main/files/en-us/web/javascript/reference/global_objects/sharedarraybuffer/index.md ; https://raw.githubusercontent.com/mdn/content/main/files/en-us/web/api/window/crossoriginisolated/index.md ; https://raw.githubusercontent.com/mdn/content/main/files/en-us/web/javascript/reference/global_objects/atomics/wait/index.md |
| CSRF / SSRF | CSRF: synchronizer token, signed double-submit cookie, Fetch Metadata, SameSite, Origin header verification. SSRF: "Domain allowlisting alone does not prevent DNS rebinding. Validate the resolved destination IP addresses ..."; disable redirect following | https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.md ; https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.md |
| Workspaces / releases / telemetry | npm `-w <name>`, `npm run test --workspaces --if-present`; pnpm `pnpm-workspace.yaml` `packages:` and `workspace:*`; Changesets `changeset` / `changeset version` / `changeset publish` (changesets/changesets: 12542 stars, pushed 2026-10-26, MIT); OpenTelemetry Node: `NodeSDK` + `getNodeAutoInstrumentations()` loaded with `--import` before app code | https://raw.githubusercontent.com/npm/cli/v12.2.1/docs/lib/content/using-npm/workspaces.md ; https://raw.githubusercontent.com/pnpm/pnpm.io/main/docs/workspaces.md ; https://raw.githubusercontent.com/changesets/changesets/main/docs/intro-to-using-changesets.md ; https://raw.githubusercontent.com/open-telemetry/opentelemetry.io/main/content/en/docs/languages/js/getting-started/nodejs.md |
| Benchmark statistics | hyperfine v2.0.0 (2026-10-07): `--warmup`, `--runs`, `--export-json`; `scripts/welch_ttest.py` "Compare two benchmarks using Welch's t-test", run via `uvx --from 'git+https://github.com/sharkdp/hyperfine' <script>`. autocannon prints 2.5/50/97.5/99 % latency columns. `@platformatic/flame` README usage `flame run server.js` | https://github.com/sharkdp/hyperfine/releases ; https://raw.githubusercontent.com/sharkdp/hyperfine/master/scripts/README.md ; https://registry.npmjs.org/autocannon ; https://registry.npmjs.org/@platformatic/flame |

## 3. MCP servers declared in the agent (verified 2026-10-29)

| Server | Repo (ghapi JSON) | Install form used | Verification |
|---|---|---|---|
| context7 | upstash/context7 `{"stargazers_count": 63882, "pushed_at": "2026-10-28T20:26:24Z", "license": "MIT"}` | `type: http`, `url: https://mcp.context7.com/mcp` (README: "use the Context7 server URL `https://mcp.context7.com/mcp`"; API key optional, raises rate limits) | MCP `initialize` POST returned HTTP 200 without a key |
| chrome-devtools | ChromeDevTools/chrome-devtools-mcp `{"stargazers_count": 54397, "pushed_at": "2026-10-29T09:31:38Z", "license": "Apache-2.0"}` | README: `"command": "npx", "args": ["-y", "chrome-devtools-mcp@latest"]`; pinned here to npm 1.12.0 (2026-10-22) plus `--isolated` and `--no-usage-statistics` (both documented in the README) | npm registry + README + `docs/tool-reference.md` (tool names cited in the agent) |
| playwright | microsoft/playwright-mcp `{"stargazers_count": 38797, "pushed_at": "2026-10-22T17:43:26Z", "license": "Apache-2.0"}` | README: `claude mcp add playwright npx @playwright/mcp@latest`; pinned here to npm 0.0.83 (2026-09-28) with `--isolated`, `--headless` (README options table) | npm registry + README |
| socket-mcp | SocketDev/socket-mcp `{"stargazers_count": 137, "pushed_at": "2026-10-27T15:47:31Z", "license": "MIT"}` | README: `claude mcp add --transport http socket-mcp https://mcp.socket.dev/`, OAuth sign-in via `/mcp`; tools `depscore`, `organizations`, `alerts` | MCP `initialize` POST returned HTTP 200; tool calls need OAuth (not exercised) |
| github | by-name reference per SPEC | already configured | not re-verified here |

Pinning note: the READMEs recommend `@latest`; the agent pins exact versions so a compromised or
broken release cannot enter silently. Bump them deliberately.

## 4. Template smoke test (configs.md executed)

The templates in `references/configs.md` were extracted verbatim by a script into a scratch project
and run with Node v22.23.1 / npm 10.9.8 (the box's toolchain; npm 12 was not installed, so the
`packageManager` field was not enforced). First run found three real defects in the draft templates,
all fixed in the published version:

```
format exit=1   [warn] package.json  (inline objects; Prettier expands them)
lint exit=1     src/index.js 39:40 error Return values from promise executor functions cannot be read  no-promise-executor-return
types exit=1    src/index.js(1,15): error TS6196: 'Agent' is declared but never used.
```

Second run on the fixed templates (`npm ci` from the generated lockfile):

```
install exit=0   added 154 packages in 7s
format exit=0    All matched files use Prettier code style!
lint exit=0
types exit=0     (tsc Version 7.0.2)
test exit=0      RUN v5.0.5 ... Test Files 1 passed (1)  Tests 4 passed (4)
                 Statements 100% (13/13)  Branches 100% (3/3)  Functions 100% (2/2)  Lines 100% (12/12)
shuffle exit=0   Running tests with seed "1793267093565"  Tests 4 passed (4)
```

Correction (fix pass): the mutation line first recorded here (`... 2010ms`) did not reproduce; that
test only failed through Vitest's 5 s default timeout (5011 ms), and a mutant capped at 2 s passed.
The abort test now asserts `performance.now() - started < 100` and has a 1 s per-test timeout.

### 4.1 Fix-pass smoke test (2026-10-29, Node v22.23.1, npm 10.9.8)

Service template extracted from `configs.md` by `scaffold.py` (now includes `.gitignore`), lockfile
generated, then the SKILL section 13 gate block. `npm ci` printed `EBADENGINE ... required: { node:
'>=26' }` because the box runs Node 22; the gates still ran.

```
install exit=0      added 154 packages, and audited 155 packages in 3s
format exit=0       All matched files use Prettier code style!
lint exit=0
types exit=0        (tsc Version 7.0.2, target/lib esnext)
test exit=0         RUN v5.0.5  Tests 4 passed (4)  Statements 100% (13/13)  Branches 100% (3/3)
shuffle exit=0      --sequence.shuffle.files --sequence.shuffle.tests  seed "1793268149068"  Tests 4 passed (4)
knip exit=0         (knip 6.43.0)
oxlint exit=0       (oxlint 1.90.0 --deny-warnings)
audit exit=0        found 0 vulnerabilities
signatures exit=0   54 packages have verified attestations
vitest hang exit=0  --reporter=default --reporter=hanging-process  Tests 4 passed (4)
```

Same template with `.gitignore` moved away: `knip exit=1` (`Unused files (3) coverage/block-navigation.js ...`)
and `oxlint --deny-warnings exit=1` (warnings in `node_modules/vite/dist/...`); restored: knip exit=0.

Abort-test mutation check (each mutant replaces the abortable `delay(..., { signal })` in `retry`):

```
mutant delay(baseDelayMs * 2 ** i)                  exit=1  Error: Test timed out in 1000ms.  (1008ms)
mutant delay(Math.min(baseDelayMs * 2 ** i, 2000))  exit=1  Error: Test timed out in 1000ms.  (1014ms)
mutant delay(Math.min(baseDelayMs * 2 ** i, 150))   exit=1  AssertionError: expected 152.89302500000008 to be less than 100
original                                            exit=0  Tests 4 passed (4)
original abort test, 20 repeated runs: failures=0
```

TypeScript lib check (file using `Map#getOrInsert`, `Error.isError`, `Promise.try`, `RegExp.escape`,
Temporal, `Uint8Array.fromBase64`, `Iterator.concat`, `using`): `lib es2024` gives exit=1 with
TS2550 x5, TS2304 (`Temporal`), TS2693 (`Iterator`); `lib esnext` gives exit=1 with only
`TS2339: Property 'concat' does not exist on type 'IteratorConstructor'`; with a
`// @ts-expect-error` line or a generator `concat` exit=0.

typescript-eslint side by side:

```
old recipe {typescript:7.0.2, typescript6:npm:@typescript/typescript6@^6.0.2, typescript-eslint:8.72.1}
  npm install --package-lock-only exit=1  ERESOLVE ... peer typescript@">=4.8.4 <6.1.0" from typescript-eslint@8.72.1
blog recipe {@typescript/native:npm:typescript@^7.0.2, typescript:npm:@typescript/typescript6@^6.0.2}
  npm install exit=0; npx tsc --version -> Version 7.0.2; npx tsc6 --version -> Version 6.0.3
  template + type-aware fragment from configs.md: eslint exit=0; after adding an unawaited retry() call:
  error @typescript-eslint/no-floating-promises, exit=1
```

Library variant (package.json changes, `tsconfig.build.json`, es2024, @types/node 22.20.5):

```
format/lint/types/test exit=0 (Tests 4 passed)
build:types exit=0  -> dist/types/index.d.ts (+ .d.ts.map): export declare function retry<T>(fn: (signal: AbortSignal | undefined) => Promise<T>, { attempts, baseDelayMs, signal }: RetryOptions): Promise<T>;
publint exit=0      All good!
attw --pack . --profile esm-only exit=0  node16 (from ESM) green, bundler green
attw --pack . --profile node16   exit=1  CJSResolvesToESM (expected for an ESM-only package)
npm pack --dry-run: dist/types/index.d.ts, dist/types/index.d.ts.map, package.json, src/index.js (no test file)
before the fix (exports "./src/index.js", no types): attw exit=0 "This package does not contain types."
```

Other commands run in the fix pass:

```
npx flame app.js      exit=1  Error: Unknown command 'app.js'. Use --help for usage information.
npx flame run app.js  exit=0  cpu-profile-*.html/.md/.pb and heap-profile-*.html/.md/.pb written   (@platformatic/flame 1.7.0)
node --test --test-timeout=3000 leak.test.mjs (leaked setInterval)  exit=1 after 3s, 'test timed out after 3000ms', failureType 'testTimeoutFailure', no handle list
  same with --test-force-exit                                          exit=0, # pass 1  (hides the leak)
vitest bench (Vitest 5): `import { bench } from 'vitest'` -> TypeError: bench is not a function;
  test(..., async ({ bench }) => bench.compare(...)) with --reporter=verbose -> table with hz/mean/p99/rme/samples,
  toBeFasterThan(..., { delta: 0.05 }) exit=0
ALS/worker demo: ALS store after await = r1, outside run undefined; transferred ArrayBuffer byteLength on sender = 0;
  worker Atomics.wait -> 'ok' after Atomics.notify; SharedArrayBuffer in transferList -> DataCloneError
```

TypeScript 7 JSDoc probe (claims in SKILL section 3): `@import` and `@satisfies` type-check cleanly;
`@enum` used as a type gives `TS2749: 'Dir' refers to a value, but is being used as a type here. Did
you mean 'typeof Dir'?`; Closure-style `function(string): number` gives `TS1005: '}' expected.`

Not executed this session: `node --test --test-randomize` and other Node 26-only flags (box runs
Node 22), Playwright, Vite build, Biome, hyperfine and `welch_ttest` (not installed; syntax from the
hyperfine README), autocannon, OpenTelemetry and Changesets commands, the MCP servers' tool calls.
Their syntax comes from the official docs cited above. Whether TS 7.0.2 emits declarations for
every JSDoc construct is not tested beyond the sample module.

## 5. Self-check

Re-run on 2026-10-29 after the fix pass (final edit of the agent, skill and configs files). The
`lines` value for this sources file was measured before this section was rewritten.

### 5.1 `yaml.safe_load` on both frontmatters + section-heading check + size

Command: `python3 -I selfcheck.py` (loads each frontmatter with `yaml.safe_load`, compares the agent's
H2 headings to the SPEC list in order, checks for unknown frontmatter fields and ALL-CAPS imperatives).

```
claude/agents/javascript-engineer.md yaml.safe_load OK; keys = ['name', 'description', 'model', 'skills', 'mcpServers']
  mcpServers = ['github', 'context7', 'chrome-devtools', 'playwright', 'socket-mcp'] ; skills = ['javascript-engineering'] ; model = inherit
  unknown fields: none ; tools omitted: True
skills/javascript-engineering/SKILL.md yaml.safe_load OK; keys = ['name', 'description']
agent H2 headings: ['## Role and scope', '## Operating loop', '## Toolchain baseline (October 2026)', '## Engineering rules', '## Verification gates', '## Delegation', '## MCP and skills usage', '## Anti-patterns', '## Output contract']
required headings present in order: True
lines claude/agents/javascript-engineer.md 366
lines skills/javascript-engineering/SKILL.md 329
lines skills/javascript-engineering/references/configs.md 433
lines sources/javascript.md 298
ALL-CAPS imperative words in agent: none
```

Secrets grep (`(api_key|token|secret|password)\s*[:=]\s*'...'` over the four files): no match.

### 5.2 Link check (`ghapi.sh` for GitHub links, MCP `initialize` POST for MCP endpoints, `curl -L` for the rest)

56 of 57 URLs resolved. The single non-200 entry is `http://127.0.0.1:3000/route`, the
placeholder target of an `autocannon` example command, not a reference link.

```
curl   000  http://127.0.0.1:3000/route
curl   200  https://chromiumdash.appspot.com/fetch_releases?channel=Stable&platform=Windows&num=1
curl   200  https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/
curl   200  https://developer.apple.com/documentation/safari-release-notes
curl   200  https://developer.apple.com/tutorials/data/documentation/safari-release-notes.json
ghapi  ok repo=addyosmani/agent-skills  https://github.com/addyosmani/agent-skills
ghapi  ok repo=antfu/skills  https://github.com/antfu/skills
ghapi  ok repo=denoland/deno  https://github.com/denoland/deno/releases
ghapi  ok tag=v10.0.0  https://github.com/eslint/eslint/releases/tag/v10.0.0
ghapi  ok repo=goldbergyoni/nodebestpractices  https://github.com/goldbergyoni/nodebestpractices
ghapi  ok repo=mcollina/skills  https://github.com/mcollina/skills
ghapi  ok repo=microsoft/playwright  https://github.com/microsoft/playwright/releases
ghapi  ok tag=v12.0.0  https://github.com/npm/cli/releases/tag/v12.0.0
ghapi  ok repo=oven-sh/bun  https://github.com/oven-sh/bun/releases
ghapi  ok tag=v11.0.0  https://github.com/pnpm/pnpm/releases/tag/v11.0.0
ghapi  ok tag=v12.0.0  https://github.com/pnpm/pnpm/releases/tag/v12.0.0
ghapi  ok repo=sharkdp/hyperfine  https://github.com/sharkdp/hyperfine
ghapi  ok repo=sharkdp/hyperfine  https://github.com/sharkdp/hyperfine/releases
ghapi  ok tag=v8.0.0  https://github.com/vitejs/vite/releases/tag/v8.0.0
ghapi  ok tag=v5.0.0  https://github.com/vitest-dev/vitest/releases/tag/v5.0.0
ghapi  ok repo=wshobson/agents  https://github.com/wshobson/agents
mcp-init 200  https://mcp.context7.com/mcp
mcp-init 200  https://mcp.socket.dev/
curl   200  https://nodejs.org/dist/index.json
curl   200  https://nodejs.org/en/blog/release/v25.0.0
curl   200  https://nodejs.org/en/blog/release/v26.0.0
curl   200  https://nodejs.org/en/blog/release/v26.13.0
curl   200  https://product-details.mozilla.org/1.0/firefox_versions.json
curl   200  https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.md
curl   200  https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.md
curl   200  https://raw.githubusercontent.com/changesets/changesets/main/docs/intro-to-using-changesets.md
curl   200  https://raw.githubusercontent.com/eslint/eslint/v10.13.0/docs/src/use/configure/configuration-files.md
curl   200  https://raw.githubusercontent.com/mdn/content/main/files/en-us/web/api/window/crossoriginisolated/index.md
curl   200  https://raw.githubusercontent.com/mdn/content/main/files/en-us/web/javascript/reference/global_objects/atomics/wait/index.md
curl   200  https://raw.githubusercontent.com/mdn/content/main/files/en-us/web/javascript/reference/global_objects/sharedarraybuffer/index.md
curl   200  https://raw.githubusercontent.com/nodejs/Release/main/schedule.json
curl   200  https://raw.githubusercontent.com/nodejs/node/v26.13.0/doc/api/async_context.md
curl   200  https://raw.githubusercontent.com/nodejs/node/v26.13.0/doc/api/cli.md
curl   200  https://raw.githubusercontent.com/nodejs/node/v26.13.0/doc/api/modules.md
curl   200  https://raw.githubusercontent.com/nodejs/node/v26.13.0/doc/api/net.md
curl   200  https://raw.githubusercontent.com/nodejs/node/v26.13.0/doc/api/test.md
curl   200  https://raw.githubusercontent.com/nodejs/node/v26.13.0/doc/api/worker_threads.md
curl   200  https://raw.githubusercontent.com/nodejs/undici/main/docs/docs/api/Connector.md
curl   200  https://raw.githubusercontent.com/npm/cli/v12.2.1/docs/lib/content/commands/npm-install-scripts.md
curl   200  https://raw.githubusercontent.com/npm/cli/v12.2.1/docs/lib/content/using-npm/workspaces.md
curl   200  https://raw.githubusercontent.com/npm/cli/v12.2.1/workspaces/config/lib/definitions/definitions.js
curl   200  https://raw.githubusercontent.com/open-telemetry/opentelemetry.io/main/content/en/docs/languages/js/getting-started/nodejs.md
curl   200  https://raw.githubusercontent.com/pnpm/pnpm.io/main/docs/workspaces.md
curl   200  https://raw.githubusercontent.com/sharkdp/hyperfine/master/scripts/README.md
curl   200  https://raw.githubusercontent.com/tc39/proposals/main/finished-proposals.md
curl   200  https://raw.githubusercontent.com/vitest-dev/vitest/v5.0.5/docs/guide/benchmarking.md
curl   200  https://raw.githubusercontent.com/vitest-dev/vitest/v5.0.5/docs/guide/cli-generated.md
curl   200  https://registry.npmjs.org/
curl   200  https://registry.npmjs.org/@platformatic/flame
curl   200  https://registry.npmjs.org/autocannon
curl   200  https://tc39.es/ecma262/2026/
curl   200  https://unpkg.com/@mdn/browser-compat-data/data.json
```
