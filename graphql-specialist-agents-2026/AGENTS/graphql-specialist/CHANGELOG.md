# Changelog — GraphQL Specialist Agent

## 1.0.0 — 2026-10-29

Initial release.

- Agent definition: `agent.md` (workflow, evidence rule, human-in-the-loop
  thresholds, retry policy) and `config.json` (inputs/outputs, skills, MCP
  servers, limits, confidence thresholds).
- `github-sources.md`: 21 reference repositories with stars/forks/last-push
  live-verified via the GitHub REST API on 2026-10-29; 5 candidate repos
  rejected during verification and documented honestly.
- Skills wired: schema-fingerprinting, introspection-enumeration,
  clairvoyance-discovery, bola-idor-testing, alias-abuse-testing,
  batch-abuse-testing, complexity-dos-testing, deep-nesting-testing,
  nplus1-detection, report-generation.
- Default safety limits: `max_ops=100`, `max_depth=20`, `test_timeout_s=240`.
