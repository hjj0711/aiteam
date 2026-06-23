# AI Team Operating Contract

This repository is a shared workspace for Codex and Claude Code.

## Source Of Truth

Use this precedence order:

1. The user's latest explicit instruction.
2. Accepted requirements in `docs/requirements.md`.
3. Accepted architecture and decisions in `docs/architecture.md` and `memory/decisions/`.
4. Current task state in `tasks/current.md`.
5. Existing code and tests.

Chat history is context, not durable truth.

## Start Of Every Task

1. Read `.aiteam/config.yml` for project configuration.
2. Read the role file named by the task.
3. Read `memory/project.md`, `memory/decisions/`, `memory/lessons/`, and `tasks/current.md`.
4. Inspect the repository and existing uncommitted changes before editing.
5. State assumptions in the task artifact instead of silently inventing requirements.

## Delivery Flow

The default flow is BA -> UX -> Architecture -> Human approval -> Development -> QA -> Review.

- Do not implement an unaccepted requirement.
- Do not let multiple write agents share one working tree.
- Prefer deterministic workflows and explicit acceptance criteria over free-form agent discussion.
- A failed quality gate returns work to Development with a reproducible failure report.

## Durable Memory

- Record stable project facts in `memory/project.md`.
- Record accepted decisions as individual files in `memory/decisions/` (`YYYY-MM-DD-type-slug.md`).
- Record reusable lessons as individual files in `memory/lessons/` (`YYYY-MM-DD-type-slug.md`).
- Record active ownership and status in `tasks/current.md`.
- Keep memory concise. Remove stale facts when replacing them.

## Quality Gates

Before marking work complete:

1. Run the narrowest relevant tests.
2. Run broader checks when shared contracts or user-facing flows changed.
3. Inspect the final diff.
4. Report commands run, results, residual risks, and files intentionally not changed.
5. Update durable memory only when the work created a reusable fact or decision.

## Safety

- Never store credentials in the repository.
- Never discard user changes.
- Do not run destructive Git commands without explicit user approval.
- Keep external side effects behind a human approval step.

