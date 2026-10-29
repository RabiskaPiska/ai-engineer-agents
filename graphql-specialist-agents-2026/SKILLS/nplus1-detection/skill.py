"""N+1 query pattern detection for GraphQL endpoints (SKILL 9).

TIMING-HEURISTIC ONLY: compares the wall-clock time of one list query against
the average time of *n* equivalent single-item queries and flags a
disproportionate ratio â€” consistent with, but not proof of, an N+1 resolver
pattern. Findings are capped at confidence 0.6 and state the heuristic nature
explicitly.

Usage::

    from common.loader import load_skill

    skill = load_skill("nplus1-detection")
    result = skill.run(
        transport,
        list_query='query { users { id } }',
        single_query_template='query { user(id: "{id}") { id } }',
        n=10,
        threshold_ratio=3.0,
    )
    # -> {"findings": [...], "meta": {"ratio": ..., "t_list_ms": ..., ...}}

Timing prefers ``transport.last_elapsed_ms`` (``HttpTransport``); for
transports without it (e.g. ``MapTransport``) a local ``time.perf_counter``
measurement around ``execute()`` is used, and the source is recorded in
``meta.timing_source``.
"""
# ruff: noqa: I001
import sys, pathlib
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import math
import time
from collections.abc import Callable

from common.errors import GraphQLErrorEx, retry
from common.findings import new_finding, validate_finding

__all__ = ["run"]

_MAX_RATIO_RECORDED = 1_000_000.0  # keep meta JSON-friendly when avg is ~0


def _timed_call(transport: object, execute: Callable[[], dict]) -> tuple[object, float, str | None, str]:
    """Run *execute* once; return (response, elapsed_ms, error, timing_source)."""
    start = time.perf_counter()
    try:
        # backoff_s=0 keeps failure paths fast (SPEC: no long sleeps in tests).
        response = retry(execute, backoff_s=0.0)
    except GraphQLErrorEx as exc:
        return None, (time.perf_counter() - start) * 1000.0, f"GraphQLErrorEx: {exc.message}", "perf_counter"
    except Exception as exc:  # noqa: BLE001 - tool boundary, failure detail preserved in return
        return None, (time.perf_counter() - start) * 1000.0, f"{type(exc).__name__}: {exc}", "perf_counter"
    transport_ms = getattr(transport, "last_elapsed_ms", None)
    if isinstance(transport_ms, (int, float)) and transport_ms > 0:
        return response, float(transport_ms), None, "transport.last_elapsed_ms"
    return response, (time.perf_counter() - start) * 1000.0, None, "perf_counter"


def _error_messages(response: object) -> list[str]:
    if not isinstance(response, dict) or not isinstance(response.get("errors"), list):
        return []
    out: list[str] = []
    for err in response["errors"]:
        if isinstance(err, dict):
            out.append(str(err.get("message", "")))
        elif err is not None:
            out.append(str(err))
    return [m for m in out if m]


