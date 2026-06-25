"""Role engine abstraction.

A RoleEngine turns (role, state) into a RoleResult. The default StubEngine is
deterministic and needs no API key, so the graph is runnable and testable out
of the box. To go live, implement RoleEngine over the Codex / Claude Code CLIs
(see bin/codex) and load the matching `.aiteam/roles/<role>.md` contract.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ROLES_DIR = _REPO_ROOT / ".aiteam" / "roles"
_PROJECTS_DIR = _REPO_ROOT / "projects"
_COST_PER_1K = 0.003
_PROCESS_TERM_GRACE_S = 5


@dataclass
class RoleResult:
    text: str                       # the artifact / answer the role produced
    tokens: int = 0
    cost_usd: float = 0.0
    # role-specific signals consumed by nodes (e.g. {"qa_passed": False})
    signals: dict[str, Any] = field(default_factory=dict)


class RoleEngine(Protocol):
    def run(self, role: str, state: dict[str, Any]) -> RoleResult:
        ...


@dataclass
class StubEngine:
    """Deterministic placeholder engine.

    Returns canned artifacts and lets a test drive QA pass/fail via
    `qa_fail_cycles` (number of leading QA rounds that should fail).
    """

    qa_fail_cycles: int = 0
    tokens_per_call: int = 500
    cost_per_call: float = 0.01

    def run(self, role: str, state: dict[str, Any]) -> RoleResult:
        goal = state.get("goal", "")
        signals: dict[str, Any] = {}

        if role == "ba":
            text = f"Requirements for: {goal}\n- AC1 measurable\n- AC2 measurable"
        elif role == "ux":
            text = f"Design for: {goal}\n- flow, states, a11y"
        elif role == "architect":
            text = (
                f"Architecture for: {goal}\n"
                "- task1 Produces=api Consumes=- Boundaries=in:api/out:ui\n"
                "- coverage: every AC mapped to a task + verification"
            )
        elif role == "developer":
            text = f"Implemented: {goal} (scoped diff + focused tests)"
        elif role == "qa":
            should_fail = state.get("qa_cycles", 0) < self.qa_fail_cycles
            signals["qa_passed"] = not should_fail
            text = (
                "QA: all acceptance criteria have evidence — PASS"
                if not should_fail
                else "QA: AC2 fails — repair packet: fix validation in handler X"
            )
        elif role == "reviewer":
            text = "Review: no blocking issue; minor notes only."
        else:
            text = f"{role}: noop"

        return RoleResult(
            text=text,
            tokens=self.tokens_per_call,
            cost_usd=self.cost_per_call,
            signals=signals,
        )


@dataclass
class ClaudeEngine:
    """Engine that shells out to the `claude` CLI for each role.

    Loads the role contract from `.aiteam/roles/<role>.md`, builds a prompt
    with upstream artifacts as context, and calls `claude --print --output-format json`.
    Token counts are estimated from output length; cost is a rough approximation.
    """

    model: str = ""
    timeout_s: int = 600
    allow_edits: bool = True

    def run(self, role: str, state: dict[str, Any]) -> RoleResult:
        contract = self._load_contract(role)
        prompt = self._build_prompt(role, contract, state)

        cmd = ["claude", "--print", "--output-format", "json"]

        if self.model:
            cmd.extend(["--model", self.model])

        if role == "developer" and self.allow_edits:
            cmd.extend(["--allowedTools", "Read,Write,Edit,Bash"])
        elif role == "qa":
            cmd.extend(["--allowedTools", "Read,Bash"])

        proc: subprocess.Popen[str] | None = None
        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(_REPO_ROOT),
                start_new_session=True,
            )
            output, stderr = proc.communicate(input=prompt, timeout=self.timeout_s)
        except subprocess.TimeoutExpired:
            if proc is not None:
                self._terminate_process_group(proc)
            return RoleResult(
                text=f"{role}: TIMEOUT after {self.timeout_s}s",
                signals={"qa_passed": False, "timeout": True},
            )
        except BaseException:
            if proc is not None:
                self._terminate_process_group(proc)
            raise

        output = output.strip() if output else ""
        stderr = stderr.strip() if stderr else ""

        text = output
        tokens = 0
        if output:
            try:
                parsed = json.loads(output)
                text = parsed.get("result", output)
                usage = parsed.get("usage", {})
                tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
            except json.JSONDecodeError:
                pass

        if tokens == 0 and text:
            tokens = len(text) // 4

        cost = (tokens / 1000) * _COST_PER_1K

        signals: dict[str, Any] = {}
        if role == "qa":
            signals["qa_passed"] = "PASS" in text.upper() and "FAIL" not in text.upper()

        if proc.returncode != 0:
            text = f"{role}: CLI error (rc={proc.returncode})\nstderr: {stderr}\noutput: {text}"

        return RoleResult(text=text, tokens=tokens, cost_usd=cost, signals=signals)

    def _terminate_process_group(self, proc: subprocess.Popen[str]) -> None:
        """Stop the Claude CLI and any child tools it spawned."""
        if proc.poll() is not None:
            return

        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        except OSError:
            proc.terminate()

        try:
            proc.wait(timeout=_PROCESS_TERM_GRACE_S)
            return
        except subprocess.TimeoutExpired:
            pass

        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        except OSError:
            proc.kill()

        try:
            proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass

    def _load_contract(self, role: str) -> str:
        path = _ROLES_DIR / f"{role}.md"
        if path.exists():
            return path.read_text()
        return f"# {role}\n(No contract found at {path})"

    def _build_prompt(self, role: str, contract: str, state: dict[str, Any]) -> str:
        goal = state.get("goal", "")
        task_id = state.get("task_id", "")

        parts = [
            f"You are the **{role.upper()}** role in an AI team workflow.",
            f"Task ID: {task_id}",
            f"Goal: {goal}",
            "",
            "=== YOUR ROLE CONTRACT ===",
            contract,
            "",
        ]

        for label, key in [
            ("REQUIREMENTS (from BA)", "requirements"),
            ("UX DESIGN (from UX)", "design"),
            ("ARCHITECTURE (from Architect)", "architecture"),
            ("PREVIOUS DEVELOPER OUTPUT", "code_summary"),
            ("PREVIOUS QA RESULTS", "test_results"),
        ]:
            val = state.get(key, "")
            if val:
                parts.append(f"=== {label} ===")
                parts.append(val[:4000])
                parts.append("")

        parts.append("=== INSTRUCTIONS ===")
        if role == "ba":
            parts.append("Write requirements to docs/requirements.md. Include acceptance criteria.")
        elif role == "ux":
            parts.append("Write UX design to docs/design.md. Include user flows and screen states.")
        elif role == "architect":
            parts.append("Write architecture to docs/architecture.md. Include task breakdown and coverage evaluation.")
        elif role == "developer":
            parts.append(f"Implement the code changes in projects/. Run typecheck/lint/build. Update tasks/current.md. Projects dir: {_PROJECTS_DIR}")
        elif role == "qa":
            parts.append("Run tests and verify acceptance criteria. Report PASS or FAIL with evidence.")
        elif role == "reviewer":
            parts.append("Review the diff and code quality. Report any blocking issues.")

        parts.append("")
        parts.append("Produce your artifact now. Be concise and actionable.")
        return "\n".join(parts)


# Canonical role order. developer and qa always run; the rest are optional and
# decided per task by signals or by an explicit override.
ROLE_ORDER = ["ba", "ux", "architect", "developer", "qa", "reviewer"]
PRE_ROLES = ["ba", "ux", "architect"]
OPTIONAL_ROLES = ["ba", "ux", "architect", "reviewer"]

_UI_KW = ("ui", "ux", "screen", "page", "button", "form", "modal", "layout",
          "frontend", "css", "页面", "界面", "按钮", "表单", "前端", "弹窗")
_CONTRACT_KW = ("api", "endpoint", "schema", "migration", "database", "interface",
                "model", "数据库", "迁移", "接口", "数据模型")
_RISK_KW = ("auth", "security", "payment", "delete", "irreversible", "credential",
            "token", "鉴权", "安全", "支付", "删除", "密钥", "迁移")
_VAGUE_KW = ("maybe", "tbd", "unclear", "not sure", "?", "大概", "也许", "待定", "不确定", "暂定")


def infer_signals(goal: str) -> dict[str, bool]:
    """Heuristic signal extraction used by the stub.

    A real engine would ask a small model. Signals drive role selection so we
    only run agents that produce a distinct, verifiable artifact.
    """
    g = (goal or "").lower()
    return {
        "has_ui": any(k in g for k in _UI_KW),
        "touches_contract": any(k in g for k in _CONTRACT_KW),
        "risk_high": any(k in g for k in _RISK_KW),
        "requirements_clear": not any(k in g for k in _VAGUE_KW),
    }


def plan_roles(
    goal: str | None = None,
    *,
    signals: dict[str, bool] | None = None,
    override: list[str] | None = None,
) -> list[str]:
    """Assemble the active role set. developer and qa always run.

    - override: explicit list from the user; only its optional roles are honored
      (developer/qa stay on regardless), normalized to canonical order.
    - otherwise: optional roles are selected from signals.
    """
    if override is not None:
        opt = {r for r in override if r in OPTIONAL_ROLES}
    else:
        s = signals or infer_signals(goal or "")
        opt = set()
        if not s["requirements_clear"]:
            opt.add("ba")
        if s["has_ui"]:
            opt.add("ux")
        if s["touches_contract"]:
            opt.add("architect")
        if s["risk_high"]:
            opt.add("reviewer")

    active = [r for r in PRE_ROLES if r in opt] + ["developer", "qa"]
    if "reviewer" in opt:
        active.append("reviewer")
    return active


def tier_of(roles: list[str]) -> str:
    """Human-readable label for the active role set (display only)."""
    has_pre = any(r in roles for r in PRE_ROLES)
    if not has_pre and "reviewer" not in roles:
        return "dev_qa"
    if "reviewer" in roles and "architect" in roles:
        return "complex"
    return "standard"
