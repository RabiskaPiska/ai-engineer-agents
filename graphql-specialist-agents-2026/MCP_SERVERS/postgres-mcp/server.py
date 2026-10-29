"""postgres-mcp — reference MCP server exposing read-only PostgreSQL queries.

Tools:
    run_query(sql)          -> run a single read-only statement
    list_tables()           -> tables in the 'public' schema
    list_columns(table)     -> columns of one table

Connection settings come ONLY from the ``POSTGRES_URL`` environment variable
(never a literal). ``psycopg2`` is imported lazily — it is an optional
dependency, and the server imports (and lists its tools) without it.

``assert_read_only(sql)`` is a pure function: it allows a single SELECT /
WITH / EXPLAIN statement and rejects everything else (INSERT, UPDATE, DELETE,
DROP, ALTER, TRUNCATE, GRANT, COPY, ... and any multi-statement input).
"""

import os
import pathlib
import re
import sys
from typing import Any

try:  # mcp 1.x (SPEC baseline)
    from mcp.server.fastmcp import FastMCP
except ImportError:  # mcp 2.x renamed FastMCP -> MCPServer
    from mcp.server.mcpserver import MCPServer as FastMCP

_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

mcp = FastMCP("postgres-mcp")

_MAX_ROWS = 500

# Keywords that always mean "this statement writes or changes server state".
# 'into' is included to catch SELECT ... INTO (it creates a table).
_FORBIDDEN_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "grant",
    "copy",
    "into",  # the eight required by SPEC, plus SELECT...INTO guard
    "create",
    "revoke",
    "vacuum",
    "call",
    "do",
    "merge",
    "comment",
    "listen",
    "notify",
    "set",
    "reset",
    "prepare",
    "execute",
    "declare",
    "fetch",
    "move",
    "checkpoint",
    "discard",
    "refresh",
    "import",
    "reindex",
    "cluster",
    "lock",
    # NOTE: 'analyze' is deliberately NOT forbidden — "EXPLAIN ANALYZE
    # SELECT ..." is allowed, while "EXPLAIN ANALYZE DROP/INSERT/..." is
    # still caught by the keyword scan above. A bare "ANALYZE" statement is
    # rejected by the first-keyword check.
}
_ALLOWED_FIRST_KEYWORDS = {"select", "with", "explain"}


def _strip_literals_and_comments(sql: str) -> str:
    """Blank out string literals, quoted identifiers, dollar-quoted strings
    and comments so keyword analysis cannot be fooled by their contents.
    Pure function: returns a new string."""
    out: list[str] = []
    i, n = 0, len(sql)
    while i < n:
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < n else ""
        if ch == "-" and nxt == "-":  # line comment
            j = sql.find("\n", i)
            i = n if j == -1 else j
            out.append(" ")
        elif ch == "/" and nxt == "*":  # block comment
            j = sql.find("*/", i + 2)
            i = n if j == -1 else j + 2
            out.append(" ")
        elif ch == "'":  # single-quoted string ('' escapes a quote)
            i += 1
            while i < n:
                if sql[i] == "'":
                    if i + 1 < n and sql[i + 1] == "'":
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            out.append("' '")
        elif ch in {'"', "`"}:  # quoted identifier
            j = sql.find(ch, i + 1)
            i = n if j == -1 else j + 1
            out.append(f"{ch} {ch}")
        elif ch == "$":  # dollar-quoted string ($tag$ ... $tag$)
            # Tag is optional ($$) or an identifier: letter/underscore first,
            # then letters/digits/underscores ($t1$, $_x$, $$ all valid).
            m = re.match(r"\$[A-Za-z_][A-Za-z0-9_]*\$|\$\$", sql[i:])
            if m:
                tag = m.group(0)
                j = sql.find(tag, i + len(tag))
                i = n if j == -1 else j + len(tag)
                out.append(f"{tag} {tag}")
            else:
                out.append(ch)
                i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def assert_read_only(sql: str) -> None:
    """Pure function: validate that `sql` is a single read-only statement.

    Returns None when the statement is allowed; raises ValueError when it is
    not (empty input, non-SELECT/WITH/EXPLAIN, mutating keywords, SELECT ...
    INTO, or more than one statement).

    Analysis is done on a copy with string literals, quoted identifiers,
    dollar-quoted strings and comments stripped, so payloads such as
    ``SELECT 'drop table users'`` or ``/*;*/ SELECT 1`` cannot bypass it.
    """
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("SQL must be a non-empty string.")
    stripped = _strip_literals_and_comments(sql).strip()
    if not stripped:
        raise ValueError("Statement contains nothing outside comments/literals.")
    while stripped.endswith(";"):
        stripped = stripped[:-1].rstrip()
    if not stripped:
        raise ValueError("Statement is empty.")
    if ";" in stripped:
        raise ValueError(
            "Multi-statement SQL is not allowed (a ';' separator was found)."
        )
    words = re.findall(r"[A-Za-z_]+", stripped)
    if not words:
        raise ValueError("Statement contains no SQL keywords.")
    first = words[0].lower()
    if first not in _ALLOWED_FIRST_KEYWORDS:
        raise ValueError(
            f"Only SELECT / WITH / EXPLAIN statements are allowed "
            f"(statement starts with {first.upper()!r})."
        )
    lowered = [w.lower() for w in words]
    for word in lowered:
        if word in _FORBIDDEN_KEYWORDS:
            raise ValueError(
                f"Read-only check: keyword {word.upper()!r} is not allowed "
                "in this context."
            )


