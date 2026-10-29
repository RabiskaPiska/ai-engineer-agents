"""custom-api-mcp — reference MCP server running async GraphQL test pipelines.

Tools:
    start_test(url, test_types) -> test_id
    get_status(test_id)
    get_results(test_id)
    verify_finding(test_id, finding_id)

A test is an in-process background job: ``start_test`` registers a job in a
module-level dict and spawns a daemon thread that runs the pack's skills as a
pipeline — schema fingerprinting -> introspection -> the selected tests among
bola / alias / batch / complexity / deep-nesting. Results are stored as
{"findings": [...], "meta": {...}} (the pack findings schema). The server
process is single-user by design; there is no persistence across restarts.

All skill/transport imports are lazy (inside functions) so this module
imports cleanly even while sibling SKILLS/ files are mid-write.
"""

import pathlib
import sys
import threading
import time
import uuid
from typing import Any

try:  # mcp 1.x (SPEC baseline)
    from mcp.server.fastmcp import FastMCP
except ImportError:  # mcp 2.x renamed FastMCP -> MCPServer
    from mcp.server.mcpserver import MCPServer as FastMCP

_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

mcp = FastMCP("custom-api-mcp")

_ALLOWED_TESTS = ("bola", "alias", "batch", "complexity", "deep-nesting")

_TESTS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def _load_skill(name: str):
    from common import loader  # lazy

    return loader.load_skill(name)


def _make_transport(url: str):
    from common.transport import HttpTransport  # lazy

    return HttpTransport(url, timeout_s=30.0)


def _first_root_field(roots: dict | None) -> str | None:
    fields = (roots or {}).get("query") or []
    return fields[0] if fields else None


def _run_pipeline(test_id: str, url: str, selected: list[str]) -> None:
    """Background worker: fingerprint -> introspection -> selected tests."""
    started = time.time()
    results: dict[str, Any] = {
        "findings": [],
        "meta": {"url": url, "steps": {}, "errors": [], "suspicions": []},
    }
    sources: dict[str, str] = {}

    def finish(status: str, error: str | None = None) -> None:
        results["meta"]["elapsed_ms"] = round((time.time() - started) * 1000, 1)
        with _LOCK:
            entry = _TESTS.get(test_id)
            if entry is not None:
                entry["status"] = status
                entry["results"] = results
                entry["sources"] = sources
                entry["finished_at"] = time.time()
                entry["error"] = error

    try:
        transport = _make_transport(url)
    except Exception as exc:  # noqa: BLE001 — pipeline must never die mid-run
        finish("error", f"transport setup failed: {exc!r}")
        return

    # Step 1: schema fingerprinting (always).
    try:
        skill = _load_skill("schema-fingerprinting")
        results["meta"]["steps"]["fingerprinting"] = skill.run(transport)
    except Exception as exc:  # noqa: BLE001 — one failing step never kills the run
        results["meta"]["errors"].append(f"fingerprinting: {exc!r}")

    # Step 2: introspection (always — later steps need the schema map).
    schema_map: dict | None = None
    roots: dict | None = None
    try:
        skill = _load_skill("introspection-enumeration")
        intro = skill.run(transport, full=True)
        results["meta"]["steps"]["introspection"] = {
            "introspection_enabled": intro.get("introspection_enabled"),
            "roots": intro.get("roots"),
        }
        schema_map = intro.get("schema_map")
        roots = intro.get("roots")
    except Exception as exc:  # noqa: BLE001 — one failing step never kills the run
        results["meta"]["errors"].append(f"introspection: {exc!r}")

    field = _first_root_field(roots)
    base_query = f"{{ {field} }}" if field else "{ __typename }"

    def collect(step: str, outcome: Any) -> None:
        """Store one skill's {"findings","meta"} outcome and index sources."""
        if not isinstance(outcome, dict):
            results["meta"]["errors"].append(
                f"{step}: unexpected result type {type(outcome).__name__}"
            )
            return
        results["meta"]["steps"][step] = outcome.get("meta", {})
        for i, f in enumerate(outcome.get("findings", []) or []):
            results["findings"].append(f)
            fid = f.get("id") or f"{step}-{i}"
            sources.setdefault(fid, step)

    # Step 3: the selected tests, each guarded so one failure never kills the run.
    for test_type in selected:
        try:
            if test_type == "bola":
                # Single-endpoint reference run: same transport on both sides.
                outcome = _load_skill("bola-idor-testing").run(
                    transport, transport, schema_map or {}, max_tests=25, id_sample="1"
                )
                if outcome.get("meta") is not None:
                    outcome["meta"]["note"] = (
                        "control run: transport_a is transport_b (single identity) — "
                        "cross-identity BOLA findings require two identity configs; "
                        "this step cannot produce a BOLA finding"
                    )
            elif test_type == "alias":
                if field is None:
                    results["meta"]["suspicions"].append(
                        "alias: skipped — no root query field discovered to target"
                    )
                    continue
                outcome = _load_skill("alias-abuse-testing").run(
                    transport, field, n=100
                )
            elif test_type == "batch":
                outcome = _load_skill("batch-abuse-testing").run(
                    transport, base_query, n=50
                )
            elif test_type == "complexity":
                outcome = _load_skill("complexity-dos-testing").run(
                    transport,
                    schema_map or {},
                    max_depth=20,
                    max_ops=100,
                    aggressive=False,
                )
            elif test_type == "deep-nesting":
                outcome = _load_skill("deep-nesting-testing").run(
                    transport, schema_map or {}, rounds=15
                )
            else:  # unreachable: start_test validates types
                continue
            collect(test_type, outcome)
        except Exception as exc:  # noqa: BLE001 — one failing step never kills the run
            results["meta"]["errors"].append(f"{test_type}: {exc!r}")
            results["meta"]["suspicions"].append(
                f"{test_type}: step errored; no findings were produced by it"
            )

    finish("complete")


