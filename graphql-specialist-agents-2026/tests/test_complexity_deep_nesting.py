"""complexity-dos-testing + deep-nesting-testing: caps, demo cycle, honest runs."""
from __future__ import annotations

import pytest

from common.findings import validate_finding
from common.loader import load_skill

# --- builders respect the caps ------------------------------------------------

def test_build_deep_nests_exactly_depth_levels():
    skill = load_skill("complexity-dos-testing")
    chain = ["config", "parent", "key"]
    query = skill.build_deep(chain, 3)
    assert query == "query { config { parent { key } } }"
    assert query.count("{") == 3
    at_cap = skill.build_deep(["config", "parent"], 20)
    assert at_cap.count("{") == 20  # max_depth respected, never exceeded
    with pytest.raises(ValueError):
        skill.build_deep([], 3)
    with pytest.raises(ValueError):
        skill.build_deep(["config"], 0)


def test_build_fanout_exactly_n_aliases():
    skill = load_skill("complexity-dos-testing")
    query = skill.build_fanout("users(first: 5)", 7)
    assert query.count(": users(first: 5)") == 7
    assert query.startswith("query { a0:")
    with pytest.raises(ValueError):
        skill.build_fanout("users", 0)


def test_deep_nesting_build_cyclic_shape():
    skill = load_skill("deep-nesting-testing")
    query = skill.build_cyclic(["config", "parent"], 3)
    assert query == "query { config { parent { parent { __typename } } } }"
    assert query.count("{") == 4  # 3 rounds + __typename leaf
    with pytest.raises(ValueError):
        skill.build_cyclic([], 3)


# --- deep-nesting against the demo --------------------------------------------

def test_find_cycles_finds_config_parent_cycle(demo_schema_map):
    skill = load_skill("deep-nesting-testing")
    cycles = skill.find_cycles(demo_schema_map)
    assert ["config", "parent"] in cycles
    assert all(isinstance(c, list) and c for c in cycles)


def test_deep_nesting_run_demo_structured(demo_schema_map, http_transport):
    skill = load_skill("deep-nesting-testing")
    result = skill.run(http_transport, demo_schema_map, rounds=20, max_depth=20)
    meta = result["meta"]
    assert meta["cycles_found"] == [["config", "parent"]]
    assert meta["rounds_used"] == 20
    assert meta["probes"], "both variants should have been probed"
    kinds = {p["variant"] for p in meta["probes"]}
    assert {"nested", "fragments"} <= kinds
    assert all(p["accepted"] for p in meta["probes"])
    assert not any(p["limit_hit"] for p in meta["probes"])
    # at the cap (rounds == max_depth) with no depth limit -> finding
    assert len(result["findings"]) >= 1
    assert validate_finding(result["findings"][0]) == []
    assert result["findings"][0]["vuln_class"] == "deep-nesting-dos"


def test_deep_nesting_below_cap_no_finding(demo_schema_map, http_transport):
    """rounds < max_depth and not aggressive -> honest probes, zero findings."""
    skill = load_skill("deep-nesting-testing")
    result = skill.run(http_transport, demo_schema_map, rounds=3, max_depth=20)
    assert result["findings"] == []
    assert all(p["accepted"] for p in result["meta"]["probes"])


def test_deep_nesting_acyclic_schema_honest(local_transport):
    skill = load_skill("deep-nesting-testing")
    schema_map = {
        "types": [
            {
                "kind": "OBJECT",
                "name": "Query",
                "fields": [{"name": "ping", "type": "String", "args": []}],
            }
        ],
        "roots": {"query": ["ping"], "mutation": [], "subscription": []},
    }
    result = skill.run(local_transport, schema_map)
    assert result["findings"] == []
    assert any("no cyclic" in s for s in result["meta"]["suspicions"])


def test_deep_nesting_bad_schema_map_honest(http_transport):
    skill = load_skill("deep-nesting-testing")
    result = skill.run(http_transport, "not-a-dict")  # type: ignore[arg-type]
    assert result["findings"] == []
    assert result["meta"]["suspicions"]


# --- complexity against the demo -----------------------------------------------

def test_complexity_run_demo_structured(demo_schema_map, http_transport):
    skill = load_skill("complexity-dos-testing")
    result = skill.run(http_transport, demo_schema_map, max_depth=20, max_ops=100)
    meta = result["meta"]
    kinds = {p["kind"] for p in meta["probes"]}
    assert {"deep", "fanout"} <= kinds
    # the config/parent chain reaches the max_depth cap
    assert any(len(chain) == 20 for chain in meta["chains_used"])
    # caps never exceeded
    assert all(p["cap_used"] <= 100 for p in meta["probes"] if p["kind"].startswith("fanout"))
    assert all(p["cap_used"] <= 20 for p in meta["probes"] if p["kind"].startswith("deep"))
    # at-cap deep probe accepted with no complexity limit -> finding
    assert len(result["findings"]) >= 1
    finding = result["findings"][0]
    assert validate_finding(finding) == []
    assert finding["vuln_class"] == "complexity-dos"


def test_complexity_run_caps_limit_probes(demo_schema_map, http_transport):
    skill = load_skill("complexity-dos-testing")
    result = skill.run(http_transport, demo_schema_map, max_depth=5, max_ops=3)
    assert len(result["meta"]["probes"]) <= 3  # probe budget bounded by max_ops
    for probe in result["meta"]["probes"]:
        if probe["kind"].startswith("deep"):
            assert probe["cap_used"] <= 5


def test_complexity_empty_schema_honest(http_transport):
    skill = load_skill("complexity-dos-testing")
    result = skill.run(http_transport, {})
    assert result["findings"] == []
    assert result["meta"]["suspicions"]
    assert result["meta"]["probes"] == []
