"""Findings schema (fixed by SPEC.md) -- builders + validator.

``new_finding(...)`` builds and validates one finding. IDs are uuid-free and
deterministic: ``GQL-<CLASS>-<seq>`` where ``CLASS`` is the slugified
``vuln_class`` and ``seq`` is passed in by the caller.
"""
from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

__all__ = ["SEVERITY_ORDER", "new_finding", "slugify_class", "validate_finding"]

SEVERITY_ORDER: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}

_SEVERITIES = frozenset(SEVERITY_ORDER)
_ID_RE = re.compile(r"^GQL-[A-Za-z0-9-]+-[1-9][0-9]*$")
_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")

_REQUIRED_TOP = (
    "id", "title", "vuln_class", "severity", "confidence", "target",
    "timestamp", "evidence", "description", "impact", "proposed_fix", "detection",
)


def slugify_class(vuln_class: str) -> str:
    """``"alias abuse"`` -> ``"ALIAS-ABUSE"``; used inside deterministic ids."""
    slug = re.sub(r"[^A-Za-z0-9-]+", "-", str(vuln_class).strip()).strip("-").upper()
    return slug or "UNCLASSIFIED"


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def new_finding(
    *,
    vuln_class: str,
    seq: int,
    title: str,
    severity: str,
    confidence: float,
    target: str,
    evidence: dict,
    description: str,
    impact: str,
    proposed_fix: dict | None = None,
    detection: dict | None = None,
    timestamp: str | None = None,
) -> dict:
    """Build one finding dict per the SPEC.md schema and validate it.

    Raises ``ValueError`` if the constructed finding is invalid -- skills must
    never emit malformed findings.
    """
    if not isinstance(seq, int) or seq < 1:
        raise ValueError(f"seq must be a positive int, got {seq!r}")
    if severity not in _SEVERITIES:
        raise ValueError(f"severity must be one of {sorted(_SEVERITIES)}, got {severity!r}")
    if not vuln_class:
        raise ValueError("vuln_class must be a non-empty name")
    fix = proposed_fix if proposed_fix is not None else {
        "summary": "No remediation was proposed by the detecting skill.",
        "config_or_code": "", "language": "", "references": [],
    }
    det = detection if detection is not None else {
        "waf_rule": None, "log_query": None, "notes": None,
    }
    finding: dict[str, Any] = {
        "id": f"GQL-{slugify_class(vuln_class)}-{int(seq)}",
        "title": str(title),
        "vuln_class": str(vuln_class),
        "severity": severity,
        "confidence": float(confidence),
        "target": str(target),
        "timestamp": timestamp or _utc_now_iso(),
        "evidence": evidence,
        "description": str(description),
        "impact": str(impact),
        "proposed_fix": fix,
        "detection": det,
    }
    defects = validate_finding(finding)
    if defects:
        raise ValueError(f"invalid finding constructed: {defects}")
    return finding


def validate_finding(finding: dict) -> list[str]:
    """Return a list of schema defects; empty list means the finding is valid."""
    defects: list[str] = []
    if not isinstance(finding, dict):
        return ["finding is not a dict"]

    for key in _REQUIRED_TOP:
        if key not in finding:
            defects.append(f"missing key: {key}")
    if defects:
        return defects

    if not isinstance(finding["id"], str) or not _ID_RE.match(finding["id"]):
        defects.append(f"id must match GQL-<CLASS>-<n>, got {finding['id']!r}")
    if not isinstance(finding["title"], str) or not finding["title"].strip():
        defects.append("title must be a non-empty string")
    if not isinstance(finding["vuln_class"], str) or not finding["vuln_class"].strip():
        defects.append("vuln_class must be a non-empty string")
    if finding["severity"] not in _SEVERITIES:
        defects.append(f"severity must be one of {sorted(_SEVERITIES)}, got {finding['severity']!r}")
    conf = finding["confidence"]
    if not isinstance(conf, (int, float)) or isinstance(conf, bool) or not 0.0 <= float(conf) <= 1.0:
        defects.append(f"confidence must be a float in 0..1, got {conf!r}")
    if not isinstance(finding["target"], str) or not finding["target"].strip():
        defects.append("target must be a non-empty string")
    if not isinstance(finding["timestamp"], str) or not _TS_RE.match(finding["timestamp"]):
        defects.append(f"timestamp must be ISO-8601 Z like 2026-10-29T12:00:00Z, got {finding['timestamp']!r}")
    if not isinstance(finding["description"], str) or not finding["description"].strip():
        defects.append("description must be a non-empty string")
    if not isinstance(finding["impact"], str) or not finding["impact"].strip():
        defects.append("impact must be a non-empty string")

    evidence = finding["evidence"]
    if not isinstance(evidence, dict):
        defects.append("evidence must be a dict")
    else:
        request = evidence.get("request")
        if not isinstance(request, dict):
            defects.append("evidence.request must be a dict")
        else:
            for key in ("query", "variables", "operation_name", "headers"):
                if key not in request:
                    defects.append(f"evidence.request missing key: {key}")
        if "response" not in evidence:
            defects.append("evidence missing key: response")

    fix = finding["proposed_fix"]
    if not isinstance(fix, dict):
        defects.append("proposed_fix must be a dict")
    else:
        if not isinstance(fix.get("summary"), str) or not fix["summary"].strip():
            defects.append("proposed_fix.summary must be a non-empty string")
        for key in ("config_or_code", "language"):
            if not isinstance(fix.get(key), str):
                defects.append(f"proposed_fix.{key} must be a string")
        if not isinstance(fix.get("references"), list) or not all(
            isinstance(r, str) for r in fix["references"]
        ):
            defects.append("proposed_fix.references must be a list of strings")

    det = finding["detection"]
    if not isinstance(det, dict):
        defects.append("detection must be a dict")
    else:
        for key in ("waf_rule", "log_query", "notes"):
            value = det.get(key)
            if value is not None and not isinstance(value, str):
                defects.append(f"detection.{key} must be a string or None")

    return defects
