"""Complexity / DoS probing for GraphQL endpoints (SKILL 7).

Derives costly queries from a ``schema_map`` (longest object-field chains and
high-fanout list fields), sends them, and reports whether the server accepts
max-cap queries without any depth/complexity limit error.

Builders::

    build_deep(["user", "orders", "id"], 6)   # 6-level nested query
    build_fanout("users(first: 5)", 100)      # 100 aliased copies

Usage::

    from common.loader import load_skill

    skill = load_skill("complexity-dos-testing")
    result = skill.run(transport, schema_map)
    # -> {"findings": [...], "meta": {"probes": [...], ...}}

Safety: probes never exceed ``max_depth`` (default 20) nesting levels or
``max_ops`` (default 100) aliases unless ``aggressive=True`` is passed
explicitly, in which case an additional 2x-cap fan-out probe and a 2x-cap
deep chain are derived.
"""
# ruff: noqa: I001
import sys, pathlib
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import json
import time

from common.errors import GraphQLErrorEx, retry
from common.findings import new_finding, validate_finding

__all__ = ["build_deep", "build_fanout", "run"]

# Keywords whose presence in an error message suggests a depth/complexity limit.
_DEPTH_KEYWORDS: tuple[str, ...] = (
    "depth",
    "complexity",
    "cost",
    "too deep",
    "nesting",
    "expensive",
)

_SCALAR_TYPES = ("Int", "Float", "String", "Boolean", "ID")


def build_deep(field_chain: list[str], depth: int) -> str:
    """Nest *field_chain* *depth* levels deep (cycling the chain if longer).

    The innermost field is rendered bare, so the chain's last element should
    be a scalar-bearing leaf (an object-typed bare leaf makes the query
    invalid GraphQL). Field entries may include arguments, e.g.
    ``'user(id: "1")'``. Note: when ``depth > len(field_chain)`` the chain is
    cycled, which is only valid if the chain genuinely loops; callers should
    usually pass ``depth == len(field_chain)`` (``run`` does).
    """
    if not field_chain:
        raise ValueError("field_chain must be non-empty")
    if depth < 1:
        raise ValueError("depth must be >= 1")
    fields = [str(field_chain[i % len(field_chain)]) for i in range(depth)]
    query = fields[-1]
    for field in reversed(fields[:-1]):
        query = f"{field} {{ {query} }}"
    return "query { " + query + " }"


def build_fanout(field: str, n: int) -> str:
    """Return a query aliasing *field* *n* times (``a0: field a1: field ...``)."""
    if n < 1:
        raise ValueError("n must be >= 1")
    if not isinstance(field, str) or not field.strip():
        raise ValueError("field must be a non-empty string")
    aliases = " ".join(f"a{i}: {field}" for i in range(n))
    return "query { " + aliases + " }"


def _unwrap(type_str: object) -> tuple[str, bool]:
    """Return ``(named_type, is_list)`` for a type string like ``[Order!]!``."""
    text = str(type_str or "String").strip()
    is_list = text.startswith("[")
    named = text.strip("[]!").strip()
    return (named, is_list)


def _type_index(schema_map: dict) -> dict[str, dict]:
    """Index object-typed records by name.

    Tolerates missing ``kind`` and both ``"Object"`` / ``"OBJECT"`` spellings
    (introspection outputs vary); scalars/unions are excluded.
    """
    index: dict[str, dict] = {}
    for rec in schema_map.get("types", []) or []:
        if not isinstance(rec, dict) or not rec.get("name"):
            continue
        kind = str(rec.get("kind") or "OBJECT").upper()
        if kind == "OBJECT":
            index[str(rec["name"])] = rec
    return index


def _fields_of(type_rec: dict | None) -> list[dict]:
    if not isinstance(type_rec, dict):
        return []
    return [f for f in type_rec.get("fields", []) or [] if isinstance(f, dict)]


