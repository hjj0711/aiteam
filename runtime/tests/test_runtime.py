"""Deterministic node/graph tests — no API key required (stub engine)."""

from __future__ import annotations

import os
import signal
import stat
import subprocess
import time

import pytest
from langgraph.checkpoint.memory import MemorySaver

from aiteam_runtime.engine import ClaudeEngine, StubEngine, plan_roles, tier_of
from aiteam_runtime.graph import build_graph
from aiteam_runtime.guardrails import BudgetError, new_ledger
from aiteam_runtime.state import initial_state


def _run(goal, qa_fail_cycles=0, limits=None, roles_override=None):
    base = {"max_total_tokens": 200_000, "max_total_cost_usd": 5.0}
    base.update(limits or {})
    ledger = new_ledger(base)
    graph = build_graph(StubEngine(qa_fail_cycles=qa_fail_cycles),
                        checkpointer=MemorySaver(), human_approval=False)
    config = {"configurable": {"thread_id": str(goal) + str(roles_override)},
              "recursion_limit": ledger["limits"]["max_graph_steps"]}
    return graph.invoke(initial_state("T", goal, ledger, roles_override=roles_override), config)


def test_missing_token_limit_fails_closed():
    with pytest.raises(BudgetError):
        new_ledger({"max_total_cost_usd": 1.0})  # no token limit


def test_signals_and_role_planning():
    # plain code tweak -> only developer + qa
    assert plan_roles("fix a typo in footer") == ["developer", "qa"]
    # UI work pulls in ux
    assert "ux" in plan_roles("add a settings page with a save button")
    # contract + risk pulls in architect + reviewer
    roles = plan_roles("add an api endpoint for auth")
    assert "architect" in roles and "reviewer" in roles
    # vague goal pulls in ba
    assert "ba" in plan_roles("maybe improve the dashboard somehow, tbd")
    assert tier_of(["developer", "qa"]) == "dev_qa"


def test_dev_qa_only_skips_pre_and_review():
    out = _run("fix a typo in footer")
    assert out["tier"] == "dev_qa"
    assert out["active_roles"] == ["developer", "qa"]
    assert out["status"] == "done"
    assert out["requirements"] == "" and out["design"] == "" and out["review"] == ""


def test_contract_task_runs_architect_and_reviewer():
    out = _run("add an api endpoint for auth")
    assert "architect" in out["active_roles"] and "reviewer" in out["active_roles"]
    assert out["architecture"] and out["review"]
    assert out["requirements"] == ""   # BA skipped (requirements clear)
    assert out["status"] == "done"


def test_explicit_override_forces_dev_qa_with_warning():
    # high-risk goal, but user explicitly asks for only dev+qa
    out = _run("add an api endpoint for auth", roles_override=["developer", "qa"])
    assert out["active_roles"] == ["developer", "qa"]
    assert out["architecture"] == "" and out["review"] == ""
    assert out["status"] == "done"
    assert any("WARN" in h for h in out["history"])   # override risk warning surfaced


def test_qa_repair_loop_then_pass():
    out = _run("add an api endpoint for auth", qa_fail_cycles=1)
    assert out["qa_cycles"] == 1
    assert out["qa_passed"] is True
    assert out["status"] == "done"


def test_qa_repair_cycle_limit_blocks():
    # fail more times than the allowed repair cycles -> blocked, not silently passed
    out = _run("add an api endpoint for auth", qa_fail_cycles=5,
               limits={"max_qa_repair_cycles": 2})
    assert out["status"] == "blocked"
    assert "repair cycle" in out["blocker"]


def test_budget_limit_blocks():
    out = _run("add an api endpoint for auth", limits={"max_total_model_calls": 2})
    assert out["status"] == "blocked"
    assert "budget" in out["blocker"]


def _pid_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def test_claude_engine_terminates_process_group(tmp_path):
    child_pid_path = tmp_path / "child.pid"
    script = tmp_path / "spawn_child.sh"
    script.write_text(
        "#!/bin/sh\n"
        "sleep 60 &\n"
        "echo $! > \"$CLAUDE_FAKE_CHILD_PID\"\n"
        "wait $!\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)

    child_pid: int | None = None
    proc: subprocess.Popen[str] | None = None
    try:
        env = {**os.environ, "CLAUDE_FAKE_CHILD_PID": str(child_pid_path)}
        proc = subprocess.Popen([str(script)], env=env, start_new_session=True)

        deadline = time.time() + 5
        while time.time() < deadline and not child_pid_path.exists():
            time.sleep(0.05)

        assert child_pid_path.exists()
        child_pid = int(child_pid_path.read_text())
        assert _pid_exists(child_pid)

        ClaudeEngine()._terminate_process_group(proc)
        deadline = time.time() + 5
        while time.time() < deadline and _pid_exists(child_pid):
            time.sleep(0.05)

        assert not _pid_exists(child_pid)
    finally:
        if child_pid is not None and _pid_exists(child_pid):
            os.kill(child_pid, signal.SIGKILL)
        if proc is not None and proc.poll() is None:
            proc.kill()
