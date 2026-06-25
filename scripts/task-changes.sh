#!/usr/bin/env bash
# Show everything a task changed: committed diff vs its base branch + anything
# still uncommitted in the working tree.
# Usage: scripts/task-changes.sh <task_id> [base_branch]   (base defaults to main)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TASK_ID="${1:-}"
BASE_BRANCH="${2:-${AITEAM_BASE:-main}}"
if [[ -z "$TASK_ID" ]]; then
  echo "usage: scripts/task-changes.sh <task_id> [base_branch]" >&2
  exit 1
fi

BRANCH="aiteam/${TASK_ID}"
if ! git rev-parse --verify --quiet "$BRANCH" >/dev/null; then
  echo "No branch $BRANCH — has this task run yet?" >&2
  exit 1
fi

FORK_POINT="$(git merge-base "$BASE_BRANCH" "$BRANCH" 2>/dev/null || echo "$BASE_BRANCH")"

echo "=== Commits on $BRANCH (since $BASE_BRANCH) ==="
git --no-pager log --oneline "${FORK_POINT}..${BRANCH}" || true

echo
echo "=== Committed diff (${BASE_BRANCH}...${BRANCH}) ==="
git --no-pager diff "${FORK_POINT}..${BRANCH}" --stat

echo
echo "Full diff: git diff ${FORK_POINT}..${BRANCH}"

if [[ -n "$(git status --porcelain)" ]]; then
  echo
  echo "=== Uncommitted changes in working tree ==="
  git --no-pager status --short
fi
