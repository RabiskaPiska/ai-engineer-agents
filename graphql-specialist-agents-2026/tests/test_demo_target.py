"""examples/demo_target.py e2e: banner, batch, X-User-ID context, BOLA vuln."""
from __future__ import annotations

import httpx


def test_get_banner(demo_server):
    response = httpx.get(demo_server, timeout=10.0)
    assert response.status_code == 200
    assert response.json() == {"service": "demo-vulnerable-graphql"}


def test_get_unknown_path_404(demo_server):
    response = httpx.get(demo_server.rsplit("/graphql", 1)[0] + "/nope", timeout=10.0)
    assert response.status_code == 404


def test_batch_post_of_three_ops(demo_server):
    body = [
        {"query": "{ me { id } }"},
        {"query": "{ __typename }"},
        {"query": "{ me { email } }"},
    ]
    response = httpx.post(
        demo_server, json=body, headers={"X-User-ID": "u3"}, timeout=10.0
    )
    assert response.status_code == 200
    out = response.json()
    assert isinstance(out, list) and len(out) == 3
    assert out[0]["data"]["me"]["id"] == "u3"
    assert out[1]["data"]["__typename"] == "Query"
    assert out[2]["data"]["me"]["email"] == "user3@demo.local"


def test_x_user_id_sets_me_context(demo_server):
    for uid in ("u1", "u2"):
        response = httpx.post(
            demo_server,
            json={"query": "{ me { id role } }"},
            headers={"X-User-ID": uid},
            timeout=10.0,
        )
        data = response.json()["data"]["me"]
        assert data["id"] == uid
        assert data["role"] == ("admin" if uid == "u1" else "user")


def test_me_without_header_is_null(demo_server):
    response = httpx.post(demo_server, json={"query": "{ me { id } }"}, timeout=10.0)
    assert response.json()["data"]["me"] is None


def test_user_field_ignores_ownership_the_bola_bug(demo_server):
    """The intentional vuln: any identity can read any user by id."""
    response = httpx.post(
        demo_server,
        json={"query": '{ user(id: "u1") { id email orders { id } } }'},
        headers={"X-User-ID": "u3"},
        timeout=10.0,
    )
    data = response.json()["data"]["user"]
    assert data["id"] == "u1"
    assert data["email"] == "user1@demo.local"
    assert len(data["orders"]) == 2


def test_config_recurses_unboundedly(demo_server):
    """The deep-nesting target: Config.parent cycles back to the root.

    graphql-core result dicts contain only the queried fields, so ``key`` is
    read at the level where it was selected; cycling is proven by the keys
    alternating mode/region as the chain loops.
    """
    depth = 6
    inner = "key"
    for _ in range(depth):
        inner = f"key parent {{ {inner} }}"
    query = f"query {{ config {{ {inner} }} }}"
    response = httpx.post(demo_server, json={"query": query}, timeout=10.0)
    node = response.json()["data"]["config"]
    keys = []
    for _ in range(depth):
        node = node["parent"]
        keys.append(node.get("key"))
    # every level existed (unbounded recursion served), cycle restarts with mode
    assert keys[-1] == "mode"
    assert keys[0] == "region"
    assert keys[0::2] == ["region"] * 3 and keys[1::2] == ["mode"] * 3
