"""security-tools-mcp — reference MCP server wrapping external GraphQL
security tooling.

Tools:
    list_tools()                        -> what is available, honestly
    run_graphw00f(url)                  -> engine fingerprint via subprocess
    run_clairvoyance(url, wordlist)     -> field discovery via the pack skill

graphw00f is invoked as a subprocess; its binary is taken from the
``GRAPHW00F_BIN`` env var if set, otherwise ``graphw00f`` is looked up on
PATH. If it is not installed, tools degrade gracefully and return an honest
"not installed" dict — never a fabricated fingerprint. Clairvoyance runs via
the pack's clairvoyance-discovery skill (lazy import; the module imports
cleanly even while sibling SKILLS/ files are mid-write).
"""

import os
import pathlib
import shutil
import subprocess
import sys
from typing import Any

try:  # mcp 1.x (SPEC baseline)
    from mcp.server.fastmcp import FastMCP
except ImportError:  # mcp 2.x renamed FastMCP -> MCPServer
    from mcp.server.mcpserver import MCPServer as FastMCP

_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

mcp = FastMCP("security-tools-mcp")

_GRAPHW00F_TIMEOUT_S = 90


def _graphw00f_bin() -> str:
    return os.environ.get("GRAPHW00F_BIN", "").strip() or "graphw00f"


@mcp.tool()
def list_tools() -> dict[str, Any]:
    """List the security tools this server can run, with honest availability.

    Returns availability of graphw00f (subprocess on PATH / GRAPHW00F_BIN)
    and the clairvoyance-discovery skill (pack module — reported as bundled;
    runtime errors surface when actually invoked).
    """
    bin_path = shutil.which(_graphw00f_bin())
    return {
        "tools": [
            {
                "name": "graphw00f",
                "kind": "subprocess",
                "invocation": _graphw00f_bin(),
                "installed": bin_path is not None,
                "resolved_path": bin_path,
                "purpose": "GraphQL engine fingerprinting",
            },
            {
                "name": "clairvoyance",
                "kind": "bundled-skill (clairvoyance-discovery)",
                "installed": True,
                "purpose": "schema field discovery from 'Did you mean' errors",
            },
        ],
    }


@mcp.tool()
def run_graphw00f(url: str) -> dict[str, Any]:
    """Fingerprint the GraphQL engine behind 'url' using graphw00f.

    Runs the graphw00f binary (env GRAPHW00F_BIN, else 'graphw00f' on PATH)
    as a subprocess and returns its combined output. If the binary is not
    installed, returns an honest {"installed": false, ...} dict — no
    fabrication.
    """
    if not url or not str(url).strip():
        return {"error": "'url' is required."}
    bin_path = shutil.which(_graphw00f_bin())
    if bin_path is None:
        return {
            "installed": False,
            "error": f"graphw00f not found (looked for {_graphw00f_bin()!r} on PATH / GRAPHW00F_BIN).",
            "hint": "Install with `pipx install graphw00f` or set GRAPHW00F_BIN "
            "to the binary's full path. No fingerprint was produced.",
        }
    try:
        proc = subprocess.run(
            [bin_path, "-t", str(url)],
            check=False,
            capture_output=True,
            text=True,
            timeout=_GRAPHW00F_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return {
            "error": f"graphw00f timed out after {_GRAPHW00F_TIMEOUT_S}s against {url}."
        }
    except OSError as exc:
        return {"error": f"failed to launch graphw00f: {exc!r}"}
    return {
        "installed": True,
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "url": url,
    }


@mcp.tool()
def run_clairvoyance(url: str, wordlist: list[str] | None = None) -> dict[str, Any]:
    """Discover hidden/unlisted GraphQL fields via suggestion-based probing.

    Uses the pack's clairvoyance-discovery skill (works purely off "Did you
    mean" errors). 'wordlist' optionally overrides the default ~120 common
    field names. Returns {"discovered": [...], "suggestions_enabled": bool}.
    """
    if not url or not str(url).strip():
        return {"error": "'url' is required."}
    try:
        from common import loader
        from common.transport import HttpTransport

        skill = loader.load_skill("clairvoyance-discovery")
        transport = HttpTransport(str(url), timeout_s=30.0)
        return skill.run(transport, wordlist=wordlist)
    except ImportError as exc:
        return {
            "error": f"clairvoyance skill/transport unavailable: {exc!r}",
            "hint": "The pack's common/ and SKILLS/ trees must sit next to "
            "MCP_SERVERS/ (repo root = parents[2] of this file).",
        }
    except Exception as exc:  # noqa: BLE001 — MCP tool boundary must not raise
        return {"error": f"clairvoyance failed for {url}: {exc!r}"}


if __name__ == "__main__":
    mcp.run(transport="stdio")
