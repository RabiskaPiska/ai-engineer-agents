"""Shared fixtures for the pack's test suite.

- ``demo_server``  -- examples/demo_target.py ThreadingHTTPServer on a FREE
  port (port=0), started once per module and shut down after.
- ``http_transport`` -- HttpTransport pointed at the demo server.
- ``local_transport`` -- LocalTransport over the demo schema (context u1).
- ``map_transport``  -- MapTransport with canned responses.
- ``demo_schema_map`` -- full introspection schema_map + roots (the FIX-1
  contract shape that bola/complexity/deep-nesting skills consume).
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.loader import load_skill
from common.transport import (
    HttpTransport,
    LocalTransport,
    MapTransport,
)
from examples.demo_target import build_demo_schema, create_server


@pytest.fixture(scope="module")
def demo_server():
    """Start the demo target on a free port; yield its /graphql URL."""
    server = create_server(host="127.0.0.1", port=0)
    port = server.server_address[1]
    thread = threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True
    )
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}/graphql"
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture(scope="module")
def demo_url(demo_server):
    return demo_server


@pytest.fixture(scope="module")
def http_transport(demo_server):
    return HttpTransport(demo_server, timeout_s=10.0)


@pytest.fixture(scope="module")
def demo_schema_map(http_transport):
    """schema_map (+ roots) from the introspection skill against the demo."""
    intro = load_skill("introspection-enumeration")
    result = intro.run(http_transport, full=True)
    assert result["introspection_enabled"] is True
    return {**result["schema_map"], "roots": result["roots"]}


@pytest.fixture()
def local_transport():
    return LocalTransport(build_demo_schema(), context={"user_id": "u1"})


@pytest.fixture()
def map_transport():
    return MapTransport(
        {"{ __typename }": {"data": {"__typename": "Query"}}},
        default={"data": None, "errors": [{"message": "canned: not allowed"}]},
    )
