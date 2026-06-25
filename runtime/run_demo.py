"""Run the aiteam graph locally.

    python run_demo.py "Fix a typo in the footer"               # ClaudeEngine, real agent
    python run_demo.py --stub "Fix a typo in the footer"         # StubEngine, no API key needed
    python run_demo.py "Add an API endpoint for auth" 0          # qa_fail_cycles (stub only)
    python run_demo.py "Anything at all" 0 developer,qa          # explicit roles override

Args: [--stub] goal [qa_fail_cycles] [roles_csv]
Human-approval interrupts (after ba and architect) are auto-resumed here so the
demo runs end to end. In real use, a human inspects docs/ then resumes.
"""

from __future__ import annotations

import sys

from langgraph.checkpoint.memory import MemorySaver

from aiteam_runtime.engine import ClaudeEngine, StubEngine
from aiteam_runtime.graph import build_graph
from aiteam_runtime.guardrails import new_ledger
from aiteam_runtime.state import initial_state


def main() -> None:
    args = sys.argv[1:]
    use_stub = False
    if args and args[0] == "--stub":
        use_stub = True
        args = args[1:]

    goal = args[0] if args else "Add user auth with sessions"
    qa_fail_cycles = int(args[1]) if len(args) > 1 else 1
    roles_override = args[2].split(",") if len(args) > 2 else None

    ledger = new_ledger({"max_total_tokens": 200_000, "max_total_cost_usd": 5.0})

    if use_stub:
        engine = StubEngine(qa_fail_cycles=qa_fail_cycles)
    else:
        engine = ClaudeEngine()

    graph = build_graph(engine, checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "demo-1"}, "recursion_limit": ledger["limits"]["max_graph_steps"]}
    state = initial_state("DEMO-1", goal, ledger, roles_override=roles_override)

    result = graph.invoke(state, config)
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
