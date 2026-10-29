"""schema-fingerprinting: honest features, engine hints, probe budget <= 6."""
from __future__ import annotations

from common.loader import load_skill
from common.transport import MapTransport


class _CountingTransport:
    """Wraps a transport and counts execute/execute_raw calls."""

    def __init__(self, inner):
        self._inner = inner
        self.calls = 0

    def execute(self, *args, **kwargs):
        self.calls += 1
        return self._inner.execute(*args, **kwargs)

    def execute_raw(self, *args, **kwargs):
        self.calls += 1
        return self._inner.execute_raw(*args, **kwargs)


def test_fingerprint_demo_happy_path(http_transport):
    skill = load_skill("schema-fingerprinting")
    result = skill.run(http_transport)
    assert set(result) >= {"engine_candidates", "features", "findings", "meta"}

    features = result["features"]
    # demo (graphql-core): suggestions on, introspection on, batch accepted
    assert features["field_suggestions"] is True
    assert features["introspection"] is True
    assert features["batch"] is True

    assert result["engine_candidates"], "graphql-core wording should hint an engine"
    for hint in result["engine_candidates"]:
        assert set(hint) >= {"engine", "confidence", "evidence"}
        assert 0.0 < hint["confidence"] <= 1.0

    assert result["meta"]["probe_budget"] == skill.MAX_PROBES == 6
    assert result["meta"]["probes_sent"] <= skill.MAX_PROBES


def test_fingerprint_probe_budget_counted(http_transport):
    skill = load_skill("schema-fingerprinting")
    counting = _CountingTransport(http_transport)
    result = skill.run(counting)
    assert counting.calls <= 6
    assert result["meta"]["probes_sent"] == counting.calls
    assert len(result["meta"]["probe_log"]) == counting.calls


def test_fingerprint_adverse_denied_honest_none():
    """A server that answers everything with a bare error yields honest
    None features and an empty engine-candidate list -- never guesses."""
    skill = load_skill("schema-fingerprinting")
    transport = MapTransport({}, default={"errors": [{"message": "denied"}]})
    result = skill.run(transport)
    assert result["engine_candidates"] == []
    features = result["features"]
    assert features["field_suggestions"] in (None, False)
    assert features["introspection"] is None
    # MapTransport answers the batch probe with a per-entry list -> accepted
    assert features["batch"] is True
    notes = result["meta"]["notes"]
    assert any("may not be a GraphQL endpoint" in note for note in notes)


def test_fingerprint_batch_dict_answer_is_not_batch():
    """A single-dict answer to a list body must NOT count as batch support."""

    class _SingleAnswerTransport:
        def execute(self, query, variables=None, operation_name=None, headers=None):
            return {
                "data": {
                    "__typename": "Query",
                    "__schema": {"queryType": {"name": "Query"}},
                }
            }

        def execute_raw(self, body):
            return {"data": {"__typename": "Query"}}  # dict, not a list

    skill = load_skill("schema-fingerprinting")
    result = skill.run(_SingleAnswerTransport())
    assert result["features"]["batch"] is False
    assert result["features"]["introspection"] is True


def test_fingerprint_suggestions_disabled_detected():
    """Validation errors WITHOUT 'Did you mean' => field_suggestions False."""
    skill = load_skill("schema-fingerprinting")
    transport = MapTransport(
        {},
        default={
            "errors": [
                {"message": "Cannot query field 'zzz' on type 'Query'. No suggestions."}
            ]
        },
    )
    result = skill.run(transport)
    assert result["features"]["field_suggestions"] is False
