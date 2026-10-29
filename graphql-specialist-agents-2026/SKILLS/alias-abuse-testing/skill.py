# ruff: noqa: I001
"""alias-abuse-testing -- aliased-field query amplification (resource exhaustion).

Usage (via the pack loader)::

    from common.loader import load_skill
    from common.transport import HttpTransport

    skill = load_skill("alias-abuse-testing")
    result = skill.run(transport, field="__typename", n=100, max_ops=100)
    # -> {"findings": [...], "meta": {"accepted", "elapsed_ms", "response_bytes", ...}}

``build(n, field, args="")`` returns a query with ``n`` aliased copies of
``field`` (``a0: field ... a{n-1}: field``). ``run()`` sends it, measures
elapsed time + response size, and reports a finding ONLY when the server
actually executed >= n aliases (non-null results) with no limit/complexity
error. Unless ``aggressive=True``, the requested alias count is capped by
``max_ops`` (SPEC.md safety rule) -- ``meta.capped`` records when that happened.

``__typename`` is the ideal probe field: valid on any root type and scalar by
definition, so aliased results are always non-null.
"""
import sys, pathlib
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import json
import re
import time
from common.findings import new_finding
from common.transport import Transport

__all__ = ["build", "run"]

_FIELD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
# Heuristic limit-detection: honest, checked against the server's own wording.
_LIMIT_RE = re.compile(
    r"(?i)(too many|rate ?limit|complexit|max(imum)?[\s_-]*(aliases|fields|operations|nodes)"
    r"|aliases? (limit|exceeded)|exceeded)"
)


def build(n: int, field: str, args: str = "") -> str:
    """Build a query with ``n`` aliased copies of ``field`` (aliases a0..a{n-1})."""
    if not isinstance(n, int) or n < 1:
        raise ValueError(f"n must be a positive int, got {n!r}")
    if not _FIELD_RE.match(field):
        raise ValueError(f"field must be a valid GraphQL name, got {field!r}")
    selections = " ".join(f"a{i}: {field}{args}" for i in range(n))
    return f"query AliasAbuse {{ {selections} }}"


def _detect_limit_error(messages: list[str]) -> str | None:
    for message in messages:
        if _LIMIT_RE.search(message):
            return message
    return None


def run(
    transport: Transport,
    field: str,
    n: int = 100,
    max_ops: int = 100,
    aggressive: bool = False,
    args: str = "",
    headers: dict | None = None,
) -> dict:
    """Send an aliased query and measure acceptance, latency and response size."""
    if not isinstance(n, int) or n < 1:
        raise ValueError(f"n must be a positive int, got {n!r}")
    max_ops = max(1, int(max_ops))
    capped = not aggressive and n > max_ops
    effective_n = n if aggressive else min(n, max_ops)

    query = build(effective_n, field, args)
    start = time.perf_counter()
    try:
        response = transport.execute(query, headers=headers)
    except Exception as exc:  # noqa: BLE001 - transport/network failure, recorded never fabricated around
        return {
            "findings": [],
            "meta": {
                "accepted": False,
                "elapsed_ms": (time.perf_counter() - start) * 1000.0,
                "response_bytes": 0,
                "aliases_requested": effective_n,
                "aliases_executed": 0,
                "limit_error": None,
                "capped": capped,
                "suspicions": [f"probe failed: {type(exc).__name__}: {exc}"],
            },
        }
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    if not isinstance(response, dict):
        response = {}
    data = response.get("data")
    messages = [
        str(err.get("message", ""))
        for err in (response.get("errors") or [])
        if isinstance(err, dict)
    ]
    limit_error = _detect_limit_error(messages)

    aliases_executed = 0
    if isinstance(data, dict):
        aliases_executed = sum(1 for i in range(effective_n) if data.get(f"a{i}") is not None)
    accepted = isinstance(data, dict) and len(data) > 0 and limit_error is None
    try:
        response_bytes = len(json.dumps(response, default=str).encode("utf-8"))
    except (TypeError, ValueError):
        response_bytes = 0

    findings: list[dict] = []
    if accepted and aliases_executed >= effective_n:
        findings.append(new_finding(
            vuln_class="ALIAS-ABUSE",
            seq=1,
            title=f"Server executed {aliases_executed} aliased fields in one request with no limit",
            severity="medium",
            confidence=0.8,
            target=str(getattr(transport, "url", "local-transport")),
            evidence={
                "request": {"query": query, "variables": None,
                            "operation_name": "AliasAbuse", "headers": headers},
                "response": response,
            },
            description=(
                f"A single request containing {effective_n} aliased copies of '{field}' "
                f"was accepted and executed (all {aliases_executed} aliases returned "
                f"non-null) with no alias/complexity limit error. Response size was "
                f"{response_bytes} bytes in {elapsed_ms:.1f} ms. The factor is bounded "
                "by this probe's cap -- a real attacker can scale it further unless "
                "the server enforces a documented alias count."
            ),
            impact="Unauthenticated or cheap authenticated requests can amplify server "
                   "work (parsing, resolver execution, response serialization) by the "
                   "alias count, enabling resource-exhaustion DoS.",
            proposed_fix={
                "summary": "Limit the number of aliases per document and add query complexity/depth limits.",
                "config_or_code": (
                    "# graphql-js / Apollo:\n"
                    "// count Aliases in a custom validation rule, reject > N (e.g. 15)\n"
                    "# Hasura:\n"
                    "// set max_depth / max_node_count query limits per role"
                ),
                "language": "javascript",
                "references": [
                    "https://www.apollographql.com/docs/apollo-server/security/performance/",
                    "https://github.com/1Password/graphql-depth-limit",
                ],
            },
            detection={
                "waf_rule": None,
                "log_query": None,
                "notes": "Flag requests whose operation contains an unusually high alias count.",
            },
        ))

    return {
        "findings": findings,
        "meta": {
            "accepted": accepted,
            "elapsed_ms": elapsed_ms,
            "response_bytes": response_bytes,
            "aliases_requested": effective_n,
            "aliases_executed": aliases_executed,
            "limit_error": limit_error,
            "capped": capped,
            "suspicions": [],
        },
    }
