"""Real integration tests for the MCP_SERVERS pipelines (not just tool registration).

- custom-api-mcp: start_test -> poll get_status -> get_results against the
  live demo target (background pipeline thread, real skills, real HTTP).
- graphql-mcp: introspect / schema_map / run_query against the live demo.
- security-tools-mcp: run_clairvoyance against the live demo (graphql-core
  emits "Did you mean" suggestions) and the honest graphw00f degrade path.
- github-mcp: friendly-error paths with monkeypatched httpx (no network).
- postgres-mcp: run_query / list_tables / list_columns against a fake
  psycopg2 module (psycopg2 is an optional dependency and is NOT installed
  in the test environment); read-only guard + dollar-tag acceptance cases.

All network traffic is loopback-only; external services are monkeypatched.
"""
from __future__ import annotations

import sys
import time
from typing import Any, Self

import httpx
import pytest

from common.loader import load_mcp_server

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _poll_until_complete(server_module: Any, test_id: str, timeout_s: float = 10.0) -> dict:
    """Poll get_status() until the pipeline finishes; return the final status."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        status = server_module.get_status(test_id)
        if status["status"] in ("complete", "error"):
            return status
        time.sleep(0.02)
    pytest.fail(f"pipeline {test_id} did not finish within {timeout_s}s")


class _FakeResponse:
    """Minimal stand-in for httpx.Response (status_code / json() / text)."""

    def __init__(self, status_code: int, payload: Any, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self) -> Any:
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


# ---------------------------------------------------------------------------
# custom-api-mcp: full async pipeline against the live demo target
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def custom_api():
    return load_mcp_server("custom-api-mcp")


class TestCustomApiPipeline:

    def test_start_test_validates_inputs(self, custom_api):
        assert "error" in custom_api.start_test("", ["batch"])
        assert "error" in custom_api.start_test("http://127.0.0.1:1/graphql", [])
        assert "error" in custom_api.start_test("http://127.0.0.1:1/graphql", "batch")
        bad = custom_api.start_test("http://127.0.0.1:1/graphql", ["fingerprint"])
        # "fingerprint"/"introspection" are NOT selectable: they always run as
        # pipeline steps 1-2; start_test only accepts the five attack probes.
        assert "error" in bad
        assert set(bad["allowed"]) == {"bola", "alias", "batch", "complexity", "deep-nesting"}

    def test_start_test_unknown_id_status_and_results(self, custom_api):
        assert "error" in custom_api.get_status("no-such-id")
        assert "error" in custom_api.get_results("no-such-id")

    def test_full_pipeline_batch_e2e(self, custom_api, demo_url):
        """start_test -> poll get_status -> get_results, all against the demo.

        fingerprinting + introspection always run as steps 1-2; "batch" then
        produces a real finding (the demo accepts unbounded batches).
        """
        started = custom_api.start_test(demo_url, ["batch"])
        assert started["status"] == "running"
        assert started["test_types"] == ["batch"]

        final = _poll_until_complete(custom_api, started["test_id"])
        assert final["status"] == "complete", final
        assert final["finished_at"] is not None

        results = custom_api.get_results(started["test_id"])
        # Schema/recon structure is always present and non-empty.
        steps = results["meta"]["steps"]
        assert {"fingerprinting", "introspection", "batch"} <= set(steps)
        assert steps["introspection"]["introspection_enabled"] is True
        assert "user" in steps["introspection"]["roots"]["query"]
        assert steps["fingerprinting"].get("engine_candidates")
        assert results["meta"]["elapsed_ms"] > 0
        # The demo accepts a 50-operation batch with no limit -> real finding.
        assert results["findings"], "expected at least one finding from the batch step"
        finding = results["findings"][0]
        assert finding["vuln_class"] == "batch-abuse"
        assert finding["id"]

    def test_bola_step_runs_in_documented_control_mode(self, custom_api, demo_url):
        """start_test accepts only a single URL/identity -> the bola step runs
        in CONTROL mode (transport_a is transport_b) and honestly documents
        that it cannot produce a cross-identity BOLA finding."""
        started = custom_api.start_test(demo_url, ["bola"])
        final = _poll_until_complete(custom_api, started["test_id"])
        assert final["status"] == "complete", final

        results = custom_api.get_results(started["test_id"])
        assert {"fingerprinting", "introspection", "bola"} <= set(results["meta"]["steps"])
        note = results["meta"]["steps"]["bola"].get("note", "")
        assert "control" in note.lower()
        assert "identity" in note.lower()
        # Honest control run: probes executed, zero fabricated BOLA findings.
        assert results["findings"] == []

    def test_verify_finding_reexecutes_source_step(self, custom_api, demo_url):
        started = custom_api.start_test(demo_url, ["batch"])
        _poll_until_complete(custom_api, started["test_id"])
        results = custom_api.get_results(started["test_id"])
        finding = results["findings"][0]

        verdict = custom_api.verify_finding(started["test_id"], finding["id"])
        assert "error" not in verdict, verdict
        # The demo deterministically accepts unbounded batches -> re-runs true.
        assert verdict["reproduced"] is True
        assert "batch" in verdict["note"]

    def test_verify_finding_friendly_errors(self, custom_api, demo_url):
        assert "error" in custom_api.verify_finding("no-such-id", "f1")
        started = custom_api.start_test(demo_url, ["batch"])
        _poll_until_complete(custom_api, started["test_id"])
        missing = custom_api.verify_finding(started["test_id"], "does-not-exist")
        assert "error" in missing
        assert missing["known_finding_ids"]  # honest listing of what exists


# ---------------------------------------------------------------------------
# graphql-mcp: recon tools against the live demo target
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def graphql_mcp():
    return load_mcp_server("graphql-mcp")


class TestGraphqlMcp:

    def test_introspect_returns_demo_types(self, graphql_mcp, demo_url):
        result = graphql_mcp.introspect(demo_url)
        assert "error" not in result, result
        assert result["introspection_enabled"] is True
        type_names = {t["name"] for t in result["schema_map"]["types"]}
        assert {"Query", "User", "Order", "Item", "Config"} <= type_names
        assert result["roots"]["query"] == ["user", "users", "me", "config"]

    def test_schema_map_has_roots(self, graphql_mcp, demo_url):
        result = graphql_mcp.schema_map(demo_url)
        assert "error" not in result, result
        assert result["roots"]["query"]
        assert all("fields" in t for t in result["schema_map"]["types"])

    def test_run_query_roundtrip(self, graphql_mcp, demo_url):
        result = graphql_mcp.run_query(demo_url, "{ __typename }")
        assert result.get("data", {}).get("__typename") == "Query"

    def test_run_query_validates_and_survives_bad_input(self, graphql_mcp, demo_url):
        assert "error" in graphql_mcp.run_query("", "{ __typename }")
        assert "error" in graphql_mcp.run_query(demo_url, "   ")
        # A query the demo rejects must come back as GraphQL errors, not a raise.
        result = graphql_mcp.run_query(demo_url, "{ nonexistent_field_xyz }")
        assert result.get("errors")


# ---------------------------------------------------------------------------
# security-tools-mcp: real clairvoyance run + honest graphw00f degrade
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def security_mcp():
    return load_mcp_server("security-tools-mcp")


class TestSecurityTools:

    def test_run_clairvoyance_discovers_demo_fields(self, security_mcp, demo_url):
        """Small wordlist -> mutated probes -> graphql-core 'Did you mean'
        suggestions -> only real demo fields discovered, structured result."""
        result = security_mcp.run_clairvoyance(
            demo_url, wordlist=["user", "users", "config", "me"]
        )
        assert "error" not in result, result
        assert result["suggestions_enabled"] is True
        discovered = {entry["field"] for entry in result["discovered"]}
        # Suggestions only ever name REAL fields of the demo Query type.
        assert discovered <= {"user", "users", "config", "me"}
        assert "user" in discovered or "users" in discovered
        assert result["meta"]["probes_used"] >= 1
        assert result["meta"]["root_type"] == "Query"

    def test_run_clairvoyance_empty_url(self, security_mcp):
        assert "error" in security_mcp.run_clairvoyance("")

    def test_run_graphw00f_degrades_honestly_when_missing(
        self, security_mcp, demo_url, monkeypatch
    ):
        """graphw00f is not installed here: force the not-found lookup via
        GRAPHW00F_BIN and assert the honest no-fabrication degrade dict."""
        monkeypatch.setenv("GRAPHW00F_BIN", "definitely-not-graphw00f-xyz")
        result = security_mcp.run_graphw00f(demo_url)
        assert result["installed"] is False
        assert "not found" in result["error"]
        assert "hint" in result
        # The availability listing agrees with the runtime check.
        listed = security_mcp.list_tools()
        graphw00f = next(t for t in listed["tools"] if t["name"] == "graphw00f")
        assert graphw00f["installed"] is False
        assert graphw00f["invocation"] == "definitely-not-graphw00f-xyz"


# ---------------------------------------------------------------------------
# github-mcp: friendly-error paths, monkeypatched httpx (no network)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def github_mcp():
    return load_mcp_server("github-mcp")


class TestGithubMcp:

    def test_headers_use_gh_token_env_only(self, github_mcp, monkeypatch):
        monkeypatch.delenv("GH_TOKEN", raising=False)
        assert "Authorization" not in github_mcp._headers()
        monkeypatch.setenv("GH_TOKEN", "fake-token-for-tests")
        headers = github_mcp._headers()
        assert headers["Authorization"] == "Bearer fake-token-for-tests"

    def test_get_repo_validates_arguments(self, github_mcp):
        assert "error" in github_mcp.get_repo("", "repo")
        assert "error" in github_mcp.get_repo("owner", "")

    def test_get_repo_invalid_token_friendly_error(
        self, github_mcp, monkeypatch
    ):
        """GH_TOKEN set but rejected -> 401 mapped to a friendly dict, no raise."""
        monkeypatch.setenv("GH_TOKEN", "invalid-token-value")
        calls: list[str] = []

        def fake_get(url: str, **_kwargs: Any) -> _FakeResponse:
            calls.append(url)
            return _FakeResponse(
                401, {"message": "Bad credentials"}, text="Bad credentials"
            )

        monkeypatch.setattr(httpx, "get", fake_get)
        result = github_mcp.get_repo("some-owner", "some-repo")
        assert calls == ["https://api.github.com/repos/some-owner/some-repo"]
        assert result["status"] == 401
        assert "GH_TOKEN" in result["hint"]
        assert "error" in result

    def test_get_repo_network_error_friendly(self, github_mcp, monkeypatch):
        def failing_get(_url: str, **_kwargs: Any) -> Any:
            raise httpx.ConnectError("connection refused")

        monkeypatch.setattr(httpx, "get", failing_get)
        result = github_mcp.get_repo("owner", "repo")
        assert "Network error" in result["error"]
        assert "owner/repo" in result["error"]

    def test_search_repositories_maps_fields(self, github_mcp, monkeypatch):
        payload = {
            "total_count": 2,
            "items": [
                {
                    "name": "demo",
                    "full_name": "owner/demo",
                    "html_url": "https://github.com/owner/demo",
                    "description": "d",
                    "stargazers_count": 5,
                    "pushed_at": "2026-01-01T00:00:00Z",
                    "private_field_that_must_not_leak": "x",
                },
                {"name": "other"},
            ],
        }
        seen: dict[str, Any] = {}

        def fake_get(url: str, **kwargs: Any) -> _FakeResponse:
            seen["url"] = url
            seen["params"] = kwargs.get("params")
            return _FakeResponse(200, payload)

        monkeypatch.setattr(httpx, "get", fake_get)
        result = github_mcp.search_repositories("graphql language:python", per_page=7)
        assert seen["url"] == "https://api.github.com/search/repositories"
        assert seen["params"] == {"q": "graphql language:python", "per_page": 7}
        assert result["total_count"] == 2
        assert len(result["items"]) == 2
        assert set(result["items"][0]) == {
            "name",
            "full_name",
            "html_url",
            "description",
            "stargazers_count",
            "pushed_at",
        }

    def test_search_repositories_validation_and_http_error(self, github_mcp, monkeypatch):
        assert "error" in github_mcp.search_repositories("   ")

        def forbidden(_url: str, **_kwargs: Any) -> _FakeResponse:
            return _FakeResponse(403, {"message": "API rate limit exceeded"})

        monkeypatch.setattr(httpx, "get", forbidden)
        result = github_mcp.search_repositories("q")
        assert result["status"] == 403
        assert "rate limit" in result["hint"].lower()

    def test_get_file_contents_decodes_base64_text(self, github_mcp, monkeypatch):
        import base64

        encoded = base64.b64encode(b"hello = world\n").decode()
        payload = {
            "path": "README.md",
            "name": "README.md",
            "sha": "abc123",
            "size": 14,
            "html_url": "https://github.com/owner/repo/blob/main/README.md",
            "content": encoded,
            "encoding": "base64",
        }
        seen: list[str] = []

        def fake_get(url: str, **_kwargs: Any) -> _FakeResponse:
            seen.append(url)
            return _FakeResponse(200, payload)

        monkeypatch.setattr(httpx, "get", fake_get)
        result = github_mcp.get_file_contents("owner", "repo", "README.md")
        assert seen == ["https://api.github.com/repos/owner/repo/contents/README.md"]
        assert result["content"] == "hello = world\n"
        assert result["encoding"] == "utf-8"
        assert result["sha"] == "abc123"

    def test_get_file_contents_directory_listing(self, github_mcp, monkeypatch):
        payload = [
            {"name": "server.py", "type": "file", "path": "src/server.py", "size": 100},
            {"name": "extra.txt", "type": "file", "path": "src/extra.txt", "size": 1},
        ]

        monkeypatch.setattr(httpx, "get", lambda _u, **_k: _FakeResponse(200, payload))
        result = github_mcp.get_file_contents("owner", "repo", "/src/")
        assert result["type"] == "dir"
        assert result["path"] == "src/"
        assert [i["name"] for i in result["items"]] == ["server.py", "extra.txt"]

    def test_get_file_contents_binary_and_404(self, github_mcp, monkeypatch):
        import base64

        binary = base64.b64encode(bytes([0xFF, 0xFE, 0x00, 0x01])).decode()

        responses = {
            "https://api.github.com/repos/o/r/contents/logo.png": _FakeResponse(
                200,
                {
                    "path": "logo.png",
                    "name": "logo.png",
                    "sha": "s",
                    "size": 4,
                    "content": binary,
                    "encoding": "base64",
                },
            ),
            "https://api.github.com/repos/o/r/contents/nope.md": _FakeResponse(
                404, {"message": "Not Found"}
            ),
        }

        monkeypatch.setattr(
            httpx, "get", lambda url, **_k: responses[url]
        )
        binary_result = github_mcp.get_file_contents("o", "r", "logo.png")
        # Undecodable bytes: honest base64 passthrough, never a decode crash.
        assert binary_result["encoding"] == "base64"
        assert "content" in binary_result
        missing = github_mcp.get_file_contents("o", "r", "nope.md")
        assert missing["status"] == 404
        assert "owner/repo/path" in missing["hint"]


# ---------------------------------------------------------------------------
# postgres-mcp: fake psycopg2 module, SQL pass-through + read-only guard
# ---------------------------------------------------------------------------


class _FakeCursor:
    """Records execute() calls; returns canned rows via the RealDictCursor shape."""

    def __init__(self, rows: list[dict], description: list[tuple] | None) -> None:
        self._rows = rows
        self.description = description
        self.rowcount = len(rows)
        self.executed: list[tuple[str, tuple | None]] = []

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def execute(self, sql: str, params: tuple | None = None) -> None:
        self.executed.append((sql, params))

    def fetchmany(self, size: int) -> list[dict]:
        return self._rows[:size]

    def fetchall(self) -> list[dict]:
        return list(self._rows)


class _FakeConnection:
    def __init__(self, cursor: _FakeCursor) -> None:
        self._cursor = cursor

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def cursor(self, cursor_factory: Any = None) -> _FakeCursor:
        return self._cursor


def _install_fake_psycopg2(monkeypatch: pytest.MonkeyPatch, cursor: _FakeCursor) -> None:
    """Inject a fake ``psycopg2`` (+ ``psycopg2.extras``) into sys.modules so
    the server's lazy imports resolve without the real dependency."""
    import types

    fake_extras = types.ModuleType("psycopg2.extras")
    fake_extras.RealDictCursor = object()  # sentinel, only passed through
    fake_psycopg2 = types.ModuleType("psycopg2")
    fake_psycopg2.connect = lambda dsn: _FakeConnection(cursor)
    fake_psycopg2.extras = fake_extras
    monkeypatch.setitem(sys.modules, "psycopg2", fake_psycopg2)
    monkeypatch.setitem(sys.modules, "psycopg2.extras", fake_extras)


