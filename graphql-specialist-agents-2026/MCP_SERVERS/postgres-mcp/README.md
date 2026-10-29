# postgres-mcp

Reference MCP server for **read-only** PostgreSQL inspection.

## Tools

| Tool | Purpose |
|------|---------|
| `run_query(sql)` | Executes a single read-only statement (SELECT / WITH / EXPLAIN) against `POSTGRES_URL`; results capped at 500 rows with an honest `truncated` flag |
| `list_tables()` | Tables in the `public` schema (information_schema) |
| `list_columns(table)` | Columns of one table, via a **parameterized** query (table name is a bound parameter, never concatenated) |

## Run (stdio)

```bash
python MCP_SERVERS/postgres-mcp/server.py
```

stdio transport (`mcp.run(transport="stdio")`). The `endpoint` port in
`config.json` (`localhost:5432`) is a reference value — ports are assignable
via config; the stdio transport does not bind it.

## Environment variables

| Variable       | Required | Meaning                                       |
|----------------|----------|-----------------------------------------------|
| `POSTGRES_URL` | yes (at call time) | PostgreSQL DSN, e.g. `postgresql://user:pass@host:5432/db`. Read **only** from the env — never embedded. Missing at call time → friendly error dict. |

`psycopg2` is a **lazy optional dependency**: the server imports and lists
its tools without it; tools that need it report an install hint
(`pip install psycopg2-binary`) if it is absent.

## The read-only gate (`assert_read_only`)

`assert_read_only(sql)` is a **pure function** (no DB access): it returns
`None` for allowed statements and raises `ValueError` otherwise. It allows a
single `SELECT` / `WITH` / `EXPLAIN` statement and rejects:

- mutating keywords: INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, GRANT,
  COPY (the SPEC-required eight) plus CREATE, REVOKE, VACUUM, SET, PREPARE
  and other state-changers;
- `EXPLAIN ANALYZE SELECT ...` is allowed; `EXPLAIN ANALYZE DROP/INSERT/...`
  is rejected because EXPLAIN ANALYZE actually executes the statement;
- `SELECT ... INTO` (creates a table);
- multi-statement input — analysis runs on a copy with string literals,
  quoted identifiers, dollar-quoted strings and comments stripped, then any
  remaining `;` separator is rejected. This defeats bypasses such as
  `SELECT 'drop table users'`, `/*;*/ SELECT 1` or `SELECT 1; DROP TABLE x`.

## Honest notes

- **Reference implementation.** Single connection per call (no pooling), no
  role/credential management — use a least-privilege DB user.
- The read-only gate is an application-layer check, not a security boundary;
  enforce true read-only access with a read-only database role as well.
  In particular, mutating functions callable from SELECT (`lo_import`,
  `dblink`, `pg_sleep`, `pg_terminate_backend`, ...) pass this guard —
  only a read-only DB role truly enforces read-only access.
- DB values that are not JSON-native (timestamps, decimals, UUIDs, bytes)
  are stringified so MCP serialization cannot fail silently.
