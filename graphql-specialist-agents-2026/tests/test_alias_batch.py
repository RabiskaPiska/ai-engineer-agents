"""alias-abuse-testing + batch-abuse-testing: builders, demo e2e, adverse."""
from __future__ import annotations

import pytest

from common.findings import validate_finding
from common.loader import load_skill
from common.transport import MapTransport

# --- alias-abuse-testing -----------------------------------------------------

def test_alias_build_parses():
    skill = load_skill("alias-abuse-testing")
    query = skill.build(5, "__typename")
    assert query == (
        "query AliasAbuse { a0: __typename a1: __typename a2: __typename "
        "a3: __typename a4: __typename }"
    )
    assert query.count("a4: __typename") == 1


def test_alias_build_validates_inputs():
    skill = load_skill("alias-abuse-testing")
    with pytest.raises(ValueError):
        skill.build(0, "__typename")
    with pytest.raises(ValueError):
        skill.build(3, "not a field!")


def test_alias_run_demo_accepted(http_transport):
    skill = load_skill("alias-abuse-testing")
    result = skill.run(http_transport, "__typename", n=5)
    meta = result["meta"]
    assert meta["accepted"] is True
    assert meta["aliases_executed"] == 5
    assert meta["aliases_requested"] == 5
    assert meta["response_bytes"] > 0
    assert isinstance(meta["elapsed_ms"], float)
    assert meta["limit_error"] is None
    assert meta["capped"] is False
    assert len(result["findings"]) == 1
    assert validate_finding(result["findings"][0]) == []
    finding = result["findings"][0]
    assert finding["evidence"]["request"]["operation_name"] == "AliasAbuse"


def test_alias_run_respects_max_ops_cap(local_transport):
    skill = load_skill("alias-abuse-testing")
    result = skill.run(local_transport, "__typename", n=50, max_ops=10)
    assert result["meta"]["capped"] is True
    assert result["meta"]["aliases_requested"] == 10
    assert result["meta"]["aliases_executed"] == 10


def test_alias_limit_error_honest():
    """Adverse: server reports an alias-limit error -> no finding, honest meta."""
    skill = load_skill("alias-abuse-testing")
    transport = MapTransport(
        {},
        default={"errors": [{"message": "Too many aliases: limit exceeded (max 3)"}]},
    )
    result = skill.run(transport, "__typename", n=5)
    assert result["meta"]["accepted"] is False
    assert result["meta"]["limit_error"]
    assert result["findings"] == []


# --- batch-abuse-testing ------------------------------------------------------

def test_batch_build_three_ops():
    skill = load_skill("batch-abuse-testing")
    ops = skill.build(3, "{ __typename }")
    assert len(ops) == 3
    assert all(op == {"query": "{ __typename }", "variables": None} for op in ops)
    with pytest.raises(ValueError):
        skill.build(0, "{ __typename }")
    with pytest.raises(ValueError):
        skill.build(2, "   ")


def test_batch_execute_raw_demo_accepts(http_transport):
    skill = load_skill("batch-abuse-testing")
    ops = skill.build(3, "{ __typename }")
    raw = http_transport.execute_raw(ops)
    assert isinstance(raw, list) and len(raw) == 3
    assert all(entry["data"]["__typename"] == "Query" for entry in raw)


def test_batch_run_demo_finding(http_transport):
    skill = load_skill("batch-abuse-testing")
    result = skill.run(http_transport, "{ __typename }", n=3)
    meta = result["meta"]
    assert meta["batch_accepted"] is True
    assert meta["ops_success"] == 3
    assert meta["response_bytes"] > 0
    assert meta["limit_errors"] == []
    assert len(result["findings"]) == 1
    finding = result["findings"][0]
    assert validate_finding(finding) == []
    assert finding["vuln_class"] == "batch-abuse"
    assert finding["evidence"]["request"]["query"] == "{ __typename }"


def test_batch_run_cap_applies(local_transport):
    skill = load_skill("batch-abuse-testing")
    result = skill.run(local_transport, "{ __typename }", n=500, max_ops=5)
    assert result["meta"]["ops_sent"] == 5
    assert result["meta"]["cap_applied"] is True
    assert any("safety cap" in s for s in result["meta"]["suspicions"])


def test_batch_adverse_transport_raises_honest():
    """Adverse: MapTransport with no canned response raises on a list body ->
    honest 'unsupported/failed' meta, zero findings, no crash."""
    skill = load_skill("batch-abuse-testing")
    transport = MapTransport({})  # no default -> KeyError on any query
    result = skill.run(transport, "{ __typename }", n=3)
    assert result["findings"] == []
    assert result["meta"]["batch_accepted"] is None
    assert result["meta"]["suspicions"], "failure must be recorded honestly"
    assert "execute_raw failed" in result["meta"]["suspicions"][0]
