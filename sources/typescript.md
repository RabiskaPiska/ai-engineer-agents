# Sources: typescript (TypeScript engineer)

Author slug: `typescript`. All facts fetched and checked on 2026-10-29.
Deliverables:
- `claude/agents/typescript-engineer.md`
- `skills/typescript-engineering/SKILL.md`
- `skills/typescript-engineering/references/configs.md`
- `skills/typescript-engineering/references/ts7-migration.md`
- `skills/typescript-engineering/references/recipes.md` (added by the 2026-10-29 fix pass)

## The 5 GitHub repos used

Each verified with `ghapi.sh repos/<owner>/<repo>` on 2026-10-29. Repo text was read as data only; no code
from these repos was run. All five are MIT or Apache-2.0; ideas were paraphrased and adapted, with no
verbatim copying beyond rule names and config keys.

### 1. typescript-eslint/typescript-eslint
```json
{"full_name": "typescript-eslint/typescript-eslint", "html_url": "https://github.com/typescript-eslint/typescript-eslint", "stargazers_count": 16458, "pushed_at": "2026-10-28T15:03:51Z", "archived": false, "license": "MIT"}
```
Read: `docs/getting-started/Typed_Linting.mdx`, `docs/users/Shared_Configurations.mdx`,
`docs/troubleshooting/faqs/TypeScript.mdx`, `docs/users/Dependency_Versions.mdx`.
Took: the flat-config typed-linting setup (`strictTypeChecked` + `stylisticTypeChecked`,
`parserOptions.projectService`, `tsconfigRootDir: import.meta.dirname`, `disableTypeChecked` for JS files),
the promise rules used as the "race detector" gate (`no-floating-promises`, `no-misused-promises`,
`switch-exhaustiveness-check`). The npm metadata of `typescript-eslint@8.72.1` (peer
`typescript >=4.8.4 <6.1.0`) drove the TS 6 alias recommendation.

### 2. microsoft/TypeScript
```json
{"full_name": "microsoft/TypeScript", "html_url": "https://github.com/microsoft/TypeScript", "stargazers_count": 111661, "pushed_at": "2026-10-29T06:20:52Z", "archived": false, "default_branch": "main", "language": "Go", "license": "Apache-2.0"}
```
Read: `tsc/CHANGES.md` (436 lines; TS 6 vs 7 behavior differences: JSDoc/JS checking, template literal
code points, strict-false argument omission). The repo now holds the Go codebase. The old
`microsoft/typescript-go` staging repo is archived (`"archived": true`, pushed_at 2026-08-31) and its
`CHANGES.md` has identical headings (diffed this session).
Took: the "Behavior differences worth testing" list in `references/ts7-migration.md`.

### 3. Jeffallan/claude-skills
```json
{"full_name": "Jeffallan/claude-skills", "html_url": "https://github.com/Jeffallan/claude-skills", "stargazers_count": 12124, "pushed_at": "2026-10-29T01:36:45Z", "archived": false, "license": "MIT"}
```
Read: `skills/typescript-pro/SKILL.md`, `references/configuration.md`, `references/patterns.md`.
Took: the skill layout (core file plus a "load when" table pointing to `references/`), branded types created
only through a constructor, exhaustive `never` switch, "prefer `as const` objects over enums".
Rejected: its `skipLibCheck: false` default (slow, noisy for apps), `target: ES2022` (stale for Node 26),
and "type coverage" percentages as a gate (no current tool chosen for it).

### 4. wshobson/agents
```json
{"full_name": "wshobson/agents", "html_url": "https://github.com/wshobson/agents", "stargazers_count": 41969, "pushed_at": "2026-10-26T01:08:14Z", "archived": false, "license": "MIT"}
```
Read: `plugins/javascript-typescript/agents/typescript-pro.md`,
`plugins/javascript-typescript/skills/typescript-advanced-types/SKILL.md`,
`plugins/conductor/templates/code_styleguides/typescript.md`.
Took: the "Use PROACTIVELY" description pattern, `unknown` + type-guard narrowing, wrapping errors with
`{ cause }`, interface-vs-type guidance, and the type-testing section idea (turned into `*.test-d.ts` +
`expectTypeOf` gates). Rejected: its listing of every strict sub-flag (redundant under `strict: true`).

