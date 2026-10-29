# Config templates (JavaScript, October 2026)

Copy these instead of writing configs from memory. The set below (package.json scripts,
`eslint.config.js`, `tsconfig.json`, `vitest.config.js`, `.prettierrc.json`, `.gitignore`, sample
source and test, and the library variant with declaration emit) was installed and run on 2026-10-29
with Node 22.23.1 and the pinned versions shown; the outputs are in `sources/javascript.md` under
"Template smoke test". Re-run the gates after adapting them.

## package.json (Node 26 service, ESM)

```json
{
  "name": "example-service",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "engines": {
    "node": ">=26"
  },
  "packageManager": "npm@12.2.1",
  "exports": {
    ".": "./src/index.js"
  },
  "files": [
    "src"
  ],
  "scripts": {
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "lint": "eslint . --max-warnings=0",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:coverage": "vitest run --coverage",
    "test:shuffle": "vitest run --sequence.shuffle.files --sequence.shuffle.tests",
    "check": "npm run format:check && npm run lint && npm run typecheck && npm run test:coverage"
  },
  "devDependencies": {
    "@eslint/js": "10.0.1",
    "@types/node": "26.6.6",
    "@vitest/coverage-v8": "5.0.5",
    "eslint": "10.13.0",
    "eslint-plugin-n": "18.5.0",
    "eslint-plugin-regexp": "3.3.2",
    "eslint-plugin-security": "4.2.0",
    "globals": "17.13.0",
    "prettier": "3.9.10",
    "typescript": "7.0.2",
    "vitest": "5.0.5"
  }
}
```

Notes:
- `packageManager` documents the tool; with Node 25+ there is no bundled Corepack to enforce it, so
  CI installs the named version explicitly.
- `@types/node` gives `tsc` the Node API types for JSDoc checking; match its major to the oldest
  Node line you run on (26.6.6 here; 22.20.5 for the Node 22 library variant below).
- `--sequence.shuffle.tests` only reorders tests inside each file; `--sequence.shuffle.files` also
  reorders the files. Use both to prove order independence.
- Exact devDependency pins make the gate output reproducible; let Renovate/Dependabot bump them.

## eslint.config.js (ESLint 10 flat config)

```js
import js from '@eslint/js';
import { defineConfig, globalIgnores } from 'eslint/config';
import n from 'eslint-plugin-n';
import regexp from 'eslint-plugin-regexp';
import security from 'eslint-plugin-security';
import globals from 'globals';

export default defineConfig([
  globalIgnores(['dist/', 'coverage/', 'playwright-report/', 'test-results/']),
  {
    name: 'app/javascript',
    files: ['**/*.{js,mjs,cjs}'],
    plugins: { js },
    extends: ['js/recommended'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: { ...globals.node },
    },
    rules: {
      eqeqeq: ['error', 'always', { null: 'ignore' }],
      'no-var': 'error',
      'prefer-const': 'error',
      'no-eval': 'error',
      'no-implied-eval': 'error',
      'no-new-func': 'error',
      'no-promise-executor-return': 'error',
      'require-atomic-updates': 'error',
      'no-console': ['error', { allow: ['warn', 'error'] }],
    },
  },
  n.configs['flat/recommended-module'],
  regexp.configs.recommended,
  security.configs.recommended,
  {
    name: 'app/tests',
    files: ['**/*.test.js', 'test/**/*.js'],
    rules: { 'n/no-unpublished-import': 'off' },
  },
  {
    name: 'app/browser',
    files: ['src/browser/**/*.js'],
    languageOptions: { globals: { ...globals.browser } },
  },
]);
```

Notes:
- ESLint 10 reads only flat config; `.eslintrc*` files are ignored, and `/* eslint-env */` comments
  are reported as errors.
- Floating-promise detection needs type information. typescript-eslint 8.72.1 peers on
  `typescript >=4.8.4 <6.1.0`, so the package named `typescript` must be the TS 6 API package. Use
  the recipe from the TypeScript 7 announcement; `npx tsc` still runs 7.0.2 and `tsc6` runs 6.0:

  ```json
  "devDependencies": {
    "@typescript/native": "npm:typescript@^7.0.2",
    "typescript": "npm:@typescript/typescript6@^6.0.2",
    "typescript-eslint": "8.72.1"
  }
  ```

  ```js
  // add to eslint.config.js
  import tseslint from 'typescript-eslint';
  // ...
  {
    name: 'app/type-aware',
    files: ['src/**/*.js'],
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    plugins: { '@typescript-eslint': tseslint.plugin },
    rules: {
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/no-misused-promises': 'error',
    },
  },
  ```

  Naming the alias `typescript6` instead leaves `typescript` at 7.0.2 and `npm install` fails with
  `ERESOLVE ... peer typescript@">=4.8.4 <6.1.0"`.
