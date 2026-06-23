"""Role engine abstraction.

A RoleEngine turns (role, state) into a RoleResult. The default StubEngine is
deterministic and needs no API key, so the graph is runnable and testable out
of the box. To go live, implement RoleEngine over the Codex / Claude Code CLIs
(see bin/codex) and load the matching `.aiteam/roles/<role>.md` contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


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
