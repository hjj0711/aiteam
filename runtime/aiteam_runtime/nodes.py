"""Role nodes.

Each node charges the budget ledger, runs the engine, and updates state. Any
node short-circuits to a no-op once status is "blocked" so a tripped guard
flows cleanly to END instead of raising.
"""

from __future__ import annotations

from typing import Any

from . import guardrails as gr
from .engine import PRE_ROLES, RoleEngine, infer_signals, plan_roles, tier_of
from .guardrails import new_ledger
from .state import log


def _blocked(state: dict[str, Any]) -> bool:
    return state.get("status") == "blocked"


def _inactive(state: dict[str, Any], role: str) -> bool:
    """True if this optional role is not in the resolved active set."""
    return role not in state.get("active_roles", [])


def _charge_and_check(state: dict[str, Any], role: str, result) -> dict[str, Any] | None:
    """Charge the ledger for a role call; return a blocked-update dict if a
    hard budget limit was crossed, else None."""
    ledger = state["ledger"]
    gr.charge(ledger, role, model_calls=1, tokens=result.tokens, cost_usd=result.cost_usd)
    ok, reason = gr.check(ledger, role)
    if not ok:
        return {
            "status": "blocked",
            "blocker": f"budget: {reason}",
            "ledger": ledger,
            "history": [log(role, f"BLOCKED ({reason})")],
        }
    return None


def intake(state: dict[str, Any]) -> dict[str, Any]:
    """Auto-initialize state from just task_id + goal.

    In Studio, the user only needs to provide:
        {"task_id": "T1", "goal": "Add guest login API"}
    This node fills in the rest (ledger, defaults, history).
    """
    goal = state.get("goal", "")
    task_id = state.get("task_id", "TASK-1")

    # If ledger is already set, this is a resume — don't reinitialize.
    if state.get("ledger"):
        return {}

    ledger = new_ledger({"max_total_tokens": 200_000, "max_total_cost_usd": 5.0})
    roles_override = state.get("roles_override") or None

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
        "history": [log("intake", goal)],
    }


