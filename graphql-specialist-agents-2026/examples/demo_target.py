"""Offline, intentionally vulnerable GraphQL demo target.

Purpose
-------
A small self-contained GraphQL service for authorized security testing and
for the pack's own pytest suite. It is vulnerable **on purpose**:

- ``user(id: ID!)`` — INTENTIONAL BOLA/IDOR: the resolver returns any user by
  id and deliberately ignores the ``X-User-ID`` ownership context. Any caller
  can read any other user's data (id, email, orders).
- ``config: Config!`` with ``Config.parent: Config`` — unbounded recursion
  (self-referencing data) for deep-nesting / cyclic-query testing.
- ``POST /graphql`` accepts a single operation object OR a batch (JSON list)
  with **no size limit** — batch-abuse testing target.

Everything else is deliberately boring: ``me`` is properly context-bound,
``users(first: Int)`` is a plain list, ``User.orders`` / ``Order.items`` are
plain one-to-many lists (usable as the N+1 timing-heuristic probe surface).

Pure ``graphql-core`` + stdlib. No httpx on the server side.

Usage
-----
Direct::

    python examples/demo_target.py                # serves on 127.0.0.1:4000

Programmatic (importable; server creation is separate from serving)::

    from examples.demo_target import create_server, serve, get_schema, execute_query
    server = create_server(host="127.0.0.1", port=0)   # port 0 = free port
    port = server.server_address[1]
    server.serve_forever()                             # tests run it in a thread
    server.server_close()

Request format (single or batch)::

    POST /graphql
    X-User-ID: u2                      # sets the ownership context ("who am I")
    Content-Type: application/json

    {"query": "query { me { email } }", "variables": {}, "operationName": null}

    # batch: any JSON list of operation objects, no size limit (on purpose)
    [{"query": "..."}, {"query": "..."}]

    GET /graphql -> {"service": "demo-vulnerable-graphql"}
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import graphql

__all__ = [
    "ITEMS",
    "ORDERS",
    "ROOT_CONFIG",
    "SDL",
    "USERS",
    "GraphQLRequestHandler",
    "build_demo_schema",
    "create_server",
    "execute_query",
    "get_schema",
    "serve",
]

# ---------------------------------------------------------------------------
# Schema (SDL) — built with graphql-core only
# ---------------------------------------------------------------------------

SDL = """
type Query {
  user(id: ID!): User
  users(first: Int = 10): [User!]!
  me: User
  config: Config!
}

type User {
  id: ID!
  name: String!
  email: String!
  role: String!
  orders: [Order!]!
}

type Order {
  id: ID!
  total: Float!
  items: [Item!]!
}

type Item {
  id: ID!
  name: String!
  price: Float!
  quantity: Int!
}

