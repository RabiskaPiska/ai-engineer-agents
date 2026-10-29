"""graphql-mcp — reference MCP server wrapping the pack's GraphQL skills.

Tools:
    introspect(url)                          -> full introspection result
    run_query(url, query, variables, headers)-> raw GraphQL JSON response
    schema_map(url)                          -> compact schema map + root fields

Skills are loaded lazily via ``common.loader.load_skill`` at call time, so
this module imports cleanly even while sibling SKILLS/ files are mid-write.
All heavy imports live inside the tool functions for the same reason.
"""

import pathlib
import sys
from typing import Any

try:  # mcp 1.x (SPEC baseline)
    from mcp.server.fastmcp import FastMCP
except ImportError:  # mcp 2.x renamed FastMCP -> MCPServer
    from mcp.server.mcpserver import MCPServer as FastMCP

_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

mcp = FastMCP("graphql-mcp")


def _loader():
    from common import loader  # lazy: sibling common/ may be mid-write

    return loader


def _transport(url: str, headers: dict | None = None):
    from common.transport import HttpTransport  # lazy

    return HttpTransport(url, headers=headers, timeout_s=30.0)


def _skill_error(stage: str, exc: Exception) -> dict[str, Any]:
    return {
        "error": f"{stage} unavailable: {exc!r}",
        "hint": "The pack's common/ or SKILLS/ modules must exist next to "
        "MCP_SERVERS/ (repo root = parents[2] of this file).",
    }


@mcp.tool()
def introspect(url: str) -> dict[str, Any]:
    """Run introspection enumeration against a GraphQL endpoint.

    Returns {"introspection_enabled", "schema_map", "roots"} produced by the
    pack's introspection-enumeration skill (full introspection, fallback to a
    minimal query, then suggestion-mining; introspection_enabled is reported
    honestly as False when blocked).
    """
    try:
        loader = _loader()
        skill = loader.load_skill("introspection-enumeration")
        transport = _transport(url)
        return skill.run(transport, full=True)
    except ImportError as exc:
        return _skill_error("introspection skill/transport", exc)
    except Exception as exc:  # noqa: BLE001 — MCP tool boundary must not raise
        return {"error": f"introspection failed for {url}: {exc!r}"}


@mcp.tool()
def run_query(
    url: str,
    query: str,
    variables: dict | None = None,
    headers: dict | None = None,
) -> dict[str, Any]:
    """Execute a raw GraphQL operation against 'url' (POST /graphql-style).

    Returns the raw GraphQL JSON: {"data": ..., "errors": [...]} (errors may
    be absent). 'headers' are extra per-call headers (auth differences are
    expressed as headers, e.g. {"X-User-ID": "u2"}).
    """
    if not url or not query.strip():
        return {"error": "Both 'url' and a non-empty 'query' are required."}
    try:
        transport = _transport(url, headers=headers)
        return transport.execute(query, variables=variables)
    except ImportError as exc:
        return _skill_error("transport module", exc)
    except Exception as exc:  # noqa: BLE001 — MCP tool boundary must not raise
        return {"error": f"query failed for {url}: {exc!r}"}


@mcp.tool()
def schema_map(url: str) -> dict[str, Any]:
    """Return a compact schema map for a GraphQL endpoint.

    Returns {"types": [{kind, name, fields: [...]}], "roots": {"query": [...],
    "mutation": [...], "subscription": [...]}} as produced by the
    introspection-enumeration skill, or a friendly error dict when
    introspection is blocked/unavailable.
    """
    try:
        loader = _loader()
        skill = loader.load_skill("introspection-enumeration")
        transport = _transport(url)
        result = skill.run(transport, full=True)
    except ImportError as exc:
        return _skill_error("introspection skill/transport", exc)
    except Exception as exc:  # noqa: BLE001 — MCP tool boundary must not raise
        return {"error": f"schema mapping failed for {url}: {exc!r}"}
    if "error" in result:
        return result
    return {
        "introspection_enabled": result.get("introspection_enabled"),
        "schema_map": result.get("schema_map"),
        "roots": result.get("roots"),
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
