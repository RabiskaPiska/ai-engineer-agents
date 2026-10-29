---
name: python-engineering
description: "Python engineering rule catalogue and verification gates for October 2026 (CPython 3.15, uv 0.13, Ruff 0.17, ty, mypy 2.4, pytest 9). Use when writing, reviewing, testing, profiling or packaging Python: *.py, *.pyi, pyproject.toml, uv.lock, conftest.py, PEP 723 scripts. Gives the exact gate commands with pass/fail signals, Ruff-enforceable rules, a tested pyproject baseline and tested FastAPI/async service patterns."
---

# Python engineering

This skill is the working reference for the `python-engineer` agent and for anyone doing Python work
in a repo. It holds the rules, the commands that prove them, and two tested references:

- `references/pyproject-baseline.md`: a `pyproject.toml`, CI job and non-root Dockerfile. The TOML
  and the bootstrap commands were run verbatim on 2026-10-29 (CPython 3.15.0); the Dockerfile was
  not built.
- `references/service-patterns.md`: a FastAPI + async SQLAlchemy + httpx service with tests. On
  2026-10-29 gates 3 to 7 passed and the repeat gate below failed 0 of 5 invocations.

Facts are dated 2026-10-29 and sourced in `sources/python.md`. When a project already has its own
conventions, follow them and use this skill to fill gaps.

## 1. The gate (run in this order)

```bash
uv lock --check                                       # 1 lockfile matches pyproject.toml
uv sync --locked --all-groups                         # 2 environment matches lockfile
uv run --frozen ruff format --check .                 # 3 formatting
uv run --frozen ruff check .                          # 4 lint (bugs, security, style)
uv run --frozen ty check                              # 5 fast types (beta, 0.0.x)
uv run --frozen mypy src tests                        # 6 type gate of record (strict in config)
uv run --frozen pytest -q -n auto --cov --cov-report=term-missing   # 7 tests + branch coverage
req=$(mktemp) && uv export --frozen --no-emit-project --format requirements.txt -o "$req" \
  && uvx pip-audit --strict --require-hashes --disable-pip -r "$req"; rm -f "$req"   # 8 CVEs
```

Step 8 writes to a `mktemp` file, not a fixed `/tmp` path, which is what Ruff `S108` asks of
Python code too. CI can write `req-audit.txt` inside the workspace instead.

| Step | Pass looks like | Fail looks like | Typical fix |
|---|---|---|---|
| 1 | `Resolved N packages`, exit 0 | `The lockfile needs to be updated` | `uv lock`, commit `uv.lock` |
| 3 | `N files already formatted` | `Would reformat: path` | `uv run ruff format .` |
| 4 | `All checks passed!` | `path:line:col: CODE message` | fix the code; `--fix` for safe fixes |
| 5 | `All checks passed!` | `error[rule-name]` or `warning[...]` (both exit 1) | fix types; ignore only with `# ty: ignore[rule]` + reason |
| 6 | `Success: no issues found` | `error: ... [code]` | fix types; ignore only with `# type: ignore[code]` + reason |
| 7 | `N passed`, coverage `reached` | `failed`, `error`, `FAIL Required test coverage` | fix code or add the missing test |
| 8 | `No known vulnerabilities found` | table of package, version, ID, fix version | `uv lock --upgrade-package <pkg>` |

Observed on 2026-10-29 in a scratch project: steps 3 to 7 passed on 3.15.0, and step 7 exited 1 with
`FAIL Required test coverage of 90.0% not reached. Total coverage: 85.00%` before tests were added.

Extra gates when relevant:
- Async, threads or resources. Run the repeat gate in a single process:
  `uv run --frozen python -X dev -m pytest -q -p no:xdist --no-cov --count=20` (pytest-repeat,
  asyncio debug mode, ResourceWarning on unclosed resources, random order through
  pytest-randomly). Pass is `N passed` with no `PytestUnraisableExceptionWarning`. Without
  pytest-repeat, loop instead: `for i in $(seq 20); do uv run --frozen pytest -q -p no:xdist || break; done`.
  Do not count `-n auto` as a leak check. Observed on 2026-10-29: a session leaked on an error
  path failed 7 of 15 plain single-process runs and 1 of 12 `-X dev` runs, failed in a single
  `--count=20` run (2 of 100 tests), and passed 10 of 10 `-n auto --cov` runs. xdist workers did
  not surface the unraisable warning raised when the leaked connection was collected at teardown.
