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

