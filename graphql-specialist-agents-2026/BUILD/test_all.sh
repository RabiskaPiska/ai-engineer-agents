#!/usr/bin/env bash
# Run the full build check: pytest suite, then pack validation.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# Prefer the project venv when present (Linux and Windows layouts).
if [[ -x .venv/bin/python ]]; then
    PY=.venv/bin/python
elif [[ -x .venv/Scripts/python.exe ]]; then
    PY=.venv/Scripts/python.exe
else
    PY=python3
fi

echo "== pytest =="
"$PY" -m pytest tests/ -v

echo
echo "== validate_agents =="
"$PY" BUILD/validate_agents.py

echo
echo "ALL GREEN"
