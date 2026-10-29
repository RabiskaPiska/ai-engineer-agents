# bola-idor-testing

**Purpose.** Detect broken object-level authorization (BOLA / IDOOR-style
cross-identity reads) by replaying identity A's object ids through identity B's
transport and comparing what comes back.

## Usage

```python
from common.loader import load_skill
from common.transport import HttpTransport

# Auth differences are expressed as transport-level default headers (stateless):
ta = HttpTransport(url, headers={"Authorization": "Bearer token-of-userA"})
tb = HttpTransport(url, headers={"Authorization": "Bearer token-of-userB"})

skill = load_skill("bola-idor-testing")
schema_map = load_skill("introspection-enumeration").run(ta)["schema_map"]
result = skill.run(ta, tb, schema_map, max_tests=25, id_sample="1")
```

## Return shape

```jsonc
{
  "findings": [/* GQL-BOLA-n findings with both responses as evidence */],
  "tested": 3,
  "skipped": 5,
  "meta": {"candidates": [...], "skipped_reasons": [...], "max_tests": 25, "id_sample": "1"}
}
```

## Auto-probe construction (per SPEC.md)

One probe per **object-typed root field with exactly one required ID argument**:

- root fields are read from `schema_map["roots"]` (query + mutation);
- the field's single arg must be of type `ID`/`ID!`;
- the return type must resolve to a known `OBJECT` kind in `schema_map` (lists
  and unknown types are skipped and counted in `skipped` with reasons);
- the probe selects `__typename` + up to 5 scalar fields of the target object
  so responses can actually be compared.

**Finding condition:** B's response for A's id is a non-null object **with a
matching `id` field or non-empty fields**. Evidence carries B's request/response
plus A's baseline under `evidence.baseline`.

## Explicit probe escape hatch

```python
resp = skill.probe(transport, "query Q($id: ID!) { user(id: $id) { id name } }",
                   id_field="id", id_value="42")
```

## Honest limitations

- **Confidence 0.7, severity high** — a "hit" proves cross-identity
  *readability*, not that the data is private to A. Public reference objects
  produce look-alike findings; the finding text says to verify ownership.
- Only root fields are probed; nested objects (`user.orders`) are out of scope
  for v1 auto-probes (use `probe()` for those).
- `id_sample="1"` is a blind guess: fields where A legitimately owns no object
  with that id are counted as `skipped`, not findings.
- Non-`ID`-keyed lookups (email, slug) are not auto-probed in v1.
