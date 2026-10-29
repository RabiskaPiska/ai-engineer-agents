# Service patterns: FastAPI + async SQLAlchemy + httpx (tested 2026-10-29)

Every file in this reference was run on 2026-10-29 on CPython 3.15.0 with FastAPI 0.159.1,
SQLAlchemy 2.1.6 (with greenlet 3.5.6 from the `asyncio` extra), pydantic-settings 2.16.1,
httpx 0.28.1, aiosqlite 0.22.1, pytest-asyncio 1.4.0 and asgi-lifespan 2.1.0 (the versions the
7-day cooldown resolved), on top of the project that `pyproject-baseline.md` bootstraps. Results:
`ruff format --check` 0, `ruff check` 0, `ty check` 0, `mypy src tests` 0,
`pytest -n auto --cov` 8 passed at 99.03% branch coverage, and the repeat gate
(`python -X dev -m pytest -p no:xdist --no-cov --count=20`, 160 runs per invocation) failed 0 of 5
invocations. The import blocks are exactly what `ruff check --fix --unsafe-fixes` produced for a
3.15 target, including `lazy from` imports and `TYPE_CHECKING` blocks.

Add the packages with uv on top of the baseline. The `asyncio` extra matters: SQLAlchemy's asyncio
module needs `greenlet`, and without the extra, test collection fails with an ImportError that
names greenlet.

```bash
uv add fastapi "sqlalchemy[asyncio]" httpx aiosqlite pydantic-settings
uv add --group test pytest-asyncio asgi-lifespan
```

Then add `asyncio_default_fixture_loop_scope = "function"` to `[tool.pytest]`, which keeps
pytest-asyncio's future-default warning from failing the suite under `filterwarnings = ["error"]`.

What the code demonstrates, and why:
- **Lifespan-owned resources.** The DB engine and the HTTP client are created once per process in the
  FastAPI lifespan and closed on shutdown. Per-request clients leak connections and add a TLS
  handshake to every call.
- **Dependency injection through `Annotated[..., Depends(...)]`.** Handlers receive a session and a
  client instead of importing globals, so tests can swap them.
- **One unit of work per request.** `session_scope` is an `@asynccontextmanager`: it commits on
  success, rolls back on any error including cancellation (`BaseException`), re-raises, and closes
  the session. `get_session` enters it with `async with`, so an exception that FastAPI throws into
  the dependency (the 409 path) reaches the rollback before the response is sent.
- **Boundary validation only.** `ItemIn` forbids unknown fields (`extra="forbid"`), so a client
  cannot smuggle `admin: true` through. Internal code trusts the validated model.
- **Separate API and storage models.** `ItemOut` is built from the ORM row; the ORM class is never
  returned directly.
- **Domain errors mapped at the edge.** `IntegrityError` becomes HTTP 409 with `raise ... from exc`.
  Upstream failures become 504 (overall deadline or httpx timeout) or 502 (any other
  `httpx.TransportError`) through one `except*` clause chained with `from eg`; anything else stays
  a 500 so real bugs are not disguised as upstream trouble.
- **Structured concurrency with a deadline.** `asyncio.timeout()` wraps an `asyncio.TaskGroup`; if
  either upstream call fails, the other is cancelled and the errors surface as an `ExceptionGroup`.
  Use one `except*` clause that raises once: a single exception raised from an `except*` clause
  propagates unwrapped, but two clauses that both raise produce an `ExceptionGroup` of
  `HTTPException`s, which FastAPI turns into a 500 (checked on 3.15.0).
- **Secrets as `SecretStr`.** The token never appears in `repr()` or logs.
- **Tests at the process boundary.** The upstream service is replaced with `httpx.MockTransport`,
  the app is driven in-process through `httpx.ASGITransport`, and each test gets its own SQLite file
  through `tmp_path`. No network, no shared state, so `pytest -n auto` is safe. The failure
  mapping is tested by raising `httpx.ConnectError` and `httpx.ReadTimeout` from the fake
  transport and by a handler that outlives the deadline.

