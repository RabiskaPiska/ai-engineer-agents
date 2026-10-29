# Sources: python (python-engineer agent + python-engineering skill)

Fetched and verified on 2026-10-29. Deliverables:
- `claude/agents/python-engineer.md`
- `skills/python-engineering/SKILL.md`
- `skills/python-engineering/references/pyproject-baseline.md`
- `skills/python-engineering/references/service-patterns.md`

Mined repositories were read as text only. No code or install step from them was run.

## The 5 GitHub repositories used

Fields come from `ghapi.sh repos/<owner>/<repo>` on 2026-10-29 (JSON pasted per repo).

### 1. wshobson/agents
```json
{"full_name": "wshobson/agents", "html_url": "https://github.com/wshobson/agents", "stargazers_count": 41969, "pushed_at": "2026-10-26T01:08:14Z", "archived": false, "license": "MIT"}
```
Read: `plugins/python-development/agents/python-pro.md`,
`plugins/python-development/skills/python-anti-patterns/SKILL.md`,
`plugins/python-development/skills/async-python-patterns/SKILL.md`.
Taken: the anti-pattern families that became the agent's "Anti-patterns" list (scattered retry
logic, exposed internal types/ORM leakage, mixed I/O and business logic, over-mocking, only testing
happy paths, blocking in async), and the sync-vs-async decision framing. Not taken: its
"Python 3.12+ / 2024-2025 ecosystem" version claims, which are out of date, and its broad
capability lists, which I replaced with checkable rules. MIT; ideas adapted, no text copied.

### 2. VoltAgent/awesome-claude-code-subagents
```json
{"full_name": "VoltAgent/awesome-claude-code-subagents", "html_url": "https://github.com/VoltAgent/awesome-claude-code-subagents", "stargazers_count": 26164, "pushed_at": "2026-10-11T08:20:37Z", "archived": false, "license": "MIT"}
```
Read: `categories/02-language-specialists/python-pro.md`.
Taken: the "when invoked, first inspect the existing codebase, environment and conventions"
opening, which became step 1 of the Operating loop and the "existing convention beats these
defaults" rule. Not taken: Black-based formatting, a fixed ">90% coverage" target without branch
coverage, and "security scanning with bandit" (replaced by Ruff `S` rules, which implement the
bandit checks, plus pip-audit). MIT; ideas adapted, no text copied.

### 3. trailofbits/skills
```json
{"full_name": "trailofbits/skills", "html_url": "https://github.com/trailofbits/skills", "stargazers_count": 7872, "pushed_at": "2026-10-28T19:41:17Z", "archived": false, "license": "CC-BY-SA-4.0"}
```
Read: `plugins/modern-python/skills/modern-python/SKILL.md`, its `references/ruff-config.md` and
`references/security-setup.md`, and `plugins/sharp-edges/skills/sharp-edges/references/lang-python.md`.
Taken (paraphrased only, because CC-BY-SA): the uv-first workflow (`uv add` instead of editing pins,
`uv run` instead of activating venvs, `[dependency-groups]` for dev tools, ty in the type stack),
the `[tool.ty.environment] python-version` placement, `zizmor` and pip-audit as CI security tools,
and the Python sharp-edges list (mutable defaults, late-binding closures, `is` vs `==`, import
shadowing, shell injection, format-string injection, unsafe deserialisation). I mapped each sharp
edge to a Ruff rule code that enforces it and verified every code exists in the Ruff 0.17 schema.

### 4. scientific-python/cookie
```json
{"full_name": "scientific-python/cookie", "html_url": "https://github.com/scientific-python/cookie", "stargazers_count": 411, "pushed_at": "2026-10-26T06:10:20Z", "archived": false, "license": "BSD-3-Clause"}
```
Read: `docs/guides/pytest.md`, `docs/guides/style.md`, `docs/guides/typing.md`,
`docs/guides/security.md`, `docs/guides/coverage.md`.
Taken: the pytest 9 native `[tool.pytest]` table with `strict = true`, `filterwarnings = ["error"]`
and `-ra`; no `__init__.py` in `tests/`; the Ruff `extend-select` families (B, C4, PTH, PT, RUF,
SIM, TC, TRY, UP, PERF, LOG, G, PGH, T20); the per-checker defaults comparison (mypy vs Pyrefly vs
ty); and the supply-chain cooldown (`[tool.uv] exclude-newer`, Dependabot cooldown). BSD-3; the
config keys are standard tool configuration, adapted with attribution here.

