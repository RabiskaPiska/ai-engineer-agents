# graphql-mcp

Reference MCP server that turns the pack's GraphQL skills into MCP tools:

| Tool | Wraps | Purpose |
|------|-------|---------|
| `introspect(url)` | `SKILLS/introspection-enumeration` | Full introspection (with honest fallback + `introspection_enabled=False` when blocked) |
| `run_query(url, query, variables=None, headers=None)` | `common.transport.HttpTransport` | Raw GraphQL execution — returns the raw `{"data","errors"}` JSON |
| `schema_map(url)` | `SKILLS/introspection-enumeration` | Compact `{types, roots}` schema map |

## Run (stdio)

```bash
python MCP_SERVERS/graphql-mcp/server.py
```

stdio transport (`mcp.run(transport="stdio")`). The `endpoint` port in
`config.json` (`localhost:8094`) is a reference value — ports are assignable
via config; the stdio transport does not bind it.

## Environment variables

None required. (No secrets are used; auth differences are passed per-call as
extra `headers`, per the pack transport contract.)

## Honest notes

- **Reference implementation.** Skills are loaded lazily via
  `common.loader.load_skill` at call time; if `common/` or the SKILLS/ tree is
  missing next to `MCP_SERVERS/`, tools return a friendly
  `{"error": ..., "hint": ...}` dict instead of crashing the server.
- The module itself imports cleanly even while sibling files are mid-write —
  all heavy imports live inside the tool functions.
- `schema_map` returns `None` fields when introspection is blocked rather
  than fabricating a schema.
