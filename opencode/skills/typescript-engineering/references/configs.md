# Tested config templates (TypeScript 7.0.2 + TS 6 API alias, ESLint 10, Vitest 5)

Every file below was extracted from this page by a script, byte for byte, into an empty project on
2026-10-29 (Node 22.23.1 and npm 10.9.8 locally; the same files target Node 26 LTS) and run with no manual
edits. Results: `npm run check` (Prettier, ESLint, `tsc`, Vitest with coverage, knip) exit 0; `npm run build`
exit 0; `npm run check:package` exit 0 (`publint` "All good!", `attw --profile esm-only` green for
`node16 (from ESM)` and `bundler`); `npx vitest bench` exit 0; `npm audit signatures` exit 0; seeded defects
failed the expected gate (SKILL.md section 4). Adapt names and paths; keep the flags unless you know why to
drop one.

The files are already Prettier-formatted. If you edit them or paste them by hand, run `npx prettier --write .`
once before the first `npm run check`, or the format gate fails (an earlier version of this page failed it
with `[warn] eslint.config.mjs [warn] package.json`).

## package.json (ESM library or service)

```json
{
  "name": "@example/money",
  "version": "0.1.0",
  "type": "module",
  "license": "MIT",
  "engines": {
    "node": ">=22.13"
  },
  "exports": {
    ".": {
      "types": "./dist/money.d.ts",
      "default": "./dist/money.js"
    },
    "./package.json": "./package.json"
  },
  "files": [
    "dist",
    "src",
    "!src/**/*.test.ts",
    "!src/**/*.test-d.ts",
    "!src/**/*.bench.ts"
  ],
  "sideEffects": false,
  "scripts": {
    "format:check": "prettier --check .",
    "lint": "eslint . --max-warnings=0",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:coverage": "vitest run --coverage",
    "knip": "knip",
    "check": "npm run format:check && npm run lint && npm run typecheck && npm run test:coverage && npm run knip",
    "build": "tsc -p tsconfig.build.json",
    "check:package": "publint && attw --pack . --profile esm-only"
  },
  "devDependencies": {
    "@arethetypeswrong/cli": "^0.18.5",
    "@eslint/js": "10.0.1",
    "@types/node": "^22.20.5",
    "@typescript/native": "npm:typescript@7.0.2",
    "@vitest/coverage-v8": "5.0.5",
    "eslint": "10.13.0",
    "eslint-plugin-regexp": "3.3.2",
    "knip": "6.43.0",
    "prettier": "3.9.10",
    "publint": "^0.3.25",
    "typescript": "npm:@typescript/typescript6@6.0.2",
    "typescript-eslint": "8.72.1",
    "vite": "8.3.5",
    "vitest": "5.0.5"
  }
}
```

Why the two TypeScript entries: `typescript` is aliased to the TS 6 compatibility package so
typescript-eslint (peer `typescript <6.1.0`) can import the compiler API; `@typescript/native` provides
TS 7's `tsc` binary. Observed: `npx tsc --version` prints `Version 7.0.2`, `npx tsc6 --version` prints
`Version 6.0.3`. If the repo does not use typescript-eslint typed rules, use plain `"typescript": "^7.0.2"`.

`@types/node` follows the `engines.node` floor (22 here), so the compiler rejects Node APIs that the
oldest supported runtime lacks. Raise both together (for example `>=26` with `@types/node@^26.6.6`).

`check:package` uses `--profile esm-only` because this package is ESM-only: without the profile, attw also
grades `node10` (`Resolution failed`) and `node16 (from CJS)` (`ESM (dynamic import only)`) and exits 1
(observed). Drop the profile only for a dual CJS/ESM package, where those modes must pass.

For an application (not published): drop `exports`, `files`, `sideEffects`, `check:package`; add `"private": true`.
For a service run with Node type stripping: drop `build`, set `noEmit: true` in tsconfig, start with `node src/main.ts`.

### Internal import aliases (`package.json#imports`)

Pick the prefix by the runtime floor. With `engines.node` `>=22.13`, `"#/*"` is not usable: Node 22.23.1
throws `ERR_INVALID_MODULE_SPECIFIER` for `#/a.ts` (observed), because Node accepts `#/` only from v25.4.0 /
v24.14.0 (Node 26.13.0 runs the same file). Use a named prefix:

```json
{ "imports": { "#src/*": "./dist/*" } }
```

