#!/usr/bin/env bash
# Uninstall the GraphQL Specialist Agent Pack: removes the virtualenv only.
# Leaves all pack source files untouched.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

if [[ -d .venv ]]; then
    rm -rf .venv
    echo "Removed .venv."
else
    echo "Nothing to remove (.venv not found)."
fi
