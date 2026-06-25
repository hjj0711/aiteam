# AI Team Workspace

这是一个给个人使用的 Codex + Claude Code 多 Agent 工作区。

## 新手必读：这是什么、怎么用

如果你对 OpenADE、LangGraph、LLM 完全不了解，先看这一节，用大白话解释。

### 几个名词（大白话）

- **LLM（大语言模型）**：就是 ChatGPT 那种“会读会写的 AI 大脑”。这里用两个：**Claude** 和 **Codex**。
- **Codex / Claude Code**：把 AI 大脑装进电脑命令行的工具，能读你的代码、改文件、跑命令。你已经登录好了（密钥不存在仓库里）。
- **Agent（智能体）**：给 AI 大脑安排一个“角色 + 职责”，让它专心做一件事。这里有 6 个角色：BA（理需求）、UX（做设计）、Architect（定架构）、Developer（写代码）、QA（测试）、Reviewer（审查）。
- **OpenADE**：一个“看得见的工作台”（图形界面），点点鼠标就能让 Codex/Claude 干活、看代码改了哪里。**可选**，不装也能用。
- **LangGraph**：一个“流程调度器”，自动决定先让哪个角色干、再让谁干，并卡住次数/预算，防止 AI 跑飞。本仓库的 `runtime/` 文件夹就是它。
- **aiteam（本仓库）**：把上面这些拼起来，像一个“AI 开发小团队”替你做事。

### 两种使用方式（够用了）

只保留两种方式：**用法 1（CLI 自动编排）**适合放手让它按流程自动跑、要护栏和预算约束；**用法 2（手动逐角色）**适合要实时盯着、随时插话引导的协作型任务。LangGraph Studio 降级为**可选的调试工具**（见文末）。

**用法 1 ｜ CLI 自动编排（推荐入口）**

打开“终端”应用，逐行粘贴运行（需要电脑里有 Python 3.11 以上；下面的 `python3.12` 若提示找不到，换成 `python3` 试试）：

```bash
python3.12 -m venv runtime/.venv
runtime/.venv/bin/pip install -r runtime/requirements.txt

# 假引擎：只演示流程，不连真 AI、不花钱
runtime/.venv/bin/python runtime/run_demo.py --stub "把页脚的拼写改对"

# 真引擎：实时输出 + 关键节点暂停让你引导 + 改动自动进 task 分支
runtime/.venv/bin/python runtime/run_demo.py "把页脚的拼写改对"
```

真引擎模式下：

- **实时看回答**：每个角色的输出会逐步打到终端（`ClaudeEngine(stream=True)` + `stream-json`），不再是黑盒。
- **随时引导**：在 `ba / architect / developer` 之后会**暂停**，展示刚产出的产物并等你输入意见（直接回车=批准继续；输入文字=作为「HUMAN GUIDANCE」注入给下一个角色）。
- **看/取消改动**：开发改动自动落在 `aiteam/<task_id>` 分支并逐次 commit。看本次改动 `scripts/task-changes.sh <task_id>`；一键取消 `scripts/task-revert.sh <task_id>`。

只想用“开发 + 测试”两个角色？在命令末尾加 `0 developer,qa`：

```bash
runtime/.venv/bin/python runtime/run_demo.py --stub "你的需求" 0 developer,qa
```

**用法 2 ｜ 手动逐角色（OpenADE / 终端，实时协作）**

要紧密协作、边看边引导时，直接在 OpenADE 或终端里按角色逐个调用 Claude / Codex（见文末「当前手动流程」）。开工前先开一个隔离分支，结束后用同一套脚本查看 / 取消改动：

```bash
scripts/task-start.sh   <task_id>   # 在 aiteam/<task_id> 分支上开工，改动与 main 隔离
scripts/task-changes.sh <task_id>   # 查看本次任务改了哪些文件 / diff
scripts/task-revert.sh  <task_id>   # 一键丢弃本次任务的全部改动（需确认）
```

### 详细使用方法：一次真引擎任务长什么样

下面是用法 1 真引擎跑 `run_demo.py "你的需求"` 时，终端从头到尾的样子（`#` 是说明，不用输入）：

```text
=== RUN (live) ===
  [10:01:02] orchestrator: tier=standard roles=['architect', 'developer', 'qa', 'reviewer']

  ┌─ architect (live) ─       # ← 角色输出实时逐步打印（来自 stream-json）
  │ 拆解为 3 个任务，每条验收标准都映射到验证…
  └────────────────

--- PAUSED after architect (next: developer) ---   # ← 在此暂停，等你引导
（这里会展示刚产出的架构产物，便于你审阅）

Your guidance (empty = approve & continue):         # ← 你的输入位
```

