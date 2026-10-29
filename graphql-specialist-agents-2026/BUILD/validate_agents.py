"""Validate the pack against SPEC.md and import every skill via common.loader.

Checks:
  1. Layout — all 10 SKILLS/<name>/ dirs with skill.py + README.md;
     5 MCP_SERVERS/<name>/ with server.py + config.json (README.md expected);
     common/ modules (transport.py, findings.py, errors.py, loader.py);
     AGENTS/graphql-specialist/ agent files; examples/demo_target.py.
  2. Agent config.json parses and has the required top-level keys.
  3. Imports every skill through common.loader.load_skill() and reports
     pass/fail per module; each loaded skill must expose run().
  4. MCP server imports are attempted too, but a missing `mcp` dependency is
     reported as SKIP, not FAIL.

Prints one PASS/FAIL/SKIP line per check and exits non-zero on any failure.

Usage:
    python BUILD/validate_agents.py
"""

from __future__ import annotations

import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

REQUIRED_SKILLS = [
    "schema-fingerprinting",
    "introspection-enumeration",
    "clairvoyance-discovery",
    "bola-idor-testing",
    "alias-abuse-testing",
    "batch-abuse-testing",
    "complexity-dos-testing",
    "deep-nesting-testing",
    "nplus1-detection",
    "report-generation",
]
REQUIRED_MCP_SERVERS = [
    "github-mcp",
    "graphql-mcp",
    "custom-api-mcp",
    "security-tools-mcp",
    "postgres-mcp",
]
COMMON_MODULES = ["transport.py", "findings.py", "errors.py", "loader.py"]
AGENT_DIR = _ROOT / "AGENTS" / "graphql-specialist"
AGENT_FILES_REQUIRED = [
    "agent.md",
    "config.json",
    "github-sources.md",
    "README.md",
    "CHANGELOG.md",
]
AGENT_FILES_EXPECTED = ["honestscore.md"]  # in SPEC layout; warn-only if absent
AGENT_CONFIG_KEYS = {
    "name",
    "version",
    "inputs",
    "outputs",
    "mcp_servers",
    "skills",
    "limits",
    "human_in_the_loop",
}

failures: list[str] = []
warns: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> bool:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(f"{label}: {detail}" if detail else label)
    return ok


def warn(label: str, detail: str) -> None:
    print(f"[WARN] {label} — {detail}")
    warns.append(f"{label}: {detail}")


def check_file(path: pathlib.Path, label: str) -> bool:
    return check(f"file {label}", path.is_file(), str(path.relative_to(_ROOT)))


def main() -> int:
    print(f"Validating pack at {_ROOT}\n")

    # --- 1. common/ modules ------------------------------------------------
    for mod in COMMON_MODULES:
        check_file(_ROOT / "common" / mod, f"common/{mod}")

    # --- 2. SKILLS/ ---------------------------------------------------------
    for name in REQUIRED_SKILLS:
        sdir = _ROOT / "SKILLS" / name
        check_file(sdir / "skill.py", f"SKILLS/{name}/skill.py")
        check_file(sdir / "README.md", f"SKILLS/{name}/README.md")

    # --- 3. MCP_SERVERS/ ----------------------------------------------------
    for name in REQUIRED_MCP_SERVERS:
        mdir = _ROOT / "MCP_SERVERS" / name
        check_file(mdir / "server.py", f"MCP_SERVERS/{name}/server.py")
        check_file(mdir / "config.json", f"MCP_SERVERS/{name}/config.json")
        if not (mdir / "README.md").is_file():
            warn(f"MCP_SERVERS/{name}/README.md", "expected by SPEC layout, not found")

    # --- 4. agent files ------------------------------------------------------
    for fname in AGENT_FILES_REQUIRED:
        check_file(AGENT_DIR / fname, f"AGENTS/graphql-specialist/{fname}")
    for fname in AGENT_FILES_EXPECTED:
        if not (AGENT_DIR / fname).is_file():
            warn(f"AGENTS/graphql-specialist/{fname}", "in SPEC layout, not found (warn-only)")
    check_file(_ROOT / "examples" / "demo_target.py", "examples/demo_target.py")

    # --- 5. agent config.json sanity ----------------------------------------
    cfg_path = AGENT_DIR / "config.json"
    if cfg_path.is_file():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            check("agent config.json parses", True)
            missing_keys = AGENT_CONFIG_KEYS - set(cfg)
            check(
                "agent config.json required keys",
                not missing_keys,
                f"missing: {sorted(missing_keys)}" if missing_keys else "",
            )
            skills_mismatch = set(cfg.get("skills", [])) ^ set(REQUIRED_SKILLS)
            check(
                "agent config.json skills == 10 pack skills",
                not skills_mismatch,
                f"mismatch: {sorted(skills_mismatch)}" if skills_mismatch else "",
            )
        except (json.JSONDecodeError, OSError) as exc:
            check("agent config.json parses", False, repr(exc))

    # --- 6. import every skill via common.loader -----------------------------
    print()
    try:
        from common import loader
    except Exception as exc:  # noqa: BLE001
        check("import common.loader", False, repr(exc))
    else:
        check("import common.loader", True)
        for name in REQUIRED_SKILLS:
            try:
                mod = loader.load_skill(name)
                ok = hasattr(mod, "run")
                check(
                    f"skill import: {name}",
                    ok,
                    "" if ok else "loaded but has no run()",
                )
            except Exception as exc:  # noqa: BLE001 — report per module
                check(f"skill import: {name}", False, f"{type(exc).__name__}: {exc}")

        # --- 7. MCP server imports (SKIP, not FAIL, if `mcp` is not installed)
        try:
            import mcp  # noqa: F401

            mcp_available = True
        except ImportError:
            mcp_available = False
        for name in REQUIRED_MCP_SERVERS:
            if not mcp_available:
                print(f"[SKIP] mcp server import: {name} — 'mcp' package not installed")
                continue
            try:
                loader.load_mcp_server(name)
                check(f"mcp server import: {name}", True)
            except Exception as exc:  # noqa: BLE001
                check(
                    f"mcp server import: {name}",
                    False,
                    f"{type(exc).__name__}: {exc}",
                )

    # --- summary --------------------------------------------------------------
    print()
    if warns:
        print(f"{len(warns)} warning(s):")
        for w in warns:
            print(f"  - {w}")
    if failures:
        print(f"VALIDATION FAILED: {len(failures)} failure(s):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("VALIDATION PASSED: layout + imports OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