- Free-threaded build:
  `UV_PROJECT_ENVIRONMENT=.venv-ft uv run --python 3.15t --frozen --all-groups pytest -q`.
  `--all-groups` is needed when the test tools are not in the `dev` group (without it:
  `Failed to spawn: pytest`). Tested: `sys._is_gil_enabled()` returned `False`, 8 passed. Then run
  each sync test in several threads at once with pytest-run-parallel (0.10.0):
  `... --with pytest-run-parallel pytest -q -p no:randomly --no-cov --parallel-threads=4 --iterations=5 -m "not asyncio"`.
  Pass prints `All tests were run in parallel!`; a race prints `PARALLEL FAILED`. It does not run
  pytest-asyncio coroutine tests (they fail with "coroutine ... was never awaited"), so deselect
  them with `-m "not asyncio"`.
- Imports and warnings: `uv run --frozen python -X dev -W error -c "import <pkg>"`.
- Security rules even when not in config: `uv run --frozen ruff check --select S .`.
- Speed claims: compare statistically with pyperf (2.10.0). Run the same benchmark on the base
  commit (for example in `git worktree add ../base main`) and on the change, then compare:
  ```bash
  uv run --frozen --with pyperf python -m pyperf timeit -o old.json -s "<setup>" "<stmt>"   # base
  uv run --frozen --with pyperf python -m pyperf timeit -o new.json -s "<setup>" "<stmt>"   # change
  uv run --frozen --with pyperf python -m pyperf compare_to old.json new.json --table
  ```
  Pass for a speed claim is a row reading `N.NNx faster`. `Benchmark hidden because not
  significant` or `slower` means no claim (both observed 2026-10-29). Report the table and say the
  difference is significant according to `compare_to`. pytest-benchmark's
  `--benchmark-compare-fail=mean:10%` is only a coarse regression tripwire, not a significance
  test. pytest-benchmark 5.3.0 fails under pytest 9.2.0
  (`'Function' object has no attribute '_nodeid'`, observed 2026-10-29) and works under 9.1.x.
- Packaging: `uv build` then install the wheel in a clean env and import it
  (`uv run --isolated --with dist/*.whl python -c "import <pkg>"`; tested 2026-10-29).

Never make a gate pass by weakening it. A new `# noqa`, `# ruff: ignore[...]` (Ruff 0.16+),
`# type: ignore`, `# ty: ignore`, `skip`, `xfail`, lowered `fail_under` or widened
`filterwarnings` needs a specific code, a reason comment and a line in the report.

## 2. Version floor and what it unlocks

Pick features by the project's `requires-python`, not by the newest interpreter.

| Floor | Use freely |
|---|---|
| 3.11 | `ExceptionGroup`/`except*`, `asyncio.TaskGroup`, `asyncio.timeout()`, `tomllib`, `typing.Self`, `datetime.UTC`, `enum.StrEnum` |
| 3.12 | PEP 695 generics (`def f[T]`, `class C[T]`, `type X = ...`), `typing.override`, `itertools.batched`, f-string grammar (PEP 701) |
| 3.13 | `warnings.deprecated` (PEP 702), `typing.TypeIs`, `ReadOnly` TypedDict items, TypeVar defaults (PEP 696), `copy.replace` |
| 3.14 | Deferred annotations (PEP 649, drop `from __future__ import annotations`), t-strings (PEP 750), `compression.zstd`, `concurrent.interpreters`, `except A, B:` without brackets (PEP 758), free-threading supported (PEP 779) |
| 3.15 | `lazy import` (PEP 810), `frozendict` (PEP 814), `sentinel()` (PEP 661), `[*x for x in xs]` (PEP 798), UTF-8 default (PEP 686), `profiling.sampling`, `TypeForm`, closed TypedDict |

