# ruff: noqa: I001
"""schema-fingerprinting -- engine + feature fingerprinting (max 6 probe requests).

Usage (via the pack loader)::

    from common.loader import load_skill
    from common.transport import HttpTransport

    skill = load_skill("schema-fingerprinting")
    result = skill.run(HttpTransport("http://127.0.0.1:4000/graphql"))
    # -> {"engine_candidates": [...], "features": {...}, "findings": [], "meta": {...}}

The probe set (5 HTTP requests total, hard cap 6):
  1. ``{ __typename }``                 -- sanity: is this a GraphQL endpoint at all?
  2. misspelled field                   -- validation-error wording + "Did you mean"
  3. ``{ __schema { queryType { name } } }`` -- introspection on/off
  4. malformed query (``query {``)      -- parser wording
  5. batch body via ``execute_raw``     -- list body accepted?

Engine hints are HEURISTIC message-matching (inspired by graphw00f's public
technique) with honest, deliberately low confidences; when no signal matches,
``engine_candidates`` is empty rather than guessed.
"""
import sys, pathlib
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import re
from typing import Any

from common.transport import Transport

__all__ = ["MAX_PROBES", "run"]

MAX_PROBES = 6

_DID_YOU_MEAN_RE = re.compile(
    r"Did you mean (?P<alts>(?:'[^']+'|\"[^\"]+\")"
    r"(?: or (?:'[^']+'|\"[^\"]+\"))*)\?"
)

_PROBE_SANITY = "{ __typename }"
# Two unknown fields per probe: one far-miss (validation wording) and one
# near-miss ("usr" is close to the near-universal "user", so a suggestion
# should fire whenever the engine offers suggestions at all).
_PROBE_MISSPELLED = "{ zzz_no_such_field_qq7x usr }"
_PROBE_INTROSPECTION = "{ __schema { queryType { name } } }"
_PROBE_SYNTAX = "query {"
_PROBE_BATCH = [
    {"query": "{ __typename }", "operationName": None},
    {"query": "{ __typename }", "operationName": None},
]


def _suggestions(message: str) -> list[str]:
    match = _DID_YOU_MEAN_RE.search(message)
    if match is None:
        return []
    # graphql-js quotes with ", graphql-core with ' -- accept both.
    return [alt.strip("'\"") for alt in match.group("alts").split(" or ")]


def _error_messages(response: Any) -> list[str]:
    if not isinstance(response, dict):
        return []
    errors = response.get("errors")
    if not isinstance(errors, list):
        return []
    return [str(err.get("message", "")) for err in errors if isinstance(err, dict)]


def _engine_hints(messages: list[str]) -> list[dict[str, Any]]:
    """Heuristic engine identification from error wording. Honest + low-confidence."""
    joined = "\n".join(messages).lower()
    hints: list[dict[str, Any]] = []
    evidence_map: list[tuple[str, str]] = []

    if "did you mean" in joined and "cannot query field" in joined:
        evidence_map.append((
            "graphql-js reference family (GraphQL.js / graphql-core / Apollo Server / Graphene)",
            'validation wording "Cannot query field ... Did you mean ..." (reference-implementation style)',
        ))
    if "validation error of type" in joined:
        evidence_map.append(("AWS AppSync", 'validation wording "Validation error of type ..."'))
    if "not found in type" in joined and ("query_root" in joined or "mutation_root" in joined
                                          or "subscription_root" in joined):
        evidence_map.append(("Hasura GraphQL Engine", 'wording "not found in type: query_root" style'))
    if "syntax error" in joined and "expected" in joined:
        evidence_map.append((
            "graphql-js parser family (GraphQL.js / graphql-core)",
            'parser wording "Syntax Error ... Expected ..." (reference-implementation style)',
        ))

    for engine, evidence in evidence_map:
        # Deliberately modest confidences: wording similarity is a hint, not proof.
        confidence = 0.8 if engine in ("AWS AppSync", "Hasura GraphQL Engine") else 0.45
        hints.append({"engine": engine, "confidence": confidence, "evidence": evidence})
    hints.sort(key=lambda hint: hint["confidence"], reverse=True)
    return hints


def run(transport: Transport, headers: dict | None = None) -> dict:
    """Fingerprint the endpoint using at most 6 probe requests (5 by default)."""
    probe_log: list[dict[str, Any]] = []
    all_messages: list[str] = []
    suggestions_seen: list[str] = []
    notes_suspicions: list[str] = []

    def send(label: str, query: str | None = None, body: dict | list | None = None) -> Any:
        if len(probe_log) >= MAX_PROBES:
            return None
        request = body if body is not None else {"query": query}
        try:
            response = transport.execute_raw(body) if body is not None else transport.execute(
                query or "", headers=headers
            )
        except Exception as exc:  # noqa: BLE001 - transport/network failure, recorded never fabricated around
            probe_log.append({
                "label": label, "request": request,
                "response": None, "error": f"{type(exc).__name__}: {exc}",
            })
            notes_suspicions.append(f"{label} probe failed: {type(exc).__name__}: {exc}")
            return None
        probe_log.append({"label": label, "request": request, "response": response})
        msgs = _error_messages(response)
        all_messages.extend(msgs)
        for msg in msgs:
            suggestions_seen.extend(_suggestions(msg))
        return response

    sanity = send("sanity", _PROBE_SANITY)
    send("misspelled-field", _PROBE_MISSPELLED)
    introspection_resp = send("introspection", _PROBE_INTROSPECTION)
    send("syntax-error", _PROBE_SYNTAX)
    batch_resp = send("batch-probe", body=_PROBE_BATCH)

    # -- features ------------------------------------------------------------
    field_suggestions: bool | None = None
    if suggestions_seen:
        field_suggestions = True
    elif any(("cannot query field" in m.lower() or "not found in type" in m.lower()
              or "validation error of type" in m.lower()) for m in all_messages):
        field_suggestions = False  # validation ran but offered no suggestions

    introspection: bool | None = None
    if isinstance(introspection_resp, dict):
        data = introspection_resp.get("data")
        if isinstance(data, dict) and isinstance(data.get("__schema"), dict):
            introspection = True
        elif introspection_resp.get("errors"):
            joined = "\n".join(_error_messages(introspection_resp)).lower()
            introspection = False if ("introspection" in joined or "__schema" in joined) else None

    batch: bool | None = None
    if isinstance(batch_resp, list):
        batch = True
    elif isinstance(batch_resp, dict):
        batch = False  # a list body must yield a list response to count as supported

    # -- sanity note ---------------------------------------------------------
    notes: list[str] = []
    if sanity is not None and not (
        isinstance(sanity, dict) and isinstance(sanity.get("data"), dict)
    ):
        notes.append("endpoint did not answer a plain { __typename } query -- "
                     "it may not be a GraphQL endpoint at all")

    return {
        "engine_candidates": _engine_hints(all_messages),
        "features": {
            "field_suggestions": field_suggestions,
            "batch": batch,
            "introspection": introspection,
        },
        "findings": [],
        "meta": {
            "probes_sent": len(probe_log),
            "probe_budget": MAX_PROBES,
            "probe_log": probe_log,
            "notes": notes,
            "suspicions": notes_suspicions,
        },
    }