- Optional fast pre-pass: `npx oxlint --deny-warnings` before ESLint in CI.

## tsconfig.json (JSDoc type checking with TypeScript 7)

```json
{
  "compilerOptions": {
    "allowJs": true,
    "checkJs": true,
    "noEmit": true,
    "strict": true,
    "module": "nodenext",
    "moduleResolution": "nodenext",
    "target": "esnext",
    "lib": ["esnext"],
    "types": ["node"],
    "skipLibCheck": true,
    "noUnusedLocals": true,
    "noImplicitOverride": true,
    "exactOptionalPropertyTypes": false
  },
  "include": ["src", "test", "*.js"]
}
```

- `esnext` matches Node 26: it types Temporal, `Map#getOrInsert`, `Error.isError`, `Promise.try`,
  `RegExp.escape` and `Uint8Array.fromBase64`. With `es2024` each of those is a `tsc` error
  (TS2550/TS2304), so the gate would reject code this pack recommends.
- `Iterator.concat` has no lib typing in TypeScript 7.0.2 (TS2339 even with `esnext`). Until it
  does, use a generator (`function* concat(...its) { for (const it of its) yield* it; }`) or a
  `// @ts-expect-error Iterator.concat not in TS 7.0 lib` line.
- A library that supports Node 22 keeps `"target": "es2024", "lib": ["es2024"]` so `tsc` rejects
  APIs its oldest runtime lacks (see the library variant below).
- For browser code add `"DOM", "DOM.Iterable"` to `lib` and drop `"types": ["node"]` in that project.

## vitest.config.js (Vitest 5)

```js
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    include: ['src/**/*.test.js', 'test/**/*.test.js'],
    restoreMocks: true,
    coverage: {
      provider: 'v8',
      include: ['src/**/*.js'],
      exclude: ['src/**/*.test.js'],
      thresholds: { lines: 80, functions: 80, branches: 75, statements: 80 },
    },
  },
});
```

Browser-like unit tests: `environment: 'happy-dom'` (happy-dom 21) or `'jsdom'` (jsdom 30), or Vitest
Browser Mode with `@vitest/browser-playwright` for real-browser tests.

## .gitignore

Ship this with the project. Without it knip reports `coverage/*.js` as unused files and
`oxlint --deny-warnings` lints `node_modules`; both read `.gitignore`.

```gitignore
node_modules/
coverage/
dist/
playwright-report/
test-results/
blob-report/
*.tsbuildinfo
.env*
!.env.example
```

## .prettierrc.json and .prettierignore

```json
{ "singleQuote": true, "trailingComma": "all", "printWidth": 100 }
```

```
coverage
dist
package-lock.json
pnpm-lock.yaml
```

## Sample module and test (used for the smoke test)

```js
// src/index.js
import { setTimeout as delay } from 'node:timers/promises';

/**
 * @typedef {object} RetryOptions
 * @property {number} attempts
 * @property {number} baseDelayMs
 * @property {AbortSignal} [signal]
 */

export class AppError extends Error {
  /**
   * @param {string} message
   * @param {{ code: string, cause?: unknown, status?: number }} options
   */
  constructor(message, { code, cause, status = 500 }) {
    super(message, { cause });
    this.name = 'AppError';
    this.code = code;
    this.status = status;
  }
}

/**
 * Retry an async operation with exponential backoff; aborts promptly.
 * @template T
 * @param {(signal: AbortSignal | undefined) => Promise<T>} fn
 * @param {RetryOptions} options
 * @returns {Promise<T>}
 */
export async function retry(fn, { attempts, baseDelayMs, signal }) {
  let lastError;
  for (let i = 0; i < attempts; i++) {
    signal?.throwIfAborted();
    try {
      return await fn(signal);
    } catch (err) {
      lastError = err;
      if (i < attempts - 1) {
        // Abortable wait: rejects with an AbortError as soon as the signal fires.
        await delay(baseDelayMs * 2 ** i, undefined, { signal });
      }
    }
  }
  throw new AppError('retry attempts exhausted', { code: 'RETRY_EXHAUSTED', cause: lastError });
}
```

