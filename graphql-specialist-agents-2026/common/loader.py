"""Module loader for hyphen-named skill / MCP-server folders (SPEC.md).

Skill files live in non-importable directories (``SKILLS/schema-fingerprinting/``),
so this loader imports them by explicit file path via ``importlib`` and caches
them in ``sys.modules`` under safe names.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys
from types import ModuleType

__all__ = ["load_mcp_server", "load_skill"]

_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _ensure_root_on_path() -> None:
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))


def _load_from_file(path: pathlib.Path, module_name: str) -> ModuleType:
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot build import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_skill(name: str) -> ModuleType:
    """Import ``SKILLS/<name>/skill.py`` by folder name and return the module.

    Also guarantees the pack root is on ``sys.path`` so the skill's
    ``from common...`` imports resolve.
    """
    _ensure_root_on_path()
    path = _ROOT / "SKILLS" / name / "skill.py"
    if not path.is_file():
        raise FileNotFoundError(f"skill not found: {path}")
    module_name = f"graphql_pack_skills.{name.replace('-', '_')}"
    return _load_from_file(path, module_name)


def load_mcp_server(name: str) -> ModuleType:
    """Import ``MCP_SERVERS/<name>/server.py`` by folder name and return the module.

    Importing must NOT start the server (server.py guards with
    ``if __name__ == "__main__"``), so tests can introspect ``mcp`` safely.
    """
    _ensure_root_on_path()
    path = _ROOT / "MCP_SERVERS" / name / "server.py"
    if not path.is_file():
        raise FileNotFoundError(f"MCP server not found: {path}")
    module_name = f"graphql_pack_mcp.{name.replace('-', '_')}"
    return _load_from_file(path, module_name)
