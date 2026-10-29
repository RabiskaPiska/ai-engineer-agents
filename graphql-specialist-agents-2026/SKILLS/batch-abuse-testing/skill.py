"""Batch-abuse testing for GraphQL endpoints (SKILL 6).

Sends a JSON-array batch of identical GraphQL operations through
``Transport.execute_raw`` (batch = list body per the pack transport protocol)
and reports whether the server accepts the batch without any size-limit
error — a classic DoS amplification vector (one HTTP request executing N
operations).

Usage::

    from common.loader import load_skill

    skill = load_skill("batch-abuse-testing")
    result = skill.run(transport, "query { me { id } }", n=50)
    # -> {"findings": [...], "meta": {"batch_accepted": ..., ...}}

Builder::

    ops = skill.build(5, "query { me { id } }")  # 5 op dicts for one batch

Safety: ``run`` never sends more than ``max_ops`` (default 100) operations
unless ``aggressive=True`` is passed explicitly by the caller.
"""
# ruff: noqa: I001
import sys, pathlib
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import json

from common.errors import GraphQLErrorEx, retry
from common.findings import new_finding, validate_finding

__all__ = ["build", "run"]

# Keywords whose presence in an error message suggests a batch/size limit fired.
_LIMIT_KEYWORDS: tuple[str, ...] = (
    "batch",
    "too many",
    "limit",
    "size",
    "operations",
    "max ",
)


def build(n: int, query: str) -> list[dict]:
    """Return *n* copies of *query* as batch operation dicts.

    Each op has the standard single-operation shape
    ``{"query": <query>, "variables": None}``; the returned list is the
    JSON-array request body for ``Transport.execute_raw``.
    """
    if not isinstance(n, int) or n < 1:
        raise ValueError("n must be an int >= 1")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    return [{"query": query, "variables": None} for _ in range(n)]


def _error_messages(response: object) -> list[str]:
    """Extract human-readable error messages from a single or batch response."""
    messages: list[str] = []
    items: list[object] = response if isinstance(response, list) else [response]
    for item in items:
        if not isinstance(item, dict):
            continue
        errors = item.get("errors")
        if not isinstance(errors, list):
            continue
        for err in errors:
            if isinstance(err, dict):
                messages.append(str(err.get("message", "")))
            elif err is not None:
                messages.append(str(err))
    return [m for m in messages if m]


def _mentions_limit(messages: list[str]) -> bool:
    lowered = [m.lower() for m in messages]
    return any(keyword in message for message in lowered for keyword in _LIMIT_KEYWORDS)


