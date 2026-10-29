# complexity-dos-testing

**Skill 7 of the GraphQL Specialist Agent Pack.** Derives costly queries from
a `schema_map` — the longest fillable field chains (deep nesting) and
root-level list fields (alias fan-out) — executes them, and reports whether
the server accepts max-cap queries without any depth/complexity limit error.

## Purpose

- Find endpoints that accept deeply nested or massively aliased queries with
  no query-cost control (cheap DoS primitives).
- Record measured evidence per probe: acceptance, elapsed time, response size.

## Usage

```python
from common.loader import load_skill

skill = load_skill("complexity-dos-testing")

q = skill.build_deep(["user(id: \"1\")", "orders", "id"], 10)  # 10-level nesting
q2 = skill.build_fanout("users(first: 5)", 50)                 # 50 aliased copies

result = skill.run(transport, schema_map, max_depth=20, max_ops=100)
# result["meta"]["probes"] -> per-probe acceptance / elapsed / limit-hit
```

## Safety (SPEC mandate)

Probes **never** exceed `max_depth` (default 20) nesting levels or `max_ops`
(default 100) aliases unless the caller passes `aggressive=True` explicitly,
which adds one extra 2x-cap probe per family. Derived argument values are
static sample scalars (`1`, `1.0`, `true`, `"1"`); fields whose required args
cannot be safely filled are skipped entirely.

## Honest limitations

- **Derivation is greedy, not optimal.** It picks the first fillable
  object-typed field at each level, not the truly most expensive path.
- **Fan-out probes target root list fields only** (a single-field builder
  cannot reach nested list fields); if the schema has none, the fan-out probe
  is skipped with an honest suspicion.
- **Args are naive.** Enum or input-object required args cause the field to be
  skipped; supplied scalar samples may not be semantically valid on the target.
- **Acceptance ≠ exploitability.** A finding means the cap-sized query was
  accepted with no limit-keyword error; actual cost depends on resolver
  implementations, which this skill does not inspect.
- **Limit detection is keyword-based** (`depth`, `complexity`, `cost`,
  `nesting`, ...). A server that silently truncates or errors generically will
  not register as "limited".