@mcp.tool()
def start_test(url: str, test_types: list[str]) -> dict[str, Any]:
    """Start an async GraphQL security test pipeline against 'url'.

    'test_types' selects from: bola, alias, batch, complexity, deep-nesting.
    Fingerprinting and introspection always run first (later steps reuse the
    schema map). Returns {"test_id", "status": "queued"} or a friendly error
    dict. Results become available via get_results(test_id) once status is
    "complete".

    NOTE on "bola": cross-identity BOLA testing requires TWO identity configs
    (e.g. two different auth headers). This server runs against a single URL
    with a single identity, so the "bola" step always executes in CONTROL
    mode (transport_a is transport_b): it exercises the probes and reports
    skipped_reasons, but can never produce a BOLA finding. Run the
    bola-idor-testing skill directly with two transports/identities for a
    real cross-identity test.
    """
    if not url or not str(url).strip():
        return {"error": "'url' is required."}
    if not isinstance(test_types, list) or not test_types:
        return {
            "error": "'test_types' must be a non-empty list of: "
            + ", ".join(_ALLOWED_TESTS)
        }
    unknown = [t for t in test_types if t not in _ALLOWED_TESTS]
    if unknown:
        return {
            "error": f"unknown test type(s): {unknown}",
            "allowed": list(_ALLOWED_TESTS),
        }
    # de-duplicate, preserve order
    selected = list(dict.fromkeys(str(t) for t in test_types))
    test_id = uuid.uuid4().hex[:12]
    with _LOCK:
        _TESTS[test_id] = {
            "id": test_id,
            "url": url,
            "test_types": selected,
            "status": "running",
            "results": None,
            "sources": {},
            "error": None,
            "started_at": time.time(),
            "finished_at": None,
        }
    thread = threading.Thread(
        target=_run_pipeline,
        args=(test_id, url, selected),
        name=f"custom-api-mcp-{test_id}",
        daemon=True,
    )
    thread.start()
    return {"test_id": test_id, "status": "running", "url": url, "test_types": selected}


def _get_entry(test_id: str) -> dict[str, Any] | None:
    with _LOCK:
        return _TESTS.get(test_id)


