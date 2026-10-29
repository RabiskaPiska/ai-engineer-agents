"""MCP servers: tool registration + postgres read-only guard (pure fn)."""
from __future__ import annotations

import asyncio
import inspect

import pytest

from common.loader import load_mcp_server

EXPECTED_TOOLS = {
    "github-mcp": {"get_repo", "get_file_contents", "search_repositories"},
    "graphql-mcp": {"introspect", "run_query", "schema_map"},
    "custom-api-mcp": {"start_test", "get_status", "get_results", "verify_finding"},
    "security-tools-mcp": {"list_tools", "run_graphw00f", "run_clairvoyance"},
    "postgres-mcp": {"run_query", "list_tables", "list_columns"},
}


def _tool_names(module) -> list[str]:
    """list_tools() on the module's ``mcp`` object (async in mcp 1.x and 2.x)."""
    server = module.mcp
    listed = server.list_tools()
    if inspect.iscoroutine(listed) or inspect.isawaitable(listed):
        listed = asyncio.run(listed)
    return sorted(tool.name for tool in listed)


@pytest.mark.parametrize("name", sorted(EXPECTED_TOOLS))
def test_server_imports_and_lists_tools(name):
    module = load_mcp_server(name)
    names = _tool_names(module)
    assert len(names) >= 2
    assert set(names) == EXPECTED_TOOLS[name], (
        f"{name}: tool set drifted from SPEC -- got {names}"
    )


def test_loader_covers_every_mcp_server_folder():
    """Cross-check against the real MCP_SERVERS/ layout, not a constant."""
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[1]
    folders = sorted(
        p.name for p in (root / "MCP_SERVERS").iterdir() if p.is_dir()
    )
    assert folders == sorted(EXPECTED_TOOLS)


# --- postgres assert_read_only (pure function) -------------------------------

ALLOWED_SQL = [
    "SELECT 1",
    "SELECT * FROM users WHERE id = 1",
    "WITH t AS (SELECT 1) SELECT * FROM t",
    "EXPLAIN SELECT * FROM users",
    "EXPLAIN ANALYZE SELECT * FROM users",
    "SELECT 'drop table users' AS harmless",  # literal content must not fool it
    "SELECT 1;",  # trailing semicolon is fine
    "/* comment */ SELECT 1",
]

REJECTED_SQL = [
    "DROP TABLE users",
    "INSERT INTO users VALUES (1)",
    "UPDATE users SET name = 'x'",
    "DELETE FROM users",
    "TRUNCATE users",
    "ALTER TABLE users ADD COLUMN c INT",
    "SELECT 1; DROP TABLE users",  # multi-statement
    "SELECT * FROM users; SELECT 2",  # multi-statement
    "CREATE TABLE t (id INT)",
    "GRANT ALL ON users TO public",
    "SELECT * INTO copy_users FROM users",  # SELECT ... INTO writes
    "VACUUM",
    "",
    "   ",
]


@pytest.mark.parametrize("sql", ALLOWED_SQL)
def test_postgres_read_only_allows(sql):
    module = load_mcp_server("postgres-mcp")
    assert module.assert_read_only(sql) is None


@pytest.mark.parametrize("sql", REJECTED_SQL)
def test_postgres_read_only_rejects(sql):
    module = load_mcp_server("postgres-mcp")
    with pytest.raises(ValueError):
        module.assert_read_only(sql)