def _field_args_snippet(field: dict) -> str | None:
    """Render fillable required args, e.g. ``(first: 3)``.

    Returns ``None`` when a required arg cannot be safely filled (unknown /
    object / input-object type). Optional args are omitted.
    """
    parts: list[str] = []
    for arg in field.get("args", []) or []:
        if not isinstance(arg, dict):
            return None
        raw = str(arg.get("type", ""))
        required = raw.endswith("!") and arg.get("default") is None
        if not required:
            continue
        value = _scalar_value(arg)
        if value is None:
            return None
        parts.append(f"{arg.get('name')}: {value}")
    return f"({', '.join(parts)})" if parts else ""


def _scalar_value(arg: dict) -> str | None:
    raw = str(arg.get("type", "String"))
    named, is_list = _unwrap(raw)
    default = arg.get("default")
    if default is not None:
        # Introspection may render defaults as strings ("10") â€” render them
        # per the arg's named type so Int/Float/Boolean stay unquoted.
        try:
            if named == "Int":
                value = str(int(default))
            elif named == "Float":
                value = str(float(default))
            elif named == "Boolean":
                value = "true" if str(default).lower() in ("true", "1") else "false"
            elif named in ("String", "ID"):
                value = json.dumps(default)
            else:
                value = json.dumps(default)  # best effort (e.g. enums)
        except (TypeError, ValueError):
            value = None
        if value is None:
            return None
        return f"[{value}]" if is_list else value
    if named == "Int":
        value = "1"
    elif named == "Float":
        value = "1.0"
    elif named == "Boolean":
        value = "true"
    elif named in ("String", "ID"):
        value = '"1"'
    else:
        return None
    return f"[{value}]" if is_list else value


def _deepest_chain(root_field: dict | None, root_name: str,
                   tindex: dict[str, dict], max_depth: int) -> list[str]:
    """Greedy longest fillable object-chain from one Query root field.

    The chain ends in a scalar leaf (or ``__typename``) and never exceeds
    ``max_depth`` entries. Returns ``[]`` when the root cannot be probed.
    """
    args = _field_args_snippet(root_field) if root_field else ""
    if root_field is not None and args is None:
        return []
    chain = [f"{root_name}{args or ''}"]
    current = _unwrap(root_field.get("type", ""))[0] if root_field else None
    while current in tindex and len(chain) < max_depth - 1:
        extension: tuple[str, str] | None = None
        for field in _fields_of(tindex[current]):
            field_args = _field_args_snippet(field)
            if field_args is None:
                continue
            named, _ = _unwrap(field.get("type", ""))
            if named in tindex:  # object-typed (list or single) â€” nestable
                extension = (f"{field['name']}{field_args}", named)
                break
        if extension is None:
            break
        chain.append(extension[0])
        current = extension[1]
    if current in tindex:
        leaf = "__typename"
        for field in _fields_of(tindex[current]):
            named, is_list = _unwrap(field.get("type", ""))
            if not is_list and named in _SCALAR_TYPES:
                leaf = str(field["name"])
                break
        chain.append(leaf)
    return chain


def _longest_chains(schema_map: dict, tindex: dict[str, dict],
                    max_depth: int, limit: int = 3) -> list[list[str]]:
    roots = (schema_map.get("roots") or {}).get("query") or []
    query_fields = {f.get("name"): f for f in _fields_of(tindex.get("Query"))}
    if not roots:
        roots = list(query_fields)
    chains: list[list[str]] = []
    for root_name in roots:
        chain = _deepest_chain(query_fields.get(root_name), str(root_name),
                               tindex, max_depth)
        if len(chain) >= 2 and chain not in chains:
            chains.append(chain)
    chains.sort(key=len, reverse=True)
    return chains[:limit]


def _root_list_fields(tindex: dict[str, dict]) -> list[str]:
    """Root Query fields returning lists, with fillable args (fanout targets)."""
    out: list[str] = []
    for field in _fields_of(tindex.get("Query")):
        _, is_list = _unwrap(field.get("type", ""))
        field_args = _field_args_snippet(field)
        if is_list and field_args is not None:
            out.append(f"{field['name']}{field_args}")
    return out