3.15 code that, copied verbatim into a file on 2026-10-29, passed `ruff check` and
`ruff format --check` with the baseline config (Ruff 0.17.1), `ty check` (0.0.90) and
`mypy --strict` (2.4.0), and ran on 3.15.0 (`get("retries")` 3, `get("x", 5)` 5,
`type(MISSING).__name__` `sentinel`, `dump()` `{"retries": 3, "timeout_s": 10}`):

```python
lazy import json  # loaded on first use, in dump()

MISSING = sentinel("MISSING")
DEFAULTS: frozendict[str, int] = frozendict(retries=3, timeout_s=10)


def get(key: str, default: int | MISSING = MISSING) -> int:
    if key in DEFAULTS:
        return DEFAULTS[key]
    if default is MISSING:
        raise KeyError(key)
    return default


def dump() -> str:
    return json.dumps(dict(DEFAULTS), sort_keys=True)
```

`lazy` is allowed only at module scope and not inside `try`; a failing lazy import raises at first
use. Ruff 0.17 with a 3.15 target rewrites typing-only imports to `lazy from ...` under its `TC`
rules (`--unsafe-fixes`). Run the tests after accepting those fixes.

Support policy on 2026-10-29: 3.15 and 3.14 get bugfixes; 3.11 to 3.13 get security fixes only;
3.10 reached end of life on 2026-10-01. Libraries should support 3.11+; new services can target
3.15 (NumPy, pydantic-core, orjson, psycopg-binary, grpcio and cryptography all publish cp315
wheels).

## 3. Rule catalogue

Each rule lists the check that enforces it. "Review" means no tool catches it reliably.

### Correctness and idioms
| Rule | Why | Enforced by |
|---|---|---|
| No mutable default arguments | Default evaluated once, shared across calls | Ruff `B006` |
| No mutable class-level defaults on regular classes | Shared by every instance | Ruff `RUF012` |
| Loop closures bind the value, not the variable | Late binding returns the last value | Ruff `B023` |
| Compare to `None`, `True`/`False` and types with `is`, not `==` | `==` can be overridden; `is` states identity | Ruff `E711`, `E712`, `E721` (select them; not default since 0.16) |
| Never use `is` with literals (numbers, strings) | Small-int and string caching makes `is` lie | Ruff `F632` (default) |
| `pathlib` over `os.path` | One object, fewer string bugs | Ruff `PTH` |
| Timezone-aware datetimes | Naive times break across hosts and DST | Ruff `DTZ` (select it; not default since 0.17) |
| No module named after the stdlib | Shadows the real module | Review |
| Iterate dicts/sets; do not mutate while iterating | RuntimeError or skipped items | Ruff `B909`, review |
| No `print` in library/service code | Bypasses log routing | Ruff `T20` |
| No redundant `list(...)`/`dict(...)` around comprehensions or generators | Clearer, one pass less | Ruff `C4` (`C400`, `C416`, `C419`) |
| Explicit returns; no `else` after `return`, no assign-then-return | Hidden `None` returns, noise | Ruff `RET` (`RET503`, `RET505`, `RET504`) |
| Modern syntax for the target version (`list[int]`, `X \| None`) | One spelling per idiom | Ruff `UP` (`UP006`; follows `requires-python`) |

### Types
| Rule | Why | Enforced by |
|---|---|---|
| Public functions fully annotated | Callers and checkers need the contract | mypy `strict`, ty |
| Ignores carry a code and a reason | Blanket ignores hide new errors | Ruff `PGH003`, mypy `ignore-without-code` |
| No `Any` in public signatures without a reason | `Any` disables checking downstream | Review, mypy `disallow_any_explicit` if wanted |
| `Protocol` over ABC for structural contracts | Decouples callers from implementations | Review |
| Narrowing helpers return `TypeIs[T]` | Checkers narrow both branches | ty, mypy |
| Libraries ship `py.typed` | Otherwise users get `Any` | Review, packaging test |
| Overrides marked `@override` | Renames in the base class surface as errors | mypy `enable_error_code = ["explicit-override"]` |