### 5. zhanymkanov/fastapi-best-practices
```json
{"full_name": "zhanymkanov/fastapi-best-practices", "html_url": "https://github.com/zhanymkanov/fastapi-best-practices", "stargazers_count": 18258, "pushed_at": "2026-08-27T12:54:52Z", "archived": false, "license": null}
```
Read: `README.md` (async routes, Pydantic, dependencies, threadpool for sync SDKs,
BackgroundTasks vs a task queue, DB naming conventions, Alembic, async test client).
Taken (paraphrased only, because the repo has no license): never block inside `async def` routes;
run sync SDKs in a threadpool; CPU-bound work goes to processes or a queue; BackgroundTasks only for
work you can afford to lose; separate API schemas from DB models; reversible, date-slugged Alembic
migrations; async test client from day one. These appear in the agent's concurrency rules and in
`references/service-patterns.md`, whose code I wrote and tested myself.

## MCP servers declared or mentioned

| Server | Repo check (ghapi, 2026-10-29) | Install / config used | Verification |
|---|---|---|---|
| github (by name) | https://github.com/github/github-mcp-server : 34054 stars, pushed 2026-10-29T05:42:25Z, MIT | referenced by name; spec says it is already configured | name reference only |
| context7 (inline http) | https://github.com/upstash/context7 : 63882 stars, pushed 2026-10-28T20:26:24Z, MIT | `type: http`, `url: https://mcp.context7.com/mcp` | `initialize` POST returned HTTP 200 on 2026-10-29; tools `resolve-library-id` and `query-docs` are the names exposed in this session |
| serena (inline stdio) | https://github.com/oraios/serena : 30833 stars, pushed 2026-10-28T10:45:55Z, licence per component (SolidLSP MIT, Serena app GPL-3.0-or-later; API reports NOASSERTION) | `command: serena`, `args: [start-mcp-server, --context, claude-code, --project-from-cwd]` from `docs/02-usage/030_clients.md`; install `uv tool install -p 3.13 serena-agent` from `docs/02-usage/010_installation.md`; Python uses Pyright by default (ty, basedpyright, pyrefly, jedi selectable) per `docs/01-about/020_programming-languages.md`; tool names derived from `src/serena/tools/symbol_tools.py` class names via `get_name_from_cls` | config read from docs; `[UNVERIFIED]` not installed or started here (rule: never run code from mined repos) |
| jupyter-mcp-server (optional, not declared) | https://github.com/datalayer/jupyter-mcp-server : 1315 stars, pushed 2026-10-27T15:00:40Z, BSD-3-Clause | `uvx jupyter-mcp-server@latest` with `JUPYTER_URL`, `JUPYTER_TOKEN` env (README) | config read from README only |

Rejected: `pydantic/mcp-run-python` (archived, last push 2026-01-30); PyPI-metadata MCP servers
found by search (all under 20 stars or last pushed in 2025).

## Official version sources (fetched 2026-10-29)

