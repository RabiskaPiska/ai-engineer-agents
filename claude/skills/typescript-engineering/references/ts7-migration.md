# Migrating to TypeScript 7 (from 5.x or 6.0)

Sources: "Announcing TypeScript 6.0" (2026-03-23), "Announcing TypeScript 7.0" (2026-07-08),
"Announcing TypeScript 7.1 Beta" (2026-10-20) on devblogs.microsoft.com/typescript, and
`tsc/CHANGES.md` in microsoft/TypeScript (the Go codebase now lives there; the old microsoft/typescript-go
staging repo is archived and holds an identical copy). Fetched 2026-10-29.

## Path

1. Get green on TypeScript 6.0 first (`npm i -D typescript@6`). 7.0 is designed so code that compiles
   cleanly on 6.0 with `stableTypeOrdering` on and without `ignoreDeprecations` compiles identically on 7.0.
2. Fix every 6.0 deprecation warning instead of setting `"ignoreDeprecations": "6.0"`; 7.0 turns them into
   hard errors. The experimental `ts5to6` tool (github.com/andrewbranch/ts5to6) rewrites `baseUrl` and `rootDir`.
3. Install 7.0 and run `tsc --noEmit`. Compare error counts with `tsc6` if both are installed.
4. Decide linting (SKILL.md table 2.2) and editor setup (VS Code: TypeScript 7 extension; command
   "Disable TypeScript 7 Language Server" reverts to 6.0 when a plugin needs it).

## Default changes in 6.0 (kept by 7.0)

| Option | New default | Typical symptom | Fix |
|---|---|---|---|
| `strict` | `true` | many new errors in loose code | fix them, or set `"strict": false` explicitly while migrating |
| `module` | `esnext` | CommonJS output changes | set `module` explicitly (`nodenext` for Node) |
| `target` | latest ES (es2025 in 6.0) | newer syntax in output | set `target` to your runtime floor |
| `types` | `[]` | `Cannot find name 'process'` / `'describe'` | `"types": ["node"]` plus test globals if used |
| `rootDir` | tsconfig directory | output lands in `dist/src/` | `"rootDir": "./src"` |
| `noUncheckedSideEffectImports` | `true` | errors on typo'd `import "./x"` | fix the path |
| `libReplacement` | `false` | custom `@typescript/lib-*` ignored | set `true` only if you use lib replacement |
| `stableTypeOrdering` | `true` in 7.0 (cannot be off) | union order in messages/`.d.ts` differs | none; regenerate snapshots of type output |

## Hard errors in 7.0 (deprecated in 6.0)

- `target: es5`; `downlevelIteration`.
- `moduleResolution: node` / `node10` / `classic` (use `nodenext` or `bundler`).
- `module: amd | umd | systemjs | none` (use `esnext` or `preserve`); `outFile`.
- `baseUrl` (make `paths` relative to the tsconfig, or better, move to `package.json#imports`; SKILL.md
  TS-MOD-2 says which prefix your Node floor supports, since `#/*` fails on Node 22).
- `esModuleInterop: false`, `allowSyntheticDefaultImports: false`, `alwaysStrict: false`.
- `module Foo {}` namespace syntax (use `namespace`); `import x from "y" assert {...}` (use `with`).
- `/// <reference no-default-lib />` under `skipDefaultLibCheck`.

## Errors since 6.0 (not deprecations)

- `tsc file.ts` when a `tsconfig.json` exists in the directory: already an error in 6.0,
  `error TS5112: tsconfig.json is present but will not be loaded if files are specified on commandline. Use
  '--ignoreConfig' to skip this error.` Pass `--ignoreConfig` to compile the file with default options.
  Observed with both `tsc6` 6.0.3 and `tsc` 7.0.2 (exit 1; `tsc6 --ignoreConfig` exit 0).

## Behavior differences worth testing

- Template literal inference splits on Unicode code points (`"😀abc"` head is `"😀"`), which breaks
  type-level string-length utilities that assumed UTF-16 units.
- JavaScript/JSDoc checking was reworked: `@enum`, `@class`, Closure function syntax, postfix `!`,
  standalone `?` and value-as-type references are no longer recognized. Projects that type-check `.js` via
  JSDoc need a pass; see `tsc/CHANGES.md` in microsoft/TypeScript.
- With `"strict": false`, call sites can no longer omit arguments for parameters typed `undefined`/`unknown`/`any`
  (CHANGES.md shows this with JSDoc-typed JS; `void` parameters can still be omitted).

## New CLI controls

- `--checkers N` (default 4): parallel type-checker workers. More is faster on big machines and uses more memory;
  keep N fixed across environments because a different N can rarely surface order-dependent results.
- `--builders N`: parallel project-reference builds under `--build`; multiplies with `--checkers`.
- `--singleThreaded`: everything on one thread (debugging, constrained CI runners).
- `--watch` is rebuilt on a Go port of `@parcel/watcher`.

## What still needs TypeScript 6

TypeScript 7.0 ships no programmatic API. Tools that import `typescript` keep using 6.0 via
`"typescript": "npm:@typescript/typescript6@^6.0.2"` (binary `tsc6`), with TS 7 added as
`"@typescript/native": "npm:typescript@^7.0.2"` so `npx tsc` is 7.0. Affected: typescript-eslint typed rules,
webpack/ts-loader style integrations, Volar-based tooling (Vue, Svelte, Astro, MDX) and Angular template
checking. TS 7.1 (beta 2026-10-20) adds a new, different API: entry points `typescript/sync`, `typescript/async`,
`typescript/fs`, `typescript/ast`, `typescript/ast/is`, `typescript/ast/factory`, with Disposable `API`,
`Program` and snapshot objects (use `using` or call `dispose()`/`close()` to avoid leaking Go-side memory).
Do not port tools to the 7.1 API in production until 7.1 is stable and the tool's maintainers support it.

## Verification after migrating

```bash
npx tsc --version                  # expect Version 7.0.x
npx tsc --noEmit                   # zero errors
npx tsc --noEmit --extendedDiagnostics | grep -E "Check time|Total time"   # record the speedup
npm run lint && npm test           # tooling that still uses the TS 6 API keeps working
```
