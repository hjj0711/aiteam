# Feature Workflow Prompt

Use the shared contract in `AGENTS.md`.

Goal:
<describe the desired outcome>

Current phase:
<BA | UX | Architecture | Development | QA | Review>

Role:
Read `.aiteam/roles/<role>.md` and act only within that role.

Required inputs:
- `.aiteam/config.yml`
- `docs/requirements.md`
- `docs/design.md`
- `docs/architecture.md`
- `memory/project.md`
- `memory/decisions/`
- `tasks/current.md`

Expected output:
<name the artifact or code change>

Acceptance gate:
<state the measurable condition and whether human approval is required>

Before finishing, run relevant verification and update only the durable memory made true by this task.

