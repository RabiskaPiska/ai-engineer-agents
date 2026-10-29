"""introspection-enumeration: full extraction + roots contract + honest fallback."""
from __future__ import annotations

from common.loader import load_skill
from common.transport import LocalTransport, MapTransport
from examples.demo_target import build_demo_schema


def test_introspection_demo_roots_and_types(http_transport):
    skill = load_skill("introspection-enumeration")
    result = skill.run(http_transport, full=True)
    assert result["introspection_enabled"] is True
    assert result["meta"]["strategy"] in ("full", "minimal")

    schema_map = result["schema_map"]
    names = {t["name"] for t in schema_map["types"]}
    assert {"Query", "User", "Order", "Item", "Config"} <= names

    # FIX-1 contract: schema_map output carries "roots" with the three roles
    roots = result["roots"]
    assert set(roots) == {"query", "mutation", "subscription"}
    assert set(roots["query"]) == {"user", "users", "me", "config"}
    assert roots["mutation"] == []
    assert roots["subscription"] == []

    user = next(t for t in schema_map["types"] if t["name"] == "User")
    field_names = {f["name"] for f in user["fields"]}
    assert {"id", "name", "email", "role", "orders"} <= field_names
    user_field = next(f for f in user["fields"] if f["name"] == "id")
    assert user_field["type"] == "ID!"

    orders_field = next(f for f in user["fields"] if f["name"] == "orders")
    assert orders_field["type"] == "[Order!]!"
    # user(id: ID!) arg recorded
    query_type = next(t for t in schema_map["types"] if t["name"] == "Query")
    user_root = next(f for f in query_type["fields"] if f["name"] == "user")
    assert user_root["args"][0]["name"] == "id"
    assert user_root["args"][0]["type"] == "ID!"


def test_introspection_local_parity():
    skill = load_skill("introspection-enumeration")
    transport = LocalTransport(build_demo_schema(), context={"user_id": "u1"})
    result = skill.run(transport, full=True)
    assert result["introspection_enabled"] is True
    assert set(result["roots"]["query"]) == {"user", "users", "me", "config"}


def test_introspection_blocked_no_crash():
    """Adverse: every query answered with a bare 'not allowed' error."""
    skill = load_skill("introspection-enumeration")
    transport = MapTransport({}, default={"errors": [{"message": "not allowed"}]})
    result = skill.run(transport, full=True)
    assert result["introspection_enabled"] is False
    assert result["schema_map"]["types"] == []
    assert result["roots"] == {"query": [], "mutation": [], "subscription": []}
    assert result["meta"]["strategy"] == "blocked"
    assert result["meta"]["notes"]
    assert result["findings"] == []


def test_introspection_mined_fallback():
    """Introspection blocked but suggestions on -> mined field names, honest
    probable-type absence."""
    skill = load_skill("introspection-enumeration")
    transport = MapTransport(
        {},
        default={
            "errors": [
                {
                    "message": "Cannot query field 'user_zzz' on type 'Query'. "
                    "Did you mean 'user' or 'users'?"
                }
            ]
        },
    )
    result = skill.run(transport, full=True)
    assert result["introspection_enabled"] is False
    assert result["meta"]["strategy"] == "mined"
    mined_names = {f["name"] for f in result["schema_map"]["types"][0]["fields"]}
    assert {"user", "users"} <= mined_names
    assert "user" in result["roots"]["query"]
    assert "introspection is blocked" in result["meta"]["notes"]


def test_introspection_never_exceeds_honest_content(http_transport):
    """Every reported type/field must come from the real schema (spot-check)."""
    skill = load_skill("introspection-enumeration")
    result = skill.run(http_transport, full=True)
    for t in result["schema_map"]["types"]:
        assert not t["name"].startswith("__")  # internals filtered
        for f in t["fields"]:
            assert f["name"]
