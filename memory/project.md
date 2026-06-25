# Project Memory

## Purpose

Provide a visual, personal multi-agent development workflow using existing Codex and Claude Code access.

## Working Agreement

- OpenADE is the visual execution surface.
- Git-tracked documents are the shared memory and source of truth.
- Claude is preferred for BA, UX, architecture, and review.
- Codex is preferred for implementation and focused code review.
- Model choice remains adjustable per task.

## Repository Conventions

- Role contracts live in `.aiteam/roles/`.
- Active work lives in `tasks/current.md`.
- Accepted product artifacts live in `docs/`.
- Stable cross-task facts live in `memory/`.
- Project code lives under `projects/` (path configurable via `.aiteam/config.yml`).

## Projects Path

Source code for each project lives under the directory set in `.aiteam/config.yml` (`projects.path`). The default is `projects/`. Developer agents must read this config before creating project code.

## Runtime Conventions

- Two supported ways to run: usage 1 = CLI orchestration (`runtime/run_demo.py`), usage 2 = manual per-role via OpenADE/terminal. LangGraph Studio is an optional debug tool, not a required mode.
- Real-engine runs stream each role's output live and pause for human guidance after `ba`/`architect`/`developer` (configurable via `_PAUSE_POINTS`).
- Every task's code changes go on an `aiteam/<task_id>` branch. View with `scripts/task-changes.sh <id>`; cancel with `scripts/task-revert.sh <id>`. Never commit task edits directly onto `main`.

