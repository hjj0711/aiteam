"""Per-task git isolation.

Every task gets a dedicated branch (`aiteam/<task_id>`) so a run's code
changes are easy to **see** (diff the branch against its base) and easy to
**cancel** (delete the branch, return to the base). The developer node calls
`start` once per task and `snapshot` after each edit iteration. The same model
is exposed to the manual flow via `scripts/task-*.sh`.

Everything fails soft: if git is missing or a command errors, we return a note
instead of raising, so a VCS hiccup never crashes the workflow.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BRANCH_PREFIX = "aiteam/"


def branch_name(task_id: str) -> str:
    """Deterministic branch name for a task."""
    safe = (task_id or "task").strip().replace(" ", "-")
    return f"{_BRANCH_PREFIX}{safe}"


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
    )


def _head() -> str | None:
    r = _git("rev-parse", "HEAD")
    return r.stdout.strip() if r.returncode == 0 else None


def _current_branch() -> str | None:
    r = _git("rev-parse", "--abbrev-ref", "HEAD")
    return r.stdout.strip() if r.returncode == 0 else None


def _branch_exists(branch: str) -> bool:
    return _git("rev-parse", "--verify", "--quiet", branch).returncode == 0


def start(task_id: str) -> dict[str, str]:
    """Ensure the run is on the task branch.

    Returns {base, branch, base_branch, note}. `base` is the commit the branch
    started from (used for diff/revert); `base_branch` is where we came from so
    revert can switch back.
    """
    branch = branch_name(task_id)
    base = _head()
    if base is None:
        return {"branch": branch, "note": "git unavailable — VCS isolation skipped"}

    origin = _current_branch() or "HEAD"

    # Already on the task branch (resume or fix-loop re-entry): nothing to do.
    if origin == branch:
        return {"base": base, "branch": branch, "base_branch": branch,
                "note": f"on branch {branch}"}

    if _branch_exists(branch):
        co = _git("checkout", branch)
        note = f"switched to existing branch {branch}"
    else:
        co = _git("checkout", "-b", branch)
        note = f"created branch {branch} from {origin}"

    if co.returncode != 0:
        return {"base": base, "branch": branch, "base_branch": origin,
                "note": f"branch switch failed ({co.stderr.strip()}) — editing on {origin}"}

    return {"base": base, "branch": branch, "base_branch": origin, "note": note}


def snapshot(task_id: str, message: str) -> dict[str, str]:
    """Stage everything and commit if there is anything to commit.

    Returns {commit, note}. `commit` is the new sha, or absent when the tree was
    clean (e.g. the engine produced no file changes).
    """
    add = _git("add", "-A")
    if add.returncode != 0:
        return {"note": f"git add failed: {add.stderr.strip()}"}

    # Nothing staged -> no commit (developer may have only written docs/memory,
    # or stub engine made no edits).
    if _git("diff", "--cached", "--quiet").returncode == 0:
        return {"note": "no file changes to snapshot"}

    commit = _git("commit", "-m", f"aiteam({task_id}): {message}", "--no-verify")
    if commit.returncode != 0:
        return {"note": f"commit failed: {commit.stderr.strip()}"}

    sha = _head() or ""
    return {"commit": sha, "note": f"snapshot {sha[:8]} committed"}