@pytest.fixture(scope="module")
def postgres_mcp():
    return load_mcp_server("postgres-mcp")


class TestPostgresMcp:

    def test_run_query_passes_sql_through(self, postgres_mcp, monkeypatch):
        cursor = _FakeCursor(
            rows=[{"id": 1, "name": "u1"}],
            description=[("id",), ("name",)],
        )
        _install_fake_psycopg2(monkeypatch, cursor)
        monkeypatch.setenv("POSTGRES_URL", "postgresql://fake:fake@127.0.0.1/fake")

        result = postgres_mcp.run_query("SELECT id, name FROM users WHERE id = 1")
        assert "error" not in result, result
        assert cursor.executed[0][0] == "SELECT id, name FROM users WHERE id = 1"
        assert result["columns"] == ["id", "name"]
        assert result["rows"] == [{"id": 1, "name": "u1"}]
        assert result["truncated"] is False
        assert result["rowcount"] == 1

    def test_run_query_dollar_tag_accepted(self, postgres_mcp, monkeypatch):
        """$t1$ dollar-quoted content must not fool OR block the guard."""
        cursor = _FakeCursor(rows=[{"note": "drop table users"}], description=[("note",)])
        _install_fake_psycopg2(monkeypatch, cursor)
        monkeypatch.setenv("POSTGRES_URL", "postgresql://fake/fake")

        sql = "SELECT $t1$drop table users$t1$ AS note"
        assert postgres_mcp.assert_read_only(sql) is None
        assert postgres_mcp.assert_read_only("SELECT $$anonymous$$") is None
        result = postgres_mcp.run_query(sql)
        assert "error" not in result, result
        assert cursor.executed[0][0] == sql
        assert result["rows"] == [{"note": "drop table users"}]

    def test_run_query_read_only_guard_blocks_before_connect(
        self, postgres_mcp, monkeypatch
    ):
        cursor = _FakeCursor(rows=[], description=None)
        _install_fake_psycopg2(monkeypatch, cursor)
        monkeypatch.setenv("POSTGRES_URL", "postgresql://fake/fake")

        result = postgres_mcp.run_query("DROP TABLE users")
        assert result["stage"] == "read-only check"
        assert "DROP" in result["error"]
        assert cursor.executed == [], "guard must reject before any connection/execute"

    def test_run_query_missing_config(self, postgres_mcp, monkeypatch):
        monkeypatch.delenv("POSTGRES_URL", raising=False)
        result = postgres_mcp.run_query("SELECT 1")
        assert result["stage"] == "config"
        assert "POSTGRES_URL" in result["error"]

    def test_run_query_no_result_statement_rowcount(self, postgres_mcp, monkeypatch):
        cursor = _FakeCursor(rows=[], description=None)
        _install_fake_psycopg2(monkeypatch, cursor)
        monkeypatch.setenv("POSTGRES_URL", "postgresql://fake/fake")

        result = postgres_mcp.run_query("EXPLAIN SELECT 1")
        assert "error" not in result, result
        assert result == {"rowcount": 0, "rows": [], "columns": []}

    def test_list_tables_information_schema_sql(self, postgres_mcp, monkeypatch):
        cursor = _FakeCursor(
            rows=[{"table_name": "users"}, {"table_name": "orders"}],
            description=[("table_name",)],
        )
        _install_fake_psycopg2(monkeypatch, cursor)
        monkeypatch.setenv("POSTGRES_URL", "postgresql://fake/fake")

        result = postgres_mcp.list_tables()
        assert "error" not in result, result
        sql = cursor.executed[0][0]
        assert "information_schema.tables" in sql
        assert "table_schema = 'public'" in sql
        assert result["rows"] == [{"table_name": "users"}, {"table_name": "orders"}]

    def test_list_columns_parameterized_table_name(self, postgres_mcp, monkeypatch):
        cursor = _FakeCursor(
            rows=[
                {
                    "column_name": "id",
                    "data_type": "integer",
                    "is_nullable": "NO",
                    "column_default": None,
                }
            ],
            description=[
                ("column_name",),
                ("data_type",),
                ("is_nullable",),
                ("column_default",),
            ],
        )
        _install_fake_psycopg2(monkeypatch, cursor)
        monkeypatch.setenv("POSTGRES_URL", "postgresql://fake/fake")

        result = postgres_mcp.list_columns("users")
        assert "error" not in result, result
        sql, params = cursor.executed[0]
        assert "information_schema.columns" in sql
        # The table name travels as a bound parameter, never concatenated.
        assert params == ("users",)
        assert "%s" in sql
        assert result["table"] == "users"
        assert result["columns"][0]["column_name"] == "id"

    def test_list_columns_validates_and_needs_config(self, postgres_mcp, monkeypatch):
        assert "error" in postgres_mcp.list_columns("")

        monkeypatch.delenv("POSTGRES_URL", raising=False)
        assert postgres_mcp.list_columns("users")["stage"] == "config"

    def test_optional_dependency_degrades_honestly(self, postgres_mcp, monkeypatch):
        """Without psycopg2 installed, tools return a friendly dependency
        error with install guidance instead of raising."""
        monkeypatch.setenv("POSTGRES_URL", "postgresql://fake/fake")
        monkeypatch.setitem(sys.modules, "psycopg2", None)  # None -> ImportError
        result = postgres_mcp.run_query("SELECT 1")
        assert result["stage"] == "dependency"
        assert "psycopg2" in result["error"]
        assert postgres_mcp.list_columns("users")["stage"] == "dependency"