```js
// src/index.test.js
import { describe, expect, it, vi } from 'vitest';
import { AppError, retry } from './index.js';

describe('retry', () => {
  it('returns the first successful result', async () => {
    const fn = vi.fn().mockRejectedValueOnce(new Error('boom')).mockResolvedValue('ok');
    await expect(retry(fn, { attempts: 3, baseDelayMs: 1 })).resolves.toBe('ok');
    expect(fn).toHaveBeenCalledTimes(2);
  });

  it('wraps the last error with code and cause when attempts run out', async () => {
    const cause = new Error('down');
    const err = await retry(() => Promise.reject(cause), { attempts: 2, baseDelayMs: 1 }).catch(
      (e) => e,
    );
    expect(err).toBeInstanceOf(AppError);
    expect(err.code).toBe('RETRY_EXHAUSTED');
    expect(err.cause).toBe(cause);
  });

  it('stops when the signal is already aborted', async () => {
    const fn = vi.fn();
    await expect(
      retry(fn, { attempts: 3, baseDelayMs: 1, signal: AbortSignal.abort() }),
    ).rejects.toThrow();
    expect(fn).not.toHaveBeenCalled();
  });

  // The elapsed-time assertion and the 1 s per-test timeout make a wait that ignores the signal
  // fail on its own, instead of relying on Vitest's 5 s default timeout.
  it('aborts while waiting between attempts instead of sleeping out the backoff', async () => {
    const controller = new AbortController();
    const fn = vi.fn(async () => {
      controller.abort();
      throw new Error('fail');
    });
    const started = performance.now();
    await expect(
      retry(fn, { attempts: 3, baseDelayMs: 10_000, signal: controller.signal }),
    ).rejects.toThrow(/abort/i);
    expect(performance.now() - started).toBeLessThan(100);
    expect(fn).toHaveBeenCalledTimes(1);
  }, 1_000);
});
```

## Library variant (Node 22+, JSDoc types shipped as .d.ts)

A JSDoc-typed library has no type declarations until you emit them; without this step
`attw --pack .` passes vacuously ("This package does not contain types") and consumers get `any`.
Changes against the service template:

```json
{
  "name": "example-lib",
  "version": "0.1.0",
  "type": "module",
  "engines": {
    "node": ">=22.12"
  },
  "exports": {
    ".": {
      "types": "./dist/types/index.d.ts",
      "default": "./src/index.js"
    }
  },
  "files": [
    "src",
    "dist/types",
    "!src/**/*.test.js"
  ],
  "scripts": {
    "build:types": "tsc -p tsconfig.build.json",
    "prepack": "npm run build:types"
  }
}
```

`tsconfig.json` for this variant uses `"target": "es2024", "lib": ["es2024"]` and
`@types/node` 22.20.5. Add `tsconfig.build.json`:

```json
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "noEmit": false,
    "declaration": true,
    "emitDeclarationOnly": true,
    "declarationMap": true,
    "outDir": "dist/types",
    "rootDir": "src"
  },
  "include": ["src"],
  "exclude": ["src/**/*.test.js"]
}
```

Library gates: `npm run build:types && npx publint && npx @arethetypeswrong/cli --pack . --profile esm-only`.
The `esm-only` profile skips the `node10` and CommonJS-`require` checks, which an ESM-only package
fails by design (with the default or `node16` profile attw exits 1 on `CJSResolvesToESM`); drop it
for a dual package. Treat "This package does not contain types" in the attw output as a failure even
though attw exits 0. TypeScript 7.0.2 emitted `dist/types/index.d.ts` from the JSDoc sample in the
smoke test; see `sources/javascript.md` section 4 for the output.

## Supply-chain settings

npm 12 (`.npmrc` in the repo):

```ini
save-exact=true
min-release-age=3
engine-strict=true
```

Dependency install scripts are blocked by default in npm 12; approve the ones you need with
`npm install-scripts approve <pkg>` (writes pinned entries to `allowScripts` in `package.json`) and
run `npm rebuild`.

pnpm 11/12 (`pnpm-workspace.yaml`; `.npmrc` is auth/registry only since pnpm 11):

```yaml
minimumReleaseAge: 4320   # minutes (3 days); default is 1440
allowBuilds:
  esbuild: true
```

## CI job (GitHub Actions, outline)

```yaml
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7            # v7.0.1 (2026-07-20); pin to a commit SHA in real repos
      - uses: actions/setup-node@v7          # v7.1.0 (2026-10-08)
        with: { node-version: 26, cache: npm }
      - run: npm i -g npm@12.2.1
      - run: npm ci
      - run: npm run check
      - run: npx vitest run --sequence.shuffle.files --sequence.shuffle.tests
      - run: npm audit --audit-level=high && npm audit signatures
```

Action versions were read from each action's GitHub releases on 2026-10-29; pin them by commit SHA
in real repositories so a moved tag cannot change your pipeline.
