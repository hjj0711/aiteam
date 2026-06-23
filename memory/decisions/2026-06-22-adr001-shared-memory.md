# ADR-001: Repository-Native Shared Memory

- **日期**: 2026-06-22
- **类型**: chore
- **关联**: SETUP-001

## 内容

Decision: Store shared project memory in concise Git-tracked Markdown files rather than relying on vendor chat memory.

Rationale: Codex and Claude Code can both read the same files, changes are reviewable, and stale facts can be corrected explicitly.

Consequences: Agents must read memory at task start and update it only when stable facts change.
