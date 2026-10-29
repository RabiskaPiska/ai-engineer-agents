# introspection-enumeration

**Purpose.** Extract the full schema (types, fields, args, root operations) and
report honestly when introspection is blocked. Never fabricates schema content.

## Usage

```python
from common.loader import load_skill
from common.transport import HttpTransport

skill = load_skill("introspection-enumeration")
result = skill.run(HttpTransport("http://127.0.0.1:4000/graphql"), full=True)

print(result["introspection_enabled"])       # bool, honest
print(result["schema_map"]["types"])         # [{kind, name, fields: [{name, type, args}]}]
print(result["roots"])                       # {"query": [...], "mutation": [...], "subscription": [...]}
print(result["meta"]["strategy"])            # "full" | "minimal" | "mined" | "blocked"
```

## Return shape

```jsonc
{
  "introspection_enabled": true,
  "schema_map": {"types": [{"kind": "OBJECT", "name": "User",
                            "fields": [{"name": "orders", "type": "[Order!]",
                                        "args": [{"name": "first", "type": "Int", "default": null}]}]}]},
  "roots": {"query": ["user", "me"], "mutation": [], "subscription": []},
  "findings": [],
  "meta": {"strategy": "full", "errors": [], "probes_sent": 1, "notes": null}
}
```

Type references are serialized to readable strings (`[Order!]!`) via the
standard kind/name/ofType nesting. Meta types (`__*`) are filtered out.

## Fallback chain (SPEC.md)

1. **Full** standard introspection query (fields include args, inputFields,
   enumValues, interfaces, possibleTypes, directives).
2. **Minimal** query — for servers that reject `includeDeprecated` or deep
   `ofType` nesting.
3. **Suggestion-mining** — up to 8 misspelled-field probes harvesting
   `"Did you mean"` errors; field **names** only (types unknown → `null`).
4. **Blocked** — `introspection_enabled: False`, empty schema map, honest notes.

## Honest limitations

- `full` and `minimal` each cost 1 request; the mined fallback costs up to 8.
- Mining only sees fields similar to the 8 seed misspellings — it is a partial
  glimpse, not enumeration (that is `clairvoyance-discovery`'s job).
- Deprecated-argument quirks: servers older than the `includeDeprecated` spec
  may fail the full query; that is exactly what the minimal fallback covers.
- On partial-success servers (data + errors together) we accept `__schema`
  when present; `meta.errors` records everything observed.