type Config {
  key: String!
  value: String!
  parent: Config
}
"""

# ---------------------------------------------------------------------------
# In-memory data: 3 users (u1/u2/u3), each with 2 orders, each order 2 items
# ---------------------------------------------------------------------------


def _build_data() -> tuple[dict, dict, dict]:
    users: dict[str, dict] = {}
    orders: dict[str, dict] = {}
    items: dict[str, dict] = {}
    prices = [9.99, 24.5, 3.75, 59.0]
    n = 0
    for u in (1, 2, 3):
        uid = f"u{u}"
        users[uid] = {
            "id": uid,
            "name": f"User {u}",
            "email": f"user{u}@demo.local",
            "role": "admin" if u == 1 else "user",
            "orders": [],
        }
        for o in (1, 2):
            oid = f"o{u}-{o}"
            order_items: list[dict] = []
            for i in (1, 2):
                iid = f"{oid}-i{i}"
                n += 1
                item = {
                    "id": iid,
                    "name": f"Item {n}",
                    "price": prices[n % len(prices)],
                    "quantity": (n % 3) + 1,
                }
                items[iid] = item
                order_items.append(item)
            order = {
                "id": oid,
                "total": round(sum(it["price"] * it["quantity"] for it in order_items), 2),
                "items": order_items,
            }
            orders[oid] = order
            users[uid]["orders"].append(order)
    return users, orders, items


USERS, ORDERS, ITEMS = _build_data()

# Self-referencing config chain -> unbounded recursion for Config.parent.
ROOT_CONFIG: dict = {"key": "mode", "value": "production"}
ROOT_CONFIG["parent"] = {"key": "region", "value": "eu-1", "parent": ROOT_CONFIG}

# ---------------------------------------------------------------------------
# Resolvers
# ---------------------------------------------------------------------------


def _resolve_user(_obj: Any, info: graphql.GraphQLResolveInfo, id: str) -> dict | None:
    """INTENTIONAL BOLA: returns any user by id, ignoring X-User-ID ownership.

    A correct implementation would check ``info.context["user_id"]`` ownership
    here (or role-based access) before returning the record.
    """
    return USERS.get(id)


def _resolve_users(_obj: Any, info: graphql.GraphQLResolveInfo, first: int = 10) -> list[dict]:
    return list(USERS.values())[: max(0, int(first))]


def _resolve_me(_obj: Any, info: graphql.GraphQLResolveInfo) -> dict | None:
    """Context-bound: honors the X-User-ID header (via transport context)."""
    user_id = (info.context or {}).get("user_id")
    return USERS.get(user_id) if user_id else None


def _resolve_config(_obj: Any, info: graphql.GraphQLResolveInfo) -> dict:
    return ROOT_CONFIG


def build_demo_schema() -> graphql.GraphQLSchema:
    """Build (and wire resolvers into) the demo schema. Pure, reusable."""
    schema = graphql.build_schema(SDL)
    fields = schema.query_type.fields
    fields["user"].resolve = _resolve_user
    fields["users"].resolve = _resolve_users
    fields["me"].resolve = _resolve_me
    fields["config"].resolve = _resolve_config
    return schema


_SCHEMA: graphql.GraphQLSchema | None = None


def get_schema() -> graphql.GraphQLSchema:
    """Lazily built shared schema (so importing this module has no side effects)."""
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = build_demo_schema()
    return _SCHEMA


def _format_error(err: graphql.GraphQLError) -> dict:
    formatted = getattr(err, "formatted", None)
    if isinstance(formatted, dict):
        return formatted
    return {"message": str(err)}


def execute_query(
    query: str | None,
    variables: dict | None = None,
    operation_name: str | None = None,
    context: dict | None = None,
) -> dict:
    """Execute one GraphQL operation against the demo schema (no HTTP involved)."""
    result = graphql.graphql_sync(
        get_schema(),
        query or "",
        variable_values=variables,
        operation_name=operation_name,
        context_value=context or {},
    )
    response: dict = {"data": result.data}
    if result.errors:
        response["errors"] = [_format_error(e) for e in result.errors]
    return response


# ---------------------------------------------------------------------------
# HTTP server (stdlib http.server only)
# ---------------------------------------------------------------------------


class GraphQLRequestHandler(BaseHTTPRequestHandler):
    server_version = "demo-vulnerable-graphql/1.0"
    protocol_version = "HTTP/1.1"

    # -- helpers -----------------------------------------------------------

    def _send_json(self, status: int, payload: Any) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _path(self) -> str:
        return self.path.split("?", 1)[0]

    def log_message(self, format: str, *args: Any) -> None:
        pass  # keep the demo target quiet (tests capture stderr)

    # -- routes ------------------------------------------------------------

    def do_GET(self) -> None:
        if self._path() == "/graphql":
            self._send_json(200, {"service": "demo-vulnerable-graphql"})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self._path() != "/graphql":
            self._send_json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length > 0 else b""
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError):
            self._send_json(400, {"errors": [{"message": "request body is not valid JSON"}]})
            return

        # X-User-ID header -> ownership context ("me" honors it; "user" does not).
        context = {"user_id": self.headers.get("X-User-ID")}

        if isinstance(body, list):
            # Batch operations: deliberately allowed with NO size limit.
            responses: list[dict] = []
            for op in body:
                if isinstance(op, dict):
                    responses.append(
                        execute_query(
                            op.get("query"),
                            op.get("variables"),
                            op.get("operationName"),
                            context,
                        )
                    )
                else:
                    responses.append(
                        {"errors": [{"message": "batch entry must be an operation object"}]}
                    )
            self._send_json(200, responses)
        elif isinstance(body, dict):
            self._send_json(
                200,
                execute_query(
                    body.get("query"), body.get("variables"), body.get("operationName"), context
                ),
            )
        else:
            self._send_json(
                400, {"errors": [{"message": "request body must be an object or a list"}]}
            )


def create_server(host: str = "127.0.0.1", port: int = 4000) -> ThreadingHTTPServer:
    """Create (but do NOT start) the demo server.

    Separate from :func:`serve` so tests can construct it, read the bound port
    (``server.server_address[1]``, supports ``port=0``) and run it in a thread.
    """
    demo_server = type("DemoThreadingHTTPServer", (ThreadingHTTPServer,), {"daemon_threads": True})
    return demo_server((host, port), GraphQLRequestHandler)


def serve(host: str = "127.0.0.1", port: int = 4000) -> None:
    """Create and serve forever (blocking). Ctrl+C to stop."""
    get_schema()  # surface schema errors before binding
    server = create_server(host, port)
    print(f"demo-vulnerable-graphql on http://{host}:{port}/graphql", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    serve()