Import it as `#src/money.js`. With `rootDir: ./src` and `outDir: ./dist`, `tsc --noEmit` resolves it to
`src/money.ts` even before the first build (observed with TS 7.0.2 and 6.0.3), and the built
`dist/main.js` runs. For a type-stripping app with no build, map `"#src/*": "./src/*"`, import `#src/x.ts`,
and use `allowImportingTsExtensions` instead of `rewriteRelativeImportExtensions` (the latter reports
`TS2877` for non-relative `.ts` imports).

## tsconfig.json

```json
{
  "compilerOptions": {
    "target": "es2025",
    "lib": ["es2025"],
    "module": "nodenext",
    "moduleResolution": "nodenext",
    "rootDir": "./src",
    "outDir": "./dist",
    "types": ["node"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noPropertyAccessFromIndexSignature": true,
    "useUnknownInCatchVariables": true,
    "verbatimModuleSyntax": true,
    "erasableSyntaxOnly": true,
    "isolatedModules": true,
    "rewriteRelativeImportExtensions": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "skipLibCheck": true
  },
  "include": ["src"]
}
```

Notes:
- `lib: ["es2025"]` has no DOM. Add `"dom"` for browser code (TS 6.0+ `dom` already includes
  `dom.iterable`/`dom.asynciterable`). Add `"esnext.temporal"` to type the `Temporal` global (Node 26).
- `rootDir` and `types` are explicit because TS 6/7 changed their defaults (`./` and `[]`).
- `rewriteRelativeImportExtensions` lets source import `./money.ts`; emitted JS imports `./money.js`.
- Bundler projects: `"module": "preserve"`, `"moduleResolution": "bundler"`, `"noEmit": true`, drop
  `rewriteRelativeImportExtensions`, `declaration*`, `outDir`.

## tsconfig.build.json (emit without tests and benchmarks)

```json
{
  "extends": "./tsconfig.json",
  "compilerOptions": { "noEmit": false },
  "exclude": ["src/**/*.test.ts", "src/**/*.test-d.ts", "src/**/*.bench.ts"]
}
```

The `*.bench.ts` exclude matters: without it the build emitted `dist/money.bench.js`, which shipped in the
package and which `vitest bench` then ran as a second benchmark file (observed).

## eslint.config.mjs (ESLint 10, flat config, typed and security rules)

```js
// @ts-check
import js from "@eslint/js";
import { defineConfig } from "eslint/config";
import regexp from "eslint-plugin-regexp";
import tseslint from "typescript-eslint";

export default defineConfig(
  { ignores: ["dist/", "coverage/", ".vitest/"] },
  {
    files: ["**/*.ts"],
    extends: [
      js.configs.recommended,
      tseslint.configs.strictTypeChecked,
      tseslint.configs.stylisticTypeChecked,
      regexp.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        projectService: { allowDefaultProject: ["*.config.ts"] },
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      "@typescript-eslint/switch-exhaustiveness-check": "error",
      "@typescript-eslint/consistent-type-imports": "error",
      "@typescript-eslint/no-import-type-side-effects": "error",
      "no-eval": "error",
      "no-new-func": "error",
    },
  },
  {
    files: ["**/*.{js,mjs}"],
    extends: [js.configs.recommended, tseslint.configs.disableTypeChecked],
  },
);
```

`allowDefaultProject` is needed for root config files outside `include` (without it ESLint reported
"vitest.config.ts was not found by the project service", observed). `strictTypeChecked` already enables
`@typescript-eslint/no-implied-eval`; `no-eval` and `no-new-func` are core rules that no shared config here
turns on. `regexp.configs.recommended` includes `regexp/no-super-linear-backtracking` (ReDoS). The `.js`/`.mjs`
block defines no Node globals, so scripts import them (`import process from "node:process"`), as
`scripts/bench-stats.mjs` in `recipes.md` does.

## oxlint alternative (typescript-go powered type-aware rules)

```bash
npm add -D oxlint oxlint-tsgolint
npx oxlint --type-aware --deny-warnings          # observed: silent, exit 0 when clean
```

### .oxlintrc.json

```json
{
  "plugins": ["typescript"],
  "rules": {
    "typescript/no-floating-promises": "error",
    "typescript/no-misused-promises": "error"
  }
}
```

