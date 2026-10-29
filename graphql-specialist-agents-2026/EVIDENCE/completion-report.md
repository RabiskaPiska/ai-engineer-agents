# EVIDENCE — completion report (GraphQL Specialist Agent Pack v1.0.0, 2026-10-29)

## Delivered
- 1 specialist agent (AGENTS/graphql-specialist: agent.md, config.json, github-sources.md, honestscore.md, README, CHANGELOG)
- 10 skills (SKILLS/: fingerprinting, introspection, clairvoyance, BOLA/IDOR, alias abuse, batch abuse, complexity DoS, deep nesting, N+1, report generation) — each with run() per SPEC, safety caps, honest meta
- 5 MCP servers (MCP_SERVERS/: github, graphql, custom-api, security-tools, postgres) — FastMCP/MCPServer 2.x-shimmed, env-only secrets
- common/ (Transport protocol: HttpTransport/LocalTransport/MapTransport; findings schema + validator; retry; loader)
- examples/demo_target.py — offline vulnerable GraphQL target (BOLA by design, unbounded recursion, batch accepted)
- 156 passing tests (unit + e2e + MCP pipeline integration), ruff clean, structure validator green
- INSTALLERS (Linux/macOS/Windows) + BUILD (build_pack.py, validate_agents.py, test_all.sh)
- EVIDENCE/ (this folder) + ZIP: graphql-specialist-agents-2026.zip

## Crew
7 subagent spawns across 3 waves + orchestrator (floor 5 respected, scopes disjoint):
wave 1 = 4 builders (common+skills1-5 / skills6-10 / MCP servers / demo+docs+installers);
wave 2 = test builder; wave 3 = adversarial verifier; + 1 fix dispatch + 1 quality round.
Recon executed by the orchestrator with live GitHub API evidence (no recon agent needed).

## Honest deviations from the original request
- "25+ repos": 26 candidates checked, 21 verified with live API data, 5 rejected as
  nonexistent/misattributed (the original list contained fabrications — documented in
  EVIDENCE/github-research.md).
- "10 subagents": 7 disjoint-scope agents (no scope padding to hit a count).
- "9.7/10 per agent": honest final 9.0 (MIN) at the 2-round cap — EVIDENCE/honestscore-summary.md
  names every open defect and the path to 9.5+.
- "90% test coverage": 80% actual (MCP servers were 18–49% before quality round 2).
- MCP endpoints: reference implementations + configurable configs, NOT deployed services.
- 5.75h estimate: not tracked as wall-clock; work was wave-parallel.

## Reproduce
```
pip install -r INSTALLERS/requirements.txt
python -m pytest tests -q
python BUILD/validate_agents.py
python examples/demo_target.py        # then point the agent at http://127.0.0.1:4000/graphql
```