def make_nodes(engine: RoleEngine):
    def orchestrator(state: dict[str, Any]) -> dict[str, Any]:
        goal = state.get("goal", "")
        override = state.get("roles_override") or None
        active = plan_roles(goal, override=override)
        tier = tier_of(active)
        hist = [log("orchestrator", f"tier={tier} roles={active}"
                    + (" (explicit override)" if override else ""))]
        # Respect an explicit override but warn if it skips a role the signals want.
        if override:
            s = infer_signals(goal)
            if s["touches_contract"] and "architect" not in active:
                hist.append(log("orchestrator", "WARN: override skips Architect but task touches a contract/data model"))
            if s["risk_high"] and "reviewer" not in active:
                hist.append(log("orchestrator", "WARN: override skips Reviewer but task is high-risk"))
        return {"tier": tier, "active_roles": active, "phase": "routed", "history": hist}

    def ba(state: dict[str, Any]) -> dict[str, Any]:
        if _blocked(state):
            return {}
        if _inactive(state, "ba"):
            return {"history": [log("ba", "skipped (requirements already clear)")]}
        r = engine.run("ba", state)
        if (b := _charge_and_check(state, "ba", r)):
            return b
        return {"requirements": r.text, "phase": "ba", "ledger": state["ledger"],
                "history": [log("ba", "requirements drafted (awaiting human approval)")]}

    def ux(state: dict[str, Any]) -> dict[str, Any]:
        if _blocked(state):
            return {}
        if _inactive(state, "ux"):
            return {"history": [log("ux", "skipped (no user-facing UI)")]}
        r = engine.run("ux", state)
        if (b := _charge_and_check(state, "ux", r)):
            return b
        return {"design": r.text, "phase": "ux", "ledger": state["ledger"],
                "history": [log("ux", "design drafted")]}

    def architect(state: dict[str, Any]) -> dict[str, Any]:
        if _blocked(state):
            return {}
        if _inactive(state, "architect"):
            return {"history": [log("architect", "skipped (no contract/architecture impact)")]}
        r = engine.run("architect", state)
        if (b := _charge_and_check(state, "architect", r)):
            return b
        passes = state.get("coverage_passes", 0) + 1
        ledger = state["ledger"]
        limit = ledger["limits"]["max_coverage_passes"]
        note = "coverage ok" if passes <= limit else "coverage pass limit reached"
        return {"architecture": r.text, "coverage_passes": passes, "phase": "architect",
                "ledger": ledger,
                "history": [log("architect", f"plan + coverage eval (pass {passes}/{limit}: {note})")]}

    def developer(state: dict[str, Any]) -> dict[str, Any]:
        if _blocked(state):
            return {}
        ledger = state["ledger"]
        iters = state.get("fix_iterations", 0) + 1
        # Fix-Loop guard: repeated developer entries for the same task are bounded.
        n = gr.record_action(ledger, f"developer:{state.get('task_id')}")
        if iters > ledger["limits"]["max_fix_iterations"] or n >= ledger["limits"]["repeat_action_stop"] + 2:
            return {"status": "blocked", "blocker": "fix-loop guard tripped",
                    "fix_iterations": iters, "ledger": ledger,
                    "history": [log("developer", "BLOCKED (fix-loop guard)")]}
        r = engine.run("developer", state)
        if (b := _charge_and_check(state, "developer", r)):
            b["fix_iterations"] = iters
            return b
        return {"code_summary": r.text, "fix_iterations": iters, "phase": "developer",
                "ledger": ledger,
                "history": [log("developer", f"edit-test-fix loop (iter {iters})")]}

    def qa(state: dict[str, Any]) -> dict[str, Any]:
        if _blocked(state):
            return {}
        r = engine.run("qa", state)
        if (b := _charge_and_check(state, "qa", r)):
            return b
        passed = bool(r.signals.get("qa_passed", True))
        update = {"test_results": r.text, "qa_passed": passed, "phase": "qa",
                  "ledger": state["ledger"]}
        if passed:
            # if no Reviewer is in the active set, QA is the terminal gate
            if _inactive(state, "reviewer"):
                update["status"] = "done"
            update["history"] = [log("qa", "PASS — evidence attached")]
            return update
        cycles = state.get("qa_cycles", 0) + 1
        update["qa_cycles"] = cycles
        limit = state["ledger"]["limits"]["max_qa_repair_cycles"]
        if cycles > limit:
            update["status"] = "blocked"
            update["blocker"] = "qa repair cycle limit reached"
            update["history"] = [log("qa", f"BLOCKED (repair cycle {cycles}>{limit})")]
        else:
            update["history"] = [log("qa", f"FAIL — repair packet -> developer (cycle {cycles}/{limit})")]
        return update

    def reviewer(state: dict[str, Any]) -> dict[str, Any]:
        if _blocked(state):
            return {}
        r = engine.run("reviewer", state)
        if (b := _charge_and_check(state, "reviewer", r)):
            return b
        return {"review": r.text, "status": "done", "phase": "review",
                "ledger": state["ledger"], "history": [log("reviewer", "done — no blocker")]}

    return {
        "orchestrator": orchestrator,
        "ba": ba,
        "ux": ux,
        "architect": architect,
        "developer": developer,
        "qa": qa,
        "reviewer": reviewer,
    }


# --- conditional edge routers ---

def route_after_orchestrator(state: dict[str, Any]) -> str:
    if _blocked(state):
        return "end"
    # enter the pre-chain only if any of ba/ux/architect is active; the chain
    # nodes self-skip when inactive. Otherwise go straight to developer.
    active = state.get("active_roles", [])
    return "ba" if any(r in active for r in PRE_ROLES) else "developer"


def route_after_qa(state: dict[str, Any]) -> str:
    if _blocked(state):
        return "end"
    if state.get("qa_passed"):
        return "reviewer" if "reviewer" in state.get("active_roles", []) else "end"
    return "developer"