Four lessons from running it:
- The first version wrapped the context-manager-shaped generator as
  `async for session in session_scope(...): yield session`. FastAPI throws the handler's exception
  into `get_session`, but an `async for` loop does not forward it into the inner generator, so on
  the 409 path the rollback and close ran only when the generator was garbage-collected or the
  lifespan exited. A probe that logged `AsyncSession.rollback` showed it after the response, and
  the leaked aiosqlite connection made a plain `pytest -q -p no:randomly --no-cov` fail 7 of 15
  runs with `PytestUnraisableExceptionWarning` ("Connection ... was deleted before being closed").
  The `-n auto --cov` gate failed 0 of 10 runs and hid it. With `async with`, the probe logs the
  rollback before the response, and the plain loop failed 0 of 15.
- ty flagged `@asynccontextmanager` on a function annotated `-> AsyncIterator[...]` as deprecated
  (typeshed now wants `-> AsyncGenerator[...]`). mypy 2.4.1 did not flag it.
- In pytest-asyncio strict mode (the default), an async fixture needs `@pytest_asyncio.fixture`;
  a plain `@pytest.fixture` on an `async def` errors with "requested an async fixture ... with no
  plugin or hook that handled it".
- After applying Ruff's `TC` fixes, run the tests: FastAPI, Pydantic, SQLAlchemy `Mapped[...]` and
  Typer read some annotations at runtime. Here Ruff kept every runtime-needed import eager and the
  suite stayed green, but that is a property of this code, not a guarantee.

## `src/myapp/settings.py`

```python
from functools import cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process configuration, read once from the environment (prefix MYAPP_)."""

    model_config = SettingsConfigDict(env_prefix="MYAPP_", frozen=True)

    database_url: str = "sqlite+aiosqlite:///./app.db"
    upstream_url: str = "https://example.invalid"
    upstream_timeout_s: float = 5.0
    api_token: SecretStr = SecretStr("")


@cache
def get_settings() -> Settings:
    return Settings()
```

## `src/myapp/db.py`

```python
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING
lazy from collections.abc import AsyncGenerator

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


class Base(DeclarativeBase):
    pass


class Item(Base):
    __tablename__ = "item"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)


@asynccontextmanager
async def session_scope(factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession]:
    """One session per unit of work; commit on success, roll back on any error, always close."""
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except BaseException:
            await session.rollback()
            raise


async def create_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

## `src/myapp/api.py`

```python
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from myapp.db import Item, create_schema, session_scope
from myapp.settings import Settings, get_settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)


class ItemIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


def create_app(settings: Settings | None = None) -> FastAPI:
    cfg = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        # Process-lifetime resources: created once, closed on shutdown.
        engine = create_async_engine(cfg.database_url)
        await create_schema(engine)
        app.state.sessions = async_sessionmaker(engine, expire_on_commit=False)
        async with httpx.AsyncClient(
            base_url=cfg.upstream_url, timeout=cfg.upstream_timeout_s
        ) as client:
            app.state.http = client
            yield
        await engine.dispose()

    app = FastAPI(lifespan=lifespan)

    async def get_session(request: Request) -> AsyncGenerator[AsyncSession]:
        # `async with`, not `async for`: FastAPI throws the handler's exception in at `yield`,
        # and only a context manager forwards it to session_scope, which rolls back and closes
        # the session before the response is sent.
        async with session_scope(request.app.state.sessions) as session:
            yield session

    def get_http(request: Request) -> httpx.AsyncClient:
        client: httpx.AsyncClient = request.app.state.http
        return client

    session_dep = Annotated[AsyncSession, Depends(get_session)]
    http_dep = Annotated[httpx.AsyncClient, Depends(get_http)]

    @app.post("/items", status_code=status.HTTP_201_CREATED)
    async def create_item(body: ItemIn, session: session_dep) -> ItemOut:
        item = Item(name=body.name)
        session.add(item)
        try:
            await session.flush()
        except IntegrityError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, "item exists") from exc
        return ItemOut.model_validate(item)

    @app.get("/items")
    async def list_items(session: session_dep) -> list[ItemOut]:
        rows = await session.scalars(select(Item).order_by(Item.id))
        return [ItemOut.model_validate(r) for r in rows]

    @app.get("/status")
    async def upstream_status(http: http_dep) -> dict[str, int]:
        # Fan out with structured concurrency and one overall deadline.
        try:
            async with asyncio.timeout(cfg.upstream_timeout_s), asyncio.TaskGroup() as tg:
                a = tg.create_task(http.get("/a"))
                b = tg.create_task(http.get("/b"))
        except* (TimeoutError, httpx.TransportError) as eg:
            # One clause, one raise: a single exception raised from except* propagates
            # unwrapped, so FastAPI sees the HTTPException. Other errors stay a 500.
            timed_out = eg.subgroup((TimeoutError, httpx.TimeoutException)) is not None
            code = status.HTTP_504_GATEWAY_TIMEOUT if timed_out else status.HTTP_502_BAD_GATEWAY
            raise HTTPException(code, "upstream unavailable") from eg
        return {"a": a.result().status_code, "b": b.result().status_code}

    return app
