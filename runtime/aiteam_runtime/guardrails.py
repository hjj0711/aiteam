"""Budget ledger and deterministic guardrails.

Mirrors the Guardrail Contract in `docs/runtime-evaluation.md`. Token and cost
limits are mandatory: `validate_limits` fails closed if they are unset, because
the correct numbers depend on whether a role uses an API key or a CLI login.
"""

from __future__ import annotations

import time
from typing import Any

# Defaults from docs/runtime-evaluation.md. Token/cost are 0 here on purpose so
# validate_limits forces the caller to set them before a run starts.
DEFAULT_LIMITS: dict[str, Any] = {
    "max_graph_steps": 30,       # graph recursion limit
    "max_role_calls": 6,         # per-role model calls
    "max_total_model_calls": 24,
    "max_tool_calls": 40,
    "node_timeout_s": 600,       # 10 minutes
    "workflow_timeout_s": 3600,  # 60 minutes
    "max_qa_repair_cycles": 2,
    "max_fix_iterations": 5,
    "max_coverage_passes": 3,
    "repeat_action_stop": 3,     # stop on third identical action fingerprint
    "max_total_tokens": 0,       # MUST be set > 0 by the caller
    "max_total_cost_usd": 0.0,   # MUST be set > 0 by the caller
}


class BudgetError(ValueError):
    """Raised when limits are invalid before a run begins."""


def validate_limits(limits: dict[str, Any]) -> None:
    if limits.get("max_total_tokens", 0) <= 0:
        raise BudgetError("max_total_tokens must be configured (> 0) before a run")
    if limits.get("max_total_cost_usd", 0.0) <= 0:
        raise BudgetError("max_total_cost_usd must be configured (> 0) before a run")


def new_ledger(limits: dict[str, Any] | None = None) -> dict[str, Any]:
    merged = {**DEFAULT_LIMITS, **(limits or {})}
    validate_limits(merged)
    return {
        "limits": merged,
        "spent": {
            "model_calls": 0,
            "tool_calls": 0,
            "tokens": 0,
            "cost_usd": 0.0,
        },
        "role_calls": {},          # role -> count
        "action_counts": {},       # fingerprint -> count
        "started_at": time.time(),
    }


def charge(
    ledger: dict[str, Any],
    role: str,
    *,
    model_calls: int = 1,
    tool_calls: int = 0,
    tokens: int = 0,
    cost_usd: float = 0.0,
) -> None:
    spent = ledger["spent"]
    spent["model_calls"] += model_calls
    spent["tool_calls"] += tool_calls
    spent["tokens"] += tokens
    spent["cost_usd"] += cost_usd
    ledger["role_calls"][role] = ledger["role_calls"].get(role, 0) + model_calls


def record_action(ledger: dict[str, Any], fingerprint: str) -> int:
    counts = ledger["action_counts"]
    counts[fingerprint] = counts.get(fingerprint, 0) + 1
    return counts[fingerprint]


def check(ledger: dict[str, Any], role: str | None = None) -> tuple[bool, str]:
    """Return (ok, reason). ok=False means a hard budget limit was crossed."""
    limits = ledger["limits"]
    spent = ledger["spent"]

    if spent["model_calls"] > limits["max_total_model_calls"]:
        return False, "max_total_model_calls exceeded"
    if spent["tool_calls"] > limits["max_tool_calls"]:
        return False, "max_tool_calls exceeded"
    if spent["tokens"] > limits["max_total_tokens"]:
        return False, "max_total_tokens exceeded"
    if spent["cost_usd"] > limits["max_total_cost_usd"]:
        return False, "max_total_cost_usd exceeded"
    if role is not None and ledger["role_calls"].get(role, 0) > limits["max_role_calls"]:
        return False, f"max_role_calls exceeded for {role}"
    if time.time() - ledger["started_at"] > limits["workflow_timeout_s"]:
        return False, "workflow_timeout_s exceeded"
    return True, ""
