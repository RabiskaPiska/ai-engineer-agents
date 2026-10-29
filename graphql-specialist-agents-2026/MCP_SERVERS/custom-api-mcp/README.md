# custom-api-mcp

Reference MCP server that runs the pack's GraphQL testing skills as async
in-process pipelines against a target API.

## Tools

| Tool | Signature | Purpose |
|------|-----------|---------|
| `start_test` | `(url, test_types: list[str]) -> test_id` | Registers a job and spawns a background thread running the pipeline |
| `get_status` | `(test_id)` | `running` / `complete` / `error` + timestamps |
| `get_results` | `(test_id)` | `{"findings": [...], "meta": {...}}` (pack findings schema) |
| `verify_finding` | `(test_id, finding_id)` | Re-runs the single originating step and reports `reproduced: bool` honestly |

Pipeline order (fixed): **schema fingerprinting → introspection →** the
selected tests among `bola`, `alias`, `batch`, `complexity`, `deep-nesting`.
Later steps reuse the schema map from introspection. Every step is guarded:
one failing step is recorded in `meta.errors` / `meta.suspicions` and never
kills the run. `verify_finding` re-executes the originating skill with the
same conservative caps and compares — it reports `reproduced: false` or
`null` when it cannot confirm; it never fabricates confirmation.

## Run (stdio)

```bash
python MCP_SERVERS/custom-api-mcp/server.py
```

stdio transport (`mcp.run(transport="stdio")`). The `endpoint` port in
`config.json` (`localhost:8083`) is a reference value — ports are assignable
via config; the stdio transport does not bind it.

## Environment variables

None required. Targets are passed per-call as URLs.

## Honest notes

- **Reference implementation.** The job registry is an in-process dict: no
  persistence, jobs are lost when the server restarts (error dicts say so).
- Single-user design: no queue limits beyond `rate_limit_per_min` in
  `config.json`, no auth on the MCP surface itself.
- DoS-style steps run with the SPEC-mandated conservative caps
  (`max_ops`/`max_depth` defaults, `aggressive=False`) — this server never
  escalates to aggressive probing.
- BOLA runs use the same transport for both sides (single-endpoint reference
  run); the meta note states this limitation explicitly.
- Skills load lazily via `common.loader.load_skill`; if `common/`/`SKILLS/`
  are missing, steps fail gracefully into `meta.errors` and the module still
  imports cleanly.
