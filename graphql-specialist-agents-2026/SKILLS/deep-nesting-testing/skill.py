"""Deep-nesting / cyclic-query testing for GraphQL endpoints (SKILL 8).

Finds cyclic field chains in a ``schema_map`` (e.g. ``Query.config:Config``
where ``Config.parent:Config``), builds cyclic and fragment-nested queries,
and reports whether the server accepts nesting at the safety cap without any
depth-limit error.

API::

    find_cycles(schema_map)   # -> [["config", "parent"], ...]
    build_cyclic(cycle, 15)   # 15-level nested cyclic query
    run(transport, schema_map, rounds=15, max_depth=20, aggressive=False)

Usage::

    from common.loader import load_skill

    skill = load_skill("deep-nesting-testing")
    result = skill.run(transport, schema_map)
    # -> {"findings": [...], "meta": {"cycles_found": [...], ...}}

Safety: nesting never exceeds ``max_depth`` (default 20) unless the caller
passes ``aggressive=True`` explicitly, and no more than a handful of probe
queries are sent.
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

__all__ = ["build_cyclic", "find_cycles", "run"]

_DEPTH_KEYWORDS: tuple[str, ...] = (
    "depth",
    "complexity",
    "cost",
    "too deep",
    "nesting",
    "expensive",
)

_MAX_DFS_STEPS = 5000
_MAX_CYCLES = 20
_MAX_PROBE_CYCLES = 3


def _unwrap(type_str: object) -> tuple[str, bool]:
    """Return ``(named_type, is_list)`` for a type string like ``[Config!]!``."""
    text = str(type_str or "String").strip()
    is_list = text.startswith("[")
    return (text.strip("[]!").strip(), is_list)


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


def _fields_of(type_rec: dict | None) -> list[tuple[str, str]]:
    """``[(field_name, named_target_type), ...]`` for object-typed targets only."""
    if not isinstance(type_rec, dict):
        return []
    out: list[tuple[str, str]] = []
    for field in type_rec.get("fields", []) or []:
        if not isinstance(field, dict) or not field.get("name"):
            continue
        named, _ = _unwrap(field.get("type", ""))
        out.append((str(field["name"]), named))
    return out


def find_cycles(schema_map: dict) -> list[list[str]]:
    """Return cyclic field-name chains reachable from root (Query) fields.

    Each cycle starts with the root/entry field and lists one field per hop
    around the loop, e.g. ``["config", "parent"]`` for ``Query.config:Config``
    with ``Config.parent:Config``. Best-effort and bounded (dedup + caps); if
    no root-seeded cycle exists, object-seeded cycles (entry field may not be
    a root field) are reported as fallback.
    """
    if not isinstance(schema_map, dict):
        return []
    tindex = _type_index(schema_map)
    if not tindex:
        return []

    cycles: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    steps = {"n": 0}

    def record(cycle: list[str]) -> None:
        key = tuple(cycle)
        if key not in seen:
            seen.add(key)
            cycles.append(cycle)

    def dfs(type_name: str, path_fields: list[str], path_types: list[str]) -> None:
        if steps["n"] >= _MAX_DFS_STEPS or len(path_types) > 50:
            return
        for fname, target in _fields_of(tindex.get(type_name)):
            steps["n"] += 1
            if steps["n"] >= _MAX_DFS_STEPS:
                return
            if target in path_types:
                j = path_types.index(target)
                cycle = path_fields[max(j - 1, 0):] + [fname]
                record(cycle)
                continue  # keep exploring siblings; do not recurse into the loop
            if target in tindex:
                dfs(target, path_fields + [fname], path_types + [target])

    roots = (schema_map.get("roots") or {}).get("query") or []
    query_fields = dict(_fields_of(tindex.get("Query")))
    for root_name in roots:
        target = query_fields.get(str(root_name))
        if target is not None and target in tindex:
            # Invariant: path_types[-1] is the type we are currently inside;
            # path_fields[i] leads from path_types[i] to path_types[i + 1].
            dfs(target, [str(root_name)], ["Query", target])
    if not cycles:
        # Fallback: cycles not reachable from root fields (entry field may be
        # a non-root field; run() will report those probes honestly if they fail).
        for type_name in tindex:
            dfs(type_name, [], [type_name])
    return cycles[:_MAX_CYCLES]


def build_cyclic(cycle: list[str], rounds: int) -> str:
    """Return a query nesting the cycle *rounds* levels deep.

    ``cycle`` uses the compact ``find_cycles`` shape: ``cycle[0]`` is the
    entry field (from the root type) and ``cycle[1:]`` are the loop fields
    that repeat for every further level (a single-element cycle is repeated
    as-is). The innermost selection is ``{ __typename }`` so the query stays
    valid even when every loop field is object-typed.
    """
    if not cycle:
        raise ValueError("cycle must be non-empty")
    if rounds < 1:
        raise ValueError("rounds must be >= 1")
    if len(cycle) > 1:
        entry, loop = str(cycle[0]), [str(f) for f in cycle[1:]]
        fields = [entry] + [loop[i % len(loop)] for i in range(rounds - 1)]
    else:
        loop = [str(cycle[0])]
        fields = [loop[i % len(loop)] for i in range(rounds)]
    query = "__typename"
    for field in reversed(fields):
        query = f"{field} {{ {query} }}"
    return "query { " + query + " }"


def _fragment_query(cycle: list[str], tindex: dict[str, dict], rounds: int) -> str | None:
    """Linear fragment-chain variant (fragments must not spread cyclically).

    ``cycle[0]`` is the root entry field; ``cycle[1:]`` loop fields repeat for
    the remaining ``rounds - 1`` levels, split across ``rounds - 1`` fragments.
    Returns ``None`` when the variant cannot be built (including ``rounds < 2``
    and cycles without a root entry field).
    """
    if rounds < 2 or len(cycle) < 2:
        return None
    entry, loop = str(cycle[0]), [str(f) for f in cycle[1:]]
    query_fields = {f: t for f, t in _fields_of(tindex.get("Query"))}
    entry_type = query_fields.get(entry)
    if entry_type is None or entry_type not in tindex:
        return None
    lines = [f"query {{ {entry} {{ ...gq_c0 }} }}"]
    current = entry_type
    for i in range(rounds - 1):
        fname = loop[i % len(loop)]
        fields = dict(_fields_of(tindex.get(current)))
        target = fields.get(fname)
        if target is None or target not in tindex:
            return None
        if i < rounds - 2:
            lines.append(f"fragment gq_c{i} on {current} {{ {fname} {{ ...gq_c{i + 1} }} }}")
            current = target
        else:
            lines.append(f"fragment gq_c{i} on {current} {{ {fname} {{ __typename }} }}")
    return "\n".join(lines)


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
    rounds: int = 15,
    max_depth: int = 20,
    max_ops: int = 100,
    aggressive: bool = False,
) -> dict:
    """Probe with cyclic / fragment-nested queries at the safety cap.

    Returns ``{"findings": [...], "meta": {...}}``. A finding is produced when
    a cyclic query nested at/over ``max_depth`` levels is accepted with no
    depth-limit error. Nesting is clamped to ``max_depth`` unless
    ``aggressive=True``; ``max_ops`` bounds the total number of probe queries.
    """
    effective_rounds: int = int(rounds) if aggressive else min(int(rounds), int(max_depth))
    meta: dict = {
        "requested_rounds": rounds,
        "rounds_used": effective_rounds,
        "max_depth": max_depth,
        "max_ops": max_ops,
        "aggressive": bool(aggressive),
        "cycles_found": [],
        "probes": [],
        "suspicions": [],
    }
    findings: list[dict] = []
    if not isinstance(schema_map, dict):
        meta["suspicions"].append("schema_map is not a dict; no cycles were derived")
        return {"findings": findings, "meta": meta}

    cycles = find_cycles(schema_map)
    meta["cycles_found"] = cycles
    if not cycles:
        meta["suspicions"].append("no cyclic field chains found in schema_map")
        return {"findings": findings, "meta": meta}

    tindex = _type_index(schema_map)
    target = str(getattr(transport, "url", "unknown"))
    seq = 0
    budget = int(max_ops)
    if budget < 1:
        meta["suspicions"].append(f"max_ops={max_ops} < 1; no probes were sent")
        return {"findings": findings, "meta": meta}
    at_cap = effective_rounds >= int(max_depth)

    for cycle in cycles[:_MAX_PROBE_CYCLES]:
        if budget <= 0:
            meta["suspicions"].append("max_ops probe budget exhausted; remaining cycles skipped")
            break
        variants: list[tuple[str, str]] = [("nested", build_cyclic(cycle, effective_rounds))]
        fragment_query = _fragment_query(cycle, tindex, effective_rounds)
        if fragment_query is not None:
            variants.append(("fragments", fragment_query))
        else:
            meta["suspicions"].append(
                f"fragment variant unresolvable for cycle {cycle}; nested variant only"
            )
        for variant, query in variants:
            if budget <= 0:
                break
            budget -= 1
            response, elapsed, error = _timed_execute(transport, query)
            accepted: bool | None = None
            limit_hit = False
            response_bytes: int | None = None
            if error is not None:
                meta["suspicions"].append(
                    f"cycle {cycle} ({variant}) probe failed: {error}"
                )
            else:
                response_bytes = len(json.dumps(response, default=str).encode("utf-8"))
                messages = _error_messages(response)
                limit_hit = _mentions_depth_limit(messages)
                accepted = isinstance(response, dict) and "data" in response
            meta["probes"].append({
                "cycle": cycle,
                "variant": variant,
                "rounds": effective_rounds,
                "accepted": accepted,
                "limit_hit": limit_hit,
                "elapsed_ms": round(elapsed, 3),
                "response_bytes": response_bytes,
                "error": error,
            })
            if accepted and (at_cap or aggressive) and not limit_hit:
                seq += 1
                finding = new_finding(
                    seq=seq,
                    title=(
                        f"Server accepted a cyclic query nested {effective_rounds} "
                        f"levels deep without a depth-limit error"
                    ),
                    vuln_class="deep-nesting-dos",
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
                        f"The server executed a query following the cyclic field chain "
                        f"{cycle} nested {effective_rounds} levels "
                        f"({variant} variant) and returned data with no depth or nesting "
                        f"limit error. The effective depth limit is absent or at least "
                        f"{effective_rounds}."
                    ),
                    impact=(
                        "Unbounded recursion through cyclic types forces deep parser and "
                        "resolver recursion per request, enabling denial of service with "
                        "tiny payloads (also stresses fragment-based clients)."
                    ),
                    proposed_fix={
                        "summary": (
                            "Enforce a maximum query depth (and maximum fragment "
                            "nesting) before execution; reject queries beyond the limit "
                            "with a clear error."
                        ),
                        "config_or_code": (
                            "# example: depth check before execution\n"
                            "MAX_DEPTH = 10\n"
                            "if query_depth(document) > MAX_DEPTH:\n"
                            '    raise GraphQLError("Query exceeds maximum depth")'
                        ),
                        "language": "python",
                        "references": [
                            "https://graphql.org/learn/best-practices/",
                            "https://spec.graphql.org/",
                        ],
                    },
                    detection={
                        "waf_rule": (
                            "Flag GraphQL queries whose selection-set depth exceeds N "
                            "(e.g. 12) or whose fragment chain spans more than M "
                            "definitions."
                        ),
                        "log_query": (
                            "Log computed selection depth per request; alert when "
                            "depth > 12."
                        ),
                        "notes": (
                            "Cyclic probe accepted at the safety cap with no "
                            "depth/complexity keyword in any returned error."
                        ),
                    },
                )
                defects = validate_finding(finding)
                if defects:
                    meta["suspicions"].append(f"finding validation defects: {defects}")
                findings.append(finding)

    return {"findings": findings, "meta": meta}
