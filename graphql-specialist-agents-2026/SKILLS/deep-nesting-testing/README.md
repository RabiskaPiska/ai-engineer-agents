# deep-nesting-testing

**Skill 8 of the GraphQL Specialist Agent Pack.** Finds cyclic field chains
in a schema (e.g. `Query.config:Config` with `Config.parent:Config`), builds
cyclic and fragment-nested queries, and detects servers that accept deep
nesting with no depth limit.

## Purpose

- `find_cycles(schema_map)` — locate loops in the field graph, rooted at
  Query fields where possible (returns e.g. `[["config", "parent"]]`).
- `build_cyclic(cycle, rounds)` — build a valid nested query following the
  cycle for `rounds` levels (innermost leaf is `{ __typename }` so object-only
  cycles stay valid GraphQL).
- `run(...)` — probe with both a **nested** variant and a **linear
  fragment-chain** variant (GraphQL forbids cyclic fragment spreads, so the
  fragment variant is a linear chain of fragments, still deep nesting), and
  report acceptance without depth-limit errors.

## Usage

```python
from common.loader import load_skill

skill = load_skill("deep-nesting-testing")

cycles = skill.find_cycles(schema_map)          # [["config", "parent"], ...]
q = skill.build_cyclic(cycles[0], 15)           # 15-level cyclic query

result = skill.run(transport, schema_map, rounds=15, max_depth=20)
# result["meta"]["probes"] -> per-variant acceptance / elapsed / limit-hit
```

## Safety (SPEC mandate)

Nesting is clamped to `max_depth` (default 20) unless `aggressive=True`, and
the total number of probe queries is bounded by `max_ops` (default 100; the
skill sends at most 3 cycles x 2 variants regardless).

## Honest limitations

- **Cycle detection is best-effort and bounded** (DFS step cap, dedup by exact
  field tuple, first-found per class). Rotations of the same cycle may appear
  as separate entries; some rare cycles may be missed — never fabricated.
- **Fallback cycles may not start at a root field**; such probes will simply
  error server-side and be recorded honestly in `meta.probes`.
- **Fragment chains are linear, not recursive** — GraphQL validation forbids
  cyclic fragment spreads, so "fragment nesting" here means deep chained
  fragments, which is what servers actually must bound.
- **Acceptance ≠ exploitability.** A finding means the server returned data
  for a cap-deep cyclic query without a limit error; real impact depends on
  parser/resolver cost.
- **Limit detection is keyword-based** (`depth`, `complexity`, `cost`, ...);
  silent truncation or generic errors are not recognized as limits.