def _error_messages(response: object) -> list[str]:
    if not isinstance(response, dict):
        return []
    errors = response.get("errors")
    if not isinstance(errors, list):
        return []
    messages: list[str] = []
    for err in errors:
        if isinstance(err, dict):
            messages.append(str(err.get("message", "")))
        elif err is not None:
            messages.append(str(err))
    return [m for m in messages if m]


def _mentions_depth_limit(messages: list[str]) -> bool:
    lowered = [m.lower() for m in messages]
    return any(keyword in message for message in lowered for keyword in _DEPTH_KEYWORDS)


def _timed_execute(transport: object, query: str) -> tuple[object, float, str | None]:
    """Execute one query; prefer ``transport.last_elapsed_ms``, else local timer."""
    start = time.perf_counter()
    try:
        # backoff_s=0 keeps failure paths fast (SPEC: no long sleeps in tests).
        response = retry(lambda: transport.execute(query), backoff_s=0.0)
    except GraphQLErrorEx as exc:
        return None, (time.perf_counter() - start) * 1000.0, f"GraphQLErrorEx: {exc.message}"
    except Exception as exc:  # noqa: BLE001 - tool boundary, failure detail preserved in return
        return None, (time.perf_counter() - start) * 1000.0, f"{type(exc).__name__}: {exc}"
    transport_ms = getattr(transport, "last_elapsed_ms", None)
    if isinstance(transport_ms, (int, float)) and transport_ms > 0:
        elapsed = float(transport_ms)
    else:
        elapsed = (time.perf_counter() - start) * 1000.0
    return response, elapsed, None


