# Multi-Agent Runtime Evaluation

Evaluated on 2026-06-22 for a personal BA, UX, architecture, development, QA, and review workflow using Codex and Claude.

LangGraph itself is MIT-licensed. LangSmith currently offers one free Developer seat with 5,000 base traces per month, which is sufficient for personal visual debugging if tracing is sampled and capped. Model API charges are separate; Codex and Claude subscription logins can instead be reached through bounded CLI adapters.

## Required Controls

- Durable short-term checkpoints and curated long-term memory.
- Maximum graph steps, per-agent turns, tool calls, elapsed time, tokens, and cost.
- Detection of repeated actions and repeated observations with no measurable progress.
- Bounded retries for transient failures only.
- Human approval after requirements and design, and before destructive tools.
- Evidence-based completion: tests and review findings must be attached to the final state.
- Resume after interruption, trace inspection, deterministic unit tests, and model-independent adapters.

## Findings

| Candidate | Strengths | Blocking gaps | Decision |
| --- | --- | --- | --- |
| LangGraph + Studio | Durable checkpoints, graph state, interrupts, recursion limit, retry policy, step timeout, visual state/debugging, node-level tests | Token/cost and convergence limits must be implemented in project state; Studio is not drag-and-drop | Adopt as runtime |
| OpenADE | Free visual Codex/Claude console, planning, diffs, snapshots, worktrees, existing subscription login | No durable role DAG, runtime budget ledger, convergence detector, or automated evaluation gate | Keep as optional coding UI |
| Flowise Agentflow V2 | Easiest free visual builder; max agent iterations, loop count, checkpoints, HITL | Flow state is execution-scoped; no complete built-in timeout/retry/budget/eval story; hosted evaluations are not part of the free local core | Do not use as core runtime |
| AutoGen + Studio | Useful termination policies, save/load state, flexible memory, multi-agent APIs | Studio is documented as a prototype; production controls and visual lifecycle need more integration | Prototype only |
| CrewAI | Simple role/crew model, memory, max iterations/time/retries | Full visual management is commercial; weaker graph-level persistence and debugging fit for this project | Not selected |
| Shannon | Temporal durability, token budget, ReAct convergence controls, WASI sandbox, HITL, audit-oriented architecture | Audited CI masks some test failures; desktop build disabled; heavy stack; ARM image gap; OpenAI key required for semantic memory | Reference only |

## Implemented Runtime (as of 2026-06-25)

The skeleton evaluated above is now wired in `runtime/`. Beyond the orchestration graph and budget ledger, three operator-facing controls are implemented:

- **Live output** — `ClaudeEngine(stream=True)` uses `claude --output-format stream-json` and echoes each role's text and tool activity to the terminal as it is produced; `run_demo.py` drives the graph with `graph.stream(stream_mode="updates")` for node-level progress. The run is no longer a black box.
- **Human-in-the-loop guidance** — `build_graph(interrupt_after=[...])` pauses after configurable nodes (default `ba`, `architect`, `developer`). On pause, `run_demo.py` shows the artifact and reads free-text guidance into `state.human_feedback`, which `engine._build_prompt` injects as `HUMAN GUIDANCE` for the next role and the developer node clears after one use.
- **Change isolation & revert** — `vcs.py` puts every task's developer edits on a dedicated `aiteam/<task_id>` branch and commits each iteration, so changes are easy to view (`scripts/task-changes.sh`) and cancel (`scripts/task-revert.sh`). This is the concrete "human approval before destructive tools" boundary for code edits and honors the "no shared working tree" rule. Active only when `vcs_enabled` (real engine); the stub stays side-effect free.

## Guardrail Contract

Initial defaults for personal use:

| Limit | Default |
| --- | ---: |
| Graph recursion limit | 30 steps |
| Per-role model calls | 6 |
| Total model calls | 24 |
| Total tool calls | 40 |
| Same action fingerprint | Stop on third occurrence |
| Similar no-progress observations | Stop after 2 repeats |
| Transient retries | 2 with backoff |
| Node timeout | 10 minutes |
| Workflow timeout | 60 minutes |
| QA repair cycles | 2 |

Token and cost limits are mandatory configuration, because the correct numbers depend on whether a role uses an API key or an existing CLI subscription. Missing limits must fail validation before a run begins.

## Memory Model

1. Thread state: LangGraph checkpointer for exact resumability.
2. Long-term structured memory: namespaced store for stable facts and reusable lessons.
3. Repository memory: reviewed Markdown in `memory/` for cross-provider portability.
4. Artifacts: requirements, design, architecture, patches, test output, and review reports remain Git-tracked.

Raw chain-of-thought, full chat transcripts, secrets, and unreviewed guesses are never promoted to durable memory.

## Source Audit

- [Wayland Agent book: Agent basics](https://waylandz.com/ai-agent-book/%E7%AC%AC01%E7%AB%A0-Agent%E7%9A%84%E6%9C%AC%E8%B4%A8/) and [ReAct loop](https://waylandz.com/ai-agent-book/%E7%AC%AC02%E7%AB%A0-ReAct%E5%BE%AA%E7%8E%AF/) define the needed Agent components and stop conditions.
- LangGraph official documentation covers [memory](https://docs.langchain.com/oss/python/langgraph/memory), [persistence](https://docs.langchain.com/oss/python/langgraph/persistence), [recursion limits](https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT), and [graph testing](https://docs.langchain.com/oss/python/langgraph/test).
- [Flowise Agentflow V2](https://docs.flowiseai.com/using-flowise/agentflowv2) confirms max iterations, loop count, and checkpoint-based human input, but its Flow State is scoped to a single execution.
- [AutoGen termination](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/termination.html) exposes message, timeout, token-usage, and external termination conditions.
- [Shannon](https://github.com/Kocoro-lab/Shannon) source was inspected at its 2026-06-02 repository state, including ReAct stopping logic, defaults, tests, CI, release workflow, and environment requirements.
- [LangSmith pricing](https://www.langchain.com/pricing) documents the personal Developer plan and included trace allowance; [LangGraph](https://github.com/langchain-ai/langgraph) is MIT-licensed.
