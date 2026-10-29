"""Report generation for GraphQL assessment findings (SKILL 10).

Turns a list of findings (the pack's standard finding schema) into a
Markdown report — executive summary with per-severity counts, per-finding
sections with fenced evidence blocks and a CVSS-qualitative band, a
remediation appendix, and a detection-rules appendix — or into a structured
dict (``fmt="json"``). Never crashes on empty or malformed input: an empty
finding list produces an honest "no findings" report.

API::

    cvss_qualitative("critical")  # -> "9.1-10.0"
    generate(findings, fmt="markdown", meta=None)  # -> str
    generate(findings, fmt="json", meta={"target": "..."})  # -> dict

Usage::

    from common.loader import load_skill

    skill = load_skill("report-generation")
    report_md = skill.generate(result["findings"], fmt="markdown")
"""
# ruff: noqa: I001
import sys, pathlib
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import json
from datetime import UTC, datetime

from common.findings import SEVERITY_ORDER

__all__ = ["cvss_qualitative", "generate"]

# CVSS-qualitative bands per the pack spec (critical band 9.1-10.0 as
# specified; the CVSS v3.1 standard prints 9.0-10.0).
_CVSS_BANDS: dict[str, str] = {
    "critical": "9.1-10.0",
    "high": "7.0-8.9",
    "medium": "4.0-6.9",
    "low": "0.1-3.9",
    "info": "0.0",
}

_KNOWN_SEVERITIES = ("critical", "high", "medium", "low", "info")

_EVIDENCE_RESPONSE_MAX_CHARS = 4000


def cvss_qualitative(severity: str) -> str:
    """Map a severity name to its CVSS-qualitative score band (or ``"n/a"``)."""
    return _CVSS_BANDS.get(str(severity).lower(), "n/a")


def _severity_rank(severity: str) -> int:
    """Higher rank = more severe; unknown severities rank lowest.

    Tolerates ``SEVERITY_ORDER`` being a severity -> rank mapping (where a
    *lower* value means more severe, e.g. ``{"critical": 0, ...}``), an
    ascending list, or a descending list starting with "critical".
    """
    sev = str(severity).lower()
    try:
        if isinstance(SEVERITY_ORDER, dict):
            return -int(SEVERITY_ORDER.get(sev, 100))
        items = [str(s).lower() for s in SEVERITY_ORDER]
        if items and items[0] == "critical":
            items = list(reversed(items))
        return items.index(sev)
    except (TypeError, ValueError, AttributeError):
        return -1


def _as_str(value: object) -> str:
    return str(value) if value is not None else "n/a"


def _fenced(code: object, language: str) -> str:
    text = str(code) if code not in (None, "") else "(none)"
    return f"```{language}\n{text}\n```"


def _json_block(value: object, max_chars: int = _EVIDENCE_RESPONSE_MAX_CHARS) -> str:
    try:
        text = json.dumps(value, indent=2, default=str)
    except (TypeError, ValueError):
        text = str(value)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n... (truncated)"
    return f"```json\n{text or '(none)'}\n```"


def _summary_counts(findings: list[dict]) -> dict[str, int]:
    counts = {sev: 0 for sev in _KNOWN_SEVERITIES}
    for finding in findings:
        sev = str(finding.get("severity", "info")).lower()
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def _finding_section(index: int, finding: dict) -> list[str]:
    sev = str(finding.get("severity", "info")).lower()
    evidence = finding.get("evidence") or {}
    request = evidence.get("request") or {}
    fix = finding.get("proposed_fix") or {}
    lines: list[str] = [
        (f"## {index}. {_as_str(finding.get('title'))} "
         f"[{_as_str(finding.get('id'))}]"),
        "",
        f"- **Severity:** {sev} (CVSS-qualitative band {cvss_qualitative(sev)})",
        f"- **Vulnerability class:** {_as_str(finding.get('vuln_class'))}",
        f"- **Confidence:** {_as_str(finding.get('confidence'))}",
        f"- **Target:** {_as_str(finding.get('target'))}",
        f"- **Detected:** {_as_str(finding.get('timestamp'))}",
        "",
        f"{_as_str(finding.get('description'))}",
        "",
        f"**Impact.** {_as_str(finding.get('impact'))}",
        "",
        "### Evidence",
        "",
        "**Request**",
        _fenced(request.get("query"), "graphql"),
        "",
    ]
    extras = {
        key: request.get(key)
        for key in ("variables", "operation_name", "headers")
        if request.get(key) is not None
    }
    if extras:
        lines += ["Request parameters", _json_block(extras), ""]
    lines += [
        "**Response**",
        _json_block(evidence.get("response")),
        "",
        "### Proposed fix",
        "",
        f"{_as_str(fix.get('summary'))}",
        "",
        _fenced(fix.get("config_or_code"), str(fix.get("language") or "text")),
        "",
    ]
    references = fix.get("references") or []
    if references:
        lines.append("References:")
        lines += [f"- {ref}" for ref in references]
        lines.append("")
    return lines