@mcp.tool()
def get_status(test_id: str) -> dict[str, Any]:
    """Return the status of a started test: queued/running/complete/error."""
    entry = _get_entry(test_id)
    if entry is None:
        return {
            "error": f"unknown test_id '{test_id}' (registry is in-process "
            "and resets when the server restarts)."
        }
    return {
        "test_id": entry["id"],
        "url": entry["url"],
        "test_types": entry["test_types"],
        "status": entry["status"],
        "error": entry["error"],
        "started_at": entry["started_at"],
        "finished_at": entry["finished_at"],
    }


@mcp.tool()
def get_results(test_id: str) -> dict[str, Any]:
    """Return the full results of a completed test.

    Shape: {"findings": [...], "meta": {...}} — findings follow the pack's
    fixed findings schema; meta carries per-step metadata, errors and
    suspicions (suspicions are unproven observations, never fabricated
    findings). Returns a friendly error dict if the test is unknown or still
    running.
    """
    entry = _get_entry(test_id)
    if entry is None:
        return {"error": f"unknown test_id '{test_id}'."}
    if entry["status"] == "error":
        return {"error": f"test {test_id} failed: {entry['error']}"}
    if entry["status"] != "complete" or entry["results"] is None:
        return {
            "error": f"test {test_id} is not complete yet "
            f"(status: {entry['status']}); poll get_status()."
        }
    return dict(entry["results"])


@mcp.tool()
def verify_finding(test_id: str, finding_id: str) -> dict[str, Any]:
    """Re-run the single pipeline step that produced a finding and check
    whether it still reproduces.

    Returns {"finding", "reproduced": bool, "note"} — honest verification by
    re-execution, not a rubber stamp. If the originating step now errors,
    'reproduced' is None with the error attached.
    """
    entry = _get_entry(test_id)
    if entry is None:
        return {"error": f"unknown test_id '{test_id}'."}
    if entry["status"] != "complete":
        return {"error": f"test {test_id} is not complete (status: {entry['status']})."}
    results = entry["results"] or {}
    finding = next(
        (f for f in results.get("findings", []) if f.get("id") == finding_id), None
    )
    if finding is None:
        ids = [f.get("id") for f in results.get("findings", [])]
        return {
            "error": f"finding '{finding_id}' not found in test {test_id}.",
            "known_finding_ids": ids,
        }
    step = entry["sources"].get(finding_id)
    if step is None:
        return {
            "error": f"no source step recorded for finding '{finding_id}'; "
            "cannot re-verify honestly."
        }
    url = entry["url"]
    try:
        transport = _make_transport(url)
        # Re-run just the originating step with the same parameters used in
        # the pipeline (conservative caps, aggressive=False).
        if step == "bola":
            outcome = _load_skill("bola-idor-testing").run(
                transport, transport, {}, max_tests=25, id_sample="1"
            )
        elif step == "alias":
            field = _first_root_field(
                results["meta"]["steps"].get("introspection", {}).get("roots")
            )
            if field is None:
                return {
                    "finding": finding,
                    "reproduced": None,
                    "note": "cannot re-verify: root field no longer discoverable",
                }
            outcome = _load_skill("alias-abuse-testing").run(transport, field, n=100)
        elif step == "batch":
            outcome = _load_skill("batch-abuse-testing").run(
                transport, "{ __typename }", n=50
            )
        elif step == "complexity":
            outcome = _load_skill("complexity-dos-testing").run(
                transport, {}, max_depth=20, max_ops=100, aggressive=False
            )
        else:  # deep-nesting
            outcome = _load_skill("deep-nesting-testing").run(transport, {}, rounds=15)
        fresh = outcome.get("findings", []) or []
        reproduced = any(
            f.get("id") == finding_id or f.get("title") == finding.get("title")
            for f in fresh
        )
        return {
            "finding": finding,
            "reproduced": reproduced,
            "note": f"re-ran '{step}' step; {len(fresh)} finding(s) in fresh run.",
        }
    except Exception as exc:  # noqa: BLE001 — MCP tool boundary must not raise
        return {
            "finding": finding,
            "reproduced": None,
            "error": f"re-verification run failed: {exc!r}",
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")