### 5. mattpocock/skills
```json
{"full_name": "mattpocock/skills", "html_url": "https://github.com/mattpocock/skills", "stargazers_count": 306091, "pushed_at": "2026-10-27T07:44:25Z", "archived": false, "license": "MIT"}
```
Read: `skills/in-progress/setup-ts-deep-modules/SKILL.md`.
Took: module boundaries (root entry points public, subfolders private, no barrels, no cycles) enforced
with dependency-cruiser (TS-MOD-4), and the "prove the rule bites" practice: pass, seed a violation and see
it fail, revert and pass. That practice became the seeded-defect table in SKILL.md section 4.

### Read but not counted among the 5
- VoltAgent/awesome-claude-code-subagents `categories/02-language-specialists/typescript-pro.md`
  (26164 stars, pushed 2026-10-11, MIT): rejected as a source because it targets "TypeScript 5.0+" and
  recommends `const enum` for performance, which is not erasable (fails `erasableSyntaxOnly` and Node type
  stripping). A local `const enum` does compile under `isolatedModules` (TS 7.0.2 and 6.0.3, checked); only
  ambient ones fail there (`TS2748`).

## MCP servers declared in the agent

| Server | Repo (ghapi verified) | Stars / pushed_at / license | Install command (from the README or official docs) |
|---|---|---|---|
| github | github/github-mcp-server | 34054 / 2026-10-29 / MIT | by-name reference (pre-configured per SPEC) |
| context7 | upstash/context7 | 63882 / 2026-10-28 / MIT | `type: http`, `url: https://mcp.context7.com/mcp` (README line 59). A POST `initialize` to that URL returned HTTP 200 on 2026-10-29 without a key |
| eslint | eslint/rewrite (`packages/mcp`, npm `@eslint/mcp` 0.3.15, 2026-10-16) | 352 / 2026-10-27 / Apache-2.0 | Declared pinned as `npx @eslint/mcp@0.3.15`. The docs (eslint.org/docs/latest/use/mcp) show `npx @eslint/mcp@latest`; README also shows `npx eslint --mcp` |
| playwright | microsoft/playwright-mcp (npm `@playwright/mcp` 0.0.83, 2026-09-28) | 38797 / 2026-10-22 / Apache-2.0 | Declared pinned as `npx @playwright/mcp@0.0.83`. README shows `claude mcp add playwright npx @playwright/mcp@latest` |
| serena | oraios/serena | 30833 / 2026-10-28 / per-component (SolidLSP MIT, app GPL-3.0-or-later; GitHub reports NOASSERTION) | `uv tool install -p 3.13 serena-agent`, `serena init`; launch `serena start-mcp-server --context claude-code --project-from-cwd` (docs `02-usage/030_clients.md`) |

The stdio servers were not started this session (their install commands are from the docs; untested here).
Pinning: both versions re-checked with `npm view <pkg> version time --json` on 2026-10-29 (`@eslint/mcp`
0.3.15 published 2026-10-16T17:04:59Z; `@playwright/mcp` 0.0.83 published 2026-09-28T23:19:13Z, still
`latest`). The agent tells the user to refresh them monthly.

## Additional tool repos referenced (not among the 5; verified with ghapi.sh 2026-10-29)