def run(
    transport: object | None = None,
    findings: list[dict] | None = None,
    fmt: str = "markdown",
    meta: dict | None = None,
) -> dict:
    """SPEC-standard ``run()`` entry point.

    Report generation does not probe a target, so ``transport`` is accepted
    (and ignored) for interface uniformity with the other nine skills.
    Returns the SPEC result shape: ``{"findings": [...], "meta": {...}}``
    where ``meta`` carries the rendered report.
    """
    report = generate(findings or [], fmt=fmt, meta=meta)
    return {
        "findings": list(findings or []),
        "meta": {"report": report, "fmt": fmt},
    }


def generate(findings: list[dict], fmt: str = "markdown", meta: dict | None = None) -> str | dict:
    """Render *findings* as a Markdown report (str) or structured JSON (dict).

    ``fmt`` is ``"markdown"`` or ``"json"``; anything else raises
    ``ValueError``. ``meta`` (optional) is echoed into the report as
    assessment context. An empty finding list yields an honest "no findings"
    report in both formats.
    """
    if fmt not in ("markdown", "json"):
        raise ValueError('fmt must be "markdown" or "json"')
    clean: list[dict] = [f for f in (findings or []) if isinstance(f, dict)]
    skipped = len(findings or []) - len(clean)
    ordered = sorted(
        clean, key=lambda f: -_severity_rank(str(f.get("severity", "info")).lower())
    )
    counts = _summary_counts(clean)
    generated = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    if fmt == "json":
        return {
            "generated": generated,
            "meta": dict(meta) if meta else {},
            "summary": {"total": len(clean), "by_severity": counts},
            "findings": ordered,
        }

    lines: list[str] = [
        "# GraphQL Security Assessment Report",
        "",
        f"_Generated: {generated}_",
        "",
        "## Executive summary",
        "",
        f"**{len(clean)}** finding(s) in total.",
        "",
        "| Severity | Count | CVSS-qualitative band |",
        "|---|---|---|",
    ]
    lines += [
        f"| {sev} | {counts[sev]} | {cvss_qualitative(sev)} |" for sev in _KNOWN_SEVERITIES
    ]
    lines.append("")
    if skipped:
        lines.append(
            f"_Note: {skipped} malformed item(s) in the input were not dicts and "
            f"were excluded from this report._"
        )
        lines.append("")
    if meta:
        lines += ["## Assessment context", "", _json_block(meta), ""]

    if not clean:
        lines += [
            "## Findings",
            "",
            ("**No findings were produced by this assessment.** This is an honest "
             "empty result: either no probe met its finding criteria, or no probes "
             "were run. Absence of findings is not evidence of absence of "
             "vulnerabilities."),
            "",
        ]
    else:
        lines.append("## Findings")
        lines.append("")
        for index, finding in enumerate(ordered, 1):
            lines += _finding_section(index, finding)

    lines.append("## Appendix A — Remediation summary")
    lines.append("")
    if clean:
        for finding in ordered:
            fix = finding.get("proposed_fix") or {}
            lines.append(
                f"- **{_as_str(finding.get('id'))}** {_as_str(finding.get('title'))}: "
                f"{_as_str(fix.get('summary'))}"
            )
    else:
        lines.append("None required — no findings were recorded.")
    lines.append("")

    lines.append("## Appendix B — Detection rules")
    lines.append("")
    if clean:
        for finding in ordered:
            detection = finding.get("detection") or {}
            lines.append(
                f"- **{_as_str(finding.get('id'))}** "
                f"WAF rule: {_as_str(detection.get('waf_rule'))}"
            )
            lines.append(
                f"  - Log query: {_as_str(detection.get('log_query'))}"
            )
            if detection.get("notes"):
                lines.append(f"  - Notes: {detection['notes']}")
    else:
        lines.append("None produced — no findings were recorded.")
    lines.append("")

    return "\n".join(lines)