def run(
    transport: object,
    schema_map: dict,
    max_depth: int = 20,
    max_ops: int = 100,
    aggressive: bool = False,
) -> dict:
    """Probe the endpoint with derived max-cap complexity queries.

    Returns ``{"findings": [...], "meta": {...}}``. A finding is produced per
    probe that the server accepts at/over its safety cap with no
    depth/complexity limit error. Probes never exceed the caps unless
    ``aggressive=True``.
    """
    meta: dict = {
        "max_depth": max_depth,
        "max_ops": max_ops,
        "aggressive": bool(aggressive),
        "chains_used": [],
        "fanout_field": None,
        "probes": [],
        "suspicions": [],
    }
    findings: list[dict] = []
    if not isinstance(schema_map, dict):
        meta["suspicions"].append("schema_map is not a dict; no probes were derived")
        return {"findings": findings, "meta": meta}

    tindex = _type_index(schema_map)
    if not tindex:
        meta["suspicions"].append(
            "schema_map contains no object type records; deep-chain derivation degraded"
        )

    chains = _longest_chains(schema_map, tindex, int(max_depth))
    meta["chains_used"] = chains
    fanout_candidates = _root_list_fields(tindex)
    meta["fanout_field"] = fanout_candidates[0] if fanout_candidates else None
    if not chains:
        meta["suspicions"].append("no fillable root chains derived; deep probes skipped")
    elif max(len(c) for c in chains) < int(max_depth):
        meta["suspicions"].append(
            f"deepest derivable chain ({max(len(c) for c in chains)}) is shorter than "
            f"max_depth ({max_depth}); deep probes ran below the cap"
        )
    if not fanout_candidates:
        meta["suspicions"].append(
            "no root list fields with fillable args; fanout probe skipped"
        )

    if int(max_ops) < 1:
        meta["suspicions"].append(f"max_ops={max_ops} < 1; no probes were sent")
        return {"findings": findings, "meta": meta}

    probes: list[tuple[str, str, int, bool]] = []  # (kind, query, cap_used, at_cap)
    for chain in chains:
        # depth == len(chain): derived chains are valid as-is; cycling an
        # acyclic chain would produce an invalid query.
        probes.append(("deep", build_deep(chain, len(chain)), len(chain),
                       len(chain) >= int(max_depth)))
    if aggressive:
        for chain in _longest_chains(schema_map, tindex, 2 * int(max_depth), limit=1):
            if len(chain) > int(max_depth):
                probes.append(("deep-2x", build_deep(chain, len(chain)),
                               len(chain), True))
    if fanout_candidates:
        field = fanout_candidates[0]
        probes.append(("fanout", build_fanout(field, int(max_ops)), int(max_ops), True))
        if aggressive:
            probes.append(("fanout-2x", build_fanout(field, 2 * int(max_ops)),
                           2 * int(max_ops), True))
    # Each probe is one operation; keep total operations sent within max_ops.
    probes = probes[:int(max_ops)]

    target = str(getattr(transport, "url", "unknown"))
    seq = 0
    for kind, query, cap_used, at_cap in probes:
        response, elapsed, error = _timed_execute(transport, query)
        accepted: bool | None = None
        limit_hit = False
        response_bytes: int | None = None
        if error is not None:
            meta["suspicions"].append(f"{kind} probe failed: {error}")
        else:
            response_bytes = len(json.dumps(response, default=str).encode("utf-8"))
            messages = _error_messages(response)
            limit_hit = _mentions_depth_limit(messages)
            accepted = isinstance(response, dict) and "data" in response
        meta["probes"].append({
            "kind": kind,
            "cap_used": cap_used,
            "at_cap": at_cap,
            "accepted": accepted,
            "limit_hit": limit_hit,
            "elapsed_ms": round(elapsed, 3),
            "response_bytes": response_bytes,
            "error": error,
        })
        if accepted and at_cap and not limit_hit:
            seq += 1
            finding = new_finding(
                seq=seq,
                title=(
                    f"Server accepted a {kind} complexity probe at cap "
                    f"({cap_used} levels/aliases) without a complexity limit error"
                ),
                vuln_class="complexity-dos",
                severity="high",
                confidence=0.7,
                target=target,
                evidence={
                    "request": {
                        "query": query,
                        "variables": None,
                        "operation_name": None,
                        "headers": None,
                    },
                    "response": response,
                },
                description=(
                    f"The server executed a {'deeply nested' if kind.startswith('deep') else 'fanout'} "
                    f"query at the safety cap ({cap_used} "
                    f"{'nesting levels' if kind.startswith('deep') else 'aliased fields'}) and returned "
                    f"data with no depth/complexity/cost limit error. Queries at or above "
                    f"this size are accepted, so the effective query-cost limit is absent "
                    f"or higher than the cap."
                ),
                impact=(
                    "Without depth/complexity limits, a single hand-crafted query can "
                    "force disproportionate resolver execution and response construction, "
                    "enabling low-bandwidth denial of service."
                ),
                proposed_fix={
                    "summary": (
                        "Enforce a maximum query depth and/or cost/complexity budget "
                        "before execution (e.g. graphql-depth-limit / query-cost "
                        "analysis), sized to legitimate client needs."
                    ),
                    "config_or_code": (
                        "# graphql-core example\n"
                        "from graphql import validate, depth_limit_ast  # or a custom rule\n"
                        "errors = validate(schema, document, depth_rule(max_depth=10))"
                    ),
                    "language": "python",
                    "references": [
                        "https://graphql.org/learn/best-practices/",
                        "https://spec.graphql.org/",
                    ],
                },
                detection={
                    "waf_rule": (
                        "Flag GraphQL queries whose selection-set depth exceeds N (e.g. 12) "
                        "or that contain more than M aliased root fields (e.g. 50)."
                    ),
                    "log_query": (
                        "Log computed query depth/complexity per request; alert when a "
                        "single request's depth > 12 or alias count > 50."
                    ),
                    "notes": (
                        "Probe accepted at the safety cap with no depth/complexity keyword "
                        "in any returned error message."
                    ),
                },
            )
            defects = validate_finding(finding)
            if defects:
                meta["suspicions"].append(f"finding validation defects: {defects}")
            findings.append(finding)

    return {"findings": findings, "meta": meta}