mypy 2.x defaults worth knowing: `--local-partial-types` and `--strict-bytes` are on, and `-n N`
runs checking in parallel. ty checks unannotated function bodies and exits 1 on warnings by default.

### Errors
| Rule | Why | Enforced by |
|---|---|---|
| No bare `except:` | Catches `KeyboardInterrupt`, `SystemExit` | Ruff `E722` |
| No blind `except Exception` except at a boundary | Hides bugs | Ruff `BLE001` |
| No `try/except/pass` | Silent failure | Ruff `S110`, `SIM105` |
| `raise X from exc` inside `except` | Keeps the cause | Ruff `B904` |
| `logger.exception` only where the error is handled | Duplicate logs per layer | Review, Ruff `LOG004` (outside handler) |
| Package-specific exception hierarchy | Callers can catch your errors precisely | Review |
| Do not swallow `asyncio.CancelledError` | Breaks cancellation and timeouts | Review, Ruff `ASYNC` |
| Raise specific classes, not `Exception`; success path in `else`, not in `try`; `logger.exception` in handlers | Callers can catch precisely; `try` covers only what can fail | Ruff `TRY` (`TRY002`, `TRY300`, `TRY400`; `TRY003` ignored in the baseline) |

### Resources and concurrency
| Rule | Why | Enforced by |
|---|---|---|
| Files, sessions, clients in `with`/`async with` | Leaks under error paths | Ruff `SIM115`, `-X dev` ResourceWarning |
| Long-lived clients/engines created once (lifespan) | Connection reuse, latency | Review |
| No blocking calls in `async def` | Stalls every request on the loop | Ruff `ASYNC2xx`, review |
| Keep references to created tasks; prefer `TaskGroup` | Unreferenced tasks can be garbage-collected | Ruff `RUF006` |
| Deadlines on every network call | Hung peers exhaust workers | Ruff `S113` (requests), `ASYNC109`, review |
| CPU-bound work in processes or native code | GIL serialises threads on the default build | Review, profile |
| Shared mutable state behind a lock or queue | Races; free-threaded builds expose them | Review, `-n auto`, 3.15t test run |

### Security
| Rule | Why | Enforced by |
|---|---|---|
| No `eval`/`exec` on input | Code execution | Ruff `S307`, `S102` |
| No `pickle`/`marshal` on untrusted bytes | Code execution | Ruff `S301` |
| `yaml.safe_load` only | `yaml.load` can construct objects | Ruff `S506` |
| No `shell=True` with interpolated input | Command injection | Ruff `S602`, `S604` |
| Parameterised SQL only | SQL injection | Ruff `S608` |
| `secrets`, not `random`, for tokens | Predictable values | Ruff `S311` |
| No hard-coded secrets; use `SecretStr` settings | Leaks in VCS and logs | Ruff `S105`-`S107`, secret scanning |
| `defusedxml` for untrusted XML | Entity expansion attacks | Ruff `S313`-`S319` |
| User-supplied paths stay under a base: `(base / p).resolve().is_relative_to(base.resolve())` | Path traversal (`../`, absolute paths, symlinks) | Review, a test with `../` and `/etc/passwd` |
| Extract archives with `tarfile` `filter="data"`; never `extractall` untrusted archives without it | Links and `..` members write outside the target | Review; the default is `data` only from 3.14 |
| Hash passwords with Argon2id (`argon2-cffi` `PasswordHasher`); never a plain `hashlib` digest | Fast hashes fall to offline cracking | Review; Ruff `S324` catches only MD5/SHA-1 |
| Lockfile committed, audited, cooled down | Supply-chain attacks | `uv lock --check`, pip-audit, `exclude-newer` |
| Actions pinned by SHA, workflows audited | CI token theft | `zizmor` |

### Performance
| Rule | Why | Enforced by |
|---|---|---|
| Measure before and after | Intuition about Python speed is often wrong | Benchmark output in the report |
| Remove N+1 I/O first | Round-trips dominate service latency | Review, query logging |
| Use the right container (`set`/`dict` lookups, `deque`) | Algorithmic wins dwarf micro-tuning | Ruff `PERF`, review |
| `functools.cache` only on pure functions with hashable args | Unbounded growth, stale results | Review |
| Startup cost: `lazy import` or local imports for heavy modules | CLI and serverless cold starts | `python -X importtime` |
| Avoid exceptions for control flow in hot loops | Raise/catch is costly | Profile (Tachyon `--mode exception` on 3.15) |

