# Tested recipes: race stress, benchmark statistics, safe paths, shutdown, leaks, release

Every TypeScript and JavaScript block below is copied from files that passed, on 2026-10-29 (Node 22.23.1, TypeScript 7.0.2 and
6.0.3, Vitest 5.0.5), the gates of the `configs.md` template: `prettier --check`, `eslint --max-warnings=0`
(strictTypeChecked + regexp + no-eval/no-new-func), `tsc --noEmit` (TS 7 and `tsc6`), `knip`, and
`vitest run` (12 tests, exit 0). Results quoted as "observed" come from those runs.

## 1. Race stress test (TS-ASYNC-5)

Shuffled test order only shows that tests do not depend on each other. A race needs many overlapping
operations with varied interleavings and an invariant to check. The store below yields a random 0-3
event-loop turns inside every read and write, so 2000 concurrent deposits interleave differently per seed.

### `src/keyed-lock.ts`

```ts
/** Runs async critical sections one at a time per key, in call order. */
export class KeyedLock {
  readonly #tails = new Map<string, Promise<void>>();

  run<T>(key: string, fn: () => Promise<T>): Promise<T> {
    const previous = this.#tails.get(key) ?? Promise.resolve();
    const result = previous.then(fn);
    const tail = result.then(
      () => undefined,
      () => undefined,
    );
    this.#tails.set(key, tail);
    void tail.then(() => {
      if (this.#tails.get(key) === tail) this.#tails.delete(key);
    });
    return result;
  }

  /** Keys with queued or running work; 0 when idle (a leak check for tests). */
  get size(): number {
    return this.#tails.size;
  }
}
```

### `src/wallet.ts`

```ts
export interface BalanceStore {
  read(id: string): Promise<number>;
  write(id: string, value: number): Promise<void>;
}

/** Read-modify-write across two awaits: callers must serialize per id. */
export async function deposit(
  store: BalanceStore,
  id: string,
  amount: number,
): Promise<void> {
  const current = await store.read(id);
  await store.write(id, current + amount);
}
```

### `src/wallet.stress.test.ts`

```ts
import { setImmediate as nextTurn } from "node:timers/promises";
import { expect, test } from "vitest";
import { KeyedLock } from "./keyed-lock.ts";
import { deposit, type BalanceStore } from "./wallet.ts";

// Seeded PRNG: a failing interleaving replays with STRESS_SEED=<seed>.
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Yield 0-3 event-loop turns so concurrent operations interleave differently.
async function jitter(rand: () => number): Promise<void> {
  const hops = Math.floor(rand() * 4);
  for (let i = 0; i < hops; i++) await nextTurn();
}

function jitteryStore(rand: () => number): BalanceStore & {
  readonly values: Map<string, number>;
} {
  const values = new Map<string, number>();
  return {
    values,
    async read(id) {
      await jitter(rand);
      return values.get(id) ?? 0;
    },
    async write(id, value) {
      await jitter(rand);
      values.set(id, value);
    },
  };
}

const SEED = Number(process.env["STRESS_SEED"] ?? Date.now() % 2 ** 31);
const OPS = 2000;
const IDS = ["a", "b", "c"] as const;

test(`no lost updates across ${String(OPS)} concurrent deposits (seed ${String(SEED)})`, async () => {
  const rand = mulberry32(SEED);
  const store = jitteryStore(rand);
  const lock = new KeyedLock();

  await Promise.all(
    Array.from({ length: OPS }, (_, i) => {
      const id = IDS[i % IDS.length] ?? "a";
      return lock.run(id, () => deposit(store, id, 1));
    }),
  );
  await nextTurn(); // let the lock drop its finished tails

  const total = [...store.values.values()].reduce((sum, v) => sum + v, 0);
  expect(total).toBe(OPS); // the invariant: every deposit counted once
  expect(lock.size).toBe(0);
});
```

Observed: with `lock.run(...)` the test passes for seeds 1, 42 and 987654 (about 0.4 s each). With the
lock removed (`return deposit(store, id, 1);`) it fails with `expected 117 to be 2000`. Run it with
`STRESS_SEED=<seed> npx vitest run src/wallet.stress.test.ts` to replay a failure. For data in a database,
prefer a conditional update or transaction over an in-process lock, which does not protect across processes.

