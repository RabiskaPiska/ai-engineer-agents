"""bola-idor-testing: the E2E proof -- cross-identity read on the demo target."""
from __future__ import annotations

from common.findings import validate_finding
from common.loader import load_skill
from common.transport import HttpTransport, LocalTransport
from examples.demo_target import build_demo_schema


def _identities(demo_url):
    """Two HttpTransports differing ONLY in the X-User-ID identity header."""
    return (
        HttpTransport(demo_url, headers={"X-User-ID": "u1"}, timeout_s=10.0),
        HttpTransport(demo_url, headers={"X-User-ID": "u2"}, timeout_s=10.0),
    )


def test_bola_e2e_cross_identity_read(http_transport, demo_url, demo_schema_map):
    skill = load_skill("bola-idor-testing")
    transport_a, transport_b = _identities(demo_url)
    result = skill.run(transport_a, transport_b, demo_schema_map,
                       max_tests=25, id_sample="u1")

    assert result["tested"] >= 1
    assert len(result["findings"]) >= 1
    assert result["meta"]["candidates"] == ["user"]  # the demo's BOLA field

    finding = result["findings"][0]
    assert validate_finding(finding) == []
    assert finding["vuln_class"] == "BOLA"
    assert finding["severity"] == "high"

    request = finding["evidence"]["request"]
    assert request["query"].startswith("query BolaProbe")
    assert request["variables"] == {"id": "u1"}
    assert request["operation_name"] == "BolaProbe"
    assert "response" in finding["evidence"]
    # B (identity u2) actually received u1's record -- the demo's vuln
    assert finding["evidence"]["response"]["data"]["user"]["id"] == "u1"
    baseline = finding["evidence"]["baseline"]
    assert baseline["response"]["data"]["user"]["id"] == "u1"
    assert baseline["request"]["variables"] == {"id": "u1"}


def test_bola_control_same_transport_no_false_positive(
    http_transport, demo_url, demo_schema_map
):
    """False-negative check: same transport (u1 vs u1) must yield 0 findings."""
    skill = load_skill("bola-idor-testing")
    transport_a, _ = _identities(demo_url)
    result = skill.run(transport_a, transport_a, demo_schema_map,
                       max_tests=25, id_sample="u1")
    assert result["findings"] == []
    assert result["tested"] >= 1
    assert result["meta"]["control_run"] is True
    assert any("control run" in reason for reason in result["meta"]["skipped_reasons"])


def test_bola_same_transport_different_call_headers_still_tests(demo_url, demo_schema_map):
    """Same transport object but distinct per-call headers = genuine identity
    difference (the probe uses headers_a/headers_b) -> finding still fires."""
    skill = load_skill("bola-idor-testing")
    transport = HttpTransport(demo_url, timeout_s=10.0)
    result = skill.run(
        transport,
        transport,
        demo_schema_map,
        id_sample="u1",
        headers_a={"X-User-ID": "u1"},
        headers_b={"X-User-ID": "u2"},
    )
    assert len(result["findings"]) >= 1
    assert result["meta"]["control_run"] is False


def test_bola_local_transport_parity(demo_schema_map):
    skill = load_skill("bola-idor-testing")
    transport_a = LocalTransport(build_demo_schema(), context={"user_id": "u1"})
    transport_b = LocalTransport(build_demo_schema(), context={"user_id": "u2"})
    result = skill.run(transport_a, transport_b, demo_schema_map, id_sample="u1")
    assert len(result["findings"]) >= 1


def test_bola_skips_non_id_root_fields(http_transport, demo_schema_map):
    skill = load_skill("bola-idor-testing")
    result = skill.run(http_transport, http_transport, demo_schema_map, id_sample="u1")
    reasons = "\n".join(result["meta"]["skipped_reasons"])
    assert "me" in reasons and "config" in reasons  # 0 args
    assert "users" in reasons  # single arg is Int, not ID
    assert result["meta"]["control_run"] is True


def test_bola_explicit_probe_escape_hatch(http_transport):
    """SPEC: probe(query_template, id_field) executes a caller-built template."""
    skill = load_skill("bola-idor-testing")
    response = skill.probe(
        http_transport,
        "query T($uid: ID!) { user(id: $uid) { id } }",
        id_field="uid",
        id_value="u3",
    )
    assert response["data"]["user"]["id"] == "u3"


def test_bola_unknown_id_skipped(http_transport, demo_schema_map):
    skill = load_skill("bola-idor-testing")
    result = skill.run(http_transport, http_transport, demo_schema_map,
                       id_sample="no-such-id")
    assert result["findings"] == []
    assert result["tested"] == 0
    assert any("owner probe failed" in r for r in result["meta"]["skipped_reasons"])


def test_bola_distinct_transports_equal_headers_current_behavior(
    demo_url, demo_schema_map
):
    """Pinned limitation (logged, not silently accepted): the control gate
    keys on object identity + per-call headers, so two DISTINCT transport
    objects carrying the SAME identity header still produce a finding on the
    demo. Documented so a future identity-aware gate changes this test
    deliberately, not accidentally."""
    skill = load_skill("bola-idor-testing")
    transport_a = HttpTransport(demo_url, headers={"X-User-ID": "u1"}, timeout_s=10.0)
    transport_b = HttpTransport(demo_url, headers={"X-User-ID": "u1"}, timeout_s=10.0)
    result = skill.run(transport_a, transport_b, demo_schema_map, id_sample="u1")
    assert result["meta"]["control_run"] is False
    # current behavior: identical data from a same-identity pair still fires
    assert len(result["findings"]) == 1
