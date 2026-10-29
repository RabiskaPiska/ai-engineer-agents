# ruff: noqa: I001
"""introspection-enumeration -- full schema extraction with honest fallbacks.

Usage (via the pack loader)::

    from common.loader import load_skill
    from common.transport import HttpTransport

    skill = load_skill("introspection-enumeration")
    result = skill.run(HttpTransport("http://127.0.0.1:4000/graphql"))
    # -> {"introspection_enabled": bool, "schema_map": {...}, "roots": {...},
    #     "findings": [], "meta": {"strategy": "full|minimal|mined|blocked", ...}}

Fallback chain (SPEC.md):
  1. full standard introspection query
  2. minimal introspection query (for servers that choke on directives /
     includeDeprecated / deep ofType nesting)
  3. suggestion-mining: harvest "Did you mean" errors for real field names
  4. if everything is blocked, report ``introspection_enabled=False`` honestly
     with an empty schema map -- never fabricate schema content.
"""
import sys, pathlib
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import re
from typing import Any

from common.transport import Transport

__all__ = ["MINING_PROBES", "run"]

MINING_PROBES = 8

_TYPE_REF = "kind name ofType { kind name ofType { kind name ofType { kind name } } }"

_FULL_QUERY = (
    "query IntrospectionQuery { __schema {"
    " queryType { name } mutationType { name } subscriptionType { name }"
    " types { kind name description"
    f"   fields(includeDeprecated: true) {{ name description"
    f"     args {{ name description defaultValue type {{ {_TYPE_REF} }} }}"
    f"     type {{ {_TYPE_REF} }} }}"
    f"   inputFields {{ name defaultValue type {{ {_TYPE_REF} }} }}"
    "   enumValues { name }"
    "   interfaces { kind name }"
    "   possibleTypes { kind name } }"
    "   directives { name description locations"
    f"     args {{ name defaultValue type {{ {_TYPE_REF} }} }} }}"
    " } }"
)

_MINIMAL_QUERY = (
    "query MiniIntrospection { __schema {"
    " queryType { name } mutationType { name } subscriptionType { name }"
    " types { kind name"
    f"   fields {{ name type {{ {_TYPE_REF} }}"
    f"     args {{ name type {{ kind name ofType {{ kind name }} }} }} }} }}"
    " } }"
)

_DID_YOU_MEAN_RE = re.compile(
    r"Did you mean (?P<alts>(?:'[^']+'|\"[^\"]+\")"
    r"(?: or (?:'[^']+'|\"[^\"]+\"))*)\?"
)


def _quote_strip(alt: str) -> str:
    return alt.strip("'\"")
_MINING_SEEDS = ("user", "post", "item", "order", "node", "account", "me", "email")


def _type_str(ref: Any) -> str:
    """Serialize a nested type ref (kind/name/ofType) to readable form, e.g. [Order!]!."""
    if not isinstance(ref, dict):
        return "?"
    kind = ref.get("kind")
    name = ref.get("name")
    of = ref.get("ofType")
    if kind == "NON_NULL":
        return f"{_type_str(of)}!"
    if kind == "LIST":
        return f"[{_type_str(of)}]"
    return str(name) if name else str(kind or "?")


def _error_messages(response: Any) -> list[str]:
    if not isinstance(response, dict) or not isinstance(response.get("errors"), list):
        return []
    return [str(err.get("message", "")) for err in response["errors"] if isinstance(err, dict)]


def _extract_schema(response: Any) -> tuple[dict | None, list[str]]:
    messages = _error_messages(response)
    if isinstance(response, dict):
        data = response.get("data")
        if isinstance(data, dict) and isinstance(data.get("__schema"), dict):
            return data["__schema"], messages
    return None, messages


def _build_schema_map(schema: dict) -> tuple[dict, dict]:
    types_out: list[dict] = []
    fields_by_type: dict[str, list[dict]] = {}
    for t in schema.get("types") or []:
        if not isinstance(t, dict):
            continue
        name = t.get("name") or ""
        if name.startswith("__"):
            continue
        fields = [
            {
                "name": f.get("name"),
                "type": _type_str(f.get("type")),
                "args": [
                    {
                        "name": a.get("name"),
                        "type": _type_str(a.get("type")),
                        "default": a.get("defaultValue"),
                    }
                    for a in (f.get("args") or [])
                    if isinstance(a, dict)
                ],
            }
            for f in (t.get("fields") or [])
            if isinstance(f, dict)
        ]
        types_out.append({"kind": t.get("kind"), "name": name, "fields": fields})
        fields_by_type[name] = fields

    roots: dict[str, list[str]] = {"query": [], "mutation": [], "subscription": []}
    for role, key in (("query", "queryType"), ("mutation", "mutationType"),
                      ("subscription", "subscriptionType")):
        root_ref = schema.get(key) or {}
        root_name = root_ref.get("name") if isinstance(root_ref, dict) else None
        if root_name in fields_by_type:
            roots[role] = [f["name"] for f in fields_by_type[root_name]]
    return {"types": types_out}, roots