此时你有两种选择：

1. **直接回车** = 批准，按原计划继续。
2. **输入一段话**（例如「先不要动数据库，只改接口层」）= 这段话会作为 `HUMAN GUIDANCE` 注入给下一个角色，优先级高于其他上下文。

继续后会进入 `developer`，它的改动**自动落在 `aiteam/DEMO-1` 分支**并逐轮 commit。任务跑完，终端结尾会给出：

```text
=== OUTCOME ===
tier=standard  status=done  qa_cycles=1  blocker=-
changes on branch: aiteam/DEMO-1
  view:   scripts/task-changes.sh DEMO-1     # ← 看这次改了什么
  cancel: scripts/task-revert.sh  DEMO-1     # ← 不满意？一键丢弃
spent: model_calls=5 tokens=8200 cost=$0.02
```

- **暂停点可调**：默认在 `ba / architect / developer` 后暂停。想少打断，编辑 `runtime/run_demo.py` 里的 `_PAUSE_POINTS`（例如去掉 `"developer"`，则只在需求/架构后停）。
- **看改动**：`scripts/task-changes.sh DEMO-1` 会列出本次分支相对 `main` 的提交、改动文件和 diff；要看完整 diff 按提示执行 `git diff` 即可。
- **取消改动**：`scripts/task-revert.sh DEMO-1` 会切回 `main` 并删掉 `aiteam/DEMO-1` 分支（需输入 task_id 确认，避免误删）。

### 常见问题

- **看不到逐字输出？** 实时输出走的是 `stderr`，确保终端没有把它重定向掉；`--stub` 模式只有节点级日志、没有逐字流式（因为不连真模型）。
- **暂停时按了回车没反应？** 空输入即“批准继续”，这是预期行为。
- **想完全不被打断地自动跑？** 把 `_PAUSE_POINTS` 改成空列表 `[]` 即可（但就失去中途引导能力）。
- **改动去哪了？** 永远在 `aiteam/<task_id>` 分支上，不会直接污染 `main`；用 `git branch --list 'aiteam/*'` 可列出所有任务分支。
- **预算/次数超限自动停了？** 这是护栏（`docs/runtime-evaluation.md` 的预算账本），`status=blocked` 且 `blocker` 会写明原因，不会静默跑飞。

## 仓库结构

```
.aiteam/           # 角色契约 + 工作流模板 + 配置
  config.yml       # 项目路径等配置
  roles/           # BA, UX, Architect, Developer, QA, Reviewer
  workflows/       # 任务模板
AGENTS.md          # 共享契约（Codex + Claude Code）
CLAUDE.md          # Claude Code 专用指令
docs/              # 产物：需求、设计、架构、测试结果
memory/            # 共享记忆（跨模型、跨任务持久化）
  project.md       # 项目稳定事实
  decisions/       # 已确认决策（按日期+类型命名）
  lessons/         # 已验证教训
tasks/             # 当前任务看板
projects/          # 项目代码（路径可配置）
scripts/           # 启动脚本 + 任务改动隔离脚本（task-start/changes/revert）
bin/               # CLI 包装器
runtime/           # LangGraph 运行时（编排 + 护栏 + 引擎 + vcs 隔离）
```

- LangGraph 作为受控的多 Agent 运行时，负责状态、检查点、循环上限、超时、人工审批和恢复。
- 真引擎 `ClaudeEngine` 流式输出每个角色的回答，并在 `ba/architect/developer` 后暂停接受人工引导。
- 每个任务的代码改动落在独立的 `aiteam/<task_id>` 分支（`runtime/aiteam_runtime/vcs.py` + `scripts/task-*.sh`），便于查看与一键回滚，符合“不共用工作区”的约定。
- LangGraph Studio 为**可选**调试工具，用于查看执行图、节点状态、线程、检查点。
- OpenADE 作为可选的 Codex/Claude 可视化工作台，提供并行规划、Diff、Git 快照和 Worktree。
- Codex 与 Claude Code 使用各自现有登录，不在仓库保存密钥。
- `AGENTS.md`、角色文件和 `memory/` 构成跨模型共享记忆。
- Git 中的需求、决策和测试结果是事实来源，聊天记录不是。

目前角色契约、文档、OpenADE 启动脚本均已就绪。LangGraph 运行时（见 `runtime/`）有两个引擎：默认的假引擎（`--stub`，演示流程、可单测），以及真引擎 `ClaudeEngine`（实时流式输出 + 关键节点暂停引导 + 改动落到 `aiteam/<task_id>` 分支）。Codex 适配器是下一步；选型审计见 `docs/runtime-evaluation.md`。