## 2. Benchmark statistics (TS-PERF-2)

Procedure: baseline and candidate in two checkouts (for example `git worktree add ../base origin/main`,
then `npm ci` there), both containing the `money.bench.ts` pattern from `configs.md` (it honours `BENCH_OUT`).
Run at least 10 rounds, alternating which side goes first, on an idle machine with the same pinned Node, and
record the Node version and CPU model. Then compare.

### Driver (`ab.sh <baseDir> <candDir> [rounds]`)

```bash
#!/usr/bin/env bash
# Interleaved A/B benchmark: 10 rounds, order alternates each round.
set -u
BASE=$1; CAND=$2; ROUNDS=${3:-10}
node -p '`node ${process.version} | ${require("os").cpus()[0].model}`'
for i in $(seq 1 "$ROUNDS"); do
  if (( i % 2 )); then order="$BASE $CAND"; else order="$CAND $BASE"; fi
  for dir in $order; do
    (cd "$dir" && BENCH_OUT="./bench-out/run-$i.json" npx vitest bench > /dev/null 2>&1) || { echo "bench failed in $dir"; exit 2; }
  done
done
node "$CAND/scripts/bench-stats.mjs" "$BASE/bench-out" "$CAND/bench-out" 0.05 0.05
```

### `scripts/bench-stats.mjs`

```js
// Compare two sets of Vitest `writeResult` files (one JSON file per run).
// Usage: node scripts/bench-stats.mjs <baseDir> <candDir> [maxSlowdown=0.05] [alpha=0.05]
// Exit 0 = no significant regression, 1 = regression, 2 = bad input.
import console from "node:console";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import process from "node:process";

const [baseDir, candDir, maxArg = "0.05", alphaArg = "0.05"] =
  process.argv.slice(2);
if (!baseDir || !candDir) {
  console.error(
    "usage: bench-stats.mjs <baseDir> <candDir> [maxSlowdown] [alpha]",
  );
  process.exit(2);
}

// Per-run statistic: mean latency in ms. p50 is quantized by the timer for
// sub-microsecond functions, which creates ties across runs.
function runMeans(dir) {
  return readdirSync(dir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => JSON.parse(readFileSync(join(dir, f), "utf8")).latency.mean);
}

function median(xs) {
  const s = [...xs].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

// Standard normal CDF via the Abramowitz-Stegun 7.1.26 erf approximation (z >= 0).
function phi(z) {
  const x = z / Math.SQRT2;
  const t = 1 / (1 + 0.3275911 * x);
  const poly =
    t *
    (0.254829592 +
      t *
        (-0.284496736 +
          t * (1.421413741 + t * (-1.453152027 + t * 1.061405429))));
  return 0.5 * (1 + (1 - poly * Math.exp(-x * x)));
}

// Two-sided Mann-Whitney U test, normal approximation with tie and continuity correction.
function mannWhitney(a, b) {
  const all = [
    ...a.map((v) => ({ v, g: 0 })),
    ...b.map((v) => ({ v, g: 1 })),
  ].sort((x, y) => x.v - y.v);
  const ranks = new Array(all.length);
  let tieTerm = 0;
  for (let i = 0; i < all.length;) {
    let j = i;
    while (j + 1 < all.length && all[j + 1].v === all[i].v) j++;
    for (let k = i; k <= j; k++) ranks[k] = (i + j + 2) / 2;
    const t = j - i + 1;
    tieTerm += t ** 3 - t;
    i = j + 1;
  }
  const n1 = a.length;
  const n2 = b.length;
  const n = n1 + n2;
  const r1 = all.reduce((s, x, i) => (x.g === 0 ? s + ranks[i] : s), 0);
  const u = r1 - (n1 * (n1 + 1)) / 2;
  const sigma = Math.sqrt(((n1 * n2) / 12) * (n + 1 - tieTerm / (n * (n - 1))));
  const z =
    sigma === 0 ? 0 : Math.max(Math.abs(u - (n1 * n2) / 2) - 0.5, 0) / sigma;
  return { u, p: Math.min(1, 2 * (1 - phi(z))) };
}

const base = runMeans(baseDir);
const cand = runMeans(candDir);
if (base.length < 10 || cand.length < 10) {
  console.error(
    `need >= 10 runs per side, got base=${base.length} cand=${cand.length}`,
  );
  process.exit(2);
}
const change = median(cand) / median(base) - 1;
const { u, p } = mannWhitney(base, cand);
const regression = change > Number(maxArg) && p < Number(alphaArg);
console.log(
  JSON.stringify({
    runs: [base.length, cand.length],
    baseMedianMs: median(base),
    candMedianMs: median(cand),
    change: Number(change.toFixed(4)),
    u,
    p: Number(p.toFixed(5)),
    verdict: regression ? "REGRESSION" : "OK",
  }),
);
process.exit(regression ? 1 : 0);
```

