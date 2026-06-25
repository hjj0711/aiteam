"""Graph state for the aiteam runtime.

State is a plain TypedDict so LangGraph can checkpoint and resume it. `history`
uses an additive reducer; every other field is last-write-wins.
"""

from __future__ import annotations

import operator
import time
from typing import Annotated, Any, Literal, TypedDict

Tier = Literal["", "dev_qa", "standard", "complex"]
Status = Literal["running", "blocked", "done"]


class AiTeamState(TypedDict, total=False):
    # --- task identity ---
    task_id: str
    goal: str

    # --- routing / phase ---
    tier: Tier
    phase: str
    status: Status
    blocker: str
    roles_override: list[str]   # explicit user-chosen optional roles ("" = none set)
    active_roles: list[str]     # resolved role set the run will actually execute

    # --- artifacts (text in the skeleton; real engines update docs/ files) ---
    requirements: str
    design: str
    architecture: str
    code_summary: str
    test_results: str
    review: str

    # --- control counters enforced against the budget ledger ---
    coverage_passes: int
    qa_cycles: int
    fix_iterations: int
    qa_passed: bool

    # --- budget ledger (limits + spent) ---
    ledger: dict[str, Any]

    # --- per-task git isolation (see vcs.py); only active when vcs_enabled ---
    vcs_enabled: bool
    vcs_branch: str

    # --- human-in-the-loop guidance injected at an interrupt point ---
    human_feedback: str

    # --- audit log ---
    history: Annotated[list[str], operator.add]


def initial_state(
    task_id: str,
    goal: str,
    ledger: dict[str, Any],
    roles_override: list[str] | None = None,
    vcs_enabled: bool = False,
) -> AiTeamState:
    return {
        "task_id": task_id,
        "goal": goal,
        "tier": "",
        "phase": "intake",
        "status": "running",
        "blocker": "",
        "roles_override": roles_override or [],
        "active_roles": [],
        "requirements": "",
        "design": "",
        "architecture": "",
        "code_summary": "",
        "test_results": "",
        "review": "",
        "coverage_passes": 0,
        "qa_cycles": 0,
        "fix_iterations": 0,
        "qa_passed": False,
        "ledger": ledger,
        "vcs_enabled": vcs_enabled,
        "vcs_branch": "",
        "human_feedback": "",
        "history": [f"[{_ts()}] intake: {goal}"],
    }


def _ts() -> str:
    return time.strftime("%H:%M:%S")


def log(phase: str, message: str) -> str:
    return f"[{_ts()}] {phase}: {message}"