def _postgres_url() -> str:
    return os.environ.get("POSTGRES_URL", "").strip()


def _jsonify(value: Any) -> Any:
    """Make DB values JSON-safe (datetimes, decimals, UUIDs, bytes, ...)."""
    if isinstance(value, (dict, list, tuple)):
        return (
            [_jsonify(v) for v in value]
            if isinstance(value, (list, tuple))
            else {k: _jsonify(v) for k, v in value.items()}
        )
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


@mcp.tool()
def run_query(sql: str) -> dict[str, Any]:
    """Execute a single read-only SQL statement against POSTGRES_URL.

    The statement must pass assert_read_only(): one SELECT / WITH / EXPLAIN,
    no mutating keywords, no multi-statement input. SELECT results are
    returned as {"columns", "rows"} (capped at 500 rows, 'truncated' flag set
    honestly); non-result statements return {"rowcount"}. Friendly error dict
    on any failure.
    """
    try:
        assert_read_only(sql)
    except ValueError as exc:
        return {"error": str(exc), "stage": "read-only check"}
    dsn = _postgres_url()
    if not dsn:
        return {
            "error": "POSTGRES_URL environment variable is not set — cannot connect.",
            "stage": "config",
        }
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        return {
            "error": "psycopg2 is not installed. Install it with: "
            "pip install psycopg2-binary",
            "stage": "dependency",
        }
    try:
        with (
            psycopg2.connect(dsn) as conn,
            conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur,
        ):
            cur.execute(sql)
            if cur.description is None:
                return {"rowcount": cur.rowcount, "rows": [], "columns": []}
            columns = [d[0] for d in cur.description]
            rows = cur.fetchmany(_MAX_ROWS + 1)
            truncated = len(rows) > _MAX_ROWS
            rows = [_jsonify(dict(r)) for r in rows[:_MAX_ROWS]]
            return {
                "columns": columns,
                "rows": rows,
                "truncated": truncated,
                "rowcount": len(rows),
            }
    except Exception as exc:  # noqa: BLE001 — MCP tool boundary must not raise
        msg = str(getattr(exc, "diag", None) and exc.diag.message_primary or str(exc))
        return {"error": f"PostgreSQL error: {msg}", "stage": "execution"}


@mcp.tool()
def list_tables() -> dict[str, Any]:
    """List tables in the 'public' schema (read-only information_schema query)."""
    return run_query(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' ORDER BY table_name"
    )


@mcp.tool()
def list_columns(table: str) -> dict[str, Any]:
    """List the columns of one table in the 'public' schema.

    Returns {"columns": [{name, type, nullable, default}]} via a
    parameterized information_schema query (the table name is a bound
    parameter, never string-concatenated).
    """
    if not table or not str(table).strip():
        return {"error": "'table' is required."}
    dsn = _postgres_url()
    if not dsn:
        return {
            "error": "POSTGRES_URL environment variable is not set — cannot connect.",
            "stage": "config",
        }
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        return {
            "error": "psycopg2 is not installed. Install it with: "
            "pip install psycopg2-binary",
            "stage": "dependency",
        }
    try:
        with (
            psycopg2.connect(dsn) as conn,
            conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur,
        ):
            cur.execute(
                "SELECT column_name, data_type, is_nullable, column_default "
                "FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = %s "
                "ORDER BY ordinal_position",
                (str(table),),
            )
            rows = [_jsonify(dict(r)) for r in cur.fetchall()]
            return {"table": str(table), "columns": rows}
    except Exception as exc:  # noqa: BLE001 — MCP tool boundary must not raise
        return {"error": f"PostgreSQL error: {exc}", "stage": "execution"}


if __name__ == "__main__":
    mcp.run(transport="stdio")
