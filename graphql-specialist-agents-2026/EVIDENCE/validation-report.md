# EVIDENCE — validation report (GraphQL Specialist Agent Pack v1.0.0, 2026-10-29)

All commands run from the pack root on Python 3.14.8, Windows.

## Test suite
```
python -m pytest tests -q
→ 156 passed, 1 warning in 4.25s   (exit 0)
```
Coverage (pytest-cov, --cov=common --cov=SKILLS --cov=examples --cov=MCP_SERVERS):
common/ 82–96% per module; SKILLS 65–95% per skill; examples/demo_target 85%;
MCP_SERVERS 63–88% per server (was 18–49% before quality round 2); TOTAL ≈ 80%.

## Static checks
```
python -m ruff check SKILLS common examples BUILD MCP_SERVERS tests
→ All checks passed!  (exit 0)
```

## Structure validator
```
python BUILD/validate_agents.py
→ VALIDATION PASSED: layout + imports OK  (exit 0)
```
Checks: SPEC layout (10 skills × skill.py+README, 5 servers × server.py+config.json,
common/ modules, agent docs), import of every skill and MCP server via common.loader,
agent config.json parseability + key contract.

## Adversarial verification (B2, de-correlated subagent)
Verdict: pass-with-findings. Independently reproduced: 125-test green (pre-round-2),
validator exit 0, star spot-checks 4/4, DoS caps enforced under hostile n (500→10),
BOLA e2e genuine cross-identity read, secrets grep zero hits, mutation-tested 2 tests
prove failable.

Findings → status (all closed in one fix dispatch, then re-verified):
1. README quickstart produced 0 findings for 2/3 probes → fixed; live re-run yields
   exactly 3 findings (GQL-BOLA-1, GQL-ALIAS-ABUSE-1, GQL-BATCH-ABUSE-1).
2. Raising transport escaped run() in 4 skills → wrapped, structured meta.suspicions.
3. SPEC loading block missing in 5 skills → added verbatim.
4. agent.md promised unimplemented retry/Retry-After/skipped_probes → rewritten to match code.
5. Hostile-input AttributeErrors (roots=None, schema_map=None, None wordlist) → hardened.
6. custom-api-mcp bola structurally control-mode → documented honestly in tool + meta.
7. postgres dollar-quote digit-tag false-reject → regex widened; README discloses
   read-only-role requirement.
8. github-sources count arithmetic (27 vs 21+5) → corrected to 26.
9. config.json auth misuse (GRAPHW00F_BIN as auth; unused GH_TOKEN) → made truthful.
10. clairvoyance evidence.response synthesized → real probe pair attached.
11. Dead vuln_class guard in common/findings.py → simplified.
12. Stray .coverage artifact → deleted.

## End-to-end proof chain
examples/demo_target.py (stdlib HTTP, BOLA by design, unbounded Config.parent recursion,
batch accepted) ↔ common/transport.HttpTransport ↔ every skill ↔ report generation —
exercised in tests/test_bola.py, test_alias_batch.py, test_mcp_pipelines.py and the
corrected README quickstart (live-verified 3 findings).
