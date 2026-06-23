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

### 最简单的用法（从易到难）

**用法 1 ｜ 只想看看它怎么干活（不花钱、不连真 AI）**

打开“终端”应用，逐行粘贴运行（需要电脑里有 Python 3.11 以上；下面的 `python3.12` 若提示找不到，换成 `python3` 试试）：

```bash
python3.12 -m venv runtime/.venv
runtime/.venv/bin/pip install -r runtime/requirements.txt
runtime/.venv/bin/python runtime/run_demo.py "把页脚的拼写改对"
```

屏幕会打印出“AI 团队走了哪几步”。这一步用的是**假引擎**：只演示流程，不调用真模型、不产生费用。

只想用“开发 + 测试”两个角色？在命令末尾加 `0 developer,qa`：

```bash
runtime/.venv/bin/python runtime/run_demo.py "你的需求" 0 developer,qa
```

**用法 2 ｜ 想看流程图（图形界面）**

```bash
runtime/.venv/bin/pip install "langgraph-cli[inmem]"
(cd runtime && ./.venv/bin/langgraph dev)
```

然后用浏览器打开下面这个网址，就能看到角色流程图在跑：

```text
https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

看完想关掉：在终端运行 `pkill -f "langgraph dev"`。

> 注：Studio 里如果提示 `LANGSMITH_API_KEY missing`，那只是“是否把记录上传到云端”的可选项，不影响本地使用，可以无视。

**用法 3 ｜ 想让真 AI 真的帮你写代码**

目前 `runtime/` 还是骨架（用假引擎演示流程），还没接上真模型。在接通之前，可以用下面的「当前手动流程」：在 OpenADE 或终端里，按角色一个个调用 Claude / Codex 来真正干活。

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
scripts/           # 启动脚本
bin/               # CLI 包装器
```

- LangGraph 作为受控的多 Agent 运行时，负责状态、检查点、循环上限、超时、人工审批和恢复。
- LangGraph Studio 用于查看执行图、节点状态、线程、检查点和调试过程。
- OpenADE 作为可选的 Codex/Claude 可视化工作台，提供并行规划、Diff、Git 快照和 Worktree。
- Codex 与 Claude Code 使用各自现有登录，不在仓库保存密钥。
- `AGENTS.md`、角色文件和 `memory/` 构成跨模型共享记忆。
- Git 中的需求、决策和测试结果是事实来源，聊天记录不是。

目前角色契约、文档和 OpenADE 启动脚本已就绪，LangGraph 运行时骨架也已落地（见 `runtime/`，默认用假引擎演示流程，可跑通、可单测）。下一步是把角色接到真实的 Codex/Claude；选型审计见 `docs/runtime-evaluation.md`。

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

# 2) 命令行跑一个任务（试不同复杂度走不同路径）
runtime/.venv/bin/python runtime/run_demo.py "Fix a typo in the footer"     # 简单：直达 Dev→QA
runtime/.venv/bin/python runtime/run_demo.py "Add user auth with sessions"  # 标准：全链 + QA 返工

# 3) 可视化调试（LangGraph Studio，可选）
runtime/.venv/bin/pip install "langgraph-cli[inmem]"
(cd runtime && ./.venv/bin/langgraph dev)
# 浏览器打开： https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
# 停止： pkill -f "langgraph dev"
```

可选追踪：把 `runtime/.env.example` 复制为 `runtime/.env`，填 `LANGSMITH_API_KEY` 并设 `LANGSMITH_TRACING=true`，即可在 LangSmith 看到 runs；不开也能用，Studio 照常看图。

测试：`(cd runtime && ./.venv/bin/python -m pytest -q)`。完整说明见 `runtime/README.md`。

## 当前手动流程

1. 在 OpenADE 新建任务，选择 Claude，引用 `.aiteam/roles/ba.md` 完成需求澄清。
2. 人工确认 `docs/requirements.md`。
3. 选择 Claude，引用 `.aiteam/roles/ux.md` 和 `.aiteam/roles/architect.md` 完成设计。
4. 对开发计划使用 HyperPlan Cross-Review，让 Claude 与 Codex 互审。
5. 选择 Codex 执行开发，使用独立 Worktree。
6. 选择 Claude 或 Codex，引用 `.aiteam/roles/qa.md` 执行测试。
7. 选择另一个模型，引用 `.aiteam/roles/reviewer.md` 做最终审查。

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