| Fact | Source |
|---|---|
| CPython release list and dates (3.15.2, 3.14.10, 3.13.18, 3.12.16, 3.11.18 on 2026-10-25; 3.15.0 on 2026-10-09; 3.16.0a1 on 2026-10-13; 3.10.22 on 2026-10-01) | https://www.python.org/api/v2/downloads/release/?is_published=true |
| 3.15 schedule (final 2026-10-09, 3.15.2 listed 2026-10-26, security until 2031-10) | https://peps.python.org/pep-0790/ |
| Branch status (3.15/3.14 bugfix, 3.11-3.13 security, 3.10 EOL 2026-10-01) | https://devguide.python.org/versions/ |
| 3.15 features: lazy imports, frozendict, sentinel, comprehension unpacking, UTF-8 default, profiling/Tachyon, TypeForm, closed TypedDict, disjoint_base, abi3t, JIT, 3.15.2 notes | https://docs.python.org/3.15/whatsnew/3.15.html |
| Tachyon CLI flags | https://docs.python.org/3.15/library/profiling.sampling.html |
| Free-threading behaviour | https://docs.python.org/3.15/howto/free-threading-python.html |
| 3.14 features (PEP 649/750/758/779, zstd) | https://docs.python.org/3.14/whatsnew/3.14.html |
| uv 0.13.6, ruff 0.17.3, ty 0.0.94, pytest 9.2.0 releases | https://github.com/astral-sh/uv/releases, https://github.com/astral-sh/ruff/releases, https://github.com/astral-sh/ty/releases, https://github.com/pytest-dev/pytest/releases |
| uv commands, preview features (`audit-command`, `check-command`, `format-command`), `exclude-newer`, export formats | https://docs.astral.sh/uv/reference/cli/, https://docs.astral.sh/uv/concepts/preview/ |
| uv Docker and GitHub Actions guidance (`UV_COMPILE_BYTECODE`, `UV_LINK_MODE`, `UV_NO_DEV`, setup-uv v9.0.0 SHA) | https://github.com/astral-sh/uv/blob/main/docs/guides/integration/docker.md, https://github.com/astral-sh/uv/blob/main/docs/guides/integration/github.md |
| Ruff 0.16 (413 default rules, Markdown formatting, `ruff: ignore`) and 0.17 (py311 default, DTZ out of default set) | https://github.com/astral-sh/ruff/releases/tag/0.16.0, https://github.com/astral-sh/ruff/blob/main/CHANGELOG.md |
| Ruff rule codes and `py315` target | https://github.com/astral-sh/ruff/blob/main/ruff.schema.json |
| ty beta status, configuration (`environment.python-version`, `rules`, `terminal.error-on-warning`, exit 1 on warnings) | https://github.com/astral-sh/ty/blob/main/README.md, https://github.com/astral-sh/ty/blob/main/docs/reference/configuration.md |
| mypy 2.0 defaults and 2.4 Python 3.15 support | https://github.com/python/mypy/blob/master/CHANGELOG.md |
| pytest 9 native TOML config, strict mode, subtests | https://github.com/pytest-dev/pytest/blob/main/doc/en/changelog.rst |
| pytest-asyncio config (strict default, loop scope keys) | https://github.com/pytest-dev/pytest-asyncio/blob/main/docs/reference/configuration.rst |
| coverage.py `sysmon` default on 3.14+ | https://github.com/coveragepy/coveragepy/blob/main/CHANGES.rst (repo moved from nedbat/coveragepy; the old API path returns "Moved Permanently") |
| pip-audit flags (`--locked` supports pyproject/pylock only; `--disable-pip` needs hashes or `--no-deps`) | https://github.com/pypa/pip-audit/blob/main/README.md |
| Package versions and upload dates (uv, ruff, ty, mypy, pyright, pyrefly, pytest and plugins, hypothesis, coverage, pip-audit, FastAPI, Pydantic, SQLAlchemy, Django, NumPy, pandas, Polars, nox, prek, and others) and cp315 wheel availability | https://pypi.org/pypi/<name>/json |
| `python:3.15-slim` image tag (updated 2026-10-28) | https://hub.docker.com/v2/repositories/library/python/tags/3.15-slim |
| Claude Code subagent frontmatter, mcpServers format, nested subagents (depth 3 default) | https://code.claude.com/docs/en/sub-agents.md (copy fetched by the orchestrator) |
| Ruff 0.16.0: 18 E/F rules left the default set (incl. `E711`, `E712`, `E721`); `# ruff: ignore[...]` comments | `ghapi.sh repos/astral-sh/ruff/releases/tags/0.16.0` (release body), https://github.com/astral-sh/ruff/releases/tag/0.16.0 |
| Non-root container user (`groupadd`/`useradd --system`, `PATH` to the venv, `USER` before `CMD`) | `astral-sh/uv-docker-example` `Dockerfile` via `ghapi.sh repos/astral-sh/uv-docker-example/contents/Dockerfile` (Apache-2.0/MIT, pushed 2026-10-21T18:23:29Z); an official Astral example, not one of the 5 mined repos |
| `tarfile` default extraction filter became `data` in 3.14 | https://docs.python.org/3.15/library/tarfile.html |
| pytest-repeat 0.9.4 (`--count`), pytest-run-parallel 0.10.0 (`--parallel-threads`, `--iterations`, not an xdist replacement), pyperf 2.10.0 (`timeit -o`, `compare_to --table`), argon2-cffi 25.1.0 | https://pypi.org/project/pytest-repeat/, https://pypi.org/project/pytest-run-parallel/, https://pyperf.readthedocs.io/en/latest/cli.html, https://argon2-cffi.readthedocs.io/en/stable/api.html |
| pandas 3.0 Copy-on-Write and default `str` dtype | https://pandas.pydata.org/docs/whatsnew/v3.0.0.html |
| Django 6.1 `makemigrations --check`, `check --deploy`, `select_related`/`prefetch_related` | https://docs.djangoproject.com/en/6.1/ref/django-admin/, https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/, https://docs.djangoproject.com/en/6.1/ref/models/querysets/ |
| Polars lazy API and Python UDF cost | https://docs.pola.rs/user-guide/lazy/, https://docs.pola.rs/user-guide/expressions/user-defined-python-functions/ |