Acceptance: exit 0 passes. A regression needs both a median slowdown above the threshold (default 5%) and
p < 0.05. Observed on a shared 16-core host (load average about 16, so deliberately noisy):

| Comparison | Result |
|---|---|
| identical code on both sides, 10 + 10 runs | `"change":0.0183,"p":0.47268,"verdict":"OK"`, exit 0 |
| candidate 3x slower (`raw.split("").join("")` added), 10 + 10 runs | `"change":2.1442,"p":0.00018,"verdict":"REGRESSION"`, exit 1 |

The p-values match `scipy.stats.mannwhitneyu(..., method="asymptotic", use_continuity=True)` to 5 decimals on
5 synthetic data sets, including tied values. `latency.mean` is used per run because `latency.p50` came out
as exactly `0.0001` ms (timer resolution) for this sub-microsecond function. Commit `benchmarks/*.json`
baselines; keep per-run files in the git-ignored `bench-out/`.

## 3. Symlink-safe path resolution (TS-SEC-3)

### `src/safe-path.ts`

```ts
import { realpath } from "node:fs/promises";
import path from "node:path";

function isMissing(error: unknown): boolean {
  return error instanceof Error && "code" in error && error.code === "ENOENT";
}

/**
 * Resolves untrusted `input` under `root` and returns the real path, or throws
 * when the result (after following symlinks) is outside `root`. A target that
 * does not exist yet is checked through the real path of its parent directory.
 */
export async function resolveInside(
  root: string,
  input: string,
): Promise<string> {
  const realRoot = await realpath(root);
  const candidate = path.resolve(realRoot, input);
  let real: string;
  try {
    real = await realpath(candidate);
  } catch (error: unknown) {
    if (!isMissing(error)) throw error;
    real = path.join(
      await realpath(path.dirname(candidate)),
      path.basename(candidate),
    );
  }
  const prefix = realRoot.endsWith(path.sep) ? realRoot : realRoot + path.sep;
  if (real !== realRoot && !real.startsWith(prefix)) {
    throw new Error(`path escapes root: ${input}`);
  }
  return real;
}
```

### `src/safe-path.test.ts`

```ts
import { mkdir, mkdtemp, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { beforeAll, expect, test } from "vitest";
import { resolveInside } from "./safe-path.ts";

let root = "";
let outside = "";

beforeAll(async () => {
  const base = await mkdtemp(path.join(tmpdir(), "safe-path-"));
  root = path.join(base, "root");
  outside = path.join(base, "outside");
  await mkdir(path.join(root, "sub"), { recursive: true });
  await mkdir(outside);
  await writeFile(path.join(root, "sub", "ok.txt"), "ok");
  await writeFile(path.join(outside, "secret.txt"), "secret");
  await symlink(outside, path.join(root, "link")); // root/link -> ../outside
});

test.each(["sub/ok.txt", "new-file.txt", ".", ""])(
  "accepts %j",
  async (input) => {
    await expect(resolveInside(root, input)).resolves.toMatch(/root/);
  },
);

test.each([
  "../outside/secret.txt",
  "link/secret.txt",
  "link/new.txt",
  "/etc/passwd",
])("rejects %j", async (input) => {
  await expect(resolveInside(root, input)).rejects.toThrow("path escapes root");
});

test("a naive prefix check is fooled by the symlink", () => {
  const naive = path.resolve(root, "link/secret.txt");
  expect(naive.startsWith(root + path.sep)).toBe(true); // why realpath is required
});
```

Observed: all 9 cases pass, and the last test shows the naive `startsWith(root + path.sep)` check accepting
`link/secret.txt`. The check and the later `open` are separate steps, so a local attacker who can swap
symlinks inside the root can still race them; for that threat, keep the root unwritable by others.

