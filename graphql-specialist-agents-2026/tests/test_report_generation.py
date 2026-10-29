"""report-generation: formats, severity ordering, CVSS bands, honest empty."""
from __future__ import annotations

import json

import pytest

from common.findings import new_finding
from common.loader import load_skill


def _finding(vuln_class: str, seq: int, severity: str, title: str) -> dict:
    return new_finding(
        vuln_class=vuln_class,
        seq=seq,
        title=title,
        severity=severity,
        confidence=0.8,
        target="http://127.0.0.1:4000/graphql",
        evidence={
            "request": {
                "query": "{ __typename }",
                "variables": None,
                "operation_name": None,
                "headers": None,
            },
            "response": {"data": {"__typename": "Query"}},
        },
        description="Demonstration finding for report tests.",
        impact="Demonstration impact.",
        proposed_fix={
            "summary": "Do the safe thing.",
            "config_or_code": "# example\nMAX = 10",
            "language": "python",
            "references": ["https://graphql.org/learn/best-practices/"],
        },
        detection={"waf_rule": "flag deep queries", "log_query": None, "notes": None},
    )


def test_cvss_qualitative_bands():
    skill = load_skill("report-generation")
    assert skill.cvss_qualitative("critical") == "9.1-10.0"
    assert skill.cvss_qualitative("high") == "7.0-8.9"
    assert skill.cvss_qualitative("medium") == "4.0-6.9"
    assert skill.cvss_qualitative("low") == "0.1-3.9"
    assert skill.cvss_qualitative("info") == "0.0"
    assert skill.cvss_qualitative("unknown-sev") == "n/a"


def test_markdown_report_ordering_and_sections():
    skill = load_skill("report-generation")
    critical = _finding("bola", 1, "critical", "Critical issue")
    low = _finding("nplus1", 1, "low", "Low issue")
    report = skill.generate([low, critical], fmt="markdown", meta={"target": "demo"})

    assert report.startswith("# GraphQL Security Assessment Report")
    assert "## Executive summary" in report
    # severity ordering: critical section appears before the low one
    assert report.index("Critical issue") < report.index("Low issue")
    # per-finding evidence + CVSS band + appendices
    assert "9.1-10.0" in report
    assert "0.1-3.9" in report
    assert "```graphql" in report
    assert "Appendix A" in report and "Appendix B" in report
    assert "Assessment context" in report
    assert "| critical | 1 |" in report and "| low | 1 |" in report


def test_json_report_structure():
    skill = load_skill("report-generation")
    critical = _finding("bola", 1, "critical", "Critical issue")
    info = _finding("alias-abuse", 1, "info", "Info issue")
    report = skill.generate([info, critical], fmt="json", meta={"target": "demo"})
    assert isinstance(report, dict)
    assert report["summary"]["total"] == 2
    assert report["summary"]["by_severity"]["critical"] == 1
    assert report["summary"]["by_severity"]["info"] == 1
    assert report["findings"][0]["severity"] == "critical"  # ordered
    assert report["meta"] == {"target": "demo"}
    assert report["generated"].endswith("Z")


def test_empty_findings_honest_report():
    skill = load_skill("report-generation")
    markdown = skill.generate([], fmt="markdown")
    assert "No findings were produced by this assessment" in markdown
    assert "not evidence of absence" in markdown
    assert "None required" in markdown and "None produced" in markdown
    js = skill.generate([], fmt="json")
    assert js["summary"]["total"] == 0 and js["findings"] == []


def test_invalid_fmt_raises():
    skill = load_skill("report-generation")
    with pytest.raises(ValueError):
        skill.generate([], fmt="html")


def test_run_wrapper_returns_spec_shape():
    skill = load_skill("report-generation")
    finding = _finding("bola", 1, "high", "A finding")
    result = skill.run(transport=None, findings=[finding], fmt="json")
    assert set(result) == {"findings", "meta"}
    assert result["findings"] == [finding]
    assert result["meta"]["fmt"] == "json"
    rendered = result["meta"]["report"]
    assert isinstance(rendered, dict)  # json fmt -> dict report
    json.dumps(rendered)  # must be JSON-serializable
