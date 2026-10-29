# report-generation

**Skill 10 of the GraphQL Specialist Agent Pack.** Renders a list of findings
(the pack's standard finding schema) into a readable Markdown report or a
structured JSON dict.

## Purpose

- **Executive summary** — total count and per-severity table with
  CVSS-qualitative bands.
- **Per-finding sections** — severity/class/confidence/target, description,
  impact, and evidence rendered as fenced blocks (request as ```graphql`,
  response as ```json`).
- **Appendix A** — remediation summary (proposed fix per finding).
- **Appendix B** — detection rules (WAF rule / log query / notes per finding).

## Usage

```python
from common.loader import load_skill

skill = load_skill("report-generation")

md = skill.generate(findings, fmt="markdown", meta={"target": "https://api.example.com"})
data = skill.generate(findings, fmt="json")   # structured dict

skill.cvss_qualitative("high")                # -> "7.0-8.9"
```

## API notes

- `generate(findings, fmt="markdown"|"json", meta=None) -> str|dict`;
  anything else for `fmt` raises `ValueError`.
- `cvss_qualitative(severity)` bands: critical `9.1-10.0`, high `7.0-8.9`,
  medium `4.0-6.9`, low `0.1-3.9`, info `0.0` (bands as specified by the pack
  spec; note the CVSS v3.1 standard prints the critical band as `9.0-10.0`).
- Findings are ordered most-severe-first using `common.findings.SEVERITY_ORDER`
  (tolerates ascending/descending/mapping orientations); unknown severities
  sort last.

## Honest limitations

- **Empty input is not an error**: an empty finding list produces an honest
  "no findings" report that explicitly states absence of findings is not
  evidence of absence of vulnerabilities.
- **Malformed items are skipped, not repaired**: non-dict entries are dropped
  and the count is disclosed in the report; fields are rendered with
  `str()`/`"n/a"` fallbacks rather than validated.
- **Evidence responses are truncated** to 4000 characters in Markdown (with a
  visible truncation marker); the JSON format preserves them in full.
- **CVSS bands are qualitative labels only** — they are not computed CVSS
  base scores and must not be presented as such.
- No severity re-assessment, deduplication, or cross-finding correlation is
  performed; the report renders findings exactly as the skills produced them.
