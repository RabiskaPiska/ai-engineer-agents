# ruff: noqa: I001
"""bola-idor-testing -- cross-identity object access probing (BOLA / IDOR).

Usage (via the pack loader)::

    from common.loader import load_skill
    from common.transport import HttpTransport

    skill = load_skill("bola-idor-testing")
    result = skill.run(transport_a, transport_b, schema_map, max_tests=25, id_sample="1")
    # -> {"findings": [...], "tested": int, "skipped": int, "meta": {...}}

``transport_a`` is the owner identity, ``transport_b`` a DIFFERENT identity
(the auth difference is expressed via per-transport/per-call headers, e.g.
``HttpTransport(url, headers={"X-User-ID": "u2"})``).

Auto-probe construction (SPEC.md): one probe per OBJECT-typed root field that
takes exactly one required ``ID!`` argument. The probe asks for ``__typename``
plus up to 5 scalar fields of the target object so responses can be compared.
A finding fires ONLY when B receives a non-null object for A's id with a
matching ``id`` field or non-empty fields -- evidence for both responses is
attached. Public-by-design data can produce a false positive; confidence is
0.7 and the finding text says so.
"""
import sys, pathlib
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import re
from typing import Any

from common.findings import new_finding
from common.transport import Transport

__all__ = ["MAX_SCALAR_FIELDS", "probe", "run"]

MAX_SCALAR_FIELDS = 5
_SCALARS = frozenset({"Int", "Float", "String", "Boolean", "ID"})
_ROOT_TYPE_NAMES = ("query", "mutation", "query_root", "mutation_root",
                    "Query", "Mutation", "Root", "RootQuery", "RootMutation")
_FIELD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def probe(
    transport: Transport,
    query_template: str,
    id_field: str = "id",
    id_value: str = "1",
    headers: dict | None = None,
) -> dict:
    """Execute ``query_template`` (must declare ``$<id_field>: ID!``) with the id bound.

    Explicit-probe escape hatch per SPEC.md: callers may bypass auto-probe
    building and test any query template directly.
    """
    if not _FIELD_RE.match(id_field):
        raise ValueError(f"id_field must be a valid GraphQL name, got {id_field!r}")
    return transport.execute(query_template, variables={id_field: id_value}, headers=headers)


def _base_type_name(type_str: Any) -> str:
    """``[Order!]!`` -> ``Order``; unknown -> ''."""
    if not isinstance(type_str, str):
        return ""
    return type_str.replace("!", "").replace("[", "").replace("]", "").strip()


def _find_field_def(schema_map: dict, field_name: str) -> tuple[dict, dict] | None:
    """Locate (type, field) for a root field name, preferring canonical root types."""
    preferred: tuple[dict, dict] | None = None
    fallback: tuple[dict, dict] | None = None
    for t in schema_map.get("types") or []:
        if not isinstance(t, dict):
            continue
        for f in t.get("fields") or []:
            if isinstance(f, dict) and f.get("name") == field_name:
                pair = (t, f)
                if t.get("name") in _ROOT_TYPE_NAMES:
                    preferred = preferred or pair
                fallback = fallback or pair
    return preferred or fallback


def _root_field_names(schema_map: dict) -> list[str]:
    """Root field names from ``schema_map["roots"]``; else derived from the
    canonical root types (so a bare introspection ``schema_map`` works too)."""
    roots = schema_map.get("roots") or {}
    names: list[str] = []
    for role in ("query", "mutation"):
        names.extend(str(f) for f in (roots.get(role) or []))
    if names:
        return names
    derived: list[str] = []
    for t in schema_map.get("types") or []:
        if isinstance(t, dict) and t.get("name") in _ROOT_TYPE_NAMES:
            derived.extend(
                str(f["name"]) for f in (t.get("fields") or [])
                if isinstance(f, dict) and f.get("name")
            )
    return derived


def _build_query(field: str, target_type: dict | None) -> str:
    scalars: list[str] = []
    if isinstance(target_type, dict):
        for f in target_type.get("fields") or []:
            if _base_type_name(f.get("type")) in _SCALARS and f.get("name") not in scalars:
                scalars.append(str(f["name"]))
            if len(scalars) >= MAX_SCALAR_FIELDS:
                break
    if "id" not in scalars:
        scalars.insert(0, "id")  # requested but tolerated if absent (error -> skip)
    selection = " ".join(["__typename"] + scalars)
    return f"query BolaProbe($id: ID!) {{ {field}(id: $id) {{ {selection} }} }}"


