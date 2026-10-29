# pyproject.toml baseline (tested 2026-10-29)

This is a starting configuration for a new application or library. The bootstrap block and the
`[tool.*]` blocks below were run end to end on 2026-10-29 in a fresh directory on CPython 3.15.0
with uv 0.13.1. The 7-day cooldown resolved Ruff 0.17.1, ty 0.0.90, mypy 2.4.0, pytest 9.1.1,
pytest-cov 7.1.0, coverage 7.16.2, pytest-xdist 3.8.0, pytest-randomly 5.0.0, pytest-repeat 0.9.4,
Hypothesis 6.170.5 and pip-audit 2.10.1. These are older than the newest releases listed in the
agent's toolchain table, which is what a cooldown is for. Format, lint, ty, mypy,
`pytest -n auto --cov` (100% coverage) and pip-audit all exited 0. In an earlier run the coverage
gate exited 1 at 85% against `fail_under = 90`. Adapt the configuration to the repo; an existing
configuration wins over this one.

Order matters with a cooldown: write `[tool.uv] exclude-newer` first, then `uv add`, so the lower
bounds uv writes are versions the cooldown allows. A first attempt that pinned
`uv_build>=0.13.6` and `hypothesis>=6.170.13` (both newer than the cutoff) failed to resolve.

Create the project and the tool groups with uv instead of typing version pins by hand:

```bash
uv init --package --python 3.15 myapp     # src/ layout, uv_build backend, .python-version
cd myapp
printf '\n[tool.uv]\nexclude-newer = "7 days"\n' >> pyproject.toml
# uv init pins uv_build to the running uv's version; widen it so the cooldown can resolve it:
sed -i 's/"uv_build>=[0-9.]*,<\([0-9.]*\)"/"uv_build>=0.13,<\1"/' pyproject.toml
uv add --group lint ruff ty mypy
uv add --group test pytest pytest-cov pytest-xdist pytest-randomly pytest-repeat hypothesis
uv add --group audit pip-audit
uv lock && uv sync --locked --all-groups
```

Before the first gate run, replace the template's entry point. `uv init` writes a `main()` that
calls `print()`, and the `T20` rule below rejects it (observed: `T201` at
`src/myapp/__init__.py:2:5`, exit 1). The baseline's `[project.scripts]` points at `myapp.cli:main`,
so create that module and a smoke test:

```bash
: > src/myapp/__init__.py      # drop uv init's print() template
mkdir -p tests
cat > src/myapp/cli.py <<'PY'
import logging

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger.info("myapp started")
PY
cat > tests/test_cli.py <<'PY'
import logging

lazy import pytest

from myapp.cli import main


def test_main_logs_start(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        main()
    assert "myapp started" in caplog.text
PY
```

`lazy import pytest` is what Ruff's `TC002` fix writes for a 3.15 target, because `pytest` is used
only in an annotation. On a floor below 3.15, Ruff moves it into an `if TYPE_CHECKING:` block
instead.

```toml
[project]
name = "myapp"
version = "0.1.0"
description = "..."
readme = "README.md"
requires-python = ">=3.15"          # library: the oldest non-EOL version you support, e.g. ">=3.11"
dependencies = []

[project.scripts]
myapp = "myapp.cli:main"            # src/myapp/cli.py, created in the step above

[build-system]
requires = ["uv_build>=0.13,<0.14"]   # a range, so the cooldown below can still resolve it
build-backend = "uv_build"

[dependency-groups]
dev = [{ include-group = "lint" }, { include-group = "test" }, { include-group = "audit" }]
lint = ["ruff>=0.17", "ty>=0.0.90", "mypy>=2.4"]
test = ["pytest>=9.1", "pytest-cov>=7.1", "pytest-xdist>=3.8",
        "pytest-randomly>=5.0", "pytest-repeat>=0.9", "hypothesis>=6.170"]
audit = ["pip-audit>=2.10"]

[tool.uv]
# Supply-chain cooldown: ignore distributions uploaded in the last 7 days.
# Trade-off: security fixes also arrive 7 days later. Override per package with
# exclude-newer-package when you need an urgent fix.
exclude-newer = "7 days"

[tool.ruff]
line-length = 100
src = ["src", "tests"]
# target-version is inferred from requires-python; set it only if they must differ.

[tool.ruff.lint]
# Ruff 0.16+ already enables 413 default rules. Add the families that catch real bugs in
# production code; each one has a row in SKILL.md section 3.
extend-select = [
  "ASYNC", # blocking calls in async code
  "B",     # bugbear: mutable defaults, loop closures, raise-from
  "BLE",   # blind except
  "C4",    # comprehensions
  "DTZ",   # naive datetimes (removed from the default set in 0.17)
  "E711",  # `== None`; left the default set in 0.16
  "E712",  # `== True` / `== False`; left the default set in 0.16
  "E721",  # `type(x) == type(y)`; left the default set in 0.16
  "G",     # logging format
  "LOG",   # logging misuse
  "PERF",  # performance anti-patterns
  "PGH",   # blanket type: ignore / noqa
  "PT",    # pytest style
  "PTH",   # pathlib
  "RET",   # return consistency
  "RUF",   # Ruff-specific, incl. RUF006 dangling task, RUF012 mutable class attr
  "S",     # bandit security rules
  "SIM",   # simplifications, incl. SIM115 open without context manager
  "T20",   # print
  "TC",    # type-checking-only imports
  "TRY",   # exception anti-patterns
  "UP",    # pyupgrade to the target version
]
ignore = [
  "TRY003", # long messages in raise are fine for application code
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "PLR2004"]   # assert and magic numbers are normal in tests

[tool.ty.environment]
python-version = "3.15"            # library: the floor from requires-python, e.g. "3.11"

[tool.ty.rules]
possibly-unresolved-reference = "error"
unused-ignore-comment = "warn"     # ty exits 1 on warnings by default

[tool.mypy]
strict = true
python_version = "3.15"            # library: the floor, e.g. "3.11"; CI also checks each matrix version
warn_unreachable = true
enable_error_code = ["ignore-without-code", "redundant-expr", "truthy-bool"]

[tool.pytest]
minversion = "9.0"
addopts = ["-ra", "--import-mode=importlib"]
strict = true                      # strict_config, strict_markers, strict_parametrization_ids, strict_xfail
filterwarnings = ["error"]
testpaths = ["tests"]
xfail_strict = true

[tool.coverage.run]
branch = true
source = ["myapp"]

[tool.coverage.report]
fail_under = 90
show_missing = true
skip_covered = true
exclude_also = [
  "if TYPE_CHECKING:",
  "raise NotImplementedError",
  "@overload",
]
```

