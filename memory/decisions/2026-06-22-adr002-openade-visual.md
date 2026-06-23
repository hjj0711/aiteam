# ADR-002: OpenADE As Visual Surface

- **日期**: 2026-06-22
- **类型**: chore
- **关联**: SETUP-001

## 内容

Decision: Use OpenADE for visual task execution, cross-provider planning, diffs, snapshots, and worktree isolation.

Rationale: It reuses existing Codex and Claude Code authentication without introducing a second orchestration billing layer.

Consequences: The BA-to-QA lifecycle is enforced by repository role contracts and human gates rather than a fully automatic DAG.
