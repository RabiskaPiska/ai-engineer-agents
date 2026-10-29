# security-tools-mcp

Reference MCP server wrapping external GraphQL security tooling.

## Tools

| Tool | Purpose |
|------|---------|
| `list_tools()` | Reports each tool with its kind and **honest availability** (graphw00f resolved path or not installed) |
| `run_graphw00f(url)` | GraphQL engine fingerprinting via subprocess; returns exit code + stdout/stderr |
| `run_clairvoyance(url, wordlist=None)` | Field discovery from "Did you mean" errors, via the pack's `clairvoyance-discovery` skill |

## Run (stdio)

```bash
python MCP_SERVERS/security-tools-mcp/server.py
```

stdio transport (`mcp.run(transport="stdio")`). The `endpoint` port in
`config.json` (`localhost:8084`) is a reference value — ports are assignable
via config; the stdio transport does not bind it.

## Environment variables

| Variable        | Required | Meaning                                                             |
|-----------------|----------|---------------------------------------------------------------------|
| `GRAPHW00F_BIN` | no       | Full path to the graphw00f binary; falls back to `graphw00f` on PATH. Without it graphw00f tools honestly report "not installed" — install via `pipx install graphw00f`. |

## Honest notes

- **Reference implementation.** graphw00f output is passed through as plain
  text (`stdout`/`stderr` + exit code) — no parsing beyond that.
- If graphw00f is missing, `run_graphw00f` returns `{"installed": false, ...}`
  with an install hint. **No fingerprint is ever fabricated.**
- `run_clairvoyance` lazy-imports the pack skill; if `common/`/`SKILLS/` are
  missing next to `MCP_SERVERS/`, it returns a friendly error dict and the
  module still imports cleanly.
- graphw00f subprocess timeout is 90 s; timeouts and launch failures return
  structured error dicts, never exceptions.