## 启动

```bash
./scripts/check-agents.sh
./scripts/launch-openade.sh
```

首次进入 OpenADE 后，打开当前目录：

```text
/Users/kit/Documents/myself/aiteam
```

## 运行 LangGraph 运行时（快速上手）

受控编排运行时在 `runtime/`，开箱即跑（默认 Stub 引擎，无需任何 API Key）。需 Python 3.11+。

```bash
# 1) 准备环境
python3.12 -m venv runtime/.venv
runtime/.venv/bin/pip install -r runtime/requirements.txt

# 2) 命令行跑一个任务（--stub 用假引擎演示；去掉则连真 AI、实时输出 + 暂停引导）
runtime/.venv/bin/python runtime/run_demo.py --stub "Fix a typo in the footer"     # 简单：直达 Dev→QA
runtime/.venv/bin/python runtime/run_demo.py --stub "Add user auth with sessions"  # 标准：全链 + QA 返工
```

### 可选：LangGraph Studio（图形化调试工具，不是必需）

只想看流程图 / 节点 state 时再用；日常用法 1+2 不需要它。

```bash
runtime/.venv/bin/pip install "langgraph-cli[inmem]"
(cd runtime && ./.venv/bin/langgraph dev)
# 浏览器打开： https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
# 停止： pkill -f "langgraph dev"
```

可选追踪：把 `runtime/.env.example` 复制为 `runtime/.env`，填 `LANGSMITH_API_KEY` 并设 `LANGSMITH_TRACING=true`，即可在 LangSmith 看到 runs；不开也能用。Studio 里若提示 `LANGSMITH_API_KEY missing`，可忽略。

测试：`(cd runtime && ./.venv/bin/python -m pytest -q)`。完整说明见 `runtime/README.md`。

## 当前手动流程

1. 在 OpenADE 新建任务，选择 Claude，引用 `.aiteam/roles/ba.md` 完成需求澄清。
2. 人工确认 `docs/requirements.md`。
3. 选择 Claude，引用 `.aiteam/roles/ux.md` 和 `.aiteam/roles/architect.md` 完成设计。
4. 对开发计划使用 HyperPlan Cross-Review，让 Claude 与 Codex 互审。
5. 开发前先 `scripts/task-start.sh <task_id>` 切到隔离分支，再选择 Codex 执行开发（改动自动与 main 隔离）。
6. 选择 Claude 或 Codex，引用 `.aiteam/roles/qa.md` 执行测试。
7. 选择另一个模型，引用 `.aiteam/roles/reviewer.md` 做最终审查。
8. 验收看改动 `scripts/task-changes.sh <task_id>`；要放弃本次改动 `scripts/task-revert.sh <task_id>`。

可直接复制 `.aiteam/workflows/feature.md` 中的模板创建一个完整功能任务。

## 目标自动流程

Orchestrator 先做复杂度路由，简单任务跳过前置环节直达开发：

```text
Intake -> Orchestrator 复杂度路由
   | Simple   -> Developer -> QA -> Done
   | Standard -> BA -> 人工需求确认 -> UX -> Architect -> 人工设计确认
   |             -> Developer -> QA -> Reviewer -> Done
   | Complex  -> 同 Standard，并强制人工审批
                              ^         |
                              +-- 有限返工（QA 最多 2 轮）--+
```

- Architect 输出前做覆盖度评估：每条验收标准都要映射到任务与验证，确定性护栏 + 最多 3 轮。
- Developer 跑 Edit-Test-Fix 循环并自带功能测试；Fix-Loop 护栏在 5 次迭代或反复振荡时停手转 `blocked`。
- QA 失败时回传可执行的修复建议，最多 2 轮返工，同一缺陷无进展则升级给人。

每次运行必须同时受最大节点步数、每角色调用数、工具调用数、总超时、Token/费用预算和重复动作检测约束。任何一个边界触发后都进入 `blocked`，不得继续自循环。

## 共享记忆

每个 Agent 开始前读取：

```text
AGENTS.md
.aiteam/config.yml
memory/project.md
memory/decisions/
memory/lessons/
tasks/current.md
```

每个 Agent 结束前只更新与本次工作相关的事实。不要把推测、完整聊天记录或隐私信息写进记忆。

## 安全边界

- OpenADE 可以执行命令和修改代码，首次使用保持人工审批。
- 不提交 `.env`、Token、Cookie 或 API Key。
- 并行开发使用 Git Worktree，不允许两个写 Agent 修改同一个工作区。
- 需求与架构未经人工确认时，Developer 不进入实现阶段。