def run(
    transport: object,
    query: str,
    n: int = 50,
    max_ops: int = 100,
    aggressive: bool = False,
) -> dict:
    """Send a batch of *n* identical *query* ops and assess batch handling.

    Returns ``{"findings": [...], "meta": {...}}``. A finding is produced only
    when a batch of >= 2 ops is accepted and no batch/size-limit error is
    observed. If the transport cannot handle a list body, the result is an
    honest "unsupported batch" meta with no findings — never a fabricated one.
    """
    effective_n: int = int(n) if aggressive else min(int(n), int(max_ops))
    meta: dict = {
        "requested_n": n,
        "ops_sent": effective_n,
        "cap_applied": effective_n != int(n),
        "max_ops": max_ops,
        "aggressive": bool(aggressive),
        "batch_accepted": None,
        "ops_success": None,
        "response_bytes": None,
        "unsupported_batch": False,
        "limit_errors": [],
        "suspicions": [],
    }
    if effective_n < 1:
        meta["suspicions"].append("effective batch size < 1; nothing was sent")
        return {"findings": [], "meta": meta}

    ops = build(effective_n, query)
    try:
        # backoff_s=0 keeps failure paths fast (SPEC: no long sleeps in tests);
        # GraphQLErrorEx wraps the underlying error after the retry attempts.
        response = retry(lambda: transport.execute_raw(ops), backoff_s=0.0)
    except GraphQLErrorEx as exc:
        cause = exc.__cause__
        if isinstance(cause, (TypeError, AttributeError)):
            meta["unsupported_batch"] = True
            meta["suspicions"].append(
                "transport raised on execute_raw(list); batch support could not be verified"
            )
        else:
            meta["suspicions"].append(f"execute_raw failed: {exc.message}")
        return {"findings": [], "meta": meta}
    except (TypeError, AttributeError):
        meta["unsupported_batch"] = True
        meta["suspicions"].append(
            "transport raised on execute_raw(list); batch support could not be verified"
        )
        return {"findings": [], "meta": meta}
    except Exception as exc:  # noqa: BLE001 - transport/network failure, recorded never fabricated around
        meta["suspicions"].append(f"execute_raw failed: {type(exc).__name__}: {exc}")
        return {"findings": [], "meta": meta}

    meta["response_bytes"] = len(json.dumps(response, default=str).encode("utf-8"))
    messages = _error_messages(response)
    meta["limit_errors"] = [m for m in messages if _mentions_limit([m])]

    accepted: bool = False
    if isinstance(response, list):
        meta["batch_accepted"] = True
        per_op = [r for r in response if isinstance(r, dict)]
        meta["ops_success"] = sum(
            1 for r in per_op if r.get("data") is not None and not r.get("errors")
        )
        accepted = len(per_op) >= 1
    elif isinstance(response, dict):
        accepted = ("data" in response) or ("errors" in response)
        meta["batch_accepted"] = accepted
        meta["ops_success"] = int(
            accepted
            and response.get("data") is not None
            and not response.get("errors")
        )
        if accepted:
            meta["suspicions"].append(
                "server answered a list batch with a single JSON object; "
                "per-op results unavailable"
            )
    else:
        meta["batch_accepted"] = False
        meta["suspicions"].append(
            f"unexpected execute_raw response type: {type(response).__name__}"
        )

    findings: list[dict] = []
    if accepted and effective_n >= 2 and not meta["limit_errors"]:
        success = meta["ops_success"]
        finding = new_finding(
            seq=1,
            title=(
                f"GraphQL batch of {effective_n} operations accepted "
                f"without a size limit"
            ),
            vuln_class="batch-abuse",
            severity="medium",
            confidence=0.8,
            target=str(getattr(transport, "url", "unknown")),
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
                f"The server accepted a JSON-array batch of {effective_n} identical "
                f"operations and returned {success} successful per-op responses with "
                f"no batch-size or limit error. The probe was capped at "
                f"max_ops={max_ops} (aggressive=False); larger batch sizes were not "
                f"tested, so the server's actual limit may be lower than any value "
                f"above {effective_n}."
            ),
            impact=(
                "Unbounded request batching lets a single HTTP request execute many "
                "operations, amplifying backend load (CPU, database, resolver fan-out) "
                "and enabling cheap denial-of-service or brute-force amplification."
            ),
            proposed_fix={
                "summary": (
                    "Cap operations per batch (e.g. 10-25) and reject or split larger "
                    "batches; additionally apply per-request cost limits."
                ),
                "config_or_code": (
                    'if isinstance(body, list) and len(body) > 25:\n'
                    '    raise GraphQLError("Too many operations in batch request")'
                ),
                "language": "javascript",
                "references": [
                    "https://spec.graphql.org/",
                    "https://graphql.org/learn/best-practices/",
                ],
            },
            detection={
                "waf_rule": (
                    "Flag POST /graphql request bodies that parse as JSON arrays with "
                    "more than N elements (e.g. N=25)."
                ),
                "log_query": (
                    "Count GraphQL operations per HTTP request; alert when "
                    "operations_per_request > 25."
                ),
                "notes": (
                    "Batch body contained identical operations; response returned "
                    "per-op results with no size-limit error message."
                ),
            },
        )
        defects = validate_finding(finding)
        if defects:
            meta["suspicions"].append(f"finding validation defects: {defects}")
        findings.append(finding)

    if effective_n != int(n):
        meta["suspicions"].append(
            f"requested n={n} reduced to {effective_n} by the max_ops safety cap "
            f"(aggressive=False)"
        )
    return {"findings": findings, "meta": meta}
