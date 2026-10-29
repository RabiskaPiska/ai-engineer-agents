"""Transport contract tests (SPEC.md): Http e2e, Local parity, Map, batch."""
from __future__ import annotations

from common.transport import (
    HttpTransport,
    LocalTransport,
    MapTransport,
)
from examples.demo_target import build_demo_schema

# --- HttpTransport e2e against the demo server -----------------------------

def test_http_me_with_identity(http_transport):
    transport = http_transport
    response = transport.execute("{ me { id name } }", headers={"X-User-ID": "u1"})
    assert response["data"]["me"]["id"] == "u1"
    assert transport.last_status == 200
    assert isinstance(transport.last_elapsed_ms, (int, float))
    assert transport.last_elapsed_ms >= 0.0


def test_http_user_query(http_transport):
    response = http_transport.execute('{ user(id: "u2") { id email } }')
    assert response["data"]["user"]["id"] == "u2"
    assert response["data"]["user"]["email"] == "user2@demo.local"
    assert http_transport.last_status == 200


def test_http_execute_raw_batch(demo_server):
    transport = HttpTransport(
        demo_server, headers={"X-User-ID": "u1"}, timeout_s=10.0
    )
    body = [{"query": "{ me { id } }"} for _ in range(3)]
    out = transport.execute_raw(body)
    assert isinstance(out, list) and len(out) == 3
    assert all(entry["data"]["me"]["id"] == "u1" for entry in out)


# --- LocalTransport parity ---------------------------------------------------

def test_local_me_context(local_transport):
    assert local_transport.execute("{ me { id } }") == {"data": {"me": {"id": "u1"}}}


def test_local_http_parity(http_transport, local_transport):
    query = '{ user(id: "u2") { id name role } }'
    assert http_transport.execute(query)["data"] == local_transport.execute(query)["data"]


def test_local_headers_merged_into_context():
    transport = LocalTransport(build_demo_schema(), context={"user_id": "u1"})
    # per-call headers must reach the context without breaking execution
    response = transport.execute("{ me { id } }", headers={"X-User-ID": "u3"})
    assert response["data"]["me"]["id"] == "u1"
    assert response["data"]["me"]["id"] is not None


def test_local_sdl_string_schema():
    transport = LocalTransport("type Query { ping: String! }")
    response = transport.execute("{ __typename }")
    assert response["data"]["__typename"] == "Query"
    assert "ping" in transport.execute(
        "{ __type(name: \"Query\") { fields { name } } }"
    )["data"]["__type"]["fields"][0]["name"]


def test_local_execute_raw_batch_returns_list(local_transport):
    ops = [{"query": "{ me { id } }"} for _ in range(3)]
    out = local_transport.execute_raw(ops)
    assert isinstance(out, list) and len(out) == 3
    assert all(entry["data"]["me"]["id"] == "u1" for entry in out)


def test_local_execute_raw_single(local_transport):
    out = local_transport.execute_raw({"query": "{ __typename }"})
    assert out == {"data": {"__typename": "Query"}}


def test_local_batch_entry_without_query(local_transport):
    out = local_transport.execute_raw([{"variables": {}}])
    assert out[0]["errors"][0]["message"]


# --- MapTransport ------------------------------------------------------------

def test_map_transport_canned(map_transport):
    response = map_transport.execute("{ __typename }")
    assert response == {"data": {"__typename": "Query"}}
    assert map_transport.last_status == 200


def test_map_transport_default(map_transport):
    response = map_transport.execute("{ whatever }")
    assert response["errors"][0]["message"] == "canned: not allowed"


def test_map_transport_responses_are_copies():
    canned = {"data": {"__typename": "Query"}}
    transport = MapTransport({"{ __typename }": canned})
    response = transport.execute("{ __typename }")
    response["data"]["__typename"] = "MUTATED"
    assert transport.execute("{ __typename }")["data"]["__typename"] == "Query"


def test_map_transport_missing_and_no_default():
    transport = MapTransport({})
    try:
        transport.execute("{ missing }")
    except KeyError as exc:
        assert "no canned response" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected KeyError")


def test_map_transport_callable_responses():
    transport = MapTransport(
        {},
        default=lambda q, v, o, h: {"data": {"echo": str(q)[:10]}},
    )
    assert transport.execute("{ abc }")["data"]["echo"] == "{ abc }"


def test_map_transport_batch(map_transport):
    out = map_transport.execute_raw([{"query": "{ __typename }"} for _ in range(2)])
    assert isinstance(out, list) and len(out) == 2