Requires a tsconfig that is valid for TS 7 (no `baseUrl`, no deprecated options). `oxlint --type-aware --type-check`
also reports compiler diagnostics and can replace a separate `tsc --noEmit` step; keep `tsc` if you emit.

## vitest.config.ts (Vitest 5)

```ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["src/**/*.test.ts"],
    benchmark: { include: ["src/**/*.bench.ts"] },
    coverage: {
      provider: "v8",
      include: ["src/**/*.ts"],
      exclude: ["src/**/*.{test,test-d,bench}.ts"],
      thresholds: { lines: 90, branches: 85, functions: 90, statements: 90 },
    },
  },
});
```

The `exclude` must list `*.test-d.ts`: with only `*.test.ts` excluded, the type-test file was counted as
uncovered source and the run failed its thresholds (observed 83.33% lines, exit 1). Vitest 5 writes
reports under `.vitest/`; it is in `.gitignore` and `.prettierignore` below.

## knip.json

```json
{
  "$schema": "https://unpkg.com/knip@6/schema.json",
  "entry": ["src/**/*.test-d.ts", "src/**/*.bench.ts"],
  "project": ["src/**/*.ts"]
}
```

Without this file knip 6.43.0 reported `Unused files (1) src/money.test-d.ts` and exited 1 (observed): the
Vitest plugin picks up `*.test.ts` from `vitest.config.ts`, but nothing references type-test files.
With it, `npx knip` is silent and exits 0; a seeded unreferenced `src/orphan.ts` still fails it. An entry
pattern with no matching file prints a "Configuration hints" note but does not change the exit code.

## Sample source and tests

### `src/money.ts`

```ts
export type ParseResult =
  | { readonly ok: true; readonly cents: number }
  | { readonly ok: false; readonly error: "invalid" };

export function parseCents(raw: string): ParseResult {
  if (!/^\d+(?:\.\d{1,2})?$/.test(raw)) return { ok: false, error: "invalid" };
  return { ok: true, cents: Math.round(Number(raw) * 100) };
}
```

The group is non-capturing on purpose: `(\.\d{1,2})` fails `regexp/no-unused-capturing-group` (observed).

### `src/money.test.ts`

```ts
import { expect, test } from "vitest";
import { parseCents } from "./money.ts";

test("parses", () => {
  expect(parseCents("1.25")).toEqual({ ok: true, cents: 125 });
  expect(parseCents("x")).toEqual({ ok: false, error: "invalid" });
});
```

### Type test (`src/money.test-d.ts`)

```ts
import { expectTypeOf, test } from "vitest";
import { parseCents, type ParseResult } from "./money.ts";

test("parseCents returns the result union", () => {
  expectTypeOf(parseCents).returns.toEqualTypeOf<ParseResult>();
});
```
Run with `npx vitest run --typecheck.only` (type tests only) or `--typecheck.enabled` (alongside unit tests).

### Benchmark (`src/money.bench.ts`)

```ts
import { test } from "vitest";
import { parseCents } from "./money.ts";

// BENCH_OUT lets a driver store one result file per run; it must stay inside the project.
const out = process.env["BENCH_OUT"] ?? "./benchmarks/parseCents.json";

test("parseCents", async ({ bench }) => {
  await bench("parseCents", { writeResult: out }, () => {
    if (!parseCents("12.34").ok) throw new Error("unexpected parse failure");
  }).run({ time: 500 });
});
```

Run options such as `time` go to `.run()`; the second argument of `bench()` takes `writeResult` and hooks.
Using the result (the `throw`) keeps the engine from eliminating the call. A `writeResult` path outside
the project root fails the run (observed). See `recipes.md` for the interleaved A/B procedure.

## .gitignore

```
node_modules
dist
coverage
.vitest
bench-out
```

`bench-out/` holds per-run A/B results; commit `benchmarks/` (the baselines).

## .prettierignore

```
node_modules
dist
coverage
.vitest
bench-out
benchmarks
package-lock.json
pnpm-lock.yaml
```

## CI job outline (any CI)

```bash
npm ci                                   # or: pnpm install --frozen-lockfile
npm audit signatures                     # registry signatures + provenance
npm run check                            # format, lint, typecheck, tests + coverage, knip
npm run build && npm run check:package   # libraries
npm audit --audit-level=high             # exit 0 = no high/critical advisories
gitleaks git --redact .                  # secret scan (gitleaks 8.30.1 binary)
```

Publishing runs in its own job through npm trusted publishing; see `recipes.md`.