def run(
    transport_a: Transport,
    transport_b: Transport,
    schema_map: dict | None,
    max_tests: int = 25,
    id_sample: str = "1",
    headers_a: dict | None = None,
    headers_b: dict | None = None,
) -> dict:
    """Probe object root fields with A's id as B; report cross-identity reads."""
    max_tests = max(0, int(max_tests))
    # Control run: the same transport object with the same per-call headers
    # cannot establish CROSS-identity access -- both probes return identical
    # data by construction, so a finding there is always a false positive.
    control_run = (
        transport_a is transport_b and (headers_a or None) == (headers_b or None)
    )
    if not isinstance(schema_map, dict):
        # Hostile/missing input: report honestly instead of crashing.
        return {
            "findings": [],
            "tested": 0,
            "skipped": 0,
            "meta": {
                "candidates": [],
                "skipped_reasons": [
                    "schema_map is missing or not a dict; no probes were derived"
                ],
                "max_tests": max_tests,
                "id_sample": id_sample,
                "control_run": control_run,
            },
        }
    target_types = {
        t.get("name"): t
        for t in (schema_map.get("types") or [])
        if isinstance(t, dict) and t.get("kind") == "OBJECT" and t.get("name")
    }
    root_fields: list[str] = _root_field_names(schema_map)

    tested = 0
    skipped = 0
    skipped_reasons: list[str] = []
    candidates: list[str] = []
    findings: list[dict] = []
    seq = 0

    for field_name in root_fields:
        if tested >= max_tests:
            break
        if not _FIELD_RE.match(field_name):
            continue
        defn = _find_field_def(schema_map, field_name)
        if defn is None:
            skipped += 1
            skipped_reasons.append(f"{field_name}: no field definition found in schema_map")
            continue
        _, fdef = defn
        args = fdef.get("args") or []
        if len(args) != 1:
            skipped += 1
            skipped_reasons.append(f"{field_name}: takes {len(args)} args, need exactly 1")
            continue
        if not str(args[0].get("type", "")).replace("!", "").startswith("ID"):
            skipped += 1
            skipped_reasons.append(f"{field_name}: single arg is {args[0].get('type')!r}, not ID")
            continue
        base = _base_type_name(fdef.get("type"))
        if not base or base not in target_types:
            skipped += 1
            skipped_reasons.append(
                f"{field_name}: return type {base or '?'!r} is not a known OBJECT type"
            )
            continue
        candidates.append(field_name)

        query = _build_query(field_name, target_types[base])
        response_a = probe(transport_a, query, "id", id_sample, headers=headers_a)
        if not isinstance(response_a, dict) or response_a.get("errors") \
                or not isinstance(response_a.get("data"), dict) \
                or response_a["data"].get(field_name) is None:
            skipped += 1
            skipped_reasons.append(f"{field_name}: owner probe failed "
                                   f"(unknown id {id_sample!r} or field error)")
            continue
        if tested >= max_tests:
            break
        tested += 1
        response_b = probe(transport_b, query, "id", id_sample, headers=headers_b)
        data_a = response_a["data"].get(field_name)
        data_b = response_b.get("data", {}).get(field_name) if isinstance(response_b, dict) else None

        if isinstance(data_b, dict) and data_b:
            # Finding condition per spec: non-null object with matching id or non-empty fields.
            same_id = (isinstance(data_a, dict) and data_a.get("id") is not None
                       and data_a.get("id") == data_b.get("id"))
            identical = data_a == data_b
            if control_run:
                skipped += 1
                skipped_reasons.append(
                    f"{field_name}: control run (transport_a is transport_b with equal "
                    "headers); cross-identity access cannot be established -- no finding"
                )
            elif same_id or identical or bool(data_b):
                seq += 1
                findings.append(new_finding(
                    vuln_class="BOLA",
                    seq=seq,
                    title=f"Cross-identity read on root field '{field_name}' (id={id_sample!r})",
                    severity="high",
                    confidence=0.7,
                    target=str(getattr(transport_b, "url", getattr(transport_a, "url", "local"))),
                    evidence={
                        "request": {"query": query, "variables": {"id": id_sample},
                                    "operation_name": "BolaProbe", "headers": headers_b},
                        "response": response_b,
                        "baseline": {
                            "request": {"query": query, "variables": {"id": id_sample},
                                        "operation_name": "BolaProbe", "headers": headers_a},
                            "response": response_a,
                        },
                    },
                    description=(
                        f"Identity B successfully read object '{field_name}(id: {id_sample!r})' "
                        "that identity A also resolves. The object type enforces no visible "
                        "ownership check on this field. Verify the data is actually "
                        "private to A before treating this as a confirmed BOLA "
                        "(public reference data would look identical)."
                    ),
                    impact="An authenticated attacker can enumerate object ids and read "
                           "resources belonging to other identities.",
                    proposed_fix={
                        "summary": "Enforce object-level ownership checks in the resolver/data layer.",
                        "config_or_code": (
                            "# Pseudocode per resolver:\n"
                            "obj = fetch(id); if obj.owner_id != ctx.user.id: "
                            "raise Forbidden  # or return None"
                        ),
                        "language": "pseudocode",
                        "references": [
                            "https://owasp.org/API-Security/editions/2023/en/0xa1-bola/",
                            "https://owasp.org/www-project-api-security/",
                        ],
                    },
                    detection={
                        "waf_rule": None,
                        "log_query": None,
                        "notes": "Correlate access logs: same object id requested by "
                                 "multiple distinct identities.",
                    },
                ))

    return {
        "findings": findings,
        "tested": tested,
        "skipped": skipped,
        "meta": {
            "candidates": candidates,
            "skipped_reasons": skipped_reasons,
            "max_tests": max_tests,
            "id_sample": id_sample,
            "control_run": control_run,
        },
    }
