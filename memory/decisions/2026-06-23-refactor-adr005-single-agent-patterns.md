# ADR-005: Adopt Planning, Reflection, Routing, And Edit-Test-Fix Patterns In Role Contracts

- **日期**: 2026-06-23
- **类型**: refactor
- **关联**: SETUP-001

## 内容

Decision: Encode four single-agent and orchestration patterns from the AI Agent book directly into the role contracts under `.aiteam/roles/`, ahead of any runtime work.

- Architect (`architect.md`): task decomposition now declares Produces/Consumes/Boundaries, plus a Coverage Evaluation step (map every acceptance criterion to a task and a verification path) bounded by deterministic guardrails and a 3-pass limit. (Book Part 4, Ch10 Planning.)
- QA (`qa.md`): a Reflection feedback loop that returns an actionable repair packet on failure, bounded to 2 repair cycles with same-defect escalation. (Book Part 4, Ch11 Reflection.)
- Orchestrator (`orchestrator.md`): complexity routing — Simple goes straight to Development+QA, Standard/Complex run the full chain — with guardrails forcing the heavier tier on ambiguity or contract/security impact. (Book Part 5, Ch13.4.)
- Developer (`developer.md`): an Edit-Test-Fix loop, a Fix-Loop Guard (stop after 5 iterations or on oscillating fixes), and Test Integrity rules. Developer owns the tests for its own feature; QA/Reviewer remain independent black-box verifiers. (Book Part 9, Ch29 Agentic Coding; Ch13.5 context-boundary split.)

Rationale: The previous role chain was the "telephone game" anti-pattern (Ch13.11) and the roles lacked coverage evaluation, a feedback-driven repair loop, complexity routing, and a bounded fix loop. These are prompt/contract-level changes that improve quality and convergence without waiting for the LangGraph runtime.

Consequences: The numeric bounds (3 coverage passes, 2 QA repair cycles, 5 fix iterations) are stated in the contracts and must stay consistent with the Guardrail Contract in `docs/runtime-evaluation.md`; when the LangGraph runtime lands, enforce these limits in graph state rather than relying on prompt adherence. Contract changes are not auto-testable — validate by running a real task in OpenADE.
