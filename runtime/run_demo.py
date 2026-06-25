"""Run the aiteam graph locally.

    python run_demo.py "Fix a typo in the footer"               # ClaudeEngine, real agent (live + interactive)
    python run_demo.py --stub "Fix a typo in the footer"         # StubEngine, no API key, non-interactive
    python run_demo.py "Add an API endpoint for auth" 0          # qa_fail_cycles (stub only)
    python run_demo.py "Anything at all" 0 developer,qa          # explicit roles override

Args: [--stub] goal [qa_fail_cycles] [roles_csv]

Real-engine runs are LIVE and INTERACTIVE:
  - each role's output streams to your terminal as it is produced;
  - the run pauses after ba / architect / developer so you can type guidance
    (empty = approve & continue);
  - developer edits land on a dedicated `aiteam/<task_id>` branch — inspect with
    scripts/task-changes.sh and undo with scripts/task-revert.sh.

Stub runs stay non-interactive so you can watch the flow without an API key.
"""

from __future__ import annotations

import sys

from langgraph.checkpoint.memory import MemorySaver

from aiteam_runtime.engine import ClaudeEngine, StubEngine
from aiteam_runtime.graph import build_graph
from aiteam_runtime.guardrails import new_ledger
from aiteam_runtime.state import initial_state

# Pause after these nodes when running interactively, so a human can review the
# artifact and steer before the next role.
_PAUSE_POINTS = ["ba", "architect", "developer"]
_ARTIFACT_AT = {"ba": "requirements", "architect": "architecture", "developer": "code_summary"}


def _print_updates(stream) -> None:
    """Print node-level history as each role completes (node-level real-time)."""
    for chunk in stream:
        for node, update in chunk.items():
            if not isinstance(update, dict):
                continue
            for line in update.get("history", []):
                print(f"  {line}")


def _handle_pause(graph, config) -> None:
    """Show the just-produced artifact and let the user inject guidance."""
    snapshot = graph.get_state(config)
    state = snapshot.values
    phase = state.get("phase", "")
    artifact = state.get(_ARTIFACT_AT.get(phase, ""), "")

    print(f"\n--- PAUSED after {phase} (next: {', '.join(snapshot.next)}) ---")
    if artifact:
        preview = artifact if len(artifact) < 1200 else artifact[:1200] + "\n…(truncated)"
        print(preview)

    try:
        feedback = input("\nYour guidance (empty = approve & continue): ").strip()
    except EOFError:
        feedback = ""

    if feedback:
        graph.update_state(config, {"human_feedback": feedback})
        print("  (guidance injected — the next role will follow it)")


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
        interrupt_after: list[str] = []          # non-interactive: just watch the flow
    else:
        engine = ClaudeEngine(stream=True)        # live token output to stderr
        interrupt_after = _PAUSE_POINTS           # pause for guidance

    graph = build_graph(engine, checkpointer=MemorySaver(), interrupt_after=interrupt_after)
    config = {"configurable": {"thread_id": "demo-1"},
              "recursion_limit": ledger["limits"]["max_graph_steps"]}
    state = initial_state("DEMO-1", goal, ledger,
                          roles_override=roles_override, vcs_enabled=not use_stub)

    print("=== RUN (live) ===")
    _print_updates(graph.stream(state, config, stream_mode="updates"))
    while graph.get_state(config).next:
        _handle_pause(graph, config)
        _print_updates(graph.stream(None, config, stream_mode="updates"))

    result = graph.get_state(config).values
    print("\n=== OUTCOME ===")
    print(f"tier={result.get('tier')}  status={result.get('status')}  "
          f"qa_cycles={result.get('qa_cycles')}  blocker={result.get('blocker') or '-'}")
    if result.get("vcs_branch"):
        tid = result.get("task_id", "")
        print(f"changes on branch: {result['vcs_branch']}")
        print(f"  view:   scripts/task-changes.sh {tid}")
        print(f"  cancel: scripts/task-revert.sh  {tid}")
    spent = result["ledger"]["spent"]
    print(f"spent: model_calls={spent['model_calls']} tokens={spent['tokens']} cost=${spent['cost_usd']:.2f}")


if __name__ == "__main__":
    main()
