# EVIDENCE — MCP research notes (5 servers, 2026-10-29)

## Key finding: the `mcp` package is 2.x
The installed `mcp` package renamed `FastMCP` → `MCPServer` (mcp.server.mcpserver).
SPEC's original `from mcp.server.fastmcp import FastMCP` crashes on 2.x installs.
All five servers carry a version-agnostic try/except shim (v1 baseline + 2.x alias).
Root cause note mirrored in the brain: web-dev/knowledge/MCP-SDK-2x-fastmcp-rename.md.

## Servers (all import-clean; tools verified via list_tools + integration tests)
| Server | Tools | Auth (env only) | Verified |
|---|---|---|---|
| github-mcp (ref port 8081) | get_repo, get_file_contents, search_repositories | GH_TOKEN | monkeypatched httpx: 200/401/network paths; GH_TOKEN handled from env only |
| graphql-mcp (8094) | introspect, run_query, schema_map | none | live e2e vs demo target: types, roots, roundtrip query |
| custom-api-mcp (8083) | start_test, get_status, get_results, verify_finding | none | full pipeline thread e2e: start→poll→results; verify_finding reproduced=True; 30-thread stress 0 errors |
| security-tools-mcp (8084) | list_tools, run_graphw00f, run_clairvoyance | none (GRAPHW00F_BIN is a path, not auth) | clairvoyance live vs demo; graphw00f honest not-installed degrade |
| postgres-mcp (5432) | run_query, list_tables, list_columns + assert_read_only | POSTGRES_URL | fake-driver tests; 30-case SQL attack pass; $t1$ tag acceptance |

## Honest scope
Ports in config.json are reference values (assignable); servers run over stdio by default
(`mcp.run(transport="stdio")`); these are reference implementations tested at the
function/protocol level — not deployed services. psycopg2 is an optional lazy import
(honest degrade path tested). postgres guard is a convenience check, not a security
boundary — enforce read-only via a read-only DB role (disclosed in README).
