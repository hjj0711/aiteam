#!/usr/bin/env bash
# Cancel a task entirely: discard uncommitted changes, return to the base
# branch, and delete the task branch. Destructive — requires confirmation.
# Usage: scripts/task-revert.sh <task_id> [base_branch] [-y]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TASK_ID="${1:-}"
BASE_BRANCH="${2:-${AITEAM_BASE:-main}}"
ASSUME_YES="${3:-}"
if [[ -z "$TASK_ID" ]]; then
  echo "usage: scripts/task-revert.sh <task_id> [base_branch] [-y]" >&2
  exit 1
fi

BRANCH="aiteam/${TASK_ID}"
if ! git rev-parse --verify --quiet "$BRANCH" >/dev/null; then
  echo "No branch $BRANCH — nothing to revert." >&2
  exit 1
fi

echo "This will DISCARD all of task '$TASK_ID' changes:"
echo "  - drop uncommitted edits in the working tree"
echo "  - switch to '$BASE_BRANCH' and delete branch '$BRANCH'"
if [[ "$ASSUME_YES" != "-y" ]]; then
  read -r -p "Type the task id to confirm: " CONFIRM
  if [[ "$CONFIRM" != "$TASK_ID" ]]; then
    echo "Aborted."
    exit 1
  fi
fi

git checkout -f "$BASE_BRANCH"
git branch -D "$BRANCH"
echo "Reverted. Now on $BASE_BRANCH; branch $BRANCH deleted."
