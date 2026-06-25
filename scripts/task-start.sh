#!/usr/bin/env bash
# Start (or resume) a task on its own branch so the changes are isolated.
# Usage: scripts/task-start.sh <task_id>
# Mirrors runtime/aiteam_runtime/vcs.py for the manual flow.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TASK_ID="${1:-}"
if [[ -z "$TASK_ID" ]]; then
  echo "usage: scripts/task-start.sh <task_id>" >&2
  exit 1
fi

BRANCH="aiteam/${TASK_ID}"

if git rev-parse --verify --quiet "$BRANCH" >/dev/null; then
  git checkout "$BRANCH"
  echo "Resumed on existing branch: $BRANCH"
else
  FROM="$(git rev-parse --abbrev-ref HEAD)"
  git checkout -b "$BRANCH"
  echo "Created branch: $BRANCH (from $FROM)"
fi

echo "Edit code now. View changes: scripts/task-changes.sh $TASK_ID"
echo "Cancel everything:           scripts/task-revert.sh  $TASK_ID"
