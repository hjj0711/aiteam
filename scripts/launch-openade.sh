#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP="$ROOT/tools/OpenADE.app"
EXECUTABLE="$APP/Contents/MacOS/OpenADE"

if [[ ! -x "$EXECUTABLE" ]]; then
  echo "OpenADE is not installed at $APP" >&2
  exit 1
fi

export PATH="$ROOT/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
exec "$EXECUTABLE" "$ROOT"

