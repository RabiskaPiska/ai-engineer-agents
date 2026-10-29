# SPEC.md — GraphQL Specialist Agent Pack v1.0.0 (binding interface contract)

Python >= 3.10. Allowed runtime deps: `httpx`, `graphql-core`, `mcp` (MCP servers only).
Tests: `pytest`. No other third-party imports anywhere.

## Repo layout (fixed)
```
common/            transport.py findings.py errors.py loader.py
SKILLS/<name>/     skill.py README.md          (folder names use hyphens)
MCP_SERVERS/<name>/ server.py config.json README.md
AGENTS/graphql-specialist/ agent.md config.json github-sources.md honestscore.md README.md CHANGELOG.md
examples/demo_target.py
INSTALLERS/ BUILD/ tests/ EVIDENCE/
```

## Module loading convention
`skill.py` files live in hyphenated dirs (not importable names). Every skill.py
begins with this exact block, then imports from `common` normally:
```python
import sys, pathlib
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
```
`common/loader.py` provides `load_skill(name: str)` (module by folder name) and
`load_mcp_server(name: str)` used by tests and BUILD/validate_agents.py.

## Transport protocol (the one contract everything shares)
```python
class Transport(Protocol):
    def execute(self, query: str, variables: dict | None = None,
                operation_name: str | None = None,
                headers: dict | None = None) -> dict:
        """Raw GraphQL JSON: {"data": ..., "errors": [...]} (errors may be absent)."""
    def execute_raw(self, body: dict | list) -> dict | list:
        """POST an arbitrary JSON body (batch = list). Returns parsed JSON."""
```
- `common/transport.py` ships: `HttpTransport(url, headers=None, timeout_s=30.0)`
  (records `.last_status`, `.last_elapsed_ms`), `LocalTransport(schema, context=None)`
  (graphql-core `graphql_sync`; serializes errors to dicts; `execute_raw` on a list
  executes each op and returns a list of responses), `MapTransport` (dict of
  canned responses; for unit tests).
- Transports are STATELESS per call; auth differences are expressed as extra
  `headers` per call (e.g. `{"X-User-ID": "u2"}`).

## Findings schema (fixed — `common/findings.py`)
```python
{
  "id": "GQL-<class>-<n>", "title": str, "vuln_class": str,
  "severity": "critical|high|medium|low|info",
  "confidence": float 0..1, "target": url, "timestamp": iso8601Z,
  "evidence": {"request": {"query","variables","operation_name","headers"},
               "response": <raw json>},
  "description": str, "impact": str,
  "proposed_fix": {"summary","config_or_code","language","references": [str]},
  "detection": {"waf_rule": str|None, "log_query": str|None, "notes": str|None}
}
```
`new_finding(...)` builds + validates; `validate_finding(f) -> list[str]` returns defects.
Every skill returns `{"findings": [...], "meta": {...}}`. `findings` may be empty —
never fabricate; unproven suspicions go in `meta.suspicions`.

## Skill interface (each `SKILLS/<name>/skill.py`)
Every skill exposes `run(transport, **opts) -> dict` (+ any documented builder fns).
Safety is mandatory: all DoS-style generators (alias/batch/complexity/deep-nesting)
take `max_ops` (default 100) and `max_depth` (default 20) and NEVER exceed them
unless caller passes `aggressive=True` explicitly. Tests run with conservative caps.