```json
{"full_name": "gitleaks/gitleaks", "stargazers_count": 30478, "pushed_at": "2026-10-28T04:14:29Z", "archived": false, "license": "MIT"}
{"full_name": "changesets/changesets", "stargazers_count": 12542, "pushed_at": "2026-10-26T07:22:21Z", "archived": false, "license": "MIT"}
{"full_name": "changesets/action", "stargazers_count": 1092, "pushed_at": "2026-10-23T06:41:58Z", "archived": false, "license": "MIT"}
{"full_name": "ota-meshi/eslint-plugin-regexp", "stargazers_count": 782, "pushed_at": "2026-10-29T03:35:39Z", "archived": false, "license": "MIT"}
```
Used for: gitleaks commands and exit codes (README "Usage", "Exit Codes"; latest release v8.30.1, 2026-03-21);
changesets CLI commands (`docs/command-line-options.md`, `docs/automating-changesets.md`,
`docs/checking-for-changesets.md`) and the action's sub-actions and `id-token: write` note (README,
`select-mode/`, `version/`, `publish/` READMEs; latest release v2.1.2); eslint-plugin-regexp flat-config
usage and rule list (README in the installed 3.3.2 package). `actions/checkout` and `actions/setup-node`:
latest releases v7.0.1 (2026-07-20) and v7.1.0 (2026-10-08), `refs/tags/v7` exists for both, and
`setup-node`'s `action.yml` on the default branch has `registry-url` and `package-manager-cache`.

## Official version sources (fetched 2026-10-29)

