"""Graph wiring.

Flow (see README and orchestrator.md):

    orchestrator --(simple)--> developer
                 --(standard/complex)--> ba -> ux -> architect -> developer
    developer -> qa
    qa --(pass, standard/complex)--> reviewer -> END
       --(pass, simple)--> END
       --(fail, < limit)--> developer            # bounded repair loop
       --(blocked / limit)--> END

Human approval: compiled with interrupt_after on `ba` and `architect`, matching
"human approval after requirements and design". Resume by invoking again with
the same thread_id.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from .engine import ClaudeEngine, RoleEngine, StubEngine
from .nodes import intake, make_nodes, route_after_orchestrator, route_after_qa
from .state import AiTeamState


def build_workflow(engine: RoleEngine | None = None) -> StateGraph:
    engine = engine or ClaudeEngine()
    nodes = make_nodes(engine)

    g = StateGraph(AiTeamState)
    g.add_node("intake", intake)
    for name, fn in nodes.items():
        g.add_node(name, fn)

    g.add_edge(START, "intake")
    g.add_edge("intake", "orchestrator")
    g.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {"developer": "developer", "ba": "ba", "end": END},
    )
    g.add_edge("ba", "ux")
    g.add_edge("ux", "architect")
    g.add_edge("architect", "developer")
    g.add_edge("developer", "qa")
    g.add_conditional_edges(
        "qa",
        route_after_qa,
        {"reviewer": "reviewer", "developer": "developer", "end": END},
    )
    g.add_edge("reviewer", END)
    return g


def build_graph(
    engine: RoleEngine | None = None,
    *,
    checkpointer: Any | None = None,
    human_approval: bool = True,
    interrupt_after: list[str] | None = None,
    recursion_limit: int | None = None,
):
    """Compile the workflow.

    - `human_approval`: interrupt after ba and architect for human review.
    - `interrupt_after`: explicit pause points; overrides `human_approval` when
      provided (e.g. ["ba", "architect", "developer"] to also guide before QA).
    - `recursion_limit` is applied per-invocation via config, not here; pass it
      through `run.invoke(..., config={"recursion_limit": N})`.
    """
    if interrupt_after is None:
        interrupt_after = ["ba", "architect"] if human_approval else []
    return build_workflow(engine).compile(
        checkpointer=checkpointer,
        interrupt_after=interrupt_after,
    )


# Module-level compiled graph for LangGraph Studio / CLI (langgraph.json).
# Studio injects its own persistence, so no checkpointer here.
graph = build_graph(human_approval=True)
