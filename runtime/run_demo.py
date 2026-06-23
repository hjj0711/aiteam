"""Run the aiteam graph locally with the stub engine.

    python run_demo.py "Fix a typo in the footer"               # signals -> dev+qa
    python run_demo.py "Add an API endpoint for auth" 0         # signals -> architect+reviewer
    python run_demo.py "Anything at all" 0 developer,qa         # explicit override -> dev+qa

Args: goal [qa_fail_cycles] [roles_csv]
Human-approval interrupts (after ba and architect) are auto-resumed here so the
demo runs end to end. In real use, a human inspects docs/ then resumes.
"""

from __future__ import annotations

import sys

from langgraph.checkpoint.memory import MemorySaver

from aiteam_runtime.engine import StubEngine
from aiteam_runtime.graph import build_graph
from aiteam_runtime.guardrails import new_ledger
from aiteam_runtime.state import initial_state


def main() -> None:
    goal = sys.argv[1] if len(sys.argv) > 1 else "Add user auth with sessions"
    qa_fail_cycles = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    roles_override = sys.argv[3].split(",") if len(sys.argv) > 3 else None

    # Token/cost limits are mandatory; set them for this personal run.
    ledger = new_ledger({"max_total_tokens": 200_000, "max_total_cost_usd": 5.0})
    graph = build_graph(StubEngine(qa_fail_cycles=qa_fail_cycles), checkpointer=MemorySaver())

    config = {"configurable": {"thread_id": "demo-1"}, "recursion_limit": ledger["limits"]["max_graph_steps"]}
    state = initial_state("DEMO-1", goal, ledger, roles_override=roles_override)

    result = graph.invoke(state, config)
    # Auto-resume through human-approval interrupts.
    while graph.get_state(config).next:
        result = graph.invoke(None, config)

    print("\n=== HISTORY ===")
    for line in result["history"]:
        print(line)
    print("\n=== OUTCOME ===")
    print(f"tier={result.get('tier')}  status={result.get('status')}  "
          f"qa_cycles={result.get('qa_cycles')}  blocker={result.get('blocker') or '-'}")
    spent = result["ledger"]["spent"]
    print(f"spent: model_calls={spent['model_calls']} tokens={spent['tokens']} cost=${spent['cost_usd']:.2f}")


if __name__ == "__main__":
    main()