| Fact | Source |
|---|---|
| TypeScript 7.0 GA 2026-07-08, no API in 7.0, `@typescript/typescript6` alias, `--checkers`/`--builders`/`--singleThreaded`, new defaults, hard errors | https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/ |
| TypeScript 6.0 2026-03-23: default changes, deprecations, `#/` subpath imports, es2025, Temporal types (`esnext`/`esnext.temporal`) | https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/ |
| TypeScript 7.1 beta 2026-10-20: API entry points, `--target es2026`, import attributes in ambient modules | https://devblogs.microsoft.com/typescript/announcing-typescript-7-1-beta/ |
| npm versions and publish times (typescript 7.0.2, 6.0.3; typescript-eslint 8.72.1; eslint 10.13.0; vitest 5.0.5; biome 2.6.4; oxlint 1.90.0; prettier 3.9.10; pnpm 12.16.1; npm 12.2.1; jest 30.5.2; @playwright/test 1.64.1; vite 8.3.5; rolldown 1.2.15; tsdown 0.23.3; tsup 9.0.0; tsx 4.23.15; publint 0.3.25; @arethetypeswrong/cli 0.18.5; knip 6.43.0; dependency-cruiser 18.7.0; zod 4.6.7; fast-check 4.10.2; @stryker-mutator/core 10.1.1; @types/node 26.6.6; @typescript/typescript6 6.0.2) | https://registry.npmjs.org/<package> (`dist-tags.latest` + `time`) |
| Node.js 26.13.0 LTS "Lithium" 2026-10-28 (npm 11.20.0), 24.22.2, 22.23.4, 20 EOL | https://nodejs.org/dist/index.json and https://github.com/nodejs/Release/blob/main/schedule.json |
| Node 26.0.0 (2026-05-05): Temporal on by default | https://nodejs.org/en/blog/release/v26.0.0 |
| Node type stripping stable (v25.2.0/v24.12.0), `erasableSyntaxOnly` recommendation, `.tsx` unsupported | https://github.com/nodejs/node/blob/v26.13.0/doc/api/typescript.md |
| Node Permission Model stable, `--permission-audit` | https://github.com/nodejs/node/blob/v26.13.0/doc/api/permissions.md |
| Bun 1.4.4 (2026-10-22), Deno 2.9.8 (2026-10-21) | GitHub releases API: repos/oven-sh/bun/releases/latest, repos/denoland/deno/releases/latest |
| ESLint v10.0.0 2026-02-06: eslintrc removed, Node >=20.19 | https://eslint.org/blog/2026/02/eslint-v10.0.0-released |
| Vitest 5.0 2026-09-03: Node >=22.12, Vite >=6.4, `clearMocks` default, unawaited async assertions fail, bench rewrite | https://vitest.dev/blog/vitest-5.html , https://vitest.dev/guide/migration |
| Vitest CLI flags (`--typecheck.enabled`, `--typecheck.only`, coverage options), `vitest bench` | https://vitest.dev/guide/cli , https://vitest.dev/guide/benchmarking |
| pnpm 11.0 (2026-04-28) safe defaults; pnpm 12.0 (2026-08-26) Rust rewrite | https://pnpm.io/blog/releases/11.0 , https://pnpm.io/blog/releases/12.0 |
| oxlint type-aware (`--type-aware`, `--type-check`, requires TS 7.0+), CLI `--deny-warnings` | https://oxc.rs/docs/guide/usage/linter/type-aware.html , https://oxc.rs/docs/guide/usage/linter/cli.html |
| Biome `noFloatingPromises` (types domain, nursery) | https://biomejs.dev/linter/rules/no-floating-promises |
| `#/` subpath imports allowed from Node v25.4.0 / v24.14.0 (YAML history of "Subpath imports") | https://github.com/nodejs/node/blob/v26.13.0/doc/api/packages.md |
| `--unhandled-rejections` modes; default `throw` since v15.0.0; `strict` semantics; `--heapsnapshot-signal` | https://github.com/nodejs/node/blob/v26.13.0/doc/api/cli.md |
| `events.addAbortListener` (stable since v24.0.0/v22.16.0), `events.on(..., { signal })`, `MaxListenersExceededWarning` | https://github.com/nodejs/node/blob/v26.13.0/doc/api/events.md |
| `server.close()` closes only idle connections; `closeIdleConnections`/`closeAllConnections` (v18.2.0) | https://github.com/nodejs/node/blob/v26.13.0/doc/api/http.md |
| npm trusted publishing: npm >=11.5.1 and Node >=22.14, `id-token: write`, GitHub-hosted runners only, automatic provenance (public repo + public package), "Require two-factor authentication and disallow tokens", 2-day first-publish expiry, `npm stage publish` | https://docs.npmjs.com/trusted-publishers |
| `npm audit signatures` verifies registry signatures and provenance attestations; `--audit-level` "does not filter the report output, it simply changes the command's failure threshold" | https://docs.npmjs.com/cli/v11/commands/npm-audit |
| Node 26.13.0 bundles npm 11.20.0, 24.22.2 bundles 11.19.1, 22.23.4 bundles 10.9.9 | https://nodejs.org/dist/index.json |
| OpenTelemetry zero-code Node setup (`--require @opentelemetry/auto-instrumentations-node/register`, `OTEL_*` variables) | https://opentelemetry.io/docs/zero-code/js/ |
| pino log correlation (`trace_id`, `span_id`) by `@opentelemetry/instrumentation-pino` 0.70.0 | https://registry.npmjs.org/@opentelemetry/instrumentation-pino (README) |
| XSS output encoding, CSP, session cookie attributes, CSRF (synchronizer / signed double-submit / `Sec-Fetch-Site`), ReDoS | https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html , https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html , https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html , https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html , https://owasp.org/www-community/attacks/Regular_expression_Denial_of_Service_-_ReDoS |
| `__Host-` cookie prefix rules; CORS | https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie , https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS |
| `no-implied-eval` / `no-new-func` rules; `regexp/no-super-linear-backtracking` | https://typescript-eslint.io/rules/no-implied-eval/ , https://eslint.org/docs/latest/rules/no-new-func , https://ota-meshi.github.io/eslint-plugin-regexp/rules/no-super-linear-backtracking.html |
| Vitest 5 bench API: `bench().run(opts)`, `bench.compare`, `toBeFasterThan(..., { delta })`, `writeResult`, `bench.from`, `benchmark.include` | https://vitest.dev/guide/benchmarking |
| knip configuration (`entry`, `project`) | https://knip.dev/reference/configuration |
| npm versions added in the fix pass (registry `dist-tags.latest` + `time`, 2026-10-29): knip 6.43.0, eslint-plugin-regexp 3.3.2 (peer eslint >=9.38.0), @changesets/cli 3.0.3, re2js 2.9.1 (no install scripts), re2 1.27.0 (native install script), pino 10.4.0, lru-cache 11.5.3, @opentelemetry/sdk-node 0.300.0 and auto-instrumentations-node 0.82.0 (Node >=22.15.0), helmet 8.3.0, @eslint/mcp 0.3.15, @playwright/mcp 0.0.83 | https://registry.npmjs.org/<package> |

