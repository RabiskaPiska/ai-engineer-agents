# honestscore.md — GraphQL Specialist Agent v1.0.0

Scored 2026-10-29 with the honestscore rubric. Full evidence in EVIDENCE/honestscore-summary.md.

**FINAL: MIN = 9.0 / mean ≈ 9.3** (2-round cap reached; never rounded up)

| Dimension | Score | Main open defect |
|---|---|---|
| correctness | 9.5 | BOLA control gate keys on transport object identity (documented + pinned test) |
| completeness | 9.4 | 80% line coverage; cross-identity BOLA via MCP requires calling the skill directly |
| robustness | 9.3 | Residual uncovered error branches |
| security | 9.4 | postgres guard is convenience-only (disclosed; use a read-only role) |
| docs | 9.4 | CVSS band 9.1–10.0 vs v3.1 9.0–10.0 (documented); fingerprint hints directional |
| performance | N/A | No performance claims exist (justified) |
| concurrency | 9.0 | Stress-run evidence only; no CPython race detector available |

Binary gates: de-correlated adversarial pass MET (real subagent, 11 findings → all fixed →
re-verified); independent orchestrator re-verification MET (pytest/validator/ruff re-run);
honest-docs MET (all repo numbers API-verified).

Score progression: 7.0 (wave-1 self-scores, adversarial gate not yet run) → B2 pass-with-findings
(11 findings) → fix dispatch + guard-script 15/15 → quality round 2 (MCP coverage 18–49% →
63–88%, 125→156 tests) → final 9.0.

NOT verified: fingerprint heuristics vs live AppSync/Hasura/Apollo; graphw00f subprocess
(not installed; degrade path tested); psycopg2 real-driver paths (fake driver tested).