def run(
    transport: object,
    list_query: str,
    single_query_template: str,
    n: int = 10,
    threshold_ratio: float = 3.0,
) -> dict:
    """Compare list-query timing against *n* single-item queries.

    ``single_query_template`` must contain one ``{id}`` placeholder, which is
    substituted with sample ids ``"1" .. "n"``. ``ratio = t_list /
    avg(t_singles)``; a finding is produced ONLY when ``ratio >=
    threshold_ratio``, with severity "low" and confidence capped at 0.6, and
    the finding text states it is a timing heuristic.

    Returns ``{"findings": [...], "meta": {...}}``; ``meta["ratio"]`` holds the
    measured ratio (``None`` when it could not be computed).
    """
    meta: dict = {
        "n_requested": n,
        "n_measured": 0,
        "threshold_ratio": threshold_ratio,
        "t_list_ms": None,
        "t_singles_ms": [],
        "ratio": None,
        "timing_source": [],
        "list_errors": [],
        "single_errors": [],
        "suspicions": [],
    }
    if not isinstance(list_query, str) or not list_query.strip():
        meta["suspicions"].append("list_query must be a non-empty string")
        return {"findings": [], "meta": meta}
    if not isinstance(single_query_template, str) or "{id}" not in single_query_template:
        meta["suspicions"].append(
            "single_query_template must be a non-empty string containing '{id}'"
        )
        return {"findings": [], "meta": meta}

    list_response, t_list, error, source = _timed_call(
        transport, lambda: transport.execute(list_query)
    )
    meta["timing_source"].append(source)
    if error is not None:
        meta["suspicions"].append(f"list query failed: {error}")
        return {"findings": [], "meta": meta}
    meta["t_list_ms"] = round(t_list, 3)
    meta["list_errors"] = _error_messages(list_response)

    singles: list[float] = []
    for sample_id in (str(i) for i in range(1, int(n) + 1)):
        query = single_query_template.replace("{id}", sample_id)
        _, t_single, err, src = _timed_call(transport, lambda q=query: transport.execute(q))
        if src not in meta["timing_source"]:
            meta["timing_source"].append(src)
        if err is not None:
            meta["single_errors"].append(err)
            continue
        singles.append(t_single)
        meta["t_singles_ms"].append(round(t_single, 3))

    meta["n_measured"] = len(singles)
    if not singles:
        meta["suspicions"].append(
            f"no successful single-item measurements (attempted {int(n)}); "
            f"ratio not computable"
        )
        return {"findings": [], "meta": meta}
    if meta["single_errors"]:
        meta["suspicions"].append(
            f"{len(meta['single_errors'])} of {int(n)} single queries failed; "
            f"ratio computed from successful ones only"
        )

    avg_single = sum(singles) / len(singles)
    if avg_single > 0:
        ratio: float = t_list / avg_single
    elif t_list > 0:
        ratio = float("inf")
    else:
        ratio = 0.0
    if math.isinf(ratio):
        meta["ratio"] = _MAX_RATIO_RECORDED
        meta["suspicions"].append(
            "average single-query time was 0 ms; ratio recorded at the "
            f"{_MAX_RATIO_RECORDED:.0f} ceiling"
        )
    else:
        meta["ratio"] = round(ratio, 3)

    findings: list[dict] = []
    if ratio >= float(threshold_ratio):
        finding = new_finding(
            seq=1,
            title="Possible N+1 query pattern (timing heuristic)",
            vuln_class="nplus1",
            severity="low",
            confidence=0.6,
            target=str(getattr(transport, "url", "unknown")),
            evidence={
                "request": {
                    "query": list_query,
                    "variables": None,
                    "operation_name": None,
                    "headers": None,
                },
                "response": list_response,
            },
            description=(
                "TIMING HEURISTIC, NOT PROOF: the list query took "
                f"{t_list:.1f} ms while {len(singles)} equivalent single-item queries "
                f"averaged {avg_single:.1f} ms (ratio {meta['ratio']}x, threshold "
                f"{threshold_ratio}x). This is consistent with an N+1 resolver pattern "
                "(one backend call per list item), but may equally reflect payload "
                "size, caching behaviour, or server load. Confirm with resolver-level "
                "tracing before acting."
            ),
            impact=(
                "If genuine, list resolvers issue one backend call per item, so latency "
                "grows linearly with list size â€” degraded response times and higher "
                "backend load under normal traffic."
            ),
            proposed_fix={
                "summary": (
                    "Batch the per-item backend lookups with a DataLoader-style "
                    "loader (batch + cache within one request)."
                ),
                "config_or_code": (
                    "# graphql-core / aiodataloader sketch\n"
                    "from aiodataloader import DataLoader\n"
                    "loader = DataLoader(batch_load_fn)  # one batched call per request\n"
                    "author = await loader.load(author_id)"
                ),
                "language": "python",
                "references": [
                    "https://github.com/graphql/dataloader",
                    "https://graphql.org/learn/best-practices/",
                ],
            },
            detection={
                "waf_rule": None,
                "log_query": None,
                "notes": (
                    "Evidence is timing-only; confirm with resolver tracing (Apollo "
                    "tracing, OpenTelemetry spans) showing repeated identical backend "
                    "queries within one GraphQL request."
                ),
            },
        )
        defects = validate_finding(finding)
        if defects:
            meta["suspicions"].append(f"finding validation defects: {defects}")
        findings.append(finding)

    return {"findings": findings, "meta": meta}