## Executed verification of the templates (2026-10-29, local Node v22.23.1, npm 10.9.8)

Scratch project with the exact files in `references/configs.md`, installed with `npm install --ignore-scripts`:
- `npx tsc --version` -> `Version 7.0.2`; `npx tsc6 --version` -> `Version 6.0.3`.
- `npm run check` (prettier, eslint `--max-warnings=0`, `tsc --noEmit`, `vitest run --coverage`) -> `CHECK_EXIT=0`,
  `Lines : 100% ( 10/10 )`.
- Seeded `save();` -> eslint `@typescript-eslint/no-floating-promises`, `LINT_EXIT=1`; oxlint `--type-aware`
  `typescript(no-floating-promises)`, `OX_EXIT=1`.
- Seeded `xs[0].length` -> `src/bad.ts(7,10): error TS18048: 'first' is possibly 'undefined'.`, `TSC_EXIT=1`.
- Seeded `export enum Color { Red }` -> `error TS1294: This syntax is not allowed when 'erasableSyntaxOnly' is enabled.`, exit 1.
- Wrong `expectTypeOf` -> `TypeCheckError`, `TC_BAD=1`; correct type test -> `Type Errors  no errors`, exit 0.
- `vitest run --sequence.shuffle` -> exit 0. `node src/cli.ts 42` (type stripping) -> `ok:42`.
- zod 4 env snippet type-checks and runs (`5433`). `Temporal` without `esnext.temporal` -> `TS2304`; with it -> exit 0.
- `tsc -p tsconfig.build.json` -> exit 0, emitted imports rewritten to `./money.js`.
- `publint` -> `All good!`; `attw --pack . --profile esm-only` -> exit 0 (node16-from-ESM and bundler green).
- `tsc --noEmit --extendedDiagnostics` (TS 7) prints `Check time` / `Total time`.
- Re-run after aligning `@types/node` to the engines floor (`^22.20.5`, published 2026-10-01): `CHECK_EXIT=0`, `BUILD=0`, `PKG=0`.
- A defect in my first coverage config (test-d file counted as source) was caught by this run and fixed in the template.
- `npm audit --audit-level=high` -> exit 0 (`found 0 vulnerabilities` in this project; in general exit 0 means
  no high or critical advisories, lower ones can still be listed).

## Executed verification of the 2026-10-29 fix pass

Change log with defect -> change -> evidence: `_work/fixes/typescript.md`. Scratch projects lived in the
session scratchpad; Node 22.23.1 locally plus the official Node 26.13.0 linux-x64 tarball (SHA-256 checked
against `SHASUMS256.txt`) for runtime comparisons.
- `configs.md` extracted byte for byte by a script into an empty dir, `npm install --ignore-scripts` (no
  edits): `npm run check` (Prettier, ESLint, `tsc`, coverage, knip) `CHECK_EXIT=0`; `BUILD=0`, `dist/` has no
  bench file; `check:package` `PKG=0`; `npx knip` `KNIP=0`; `npx vitest bench` `BENCH=0`;
  `npx vitest run --typecheck.only` exit 0; `--sequence.shuffle` x3 exit 0; `npx tsc6 --noEmit` exit 0;
  `npm audit signatures` exit 0 (227 verified registry signatures, 76 verified attestations).
- The previous `configs.md` text extracted verbatim: `CHECK_EXIT=1` with `[warn] .oxlintrc.json`,
  `[warn] eslint.config.mjs`, `[warn] package.json` (reproduces the format defect).
- knip 6.43.0 without `knip.json`: `Unused files (1) src/money.test-d.ts`, exit 1; with it: exit 0; seeded
  `src/orphan.ts`: `Unused files (1)`, exit 1.
- `attw --pack .` with no profile on the ESM-only template: exit 1 (`node10` Resolution failed,
  `node16 (from CJS)` ESM dynamic import only); `--profile esm-only`: exit 0.
