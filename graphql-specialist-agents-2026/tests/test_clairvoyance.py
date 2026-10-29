"""clairvoyance-discovery: real-field discovery from 'Did you mean' errors."""
from __future__ import annotations

from common.findings import validate_finding
from common.loader import load_skill
from common.transport import MapTransport


def test_clairvoyance_demo_discovers_real_fields(http_transport):
    skill = load_skill("clairvoyance-discovery")
    result = skill.run(http_transport)

    names = [d["field"] for d in result["discovered"]]
    # graphql-core suggests only REAL fields; these near-misses must surface them
    assert "user" in names
    assert {"me", "config"} & set(names)
    assert result["suggestions_enabled"] is True

    for entry in result["discovered"]:
        assert set(entry) >= {"field", "probable_type", "evidence"}
        assert entry["probable_type"] is None  # never claimed from suggestions
        assert "Did you mean" in entry["evidence"]

    # one info finding per SPEC, fully valid
    assert len(result["findings"]) == 1
    assert validate_finding(result["findings"][0]) == []

    meta = result["meta"]
    assert meta["batch_mode"] is True  # demo accepts batched probes
    assert meta["probes_used"] <= meta["max_probes"]
    assert meta["wordlist_size"] == len(skill.DEFAULT_WORDLIST)


def test_clairvoyance_custom_wordlist_and_probe_cap(http_transport):
    skill = load_skill("clairvoyance-discovery")
    result = skill.run(http_transport, wordlist=["user", "users", "me"], max_probes=3)
    names = {d["field"] for d in result["discovered"]}
    assert {"user", "users", "me"} <= names
    assert result["meta"]["probes_used"] <= 3
    assert result["meta"]["wordlist_size"] == 3


def test_clairvoyance_no_suggestions_honest():
    """Adverse: validation errors without suggestions -> empty, honest meta."""
    skill = load_skill("clairvoyance-discovery")
    transport = MapTransport(
        {},
        default={
            "errors": [
                {"message": "Cannot query field 'userx' on type 'Query'."}
            ]
        },
    )
    result = skill.run(transport, wordlist=["user"], max_probes=5)
    assert result["discovered"] == []
    assert result["suggestions_enabled"] is False
    assert result["findings"] == []
    assert any(
        "suggestions appear to be disabled" in note for note in result["meta"]["notes"]
    )


def test_clairvoyance_empty_wordlist_honest():
    skill = load_skill("clairvoyance-discovery")
    transport = MapTransport({}, default={"data": {"__typename": "Query"}})
    result = skill.run(transport, wordlist=[])
    assert result["discovered"] == []
    assert result["suggestions_enabled"] is False
    assert any("empty wordlist" in note for note in result["meta"]["notes"])
