# ADR-003: LangGraph As Controlled Runtime

- **日期**: 2026-06-22
- **类型**: chore
- **关联**: SETUP-001

## 内容

Decision: Use LangGraph as the orchestration runtime and LangGraph Studio as the primary execution debugger. Keep OpenADE as an optional visual coding console for Codex and Claude Code.

Rationale: The runtime needs durable checkpoints, resumable human approval, explicit graph state, recursion limits, retry policies, timeouts, testable nodes, and persistent memory. A visual task console alone cannot enforce these guarantees.

Consequences: Budget accounting, repeated-action detection, evidence gates, and model-provider adapters remain project code and require focused tests. LangGraph Studio is a graph debugger rather than a drag-and-drop workflow builder.
