"""LangGraph orchestration runtime for the aiteam workspace.

This package turns the role contracts in `.aiteam/roles/` into a controlled
multi-agent graph: complexity routing, coverage evaluation, bounded QA repair
cycles, a Fix-Loop guard, and a budget ledger enforced as graph state.

The default engine is a deterministic stub so the graph runs and tests without
any API key. Swap in a real Codex/Claude CLI engine via `engine.RoleEngine`.
"""

from .graph import build_workflow, build_graph
from .state import AiTeamState, initial_state
from .guardrails import DEFAULT_LIMITS, new_ledger, validate_limits

__all__ = [
    "build_workflow",
    "build_graph",
    "AiTeamState",
    "initial_state",
    "DEFAULT_LIMITS",
    "new_ledger",
    "validate_limits",
]
