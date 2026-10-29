# GraphQL Specialist Agent Pack

Version 1.0.0 · 2026-10-29 · MIT licensed

A self-contained Python pack for **authorized** security testing of GraphQL
APIs: ten skills, five MCP servers, one shared transport contract, one
findings schema, one offline vulnerable demo target, and a report generator.

## What's inside

```
common/            transport.py findings.py errors.py loader.py
SKILLS/            10 skills (schema-fingerprinting ... report-generation)
MCP_SERVERS/       github-mcp graphql-mcp custom-api-mcp security-tools-mcp postgres-mcp
AGENTS/graphql-specialist/   agent definition, config, verified GitHub sources
examples/          demo_target.py — offline intentionally-vulnerable GraphQL server
INSTALLERS/        Linux/macOS/Windows installers, uninstall, requirements
BUILD/             build_pack.py, validate_agents.py, test_all.sh
tests/             pytest unit + E2E suite
EVIDENCE/          engagement evidence output directory
```

## Skills

| Skill | What it proves |
|---|---|
| `schema-fingerprinting` | Which GraphQL engine is behind the endpoint; which features (suggestions / batching / introspection) respond. |
| `introspection-enumeration` | Full or minimal schema map; honest `introspection_enabled=False` when blocked. |
| `clairvoyance-discovery` | Hidden field recovery from "Did you mean" errors when introspection is off. |
| `bola-idor-testing` | Object-level authorization failures, proven across two low-privilege contexts with control checks. |
| `alias-abuse-testing` | Alias-amplified queries: acceptance, elapsed time, response size. |
| `batch-abuse-testing` | Batch acceptance and missing size limits via raw batch bodies. |
| `complexity-dos-testing` | Deep-chain and fan-out cost probing with hard safety caps. |
| `deep-nesting-testing` | Schema cycle discovery and cyclic-query recursion testing. |
| `nplus1-detection` | N+1 resolver patterns via timing ratio (heuristic, confidence ≤ 0.6, says so). |
| `report-generation` | Markdown/JSON reports: severity-ordered findings, evidence, CVSS-qualitative map, remediation, detection rules. |

## Honest scope

**Proven by tests** (pytest, see `tests/`): the transport contract
(Http/Local/Map), the findings schema and validation, every skill's happy
path and at least one adversarial path, the demo target's BOLA / context /
batch / recursion behavior, MCP server imports and tool counts, and the
offline E2E flow against a live demo server on a local port.

**Reference implementation, not proven by tests**: the installers (run on
clean machines, not in CI), the MCP servers' live integrations (GitHub REST
against real repos, real Postgres connections, external graphw00f/clairvoyance
binaries), and the N+1 timing heuristic's judgment on production latency
profiles — timing heuristics are indicative, not proof. The GitHub
star/fork/push figures in `AGENTS/graphql-specialist/github-sources.md` were
live-verified on 2026-10-29 and will drift; re-verify before citing them
elsewhere.

## Quickstart

```bash
# 1. Install
bash INSTALLERS/install-linux.sh        # macOS: install-macos.sh
source .venv/bin/activate               # Windows: .\.venv\Scripts\Activate.ps1
                                        # (Windows install: INSTALLERS\install-windows.ps1)

# 2. Run the test suite (offline, no network beyond localhost)
pytest tests/ -v

# 3. Start the demo target
python examples/demo_target.py          # http://127.0.0.1:4000/graphql

# 4. Point the agent's skills at it and generate a report
#    — see AGENTS/graphql-specialist/README.md for the full script
```

Validate the pack layout + imports at any time with
`python BUILD/validate_agents.py`, and produce the distributable zip with
`python BUILD/build_pack.py`.

## Security note

This pack is for **authorized testing only** — your own systems, engagements
with written permission, or CTF/lab environments. The demo target ships
vulnerable **on purpose** and must not be exposed to untrusted networks.
All DoS-style generators are capped (`max_ops=100`, `max_depth=20` by
default) and never exceed the caps unless `aggressive=True` is passed
explicitly. Secrets come from environment variables only; never commit or
echo credentials, and keep engagement evidence out of public repos.

## License

MIT — see `LICENSE`.
