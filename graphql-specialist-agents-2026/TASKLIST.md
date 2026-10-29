# TASKLIST.md — GraphQL Specialist Agent Pack build (2026-10-29)

Orchestrator: main session. Crew: 6 disjoint-scope agents (floor 5 respected; no padding).
Recon (repo verification) was executed by the orchestrator with live GitHub API evidence
— no recon agent needed; results are baked into SPEC.md + A4's github-sources data.

| ID | type | IN (scope) | OUT (exclusions) | deliverable | wave |
|----|------|-----------|------------------|-------------|------|
| A1 | general | `common/` + SKILLS: schema-fingerprinting, introspection-enumeration, clairvoyance-discovery, bola-idor-testing, alias-abuse-testing | SKILLS 6-10, MCP_SERVERS, AGENTS, INSTALLERS, BUILD, examples, tests | 5 skill.py + 5 README.md + 4 common modules | 1 |
| A2 | general | SKILLS: batch-abuse-testing, complexity-dos-testing, deep-nesting-testing, nplus1-detection, report-generation | SKILLS 1-5, common/, everything else | 5 skill.py + 5 README.md | 1 |
| A3 | general | MCP_SERVERS/ (github-mcp, graphql-mcp, custom-api-mcp, security-tools-mcp, postgres-mcp) | SKILLS, common/, AGENTS, examples | 5 server.py + 5 config.json + 5 README.md | 1 |
| A4 | general | examples/demo_target.py + AGENTS/graphql-specialist/ (agent.md, config.json, README.md, CHANGELOG.md, github-sources.md) + INSTALLERS/ + BUILD/ + root README/CHANGELOG/LICENSE | SKILLS, common/, MCP_SERVERS, tests | demo target + agent docs + installers + build scripts | 1 |
| B1 | general | tests/ suite (unit + e2e against demo server), run pytest + ruff, fix only trivial integration bugs it discovers | new features, MCP_SERVERS rewrite, docs | passing pytest suite + real run output | 2 |
| B2 | general (adversarial) | adversarial verification of merged pack vs SPEC.md + honestscore rubric | fixing anything (reports only) | findings JSON + verdict | 3 |

## Wave log
- Wave 1: spawned 2026-10-29 (A1-A4, one message, parallel). Merge: orchestrator.
- Wave 2: B1 after merge + deps verified.
- Wave 3: B2 after B1 green.

## Kill criteria
Agent looping (3 same-class probes), writing outside IN-scope, or 2 failed retries → killed, scope reassigned by orchestrator. Re-verify cap: 2 rounds.