## Commands executed this session (evidence)

Scratch projects under the session scratchpad (not part of the deliverable): `py-gate-smoke/demo` and `py-gate-smoke2/myapp`, both CPython 3.15.0 via uv 0.13.1.

1. 3.15 features under the gates (`lazy import json`, `sentinel`, `frozendict`, `int | MISSING`
   annotation): `ruff format --check` "3 files already formatted" exit 0; `ruff check`
   "All checks passed!" exit 0; `ty check` "All checks passed!" exit 0; `mypy` "Success: no issues
   found in 2 source files" exit 0; pytest "5 passed", coverage gate
   "FAIL Required test coverage of 90.0% not reached. Total coverage: 85.00%" exit 1; after two
   more tests "Required test coverage of 90.0% reached. Total coverage: 100.00% / 7 passed" exit 0.
2. `uv lock --check` exit 0; `uv export --frozen --no-emit-project --format requirements.txt` then
   `uvx pip-audit --strict --require-hashes --disable-pip -r ...` "No known vulnerabilities found"
   exit 0.
3. `python -m profiling.sampling run --flamegraph -o ../profile.html -m demo` wrote a 627 KB HTML
   flame graph.
4. `pytest -p randomly`, `pytest -n auto`, `python -X dev -m pytest -p no:randomly`: 5 passed each.
5. `UV_PROJECT_ENVIRONMENT=.venv-ft uv run --python 3.15t --frozen ...`:
   "3.15.0 free-threading build ... GIL enabled: False"; tests 5 passed.
6. pytest-benchmark 5.3.0 under pytest 9.2.0: `AttributeError: 'Function' object has no attribute
   '_nodeid'`; the same test under `--with "pytest<9.2"` (9.1.1): 1 passed. No matching upstream
   issue was found by GitHub search on 2026-10-29.
7. The baseline with a 7-day `exclude-newer` cooldown and fresh lower bounds (`uv_build>=0.13.6`,
   `hypothesis>=6.170.13`) failed to resolve; with ranges (`uv_build>=0.13,<0.14`) it resolved and
   all gates passed (pytest resolved to 9.1.1). The bootstrap block in `pyproject-baseline.md` was
   then executed verbatim in a fresh directory: exit 0.
8. Service patterns (FastAPI 0.159.1, SQLAlchemy 2.1.6, httpx 0.28.1, pydantic-settings 2.16.1):
   first run surfaced 7 Ruff `TC` findings, a ty deprecation for `@asynccontextmanager` returning
   `AsyncIterator`, a mypy/ty error on `LifespanManager.app.state`, and 4 pytest errors from async
   fixtures under strict mode. After fixes: format 0, lint 0, ty 0, mypy 0, "4 passed",
   98.92% coverage. `uv build` plus `uv run --isolated --with dist/*.whl python -c "import myapp,
   myapp.api"` printed "wheel import ok".