```

## `tests/test_api.py`

```python
import asyncio
from collections.abc import AsyncIterator, Callable, Coroutine
lazy from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager

from myapp.api import create_app
from myapp.settings import Settings

type Handler = (
    Callable[[httpx.Request], httpx.Response]
    | Callable[[httpx.Request], Coroutine[None, None, httpx.Response]]
)


def upstream(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200 if request.url.path == "/a" else 503)


def refuse(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("connection refused", request=request)


def read_timeout(request: httpx.Request) -> httpx.Response:
    raise httpx.ReadTimeout("read timed out", request=request)


async def hang(request: httpx.Request) -> httpx.Response:
    await asyncio.sleep(10)  # longer than the 0.2 s deadline below
    return httpx.Response(200)


@pytest.fixture
def upstream_handler() -> Handler:
    return upstream


@pytest_asyncio.fixture
async def client(tmp_path: Path, upstream_handler: Handler) -> AsyncIterator[httpx.AsyncClient]:
    settings = Settings(database_url=f"sqlite+aiosqlite:///{tmp_path}/t.db", upstream_timeout_s=0.2)
    app = create_app(settings)
    async with LifespanManager(app):
        # Swap the real upstream client for an in-process fake transport.
        app.state.http = httpx.AsyncClient(
            transport=httpx.MockTransport(upstream_handler), base_url="http://up"
        )
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
        await app.state.http.aclose()


@pytest.mark.asyncio
async def test_create_then_list(client: httpx.AsyncClient) -> None:
    r = await client.post("/items", json={"name": "a"})
    assert r.status_code == 201
    assert (await client.get("/items")).json() == [{"id": 1, "name": "a"}]


@pytest.mark.asyncio
async def test_duplicate_is_409_and_rolled_back(client: httpx.AsyncClient) -> None:
    await client.post("/items", json={"name": "a"})
    r = await client.post("/items", json={"name": "a"})
    assert r.status_code == 409
    assert (await client.get("/items")).json() == [{"id": 1, "name": "a"}]


@pytest.mark.asyncio
async def test_rejects_unknown_fields(client: httpx.AsyncClient) -> None:
    r = await client.post("/items", json={"name": "a", "admin": True})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_status_fans_out(client: httpx.AsyncClient) -> None:
    assert (await client.get("/status")).json() == {"a": 200, "b": 503}


@pytest.mark.parametrize(
    ("upstream_handler", "expected"),
    [(refuse, 502), (read_timeout, 504), (hang, 504)],
    ids=["connect-error", "read-timeout", "deadline"],
)
@pytest.mark.asyncio
async def test_status_maps_upstream_failures(client: httpx.AsyncClient, expected: int) -> None:
    assert (await client.get("/status")).status_code == expected
```

## Production notes not covered by the test

- Swap `aiosqlite` for `psycopg` (3.3.x, async) or `asyncpg` on PostgreSQL, and manage schema with
  Alembic migrations instead of `create_all`. Keep migrations reversible and named by date and slug.
- Run under `uvicorn` or `granian` with one worker process per core behind a load balancer; do not
  use FastAPI `BackgroundTasks` for work you would page someone about losing. Use a real queue
  (Celery, taskiq, arq) with retries.
- Sync-only SDKs inside async handlers go through `await asyncio.to_thread(fn, ...)` (or
  `fastapi.concurrency.run_in_threadpool`), never a direct call.
- Add request IDs, structured logs and OpenTelemetry spans at the edge; keep `logger.exception`
  at the boundary handler, not in every layer.
