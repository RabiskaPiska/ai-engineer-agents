# batch-abuse-testing

**Skill 6 of the GraphQL Specialist Agent Pack.** Sends a JSON-array batch of
identical GraphQL operations via `Transport.execute_raw(list)` and reports
whether the endpoint accepts batches without a size limit — a DoS
amplification vector (one HTTP request executing N operations).

## Purpose

- Detect whether the server accepts batched requests at all.
- Measure per-op success count and total response size for a batch of *n* ops.
- Produce a finding when a batch of >= 2 operations is accepted with **no**
  batch/size-limit error observed.

## Usage

```python
from common.loader import load_skill

skill = load_skill("batch-abuse-testing")

ops = skill.build(5, "query { me { id } }")        # 5 op dicts -> one batch body
result = skill.run(transport, "query { me { id } }", n=50)
print(result["meta"]["batch_accepted"], result["meta"]["ops_success"])
```

`run(transport, query, n=50, max_ops=100, aggressive=False)` returns
`{"findings": [...], "meta": {...}}`.

## Honest limitations

- **Probe size is capped.** `n` is clamped to `max_ops` (default 100) unless
  `aggressive=True`. A finding therefore means "no limit error observed for a
  batch of N", not "the server has no limit at all".
- **Transport support varies.** If `execute_raw` raises `TypeError` /
  `AttributeError` on a list body, the skill reports
  `meta.unsupported_batch = True` with a suspicion and **no findings** —
  batch support is simply unverified, never assumed.
- **Single-object collapse.** Some servers answer a list batch with one JSON
  object; this is recorded as a suspicion and per-op success counts are
  unavailable.
- **Limit-error detection is keyword-based** (`batch`, `limit`, `size`,
  `too many`, ...). A server that silently truncates a batch without an error
  message will not be detected.
- A "medium" finding here is an *enabler*; exploitability depends on the cost
  of the underlying resolvers.