Profilers: `python -m profiling.sampling run --flamegraph -o out.html script.py` or `attach <PID>`
on 3.15 (wall, CPU, GIL and exception modes; `--async-aware` for asyncio), `py-spy` before 3.15,
`memray`/`tracemalloc` for memory, `scalene` for CPU+memory together.

### Packaging
| Rule | Why | Enforced by |
|---|---|---|
| `pyproject.toml` only; no `setup.py` for new code | One source of truth | Review |
| Dev tools in `[dependency-groups]` (PEP 735) | Not shipped to users | Review |
| `uv add`/`uv remove`, never hand-edited pins without relock | Lock drift | `uv lock --check` |
| `src/` layout | Tests run against the installed package | Review |
| Version bounds: apps lock exactly, libraries set lower bounds | Resolver freedom for library users | Review |
| Wheels for compiled code via cibuildwheel; `abi3`/`abi3t` where possible | Fewer wheels per release | CI |
| Trusted Publishing to PyPI | No long-lived tokens | CI config |
| Containers run as a non-root `USER`; code and venv root-owned | A compromised process cannot rewrite the app | Review, `docker run --rm <image> id -u` is not `0` |

### Frameworks (Django 6.1, pandas 3, Polars 2)
| Rule | Why | Enforced by |
|---|---|---|
| Django: querysets that cross relations use `select_related` (FK, one-to-one) or `prefetch_related` (many) | N+1 queries | `assertNumQueries` in tests |
| Django: every model change ships a migration | Models and schema drift | `python manage.py makemigrations --check --dry-run` exits non-zero |
| Django: keep `CsrfViewMiddleware`; `@csrf_exempt` only on token-authenticated APIs, with a reason | CSRF | `python manage.py check --deploy` (`security.W003`), review |
| Django: `ModelForm` lists `fields`; no `"__all__"`, no `exclude`; `mark_safe` only on trusted text | Mass assignment, XSS | Ruff `DJ006`, `DJ007` (select `DJ`), `S308` |
| pandas 3: write through `df.loc[row, col] = v`, never chained `df[col][row] = v` | Copy-on-Write is always on; chained assignment never updates `df` | `filterwarnings = ["error"]` turns `ChainedAssignmentError` into a failure |
| pandas 3: string columns are `str` dtype; test with `pd.api.types.is_string_dtype`, not `== object` | 3.0 made a dedicated string dtype the default | Tests, review |
| pandas: vectorise; no `iterrows`/`apply(axis=1)` in hot paths, no `inplace=True` | Python-level loops; `inplace` rarely saves memory | Profile, Ruff `PD002` (select `PD`) |
| Polars: pipelines use the lazy API (`pl.scan_parquet(...)` ... `.collect()`) | The optimiser pushes filters and projections into the scan | Review |
| Polars: expressions, not `map_elements` Python UDFs | Per-row Python calls | `PolarsInefficientMapWarning`, a failure under `filterwarnings = ["error"]` |
| Polars: explicit dtypes at I/O (`schema_overrides=`) | Inference changes with the data | Review |

Checked on 2026-10-29 with Django 6.1.2, pandas 3.0.6 and Polars 2.0.0 on CPython 3.15.0: the
`makemigrations --check` and `check --deploy` options exist, the chained assignment left the frame
unchanged and raised `ChainedAssignmentError` under `-W error`, `df["s"].dtype == "str"`, and
`map_elements` raised `PolarsInefficientMapWarning` under `-W error`.

## 4. Testing playbook

- Configure pytest 9 natively in `[tool.pytest]` with `strict = true` and
  `filterwarnings = ["error"]` (see the baseline). Strict mode turns unknown markers, config typos
  and unexpected xpasses into failures.
- One behaviour per test, named for the behaviour (`test_duplicate_name_returns_409`). Arrange, act,
  assert; no logic in tests.
