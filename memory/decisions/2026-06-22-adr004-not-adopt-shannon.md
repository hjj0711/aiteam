# ADR-004: Do Not Adopt Shannon Yet

- **日期**: 2026-06-22
- **类型**: chore
- **关联**: SETUP-001

## 内容

Decision: Use Shannon as a reference implementation, not as the foundation of this personal workspace.

Rationale: Shannon implements many desired controls, but the audited release still masks Go and Python test failures in CI, has temporarily disabled desktop builds, requires a comparatively heavy service stack, and its published agent-core image is not native to this ARM Mac.

Consequences: Re-evaluate Shannon after its CI becomes fail-closed, desktop releases resume, and ARM images are published.
