"""Build the pack: zip the whole repo into graphql-specialist-agents-2026.zip.

Usage (from anywhere):
    python BUILD/build_pack.py

Excludes __pycache__/, .venv/, .pytest_cache/, .git/, and any previous zip.
Exits 0 and prints the output path + size on success; non-zero on failure.
"""

from __future__ import annotations

import pathlib
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
ZIP_NAME = "graphql-specialist-agents-2026.zip"
EXCLUDE_DIR_NAMES = {"__pycache__", ".venv", ".pytest_cache", ".git", ".ruff_cache"}


def excluded(path: pathlib.Path) -> bool:
    rel_parts = path.relative_to(ROOT).parts
    return any(part in EXCLUDE_DIR_NAMES for part in rel_parts[:-1]) or (
        path.name in EXCLUDE_DIR_NAMES
    )


def build(root: pathlib.Path = ROOT, out: pathlib.Path | None = None) -> pathlib.Path:
    out = out or (root / ZIP_NAME)
    files = [
        p
        for p in sorted(root.rglob("*"))
        if p.is_file() and not excluded(p) and p.name != ZIP_NAME
    ]
    if not files:
        raise RuntimeError(f"no files to pack under {root}")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            arcname = pathlib.Path(root.name) / path.relative_to(root)
            zf.write(path, arcname=str(arcname))
    return out


def main() -> int:
    try:
        out = build()
    except Exception as exc:  # noqa: BLE001 — report and fail, don't crash ugly
        print(f"BUILD FAILED: {exc}", file=sys.stderr)
        return 1
    size = out.stat().st_size
    n_entries = len(zipfile.ZipFile(out).namelist())
    print(f"wrote {out} ({size} bytes, {n_entries} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
