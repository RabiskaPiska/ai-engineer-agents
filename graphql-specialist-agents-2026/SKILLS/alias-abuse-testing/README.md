# alias-abuse-testing

**Purpose.** Test whether the endpoint accepts and executes a large number of
aliased fields in a single document without any alias/complexity limit — the
cheapest GraphQL resource-amplification vector.

## Usage

```python
from common.loader import load_skill
from common.transport import HttpTransport

skill = load_skill("alias-abuse-testing")

# Builder only (pure function):
query = skill.build(100, "__typename")
# -> 'query AliasAbuse { a0: __typename a1: __typename ... a99: __typename }'

# Full measurement:
result = skill.run(HttpTransport(url), field="__typename", n=100, max_ops=100)
print(result["meta"])   # accepted, elapsed_ms, response_bytes, aliases_executed, ...
```

## Return shape

```jsonc
{
  "findings": [/* GQL-ALIAS-ABUSE-1 when >= n aliases executed with no limit error */],
  "meta": {"accepted": true, "elapsed_ms": 12.4, "response_bytes": 2840,
            "aliases_requested": 100, "aliases_executed": 100,
            "limit_error": null, "capped": false}
}
```

## How it works

- `build(n, field, args="")` — pure query builder, aliases `a0..a{n-1}`.
- `run(transport, field, n=100, max_ops=100, aggressive=False, args="")` —
  **safety per SPEC.md:** unless `aggressive=True`, the alias count is capped
  at `max_ops` (default 100); `meta.capped` records when a cap was applied.
  Fields are `__typename` by recommendation (valid on any root, always
  non-null), but any scalar-producing root field name works, optionally with
  `args="(first: 1)"`.
- A **finding fires only when the server actually executed >= n aliases**
  (non-null results) **and no limit-shaped error** was observed. Limit
  detection is heuristic (matches "too many", "rate limit", "complexity",
  "maximum aliases/fields/operations", "exceeded" wording) and the matched
  message is reported verbatim in `meta.limit_error`.

## Honest limitations

- `aliases_executed` counts non-null alias results; a field returning `null`
  for every alias legitimately looks "not executed" even when it was.
- Limit detection is message-based — a server that silently truncates aliases
  (no error wording) will not be recognized as limited.
- `elapsed_ms` includes HTTP round-trip overhead (transport-level timing,
  not server-side timing).
- This skill sends exactly ONE request per `run()` call (plus nothing else) —
  it measures amplification, it does not flood. Repeated flooding is the
  operator's responsibility, not this tool's default.
