"""nplus1-detection: ratio math + threshold trigger with a delayed fake transport."""
from __future__ import annotations

import time

from common.loader import load_skill


class _DelayedTransport:
    """Fake transport with controllable per-call latency.

    Two modes:
    - ``use_transport_timing=True``: sets ``last_elapsed_ms`` per call (the
      path HttpTransport exercises) -- fully deterministic, zero sleeps.
    - otherwise: actually sleeps per call (exercises the perf_counter
      fallback) with margins wide enough to survive OS timer-quantum
      overshoot on Windows (~15.6 ms).
    """

    def __init__(
        self,
        list_query: str,
        list_ms: float,
        single_ms: float,
        use_transport_timing: bool = False,
    ) -> None:
        self._list_query = list_query
        self._list_ms = list_ms
        self._single_ms = single_ms
        self._use_transport_timing = use_transport_timing
        self.calls = 0

    def execute(self, query, variables=None, operation_name=None, headers=None):
        self.calls += 1
        ms = self._list_ms if query == self._list_query else self._single_ms
        if self._use_transport_timing:
            self.last_elapsed_ms = ms
        else:
            time.sleep(ms / 1000.0)
        return {"data": {"users": [{"id": "1"}]}}

    def execute_raw(self, body):
        raise AssertionError("nplus1-detection must not batch")


LIST_QUERY = "query { users { id } }"
SINGLE_TEMPLATE = 'query { user(id: "{id}") { id } }'


def test_nplus1_ratio_math_and_finding_trigger():
    skill = load_skill("nplus1-detection")
    # Deterministic: list 16 ms vs singles 2 ms via transport timing (ratio 8x)
    transport = _DelayedTransport(
        LIST_QUERY, list_ms=16.0, single_ms=2.0, use_transport_timing=True
    )
    result = skill.run(transport, LIST_QUERY, SINGLE_TEMPLATE, n=3, threshold_ratio=3.0)

    meta = result["meta"]
    assert meta["n_measured"] == 3
    assert meta["t_list_ms"] == 16.0
    assert meta["t_singles_ms"] == [2.0, 2.0, 2.0]
    assert meta["timing_source"] == ["transport.last_elapsed_ms"]
    assert meta["ratio"] == 8.0  # 16 / avg(2, 2, 2)

    assert len(result["findings"]) == 1
    finding = result["findings"][0]
    assert finding["confidence"] == 0.6  # exactly the cap
    assert finding["severity"] == "low"
    assert "heuristic" in finding["description"].lower()
    assert "not proof" in finding["description"].lower()
    assert finding["evidence"]["request"]["query"] == LIST_QUERY


def test_nplus1_perf_counter_fallback_fires():
    """Real-sleep variant: exercises the perf_counter timing path. Margins are
    sized so even worst-case Windows sleep overshoot keeps ratio >= 3."""
    skill = load_skill("nplus1-detection")
    transport = _DelayedTransport(LIST_QUERY, list_ms=60.0, single_ms=4.0)
    result = skill.run(transport, LIST_QUERY, SINGLE_TEMPLATE, n=3, threshold_ratio=3.0)
    assert result["meta"]["timing_source"] == ["perf_counter"]
    assert result["meta"]["ratio"] >= 3.0
    assert len(result["findings"]) == 1


def test_nplus1_below_threshold_no_finding():
    skill = load_skill("nplus1-detection")
    transport = _DelayedTransport(LIST_QUERY, list_ms=2.0, single_ms=2.0)
    result = skill.run(transport, LIST_QUERY, SINGLE_TEMPLATE, n=2, threshold_ratio=50.0)
    assert result["findings"] == []
    assert result["meta"]["ratio"] < 50.0
    assert result["meta"]["ratio"] is not None


def test_nplus1_failing_transport_honest():
    class _Boom:
        def execute(self, *args, **kwargs):
            raise RuntimeError("boom")

    skill = load_skill("nplus1-detection")
    result = skill.run(_Boom(), LIST_QUERY, SINGLE_TEMPLATE, n=1)
    assert result["findings"] == []
    assert result["meta"]["ratio"] is None
    assert any("list query failed" in s for s in result["meta"]["suspicions"])


def test_nplus1_bad_template_honest():
    skill = load_skill("nplus1-detection")
    transport = _DelayedTransport(LIST_QUERY, list_ms=0.0, single_ms=0.0)
    result = skill.run(transport, LIST_QUERY, "no placeholder", n=1)
    assert result["findings"] == []
    assert any("{id}" in s for s in result["meta"]["suspicions"])
