# schema-fingerprinting

**Purpose.** Identify the GraphQL engine behind an endpoint and its security-relevant
feature surface (field suggestions, batch support, introspection) using at most
**6 probe requests** (5 by default). Recon skill: it never reports a finding on its
own -- `findings` is always empty; results feed the other skills' `meta`.

## Usage

```python
from common.loader import load_skill
from common.transport import HttpTransport

skill = load_skill("schema-fingerprinting")
result = skill.run(HttpTransport("http://127.0.0.1:4000/graphql"))

print(result["engine_candidates"])  # [{engine, confidence, evidence}, ...]
print(result["features"])           # {"field_suggestions": ..., "batch": ..., "introspection": ...}
print(result["meta"]["probes_sent"])
```

## Return shape

```jsonc
{
  "engine_candidates": [{"engine": "...", "confidence": 0.45, "evidence": "..."}],
  "features": {"field_suggestions": true, "batch": true, "introspection": true},
  "findings": [],
  "meta": {"probes_sent": 5, "probe_budget": 6, "probe_log": [...], "notes": [...]}
}
```

Feature values are `bool | None` — `None` means **unknown**, never guessed.

## How it works (5 probes)

1. `{ __typename }` — sanity: does the endpoint answer GraphQL at all?
2. Misspelled field — validation-error wording and `"Did you mean"` presence.
3. `{ __schema { queryType { name } } }` — introspection enabled?
4. Malformed document (`query {`) — parser wording.
5. A 2-operation list body via `execute_raw` — batch accepted?

Engine hints are heuristic message matches (graphw00f-style, public technique):
reference-implementation wording (`Cannot query field ... Did you mean`),
AppSync wording (`Validation error of type`), Hasura wording (`not found in
type: query_root`). Confidences are deliberately low (0.45–0.8) because wording
similarity is a hint, not proof. **No match → empty `engine_candidates`.**

## Honest limitations

- Engine identification is wording-based; proxies (Apollo Router, custom
  formatters, WAF rewrites) can mask or rewrite messages → wrong/empty hints.
- A server that requires auth may answer every probe with a 401-shaped body:
  features stay `None`.
- Batch detection only tests the standard JSON-array body convention.
- Confidence values are ordinal, not calibrated probabilities.
