#!/usr/bin/env bash
# Install the GraphQL Specialist Agent Pack on Linux.
# Idempotent: re-running creates the venv only if missing and re-syncs deps.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found (need Python >= 3.10)." >&2
    exit 1
fi

if [[ ! -d .venv ]]; then
    echo "Creating virtualenv .venv ..."
    python3 -m venv .venv
fi

echo "Installing dependencies ..."
.venv/bin/python -m pip install --upgrade pip >/dev/null
.venv/bin/python -m pip install -r INSTALLERS/requirements.txt

echo
echo "Installed. Activate with:  source .venv/bin/activate"
echo "Verify with:               .venv/bin/python -m pytest tests/ -v"