## 4. Graceful shutdown (TS-OPS-1)

### `src/graceful.ts`

```ts
import type { Server } from "node:http";

export interface ShutdownOptions {
  /** Hard limit for draining; keep it below the orchestrator's kill timeout. */
  readonly deadlineMs: number;
  /** Close pools, flush telemetry and logs; runs after the server stops. */
  readonly cleanup?: () => Promise<void>;
  readonly log?: (event: string, data?: Record<string, unknown>) => void;
}

/**
 * On SIGTERM or SIGINT: stop accepting connections, let in-flight requests
 * finish, run cleanup, then exit 0. Exit 1 if the deadline passes first.
 */
export function installGracefulShutdown(
  server: Server,
  options: ShutdownOptions,
): void {
  const log = options.log ?? (() => undefined);
  let draining = false;

  const onSignal = (signal: NodeJS.Signals): void => {
    if (draining) return;
    draining = true;
    log("shutdown.start", { signal });

    setTimeout(() => {
      log("shutdown.deadline_exceeded", { deadlineMs: options.deadlineMs });
      server.closeAllConnections();
      process.exit(1);
    }, options.deadlineMs).unref();

    // close() only drops sockets that are idle right now. A keep-alive socket
    // whose request finishes later stays open, so sweep until close completes.
    const sweep = setInterval(() => {
      server.closeIdleConnections();
    }, 100);
    sweep.unref();

    server.close((error) => {
      clearInterval(sweep);
      const cleanup = options.cleanup ?? (() => Promise.resolve());
      cleanup().then(
        () => {
          log("shutdown.done");
          process.exit(error ? 1 : 0);
        },
        (cleanupError: unknown) => {
          log("shutdown.cleanup_failed", { error: String(cleanupError) });
          process.exit(1);
        },
      );
    });
  };

  process.once("SIGTERM", onSignal);
  process.once("SIGINT", onSignal);
}
```

### `src/demo-server.ts` (test fixture)

```ts
import { createServer } from "node:http";
import { setTimeout as sleep } from "node:timers/promises";
import { installGracefulShutdown } from "./graceful.ts";

const server = createServer((req, res) => {
  const ms = req.url === "/hang" ? 60_000 : 300;
  void sleep(ms).then(() => {
    res.end("done");
  });
});

installGracefulShutdown(server, {
  deadlineMs: Number(process.env["DEADLINE_MS"] ?? 2000),
  log: (event, data) => {
    process.stderr.write(`${JSON.stringify({ event, ...data })}\n`);
  },
});

server.listen(0, () => {
  const address = server.address();
  if (address !== null && typeof address === "object") {
    process.stdout.write(`listening ${String(address.port)}\n`);
  }
});
```

### `src/graceful.test.ts`

```ts
import { spawn, type ChildProcess } from "node:child_process";
import { once } from "node:events";
import { setTimeout as sleep } from "node:timers/promises";
import { expect, test } from "vitest";

async function start(
  env: Record<string, string> = {},
): Promise<{ child: ChildProcess; port: number }> {
  const child = spawn(process.execPath, ["src/demo-server.ts"], {
    env: { ...process.env, ...env },
    stdio: ["ignore", "pipe", "inherit"],
  });
  const [chunk] = (await once(child.stdout, "data")) as [Buffer];
  const port = Number(/listening (\d+)/.exec(chunk.toString())?.[1]);
  return { child, port };
}

test("SIGTERM drains an in-flight request, then exits 0", async () => {
  const { child, port } = await start();
  const response = fetch(`http://127.0.0.1:${String(port)}/slow`);
  await sleep(50);
  child.kill("SIGTERM");
  const res = await response;
  expect(await res.text()).toBe("done");
  const [code] = (await once(child, "exit")) as [number | null];
  expect(code).toBe(0);
});