9. `mypy --enable-error-code explicit-override` flagged an un-decorated override ("[explicit-override]"),
   exit 1.
10. Every Ruff rule code cited in the agent and skill was checked against `ruff.schema.json`
    (2415 selectors); `S320` was absent and the XML range was corrected to `S313`-`S319`.

## Fix pass (2026-10-29, after review)

Scratch projects: `pyfix/w2/myapp` (baseline plus service) and `pyfix/w3/myapp` (baseline only),
CPython 3.15.0, uv 0.13.1. The full change log is `_work/fixes/python.md`.

11. Bootstrap block executed verbatim (twice, fresh directories): the cooldown resolved ruff
    0.17.1, ty 0.0.90, mypy 2.4.0, pytest 9.1.1, coverage 7.16.2, hypothesis 6.170.5, pytest-repeat
    0.9.4. With uv init's template, `ruff check` reported `T201` at `src/myapp/__init__.py:2:5`
    (exit 1); after the documented `cli.py` step, format, lint, ty, mypy, `pytest -n auto --cov`
    (100%) and the `mktemp` pip-audit gate all exited 0, and `uv run myapp` logged
    `INFO:myapp.cli:myapp started`.
12. Original service code, extracted verbatim from the old reference: plain
    `pytest -q -p no:randomly --no-cov` failed 7/15 (PytestUnraisableExceptionWarning, "aiosqlite
    Connection ... was deleted before being closed"), `python -X dev -m pytest -q -p no:randomly`
    failed 1/12, `pytest -n auto --cov` failed 0/10, and one `--count=20 -p no:xdist` run failed
    2 of 100. A rollback probe logged `['response 409', 'client closed', 'rollback', 'lifespan exited']`.
13. Fixed service (`@asynccontextmanager` + `async with`, `except*` mapping, 8 tests): format,
    lint, ty, mypy exit 0; `pytest -n auto --cov` 8 passed, 99.03%; plain loop 0/15; `-X dev` loop
    0/12; repeat gate `python -X dev -m pytest -q -p no:xdist --no-cov --count=20` 0/5 (160 passed
    each); `-n auto --cov` 0/10. Probe: `['rollback', 'response 409', 'client closed', 'lifespan exited']`.
14. `except*` on 3.15.0: one raise from one clause propagates unwrapped (`HTTPException`); raises
    from two clauses produce `ExceptionGroup('', [...])`.
15. Free-threaded: `uv run --python 3.15t --frozen pytest -q` without a `dev` group printed
    `Failed to spawn: pytest`; with `--all-groups`, 8 passed, `GIL enabled: False`.
    pytest-run-parallel on async tests: "coroutine ... was never awaited" (14 errors); with
    `-m "not asyncio"`: "All tests were run in parallel!".
16. The SKILL.md 3.15 snippet (old lines 79-90 verbatim): `ruff check` exit 1 (I001, F401),
    `ruff format --check` exit 1. New snippet: both 0, ty 0, `mypy --strict` 0, runtime
    `3 5 sentinel {"retries": 3, "timeout_s": 10}`.
17. pyperf 2.10.0: `compare_to --table` printed `215.78x faster` for list vs set membership and
    `Benchmark hidden because not significant (1): timeit` for two runs of the same code.
18. Ruff 0.17.1: `x == None`, `y == True`, `type(x) == type(y)` pass with default rules and fail
    with the baseline's `E711`/`E712`/`E721`; `import math  # ruff: ignore[F401]` passes.
19. Library floor: `mypy --python-version 3.11` and `ty check --python-version 3.11` both exit 1
    on the 3.15 service (`type` statement, `lazy` import).
20. Security snippets: `safe_join` rejected `../etc/passwd` and `/etc/passwd`; `tarfile`
    `filter="data"` raised `OutsideDestinationError` for `../evil.txt`; argon2-cffi 25.1.0 produced
    an `argon2id` hash, verified it, and raised `VerifyMismatchError` for a wrong password.
21. Frameworks: Django 6.1.2 `makemigrations` has `--check`, `check` has `--deploy`, the CSRF
    check is `security.W003`, `assertNumQueries` exists; pandas 3.0.6 chained assignment left the
    frame unchanged and raised `ChainedAssignmentError` under `-W error`, string dtype `str`;
    Polars 2.0.0 `map_elements` raised `PolarsInefficientMapWarning` under `-W error`,
    `read_csv(schema_overrides=...)` and `scan_parquet` exist.
22. Docker: `docker info` exit 1 ("permission denied while trying to connect to the docker API");
    no podman or buildah. The non-root Dockerfile is `[UNVERIFIED]`.

## Self-check

### yaml.safe_load on both frontmatters
```
claude/agents/python-engineer.md safe_load OK keys= ['name', 'description', 'model', 'skills', 'mcpServers']
  mcpServers= ['github', {'context7': {'type': 'http', 'url': 'https://mcp.context7.com/mcp'}}, {'serena': {'type': 'stdio', 'command': 'serena', 'args': ['start-mcp-server', '--context', 'claude-code', '--project-from-cwd']}}]
  skills= ['python-engineering'] name= python-engineer model= inherit
skills/python-engineering/SKILL.md safe_load OK keys= ['name', 'description']
agent fields subset of spec-allowed: True []
```

### Section-heading check (agent body, literal headings, in order)
```
required headings present in order: True
  OK  ## Role and scope
  OK  ## Operating loop
  OK  ## Toolchain baseline (October 2026)
  OK  ## Engineering rules
  OK  ## Verification gates
  OK  ## Delegation
  OK  ## MCP and skills usage
  OK  ## Anti-patterns
  OK  ## Output contract
```

Line counts after the fix pass (re-run 2026-10-29): agent 461 lines (target 250-500), SKILL.md
323 lines (target 150-400), references 260 + 347 lines. ALL-CAPS imperative words in agent + skill: 0.

### Link check
Re-run after the fix pass. Every URL in the agent, the skill, both references and this file was
extracted; each `github.com/<owner>/<repo>` was checked with `ghapi.sh repos/<owner>/<repo>` (pass =
`full_name` returned and `archived` false) and every other URL with `curl -sL` (pass = HTTP 2xx; the
context7 endpoint with an MCP `initialize` POST). Placeholder hosts used in test code
(`example.invalid`, `http://up`, `http://test`) and the `https://pypi.org/pypi/<name>/json`
template were skipped.

```
ghapi repos/VoltAgent/awesome-claude-code-subagents: OK full_name=VoltAgent/awesome-claude-code-subagents pushed_at=2026-10-11T08:20:37Z archived=False
ghapi repos/astral-sh/ruff: OK full_name=astral-sh/ruff pushed_at=2026-10-29T05:21:24Z archived=False
ghapi repos/astral-sh/ty: OK full_name=astral-sh/ty pushed_at=2026-10-28T22:10:52Z archived=False
ghapi repos/astral-sh/uv: OK full_name=astral-sh/uv pushed_at=2026-10-29T05:15:25Z archived=False
ghapi repos/coveragepy/coveragepy: OK full_name=coveragepy/coveragepy pushed_at=2026-10-28T23:54:07Z archived=False
ghapi repos/datalayer/jupyter-mcp-server: OK full_name=datalayer/jupyter-mcp-server pushed_at=2026-10-27T15:00:40Z archived=False
ghapi repos/github/github-mcp-server: OK full_name=github/github-mcp-server pushed_at=2026-10-29T05:42:25Z archived=False
ghapi repos/oraios/serena: OK full_name=oraios/serena pushed_at=2026-10-28T10:45:55Z archived=False
ghapi repos/pypa/pip-audit: OK full_name=pypa/pip-audit pushed_at=2026-10-28T16:05:07Z archived=False
ghapi repos/pytest-dev/pytest: OK full_name=pytest-dev/pytest pushed_at=2026-10-28T15:34:45Z archived=False
ghapi repos/pytest-dev/pytest-asyncio: OK full_name=pytest-dev/pytest-asyncio pushed_at=2026-10-28T21:47:18Z archived=False
ghapi repos/python/mypy: OK full_name=python/mypy pushed_at=2026-10-28T18:55:49Z archived=False
ghapi repos/scientific-python/cookie: OK full_name=scientific-python/cookie pushed_at=2026-10-26T06:10:20Z archived=False
ghapi repos/trailofbits/skills: OK full_name=trailofbits/skills pushed_at=2026-10-28T19:41:17Z archived=False
ghapi repos/upstash/context7: OK full_name=upstash/context7 pushed_at=2026-10-28T20:26:24Z archived=False
ghapi repos/wshobson/agents: OK full_name=wshobson/agents pushed_at=2026-10-26T01:08:14Z archived=False
ghapi repos/zhanymkanov/fastapi-best-practices: OK full_name=zhanymkanov/fastapi-best-practices pushed_at=2026-08-27T12:54:52Z archived=False
HTTP 200 OK https://argon2-cffi.readthedocs.io/en/stable/api.html
HTTP 200 OK https://code.claude.com/docs/en/sub-agents.md
HTTP 200 OK https://devguide.python.org/versions/
HTTP 200 OK https://docs.astral.sh/uv/concepts/preview/
HTTP 200 OK https://docs.astral.sh/uv/reference/cli/
HTTP 200 OK https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/
HTTP 200 OK https://docs.djangoproject.com/en/6.1/ref/django-admin/
HTTP 200 OK https://docs.djangoproject.com/en/6.1/ref/models/querysets/
HTTP 200 OK https://docs.pola.rs/user-guide/expressions/user-defined-python-functions/
HTTP 200 OK https://docs.pola.rs/user-guide/lazy/
HTTP 200 OK https://docs.python.org/3.14/whatsnew/3.14.html
HTTP 200 OK https://docs.python.org/3.15/howto/free-threading-python.html
HTTP 200 OK https://docs.python.org/3.15/library/profiling.sampling.html
HTTP 200 OK https://docs.python.org/3.15/library/tarfile.html
HTTP 200 OK https://docs.python.org/3.15/whatsnew/3.15.html
HTTP 200 OK https://github.com/astral-sh/ruff/blob/main/CHANGELOG.md
HTTP 200 OK https://github.com/astral-sh/ruff/blob/main/ruff.schema.json
HTTP 200 OK https://github.com/astral-sh/ruff/releases
HTTP 200 OK https://github.com/astral-sh/ruff/releases/tag/0.16.0
HTTP 200 OK https://github.com/astral-sh/ty/blob/main/README.md
HTTP 200 OK https://github.com/astral-sh/ty/blob/main/docs/reference/configuration.md
HTTP 200 OK https://github.com/astral-sh/ty/releases
HTTP 200 OK https://github.com/astral-sh/uv/blob/main/docs/guides/integration/docker.md
HTTP 200 OK https://github.com/astral-sh/uv/blob/main/docs/guides/integration/github.md
HTTP 200 OK https://github.com/astral-sh/uv/releases
HTTP 200 OK https://github.com/coveragepy/coveragepy/blob/main/CHANGES.rst
HTTP 200 OK https://github.com/pypa/pip-audit/blob/main/README.md
HTTP 200 OK https://github.com/pytest-dev/pytest-asyncio/blob/main/docs/reference/configuration.rst
HTTP 200 OK https://github.com/pytest-dev/pytest/blob/main/doc/en/changelog.rst
HTTP 200 OK https://github.com/pytest-dev/pytest/releases
HTTP 200 OK https://github.com/python/mypy/blob/master/CHANGELOG.md
HTTP 200 OK https://hub.docker.com/v2/repositories/library/python/tags/3.15-slim
HTTP 200 OK https://mcp.context7.com/mcp
HTTP 200 OK https://pandas.pydata.org/docs/whatsnew/v3.0.0.html
HTTP 200 OK https://peps.python.org/pep-0790/
HTTP 200 OK https://pyperf.readthedocs.io/en/latest/cli.html
HTTP 200 OK https://pypi.org/project/pytest-repeat/
HTTP 200 OK https://pypi.org/project/pytest-run-parallel/
HTTP 200 OK https://www.python.org/api/v2/downloads/release/?is_published=true
TOTAL ok=56 fail=0
```
