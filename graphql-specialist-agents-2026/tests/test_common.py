"""common/: findings validator, retry helper, SEVERITY_ORDER, skill loader."""
from __future__ import annotations

import pytest

from common.errors import GraphQLErrorEx, retry
from common.findings import SEVERITY_ORDER, new_finding, validate_finding
from common.loader import load_skill

ALL_SKILLS = [
    "schema-fingerprinting",
    "introspection-enumeration",
    "clairvoyance-discovery",
    "bola-idor-testing",
    "alias-abuse-testing",
    "batch-abuse-testing",
    "complexity-dos-testing",
    "deep-nesting-testing",
    "nplus1-detection",
    "report-generation",
]


def _valid_finding() -> dict:
    return new_finding(
        vuln_class="unit-test",
        seq=7,
        title="Valid finding",
        severity="medium",
        confidence=0.5,
        target="http://localhost/graphql",
        evidence={
            "request": {
                "query": "{ __typename }",
                "variables": None,
                "operation_name": None,
                "headers": None,
            },
            "response": {"data": None},
        },
        description="d",
        impact="i",
    )


def test_severity_order_descending_ranks():
    assert isinstance(SEVERITY_ORDER, dict)
    assert SEVERITY_ORDER["critical"] < SEVERITY_ORDER["high"]
    assert SEVERITY_ORDER["high"] < SEVERITY_ORDER["medium"]
    assert SEVERITY_ORDER["medium"] < SEVERITY_ORDER["low"]
    assert SEVERITY_ORDER["low"] < SEVERITY_ORDER["info"]


def test_new_finding_seq_is_keyword_only_and_deterministic():
    finding = _valid_finding()
    assert finding["id"] == "GQL-UNIT-TEST-7"
    with pytest.raises(TypeError):
        new_finding("unit-test", 7)  # type: ignore[misc] -- seq is keyword-only
    with pytest.raises(ValueError):
        new_finding(
            vuln_class="x", seq=0, title="t", severity="medium", confidence=0.5,
            target="t", evidence={}, description="d", impact="i",
        )


def test_validate_finding_accepts_valid():
    assert validate_finding(_valid_finding()) == []


def test_new_finding_default_fix_is_valid():
    """Regression guard: new_finding() without proposed_fix must build a
    finding whose defaulted proposed_fix.summary is non-empty (the default
    used to be ``""``, which could never pass the validator)."""
    finding = new_finding(
        vuln_class="default-fix",
        seq=1,
        title="No fix supplied",
        severity="info",
        confidence=0.5,
        target="http://localhost/graphql",
        evidence={
            "request": {
                "query": "q",
                "variables": None,
                "operation_name": None,
                "headers": None,
            },
            "response": {},
        },
        description="d",
        impact="i",
    )
    assert validate_finding(finding) == []
    assert finding["proposed_fix"]["summary"].strip()


def test_validate_finding_rejects_malformed():
    # Missing top-level keys: validator reports them (and returns early).
    malformed = {
        "id": "not-an-id",
        "severity": "cataclysmic",
        "confidence": 1.5,
        "timestamp": "yesterday",
    }
    defects = validate_finding(malformed)
    assert any("missing key: title" in d for d in defects)
    assert any("missing key: evidence" in d for d in defects)

    # Complete dict with bad field values: each defect is caught.
    bad_values = _valid_finding()
    bad_values["id"] = "not-an-id"
    bad_values["severity"] = "cataclysmic"
    bad_values["confidence"] = 1.5
    bad_values["timestamp"] = "yesterday"
    defects = validate_finding(bad_values)
    assert any("id must match" in d for d in defects)
    assert any("severity" in d for d in defects)
    assert any("confidence" in d for d in defects)
    assert any("timestamp" in d for d in defects)

    missing_evidence = _valid_finding()
    del missing_evidence["evidence"]
    assert any("evidence" in d for d in validate_finding(missing_evidence))

    bad_evidence = _valid_finding()
    bad_evidence["evidence"] = {"request": {"query": "q"}}  # incomplete request
    defects = validate_finding(bad_evidence)
    assert any("evidence.request missing key" in d for d in defects)

    assert validate_finding("not a dict") == ["finding is not a dict"]


def test_retry_succeeds_after_transient_failures():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("transient")
        return "ok"

    # backoff_s=0.0: no sleeping between attempts (fast, deterministic)
    assert retry(flaky, attempts=3, backoff_s=0.0) == "ok"
    assert calls["n"] == 3


def test_retry_exhaustion_wraps_cause():
    def always_fails():
        raise ValueError("permanent")

    with pytest.raises(GraphQLErrorEx) as excinfo:
        retry(always_fails, attempts=2, backoff_s=0.0)
    assert "retry exhausted after 2 attempt(s)" in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, ValueError)


def test_retry_rejects_bad_attempts():
    with pytest.raises(ValueError):
        retry(lambda: 1, attempts=0)


@pytest.mark.parametrize("name", ALL_SKILLS)
def test_loader_loads_skill(name):
    module = load_skill(name)
    assert callable(getattr(module, "run", None)), f"{name} has no run()"


def test_loader_covers_every_skill_folder():
    """Cross-check against the real SKILLS/ layout, not a constant."""
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[1]
    folders = sorted(p.name for p in (root / "SKILLS").iterdir() if p.is_dir())
    assert folders == sorted(ALL_SKILLS)


def test_loader_missing_skill_raises():
    with pytest.raises(FileNotFoundError):
        load_skill("no-such-skill")
