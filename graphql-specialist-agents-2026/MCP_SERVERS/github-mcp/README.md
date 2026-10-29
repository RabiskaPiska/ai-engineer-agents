# github-mcp

Reference MCP server exposing read-only GitHub REST operations as MCP tools:
`get_repo(owner, repo)`, `get_file_contents(owner, repo, path)`,
`search_repositories(query)`.

## Run (stdio)

```bash
python MCP_SERVERS/github-mcp/server.py
```

The server speaks MCP over stdio (`mcp.run(transport="stdio")`); wire it into
any MCP client with a stdio transport. The `endpoint` port in `config.json`
(`localhost:8081`) is a reference value — ports are assignable via config and
are not used by the stdio transport itself.

## Environment variables

| Variable   | Required | Meaning                                                          |
|------------|----------|------------------------------------------------------------------|
| `GH_TOKEN` | no       | GitHub personal access token. Read **only** from the env — never embedded. Without it, unauthenticated GitHub rate limits apply (~60 req/hour/IP). |

## Honest notes

- This is a **reference implementation**: minimal error handling beyond
  friendly error dicts, no pagination beyond `per_page` (capped at 100), no
  write operations. Endpoint ports are assignable via `config.json`.
- Errors are returned as structured dicts (`{"error", "status", "detail",
  "hint"}`), never raised, so MCP clients always get JSON back.
- API version pinned via `X-GitHub-Api-Version: 2022-11-28` (GitHub's
  documented stable header value).