test("a request that outlives the deadline makes the process exit 1", async () => {
  const { child, port } = await start({ DEADLINE_MS: "300" });
  const response = fetch(`http://127.0.0.1:${String(port)}/hang`).catch(
    () => "aborted",
  );
  await sleep(50);
  child.kill("SIGTERM");
  const [code] = (await once(child, "exit")) as [number | null];
  expect(code).toBe(1);
  await response;
});
```

Observed: both tests pass (drain then exit 0; deadline then exit 1). The first version had no sweep and only
called `server.closeIdleConnections()` once; the drain test then failed (`expected 1 to be +0`), because
`fetch` keeps the connection alive after the in-flight response and `server.close()` never completed before
the deadline. In knip, list the fixture as an entry (`"src/demo-server.ts"`) because only a child process
loads it. Coverage of `graceful.ts` is not measured here (it runs in the child process).

## 5. Leaks (TS-OPS-4, TS-OPS-5)

Heap-growth check, run with `node --expose-gc heapgrowth.mjs [leaky]`:

```js
// Heap-growth check: run the operation in rounds, force GC, and compare heapUsed.
import console from "node:console";
import process from "node:process";
const leaky = process.argv[2] === "leaky";
const cache = new Map();
function handle(i) {
  const key = leaky ? `k${i}` : `k${i % 1000}`; // leaky: unbounded keys
  cache.set(key, { payload: "x".repeat(100) });
}
const samples = [];
for (let round = 0; round < 6; round++) {
  for (let i = round * 50_000; i < (round + 1) * 50_000; i++) handle(i);
  globalThis.gc();
  samples.push(process.memoryUsage().heapUsed);
}
const growthMB = (samples.at(-1) - samples[1]) / 2 ** 20; // skip warm-up round
console.log(JSON.stringify({ leaky, growthMB: Number(growthMB.toFixed(1)) }));
process.exit(growthMB > 5 ? 1 : 0);
```

Observed: bounded keys `{"leaky":false,"growthMB":0}` exit 0; unbounded keys `{"leaky":true,"growthMB":60.9}`
exit 1. To find the culprit, start the service with `node --heapsnapshot-signal=SIGUSR2 app.js` (observed:
`kill -USR2 <pid>` wrote `Heap.<date>.<pid>.0.001.heapsnapshot`), take one snapshot after warm-up and one
after the load, load both in Chrome DevTools Memory, select the second and choose "Comparison". Sort by
size delta; listeners, closures and `Map`/`Array` entries that only grow are the usual cause.

## 6. Release workflow (TS-SEC-9, TS-MOD-7)

`.github/workflows/publish.yml`, adapted from the npm trusted-publishing docs (fetched 2026-10-29):

```yaml
name: Publish
on:
  push:
    tags: ["v*"]

permissions:
  id-token: write # OIDC token for npm trusted publishing
  contents: read

jobs:
  publish:
    runs-on: ubuntu-latest # GitHub-hosted; self-hosted runners are not supported
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-node@v7
        with:
          node-version: "26" # bundles npm 11.20.0; trusted publishing needs npm >= 11.5.1
          registry-url: "https://registry.npmjs.org"
          package-manager-cache: false # no dependency cache in release builds
      - run: npm ci
      - run: npm audit signatures
      - run: npm run check
      - run: npm run build && npm run check:package
      - run: npm publish # provenance is generated automatically; no NPM_TOKEN
```

Checked here: `yaml.safe_load` parses it and Prettier accepts it. Not checked here: an actual publish, which
needs a package with a trusted publisher configured on npmjs.com (Settings, Trusted Publisher: GitHub
Actions, the repo and the workflow filename `publish.yml`). A new trusted-publisher configuration must
complete its first publish within 2 days or it expires (npm docs). After it works, set Publishing access to
"Require two-factor authentication and disallow tokens" and revoke old automation tokens. For the strictest
setup npm documents stage-only trusted publishers (`npm stage publish`), where a maintainer approves each
release with 2FA. The npm docs example uses `actions/checkout@v6` / `setup-node@v6`; v7 of both is current
(checked with the GitHub API) and `setup-node` v7 still has `registry-url` and `package-manager-cache`.

Versioning with changesets (`@changesets/cli` 3.0.3): `npx changeset` in each PR, `npx changeset version` to
produce the release commit (versions plus `CHANGELOG.md`), then tag `v<version>` to trigger the workflow.
To automate the release PR, `changesets/action` v2 provides `select-mode`, `version` and `publish`
sub-actions; its README recommends the separate sub-actions with trusted publishing so only the publish
job gets `id-token: write`.