1. schema_fingerprinting: `run(transport) -> {"engine_candidates":[{engine,confidence,evidence}], "features":{"field_suggestions":bool|None,"batch":bool|None,"introspection":bool|None}}`
2. introspection_enumeration: `run(transport, full=True) -> {"introspection_enabled":bool,"schema_map":{"types":[{kind,name,fields:[{name,type,args:[...]}]}]},"roots":{"query":[...],"mutation":[...],"subscription":[...]}}`; falls back to a minimal introspection query, then to suggestion-mining; sets `introspection_enabled=False` honestly when blocked.
3. clairvoyance_discovery: `run(transport, wordlist=None, root_type="Query", max_probes=200) -> {"discovered":[{"field","probable_type","evidence"}], "suggestions_enabled":bool}`; default wordlist ~120 common field names; works purely off "Did you mean" errors.
4. bola_idor_testing: `run(transport_a, transport_b, schema_map, max_tests=25, id_sample="1") -> {"findings":[...],"tested":int,"skipped":int}`. Auto-builds one probe per object-typed root field with a single ID arg. Finding when B's response contains data for A's id. Also accepts explicit `probe(query_template, id_field)`.
5. alias_abuse_testing: `build(n, field, args="") -> str` (query with n aliased fields); `run(transport, field, n=100, ...) -> {"findings":[...],"meta":{"accepted":bool,"elapsed_ms","response_bytes"}}`.
6. batch_abuse_testing: `build(n, query) -> list` (n copies); `run(transport, query, n=50) -> ...` (uses `execute_raw`); detects batch acceptance + absence of size limits.
7. complexity_dos_testing: `build_deep(field_chain, depth)`, `build_fanout(field, n)`; `run(transport, schema_map, max_depth=20, max_ops=100, aggressive=False)`.
8. deep_nesting_testing: `find_cycles(schema_map) -> [["config","parent","config",...]]`; `build_cyclic(cycle, rounds)`; `run(transport, schema_map, rounds=15, ...)`.
9. nplus1_detection: `run(transport, list_query, single_query_template, n=10, threshold_ratio=3.0) -> {"ratio":float,"finding"|None}`; timing-heuristic only, confidence capped at 0.6, says so in the finding text.
10. report_generation: `generate(findings, fmt="markdown"|"json", meta=None) -> str|dict`; severity order critical>high>medium>low>info; includes executive summary, per-finding evidence + CVSS-qualitative mapping table, remediation appendix, detection-rules appendix. `cvss_qualitative(severity) -> str` mapping included.

## MCP server conventions (`MCP_SERVERS/<name>/server.py`)
`from mcp.server.fastmcp import FastMCP`; module-level `mcp = FastMCP("<name>")`;
`@mcp.tool()` functions; `if __name__ == "__main__": mcp.run(transport="stdio")`.
Secrets only from env vars (e.g. `GH_TOKEN`, `POSTGRES_URL`) — never literals.
config.json: `{"name","endpoint":"localhost:<port>","transport":"stdio|http","auth":{"type":"env","var":"..."},"rate_limit_per_min":N,"timeout_s":N}`.
- github-mcp: tools `get_repo(owner, repo)`, `get_file_contents(owner, repo, path)`, `search_repositories(query)` (GH REST via httpx, `GH_TOKEN`).
- graphql-mcp: tools `introspect(url)`, `run_query(url, query, variables=None, headers=None)`, `schema_map(url)` — reuses skills via `common.loader`.
- custom-api-mcp: tools `start_test(url, test_types) -> test_id`, `get_status(test_id)`, `get_results(test_id)`, `verify_finding(test_id, finding_id)` — in-process registry dict; pipelines call the skills.
- security-tools-mcp: tools `list_tools()`, `run_graphw00f(url)` (subprocess, degrades gracefully if not installed), `run_clairvoyance(url, wordlist=None)`.
- postgres-mcp: tools `run_query(sql)`, `list_tables()`, `list_columns(table)`; env `POSTGRES_URL`; `assert_read_only(sql)` pure fn (allows single SELECT/WITH/EXPLAIN, rejects the rest) — psycopg2 import is lazy/optional.

## examples/demo_target.py (offline E2E target)
graphql-core schema: `user(id:ID!):User` (intentional BOLA: ignores ownership of X-User-ID), `users(first:Int):[User]`, `me:User` (context-bound), `User.orders:[Order]`, `Order.items:[Item]`, `config:Config` where `Config.parent:Config` recurses unboundedly (deep-nesting target). Server: stdlib `http.server.ThreadingHTTPServer`, POST `/graphql` accepts single dict or batch list, `X-User-ID` header sets context. `serve(host="127.0.0.1", port=4000)` + `__main__` entry.

## Tests (`tests/`, pytest)
Unit tests must be deterministic (no sleeps > 50 ms total, no network except localhost demo server started in-fixture). E2E fixture: spin `demo_target` ThreadingHTTPServer on a free port, `HttpTransport` against it. Every skill ≥ 1 happy-path + ≥ 1 adversarial test (e.g. introspection disabled, suggestions disabled, batch rejected). MCP tests: import each server, `asyncio.run(mcp.list_tools())` → assert ≥ 2 tools; postgres `assert_read_only` pure-fn cases.

## Docs tone
Honest. Version numbers only when verified. Every GitHub source in
AGENTS/.../github-sources.md carries live-verified stars/forks/last-push + access date 2026-10-29.