- `#/*` imports: Node 22.23.1 `ERR_INVALID_MODULE_SPECIFIER`, exit 1; Node 26.13.0 exit 0; `#src/*` on Node 22
  exit 0. `"#src/*": "./dist/*"` with `#src/a.js`: `tsc --noEmit` exit 0 before any build (TS 7.0.2 and
  6.0.3), built `dist/main.js` runs. `"#src/*": "./src/*"` with `#src/a.ts`: `TS2877` under
  `rewriteRelativeImportExtensions`, exit 0 with `allowImportingTsExtensions`.
- const enum: local `export const enum` imported across files with `isolatedModules: true`: TS 7.0.2 exit 0,
  `tsc6` exit 0; with `erasableSyntaxOnly`: `TS1294`; ambient `declare const enum` in `.d.ts`: `TS2748` (both
  compilers); Node 22 and 26 type stripping: `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX`.
- `tsc6 --noEmit src/money.ts` and `tsc --noEmit src/money.ts` with a tsconfig present: `error TS5112`, exit 1;
  `tsc6 --ignoreConfig` exit 0.
- Security lint: seeded `/^(a+)+$/`, `eval`, `new Function`, `setTimeout("...")` -> `regexp/no-super-linear-backtracking`,
  `no-eval`, `no-new-func`, `@typescript-eslint/no-implied-eval` x2, exit 1. The first sample regex with an
  unused capture group failed `regexp/no-unused-capturing-group`; the template now uses `(?:...)`.
- gitleaks 8.30.1 (release tarball, checksum verified): clean repo `no leaks found` exit 0; committed
  `ghp_...` token `leaks found: 1` exit 1 (`gitleaks git`), and exit 1 with `gitleaks dir`.
- Race stress test (2000 deposits, 3 keys, random 0-3 `setImmediate` yields): with the lock exit 0 for seeds 1,
  42, 987654; without it `expected 117 to be 2000`, exit 1.
- Benchmark statistics: `bench-stats.mjs` p-values equal `scipy.stats.mannwhitneyu` (asymptotic, continuity
  correction) to 5 decimals on 5 synthetic sets including ties. Interleaved 10+10 real runs: identical code
  `change 0.0183, p 0.47268, OK`, exit 0; 3x slower candidate `change 2.1442, p 0.00018, REGRESSION`, exit 1.
  A `writeResult` path outside the project root fails the run; `latency.p50` was exactly 0.0001 ms
  (quantized), hence the per-run mean.
- `resolveInside()` safe-path tests: 9 cases pass (symlink escape and new file under a symlinked dir rejected,
  root itself accepted).
- Graceful shutdown tests: first version exit 1 on the drain test (`expected 1 to be +0`: keep-alive socket
  held `server.close()` open); with the idle-connection sweep both tests pass.
- Heap-growth script: bounded `growthMB 0` exit 0; unbounded `growthMB 60.9` exit 1;
  `--heapsnapshot-signal=SIGUSR2` wrote `Heap.20261029.101009.1323960.0.001.heapsnapshot`.
- All recipe code: `prettier --check` exit 0, `eslint --max-warnings=0` exit 0, `tsc` and `tsc6` exit 0, knip
  exit 0, `vitest run` 12/12 passed. `publish.yml`: `yaml.safe_load` OK, Prettier OK; not run on GitHub.

## Self-check

Output of the self-check script (re-run 2026-10-29 after the fix pass: `yaml.safe_load` on both frontmatters,
agent field whitelist from SPEC, required-heading order, line counts, `ghapi.sh repos/<owner>/<repo>` for every
github.com repo URL in the deliverables including `references/recipes.md`, and `curl -sL` status for every
other URL; this section itself is excluded from the scan):

