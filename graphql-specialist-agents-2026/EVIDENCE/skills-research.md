# EVIDENCE — skills research notes (10 skills, 2026-10-29)

Design decisions and root causes discovered during the build (each verified by test):

1. **schema-fingerprinting** — engine hints come from error wording ("Did you mean"
   suggestion presence/format), __typename behaviors, and batch acceptance. Root cause
   found: graphql-core formats suggestions with single quotes, graphql-js with double —
   regexes are quote-agnostic. Probe budget capped at 6 requests. Hints are directional
   (confidence 0.45–0.8) and flagged as unverified against live AppSync/Hasura.
2. **introspection-enumeration** — full → minimal → suggestion-mining fallback ladder;
   schema_map carries types + roots (roots added after the SPEC-gap merge finding);
   introspection_enabled=False reported honestly when blocked.
3. **clairvoyance-discovery** — hidden-field discovery purely off suggestion errors;
   126-entry default wordlist; probe budget max_probes; wordlist entries coerced via
   str() (None-proof); findings attach the real probe request/response pair.
4. **bola-idor-testing** — auto-probes object-typed root fields with a single ID arg;
   cross-identity read = finding with full evidence; control run (same identity) must
   yield zero findings; schema_map=None handled honestly.
5. **alias-abuse-testing** — alias generators + acceptance/size/timing measurement;
   max_ops cap default 100, never exceeded without aggressive=True.
6. **batch-abuse-testing** — JSON-array body via execute_raw; unsupported-batch reported
   honestly (MapTransport/LocalTransport semantics differ by design).
7. **complexity-dos-testing** — derives longest fillable chains + high-fanout list fields
   from the real schema_map; caps enforced under hostile n (B2: 500→10).
8. **deep-nesting-testing** — cycle detection on the schema graph (config/parent on the
   demo target); cyclic fragment-chain semantics corrected (GraphQL forbids cyclic
   spreads — linear fragment chains used).
9. **nplus1-detection** — timing heuristic only; confidence hard-capped 0.6; finding text
   states "TIMING HEURISTIC"; works from transport.last_elapsed_ms or perf_counter.
10. **report-generation** — markdown/json, severity ordering, CVSS-qualitative bands
    (critical band documented as 9.1–10.0 by orchestrator decision), detection-rules
    appendix, honest empty-report path, SPEC run() wrapper added at merge.

Cross-cutting: every skill returns {"findings":[...],"meta":{...}}; findings validated by
common.findings.validate_finding; raising transports never escape run() (post-B2);
SPEC loading block present in all 10 skill.py files.
