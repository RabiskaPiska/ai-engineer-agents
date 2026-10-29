# nplus1-detection

**Skill 9 of the GraphQL Specialist Agent Pack.** Detects *possible* N+1
resolver patterns by comparing the timing of one list query against the
average timing of `n` equivalent single-item queries.

## Purpose

A list query whose resolvers issue one backend call per item (classic N+1)
gets slower as the list grows. This skill measures
`ratio = t_list / avg(t_singles)` and flags a disproportionate ratio.

## Usage

```python
from common.loader import load_skill

skill = load_skill("nplus1-detection")
result = skill.run(
    transport,
    list_query="query { users { id } }",
    single_query_template='query { user(id: "{id}") { id } }',
    n=10,
    threshold_ratio=3.0,
)
print(result["meta"]["ratio"])   # e.g. 4.2  ->  one low-severity finding
```

`run(transport, list_query, single_query_template, n=10, threshold_ratio=3.0)`
returns `{"findings": [...], "meta": {...}}`; `meta["ratio"]`,
`meta["t_list_ms"]`, `meta["t_singles_ms"]` hold the measurements.

## Honest limitations — READ BEFORE ACTING

- **This is a timing heuristic, not proof.** Every finding is severity
  `low`, confidence capped at **0.6**, and says so explicitly in its text.
  Payload size, caching, JIT warm-up, and server noise can all produce a high
  ratio with no N+1 present. Confirm with resolver tracing before remediating.
- **Timing source varies.** `HttpTransport.last_elapsed_ms` is used when
  available; otherwise a local `time.perf_counter` measurement around
  `execute()` is taken (including in-process transports where HTTP overhead is
  absent, which changes what the numbers mean). The source used is recorded in
  `meta.timing_source`.
- **Single run, no warm-up.** One list measurement and `n` single
  measurements; a cold cache or GC pause can skew either side. Re-run before
  drawing conclusions.
- **Sample ids are synthetic** (`"1" .. "n"`); if those ids do not exist, the
  single queries may be cheaper (or fail) — failed singles are excluded and
  the exclusion is recorded in `meta.suspicions`.
- The list query is executed **once**; no comparative baseline request (e.g.
  an artificially truncated list) is sent.
