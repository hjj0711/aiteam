# Claude Code Instructions

Read and follow `AGENTS.md` first. It is the shared contract used by both Claude Code and Codex.

When a task names a role, load the matching file from `.aiteam/roles/` before working. Claude is the default engine for BA, UX, architecture, and adversarial review, but role instructions override that default.

Do not treat Claude conversation memory as project truth. Persist accepted facts in the repository files defined by `AGENTS.md`.

