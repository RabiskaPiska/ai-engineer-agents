# Changelog — GraphQL Specialist Agent Pack

All notable changes to this pack are documented here.

## 1.0.0 — 2026-10-29

Initial release.

- **common/** — transport contract (`HttpTransport`, `LocalTransport`,
  `MapTransport`), fixed findings schema with `new_finding` /
  `validate_finding`, error helpers, and the module loader
  (`load_skill` / `load_mcp_server`).
- **SKILLS/** (10) — schema-fingerprinting, introspection-enumeration,
  clairvoyance-discovery, bola-idor-testing, alias-abuse-testing,
  batch-abuse-testing, complexity-dos-testing, deep-nesting-testing,
  nplus1-detection, report-generation. All DoS-style generators enforce
  `max_ops` (default 100) / `max_depth` (default 20) unless the caller
  passes `aggressive=True`.
- **MCP_SERVERS/** (5) — github-mcp, graphql-mcp, custom-api-mcp,
  security-tools-mcp, postgres-mcp (read-only assertion included).
- **AGENTS/graphql-specialist/** — agent.md workflow, config.json,
  github-sources.md (21 repos live-verified via GitHub REST API on
  2026-10-29; 5 rejected candidates documented), usage guide, changelog.
- **examples/demo_target.py** — offline intentionally-vulnerable GraphQL
  server (BOLA on `user(id:)`, unbounded `Config.parent` recursion,
  unlimited batch, `X-User-ID` context) for tests and practice.
- **INSTALLERS/** — idempotent Linux/macOS/Windows installers + uninstall.
- **BUILD/** — `build_pack.py` (zip), `validate_agents.py` (layout +
  per-skill import validation, non-zero exit on failure), `test_all.sh`.
- **tests/** — pytest unit + offline E2E suite against the demo server.
