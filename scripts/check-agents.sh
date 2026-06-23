#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$ROOT/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

echo "Workspace: $ROOT"
echo

echo "Codex"
codex --version
codex login status
echo

echo "Claude Code"
claude --version
claude auth status
echo

if [[ -d "$ROOT/tools/OpenADE.app" ]]; then
  echo "OpenADE: installed at $ROOT/tools/OpenADE.app"
else
  echo "OpenADE: not installed under tools/"
  exit 1
fi