```text
yaml.safe_load(claude/agents/typescript-engineer.md): OK, keys=['description', 'mcpServers', 'model', 'name', 'skills']
yaml.safe_load(skills/typescript-engineering/SKILL.md): OK, keys=['description', 'name']
agent keys subset of valid fields: True; 'tools' omitted: True; name=typescript-engineer; skills=['typescript-engineering']
mcpServers: ['github', 'context7', 'eslint', 'playwright', 'serena']
required headings present in order: True (found 9: ['## Role and scope', '## Operating loop', '## Toolchain baseline (October 2026)', '## Engineering rules', '## Verification gates', '## Delegation', '## MCP and skills usage', '## Anti-patterns', '## Output contract'])
line counts: agent=330 skill=384 configs.md=360 ts7-migration.md=85 recipes.md=577 typescript.md=276
ghapi repos/Jeffallan/claude-skills: OK archived=False
ghapi repos/mattpocock/skills: OK archived=False
ghapi repos/microsoft/TypeScript: OK archived=False
ghapi repos/nodejs/Release: OK archived=False
ghapi repos/nodejs/node: OK archived=False
ghapi repos/typescript-eslint/typescript-eslint: OK archived=False
ghapi repos/wshobson/agents: OK archived=False
curl https://biomejs.dev/linter/rules/no-floating-promises: 200
curl https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html: 200
curl https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html: 200
curl https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html: 200
curl https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html: 200
curl https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/: 200
curl https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/: 200
curl https://devblogs.microsoft.com/typescript/announcing-typescript-7-1-beta/: 200
curl https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS: 200
curl https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie: 200
curl https://docs.npmjs.com/cli/v11/commands/npm-audit: 200
curl https://docs.npmjs.com/trusted-publishers: 200
curl https://eslint.org/blog/2026/02/eslint-v10.0.0-released: 200
curl https://eslint.org/docs/latest/rules/no-new-func: 200
curl https://github.com/nodejs/Release/blob/main/schedule.json: 200
curl https://github.com/nodejs/node/blob/v26.13.0/doc/api/cli.md: 200
curl https://github.com/nodejs/node/blob/v26.13.0/doc/api/events.md: 200
curl https://github.com/nodejs/node/blob/v26.13.0/doc/api/http.md: 200
curl https://github.com/nodejs/node/blob/v26.13.0/doc/api/packages.md: 200
curl https://github.com/nodejs/node/blob/v26.13.0/doc/api/permissions.md: 200
curl https://github.com/nodejs/node/blob/v26.13.0/doc/api/typescript.md: 200
curl https://knip.dev/reference/configuration: 200
curl https://mcp.context7.com/mcp: 405
curl https://nodejs.org/dist/index.json: 200
curl https://nodejs.org/en/blog/release/v26.0.0: 200
curl https://opentelemetry.io/docs/zero-code/js/: 200
curl https://ota-meshi.github.io/eslint-plugin-regexp/rules/no-super-linear-backtracking.html: 200
curl https://owasp.org/www-community/attacks/Regular_expression_Denial_of_Service_-_ReDoS: 200
curl https://oxc.rs/docs/guide/usage/linter/cli.html: 200
curl https://oxc.rs/docs/guide/usage/linter/type-aware.html: 200
curl https://pnpm.io/blog/releases/11.0: 200
curl https://pnpm.io/blog/releases/12.0: 200
curl https://registry.npmjs.org: 200
curl https://registry.npmjs.org/: 200
curl https://registry.npmjs.org/@opentelemetry/instrumentation-pino: 200
curl https://typescript-eslint.io/rules/no-implied-eval/: 200
curl https://unpkg.com/knip@6/schema.json: 200
curl https://vitest.dev/blog/vitest-5.html: 200
curl https://vitest.dev/guide/benchmarking: 200
curl https://vitest.dev/guide/cli: 200
curl https://vitest.dev/guide/migration: 200
```

Notes: `https://mcp.context7.com/mcp` answers 405 to a plain GET because it is an MCP Streamable HTTP endpoint;
a POST `initialize` request returned 200 (checked separately). `github.com/andrewbranch/ts5to6` (cited in
`ts7-migration.md` as plain text) exists per ghapi (pushed 2025-11-18, no license file). The five counted repos
were also verified individually above with their JSON fields.
