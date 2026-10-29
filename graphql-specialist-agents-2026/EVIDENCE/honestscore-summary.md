# EVIDENCE — honestscore summary (GraphQL Specialist Agent Pack v1.0.0)

Scored 2026-10-29 with the honestscore rubric (blind, MIN across dimensions, no rounding up).
De-correlated adversarial pass: REAL subagent (B2), executed checks, 11 findings; all closed
in one fix dispatch; guard-check script 15/15 after fixes. Round 2 closed the largest
completeness defect (MCP pipeline coverage). 2-round cap reached — stopping truthfully.

## Step 0 — what a correct version contains
Per SPEC.md: 10 skills with SPEC run() signatures, 5 MCP servers, common/ transport+findings+
errors+loader, offline demo target, deterministic test suite, honest docs, installers, build
scripts. Diff against artifact: all present; validator exit 0.

## Per-dimension ledgers (defect → cost → closing evidence)

**correctness 9.5** — [moderate 0.4: BOLA control gate keys on transport object identity; two
distinct transports with the same identity header can fire (documented + pinned test);
moderate 0.1: custom-api-mcp runs bola in single-identity control mode only] — evidence:
156 tests green (pasted twice independently), B2 mutation-verified 2 tests are failable,
BOLA e2e proven as genuine cross-identity read.

**completeness 9.4** — [moderate 0.3: total line coverage 80% (target 90%);
moderate 0.3: cross-identity BOLA via MCP start_test requires calling the skill directly] —
evidence: coverage table (MCP 63–88%, total 80%), validator exit 0, layout complete.

**robustness 9.3** — [moderate 0.4: B2 found 4 skills where a raising transport escaped
run() — all closed, guard-script 15/15; low 0.3: remaining uncovered error branches] —
evidence: BoomTransport-class probes now structured; hostile schema_map/None inputs handled.

**security 9.4** — [moderate 0.4: postgres assert_read_only is a convenience guard, not a
boundary (SELECT-callable mutating functions pass; disclosed, read-only role required);
low 0.2: annotated boundary-catch excepts] — evidence: B2 secrets grep zero hits;
30-case SQL attack pass; demo binds 127.0.0.1; no curl|bash in installers.

**docs 9.4** — [low 0.3: CVSS critical band printed as 9.1–10.0 vs v3.1's 9.0–10.0
(documented); low 0.3: engine-fingerprint hints heuristic-only, flagged in README/meta] —
evidence: quickstart executed live → exactly 3 findings as stated; github-sources numbers
API-verified; B2 star spot-checks 4/4 match.

**performance N/A** — justified: no performance claim exists in any doc (verifiable by
grep); suite runtime measured anyway: 156 tests in 4.25s.

**concurrency 9.0** — [one background thread + in-process registry in custom-api-mcp;
no Python race detector exists on this platform — evidence tier is a recorded run:
30 threads × 40 registry ops → 0 errors (A3), plus pipeline-thread polling tests in
test_mcp_pipelines.py] — honest limitation: stress evidence is not a race detector.

## Binary gates
- De-correlated adversarial pass: MET (real subagent, executed, findings fixed, re-verified).
- Independent re-verification of the fix: MET (orchestrator re-ran pytest/validator/ruff).
- Honest docs (no fabricated numbers): MET (all repo data API/shields-verified).

## FINAL: MIN = 9.0 (concurrency) / mean ≈ 9.3
Stopping truthfully at the 2-round cap. Path to 9.5+: persisted concurrency stress test in
CI, cross-identity BOLA through the MCP layer, coverage ≥ 90%.

## NOT verified
- Engine fingerprinting against live AppSync/Hasura/Apollo wording (needs real targets;
  heuristics flagged as directional in the skill README).
- graphw00f subprocess path (tool not installed; honest degrade path tested instead).
- psycopg2 paths (real driver not installed; fake-driver tests + degrade path tested).