Notes:
- `strict = true` in `[tool.pytest]` turns on every pytest strictness option, including ones added
  in future releases. Enable it only with pytest pinned through `uv.lock`, which this setup does.
- `[tool.pytest]` (native TOML, pytest 9+) and `[tool.pytest.ini_options]` cannot both be present.
- `filterwarnings = ["error"]` makes new deprecation warnings fail the suite. Add targeted
  `"ignore:<message regex>:<Category>:<module>"` entries for third-party noise, never a blanket
  ignore.
- Do not put `__init__.py` in `tests/` with `--import-mode=importlib`; test files need unique
  basenames or a package layout under `tests/`.
- For a library, also add `src/<pkg>/py.typed` (empty) and a CI matrix over every supported Python.
  Set mypy `python_version` and ty `python-version` to the floor, not the newest version, so
  newer-only syntax and APIs fail locally; the CI job below also passes `--python-version` for each
  matrix entry. Observed on 2026-10-29: the 3.15 service checked with `--python-version 3.11`
  failed in both checkers (ty: `Cannot use lazy import statement on Python 3.11`; mypy:
  `"type" statements: requires Python 3.12 or newer`).
- The `asyncio_mode` key is needed only with pytest-asyncio; its default is `strict`, which requires
  `@pytest.mark.asyncio` on each async test. Set
  `asyncio_default_fixture_loop_scope = "function"` explicitly to silence the future-default warning
  under `filterwarnings = ["error"]`.

## GitHub Actions job

`astral-sh/setup-uv` is pinned by commit SHA in uv's own integration guide (v9.0.0 at
`c771a70e6277c0a99b617c7a806ffedaca235ff9` on 2026-10-29). Pin every third-party action by SHA
and audit workflows with `zizmor`.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python: ["3.15"]            # library: ["3.11", "3.12", "3.13", "3.14", "3.15"]
    steps:
      - uses: actions/checkout@<sha>
        with: { persist-credentials: false }
      - uses: astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9  # v9.0.0
        with: { enable-cache: true, python-version: "${{ matrix.python }}" }
      - run: uv lock --check
      - run: uv sync --locked --all-groups
      - run: uv run --frozen ruff format --check --output-format=github .
      - run: uv run --frozen ruff check --output-format=github .
      - run: uv run --frozen ty check --python-version ${{ matrix.python }}
      - run: uv run --frozen mypy --python-version ${{ matrix.python }} src tests
      - run: uv run --frozen pytest -q -n auto --cov --cov-report=term-missing
      - run: |
          uv export --frozen --no-emit-project --format requirements.txt -o req-audit.txt
          uvx pip-audit --strict --require-hashes --disable-pip -r req-audit.txt
```

`<sha>` is a placeholder: resolve the current `actions/checkout` release SHA when you write the
workflow; do not copy a SHA from memory.

## Container (from uv's Docker guide and `astral-sh/uv-docker-example`)

```dockerfile
FROM python:3.15-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /uvx /bin/
# Unprivileged runtime user; the app code and venv stay root-owned and read-only to it.
RUN groupadd --system --gid 999 app \
 && useradd --system --gid 999 --uid 999 --create-home app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_NO_DEV=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked
ENV PATH="/app/.venv/bin:$PATH"
USER app
CMD ["myapp"]
```

The two-step sync caches the dependency layer so a source-only change does not reinstall
dependencies. Installing runs as root (the cache mount lives under `/root`), then `USER app` drops
privileges for the running process, so a compromised process cannot rewrite the code or the venv.
The user setup follows `astral-sh/uv-docker-example` (its `Dockerfile` creates a `nonroot` system
user with `groupadd`/`useradd`, sets `PYTHONUNBUFFERED=1` and `PATH="/app/.venv/bin:$PATH"`, and
switches with `USER` before `CMD`). `CMD` runs the venv's entry point directly, so the runtime
user never needs uv or a writable uv cache.

Checked on 2026-10-29: the `python:3.15-slim` tag exists on Docker Hub (updated 2026-10-28),
`ghcr.io/astral-sh/uv:0.13.6` resolves (HTTP 200), the `UV_*` variables and `uv sync` flags appear
in uv's CLI reference or Docker guide, and the user, `PATH` and `USER` lines match
`astral-sh/uv-docker-example` (read through the GitHub API; pushed 2026-10-21). `[UNVERIFIED]`:
the image was not built. On 2026-10-29 `docker info` exited 1 (`permission denied while trying to
connect to the docker API`) and neither podman nor buildah was installed. Build it once and check
that `docker run --rm <image> id -u` prints `999` before relying on it.