- Parametrize instead of loops (`@pytest.mark.parametrize` with `ids=`). Use `subtests` (in core since
  9.0) when cases are only known at run time.
- Property tests with Hypothesis for parsers, serialisers, pure transforms and anything with an
  invariant (round-trip, idempotence, ordering). Keep `@settings(deadline=...)` explicit for slow
  code.
- Fakes over mocks. Patch only process boundaries: network (`httpx.MockTransport`, `respx`), clock
  (`time-machine`), randomness (seeded), filesystem (`tmp_path`). Never mock the unit under test or
  your own pure functions.
- Async tests: pytest-asyncio 1.x defaults to strict mode, so mark tests `@pytest.mark.asyncio` and
  async fixtures `@pytest_asyncio.fixture`; or use AnyIO's pytest plugin when the project uses AnyIO.
- Tests are independent: they pass with `-n auto` (xdist), in random order (pytest-randomly) and
  repeated in one process (`--count=20 -p no:xdist`), because xdist hides leaks that surface only
  at teardown.
- pytest style (narrow `pytest.raises`, parametrize argument shapes) is enforced by Ruff `PT`
  (`PT011`, `PT006`).
- Snapshot tests (`syrupy`) only for large stable outputs, reviewed on every update.
- Mutation testing (`mutmut`) on critical pure logic when coverage is high but trust is low.

## 5. Async playbook

```python
async with asyncio.timeout(5.0), asyncio.TaskGroup() as tg:   # deadline + structured concurrency
    a = tg.create_task(fetch("/a"))
    b = tg.create_task(fetch("/b"))
# Here both finished; if one failed, the other was cancelled and an ExceptionGroup was raised.
```

- Bound concurrency with `asyncio.Semaphore` when fanning out over user-sized input.
- Blocking work: `await asyncio.to_thread(fn, *args)`; CPU-heavy work: a process pool or queue.
- Cancellation-safe cleanup: `try: ... finally:` and re-raise `CancelledError`.
- Queues between producers and consumers (`asyncio.Queue(maxsize=N)`) to apply back-pressure.
- `asyncio.run(main())` once at the entry point; libraries never start their own loop.
- On 3.15, `python -m profiling.sampling run --async-aware` shows task-level stacks, and
  `python -m profiling.sampling dump --async-aware <PID>` prints every task of a hung process.

## 6. Review checklist (paste into the report, mark each)

- [ ] Behaviour change has a test that failed before the fix.
- [ ] Gates 1 to 8 run; outputs pasted with exit codes.
- [ ] Public API typed; no new untyped `Any`, bare ignores or `noqa`.
- [ ] Errors: no swallowing, causes chained, boundary handling only.
- [ ] Resources closed on every path; clients reused; timeouts set.
- [ ] No blocking calls in async code; tasks owned by a TaskGroup.
- [ ] Input validated at the boundary; no injection sinks reached by input.
- [ ] Dependencies added with `uv add`, lock updated, audit clean.
- [ ] Performance claims have before/after numbers and the command.
- [ ] Docs/docstrings updated for changed public behaviour.

## 7. Tool choices and when to deviate

| Need | Default | Choose instead when |
|---|---|---|
| Env + deps | uv | Repo is on Poetry/PDM/pip-tools and migration is out of scope |
| Lint + format | Ruff | Never run Black/isort/flake8 alongside Ruff; pick one source |
| Types | mypy strict as gate + ty for speed | Repo standardised on Pyright/basedpyright or Pyrefly |
| Tests | pytest 9 + Hypothesis | Never add unittest-style suites to a pytest repo |
| Task runner | the repo's Makefile/nox | nox (2026.10.20) for multi-Python sessions |
| Pre-commit | prek or pre-commit | Repo already has one; do not add both |
| Web API | FastAPI 0.16x + Pydantic 2.14 | Django 6.1 when you need admin, ORM migrations and auth built in |
| Data frames | Polars 2.x for new pipelines | pandas 3.x when the ecosystem around it requires pandas |
| Native speed | NumPy vectorisation | PyO3/maturin, nanobind or Cython for hot loops that profiling proved |
