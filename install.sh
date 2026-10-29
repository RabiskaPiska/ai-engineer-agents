#!/usr/bin/env bash
# Install the AI-engineer agent pack (run from the unzipped ai-engineer-agents folder).
#   ./install.sh            -> Claude Code  (~/.claude/agents, ~/.claude/skills)
#   ./install.sh --opencode -> OpenCode     (~/.config/opencode/agents, ~/.config/opencode/skills)
# Existing files with the same name are backed up to *.bak-<timestamp> before being replaced.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
if [ "${1:-}" = "--opencode" ]; then src="$here/opencode"; dst="$HOME/.config/opencode"; else src="$here/claude"; dst="$HOME/.claude"; fi
ts="$(date +%Y%m%d-%H%M%S)"
for kind in agents skills; do
  [ -d "$src/$kind" ] || continue
  mkdir -p "$dst/$kind"
  for item in "$src/$kind"/*; do
    name="$(basename "$item")"; target="$dst/$kind/$name"
    [ -e "$target" ] && mv "$target" "$target.bak-$ts"
    cp -r "$item" "$target"; echo "installed $kind/$name"
  done
done
[ "${1:-}" = "--opencode" ] && echo "Now merge opencode/opencode-mcp.jsonc into $dst/opencode.jsonc (the mcp block)."
echo "Done. Restart Claude Code / OpenCode to pick up new agents."