def _mine_via_suggestions(transport: Transport, headers: dict | None,
                          suspicions: list[str]) -> tuple[list[str], int]:
    """Harvest real root field names from 'Did you mean' validation errors."""
    found: dict[str, str] = {}
    probes = 0
    for seed in _MINING_SEEDS:
        if probes >= MINING_PROBES:
            break
        probes += 1
        probe_word = seed if not seed.endswith("x") else seed + "y"
        try:
            response = transport.execute(f"{{ {probe_word}_zzz }}", headers=headers)
        except Exception as exc:  # noqa: BLE001 - transport/network failure, recorded never fabricated around
            suspicions.append(
                f"mining probe '{probe_word}_zzz' failed: {type(exc).__name__}: {exc}"
            )
            continue  # probe lost; remaining seeds still get their chance
        for message in _error_messages(response):
            match = _DID_YOU_MEAN_RE.search(message)
            if match is None:
                continue
            for alt in match.group("alts").split(" or "):
                field = _quote_strip(alt)
                if field and field not in found:
                    found[field] = message
    return list(found), probes


def run(transport: Transport, full: bool = True, headers: dict | None = None) -> dict:
    """Extract the schema map. Falls back honestly; never fabricates schema content."""
    errors: list[str] = []
    suspicions: list[str] = []
    probes_sent = 0
    schema: dict | None = None
    strategy = "blocked"

    if full:
        probes_sent += 1
        try:
            schema, errs = _extract_schema(transport.execute(_FULL_QUERY, headers=headers))
        except Exception as exc:  # noqa: BLE001 - transport/network failure, recorded never fabricated around
            schema, errs = None, []
            suspicions.append(f"full introspection probe failed: {type(exc).__name__}: {exc}")
        if schema is not None:
            strategy = "full"
        errors.extend(errs)

    if schema is None:
        probes_sent += 1
        try:
            schema, errs = _extract_schema(transport.execute(_MINIMAL_QUERY, headers=headers))
        except Exception as exc:  # noqa: BLE001 - transport/network failure, recorded never fabricated around
            schema, errs = None, []
            suspicions.append(f"minimal introspection probe failed: {type(exc).__name__}: {exc}")
        if schema is not None:
            strategy = "minimal"
        errors.extend(errs)

    if schema is not None:
        schema_map, roots = _build_schema_map(schema)
        return {
            "introspection_enabled": True,
            "schema_map": schema_map,
            "roots": roots,
            "findings": [],
            "meta": {
                "strategy": strategy,
                "errors": errors,
                "probes_sent": probes_sent,
                "suspicions": suspicions,
            },
        }

    # Introspection blocked: try suggestion-mining before giving up.
    try:
        mined_fields, mining_probes = _mine_via_suggestions(transport, headers, suspicions)
    except Exception as exc:  # noqa: BLE001 - transport/network failure, recorded never fabricated around
        mined_fields, mining_probes = [], 0
        suspicions.append(f"suggestion-mining failed: {type(exc).__name__}: {exc}")
    probes_sent += mining_probes
    if mined_fields:
        strategy = "mined"
        schema_map = {
            "types": [
                {
                    "kind": "mined",
                    "name": "Query(mined)",
                    "fields": [{"name": f, "type": None, "args": []} for f in mined_fields],
                }
            ]
        }
        roots = {"query": list(mined_fields), "mutation": [], "subscription": []}
        notes = ("introspection is blocked; fields below come from 'Did you mean' "
                 "validation errors and their types are unknown (never fabricated)")
    else:
        strategy = "blocked"
        schema_map = {"types": []}
        roots = {"query": [], "mutation": [], "subscription": []}
        notes = ("introspection is blocked and no field suggestions were observed; "
                 "schema contents are unknown")

    return {
        "introspection_enabled": False,
        "schema_map": schema_map,
        "roots": roots,
        "findings": [],
        "meta": {
            "strategy": strategy,
            "errors": errors,
            "probes_sent": probes_sent,
            "notes": notes,
            "suspicions": suspicions,
        },
    }
