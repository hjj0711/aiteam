# aiteam LangGraph 运行时

把 `.aiteam/roles/` 里的角色契约变成一个**受控的多 Agent 图**:复杂度路由、覆盖度评估、QA 有界返工、Fix-Loop 护栏,以及作为图状态强制的**预算账本**。

两个引擎:

- **StubEngine**(默认 `--stub`):确定性占位产物,无需 API Key,用于看流程和单测。
- **ClaudeEngine**(真引擎):加载 `.aiteam/roles/<role>.md` 契约 + 调 `claude` CLI,真实读写 `projects/`、`docs/`、`memory/`;支持**实时流式输出**、**关键节点暂停引导**、**改动落到 task 分支**。Codex 适配器是下一步。

## 目录

```
runtime/
  aiteam_runtime/
    state.py        # 图状态(可 checkpoint/恢复)+ vcs/反馈字段
    guardrails.py   # 预算账本 + 确定性护栏(token/cost 强制配置)
    engine.py       # RoleEngine 接口 + StubEngine + ClaudeEngine(流式)+ 复杂度分类
    nodes.py        # 各角色节点 + 条件路由 + developer 的 vcs 接入
    graph.py        # 图编排 + 可配置中断点 + 编译入口
    vcs.py          # per-task 分支隔离(start/snapshot),供 developer 与脚本共用
  run_demo.py       # 本地端到端跑一个任务(实时 + 可引导)
  tests/            # 确定性单测(无需 API Key)
  langgraph.json    # LangGraph Studio / CLI 入口
  requirements.txt
```

## 流程

```text
orchestrator 组装角色集（信号或显式覆盖）
   | 无前置角色 ----------------------------> developer -> qa
   | 含前置角色 --> [ba] -> [ux] -> [architect] -> developer -> qa   # []=按需，未选则跳过
qa --(pass, 含 reviewer)--> reviewer -> END
   --(pass, 无 reviewer)----------------> END
   --(fail, 未到上限)-------------------> developer   # 有界返工
   --(blocked / 到上限)-----------------> END
```

- **角色选择**(`orchestrator.md`):Developer + QA always-on;BA/UX/Architect/Reviewer 按信号(`requirements_clear`/`has_ui`/`touches_contract`/`risk_high`)各自决定是否上。也可在任务里显式 `roles_override=[...]` 强制(如只要 `developer,qa`),覆盖信号但会对跳过的高风险角色给出 WARN。
- **覆盖度评估**(`architect.md`):记录 pass 次数,上限 3。
- **QA 返工闭环**(`qa.md`):失败回 Developer,最多 2 轮,超限转 `blocked` 不静默放行。
- **Fix-Loop 护栏**(`developer.md`):5 次迭代或反复进入即停手转 `blocked`。
- **预算账本**(`docs/runtime-evaluation.md`):模型调用数/工具调用数/token/费用/每角色调用数/总超时,任一超限即 `blocked`。
- **人工审批**:编译时在 `ba`、`architect` 后 `interrupt`,人工查 `docs/` 后用同一 `thread_id` 恢复。

> 可视化流程图(FigJam):https://www.figma.com/board/rojw0Rr1BKgaGSvXQMuFWu

## 安装与运行

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r runtime/requirements.txt

# 端到端 demo(stub 引擎,非交互、不连真 AI)
python runtime/run_demo.py --stub "Add user auth with sessions"
python runtime/run_demo.py --stub "Fix a typo in the footer"   # 简单分支

# 真引擎(实时输出 + 关键节点暂停引导 + 改动进 task 分支)
python runtime/run_demo.py "Add user auth with sessions"

# 单测
pip install pytest
cd runtime && python -m pytest -q
```

## 实时、引导与改动隔离(真引擎)

- **实时输出**:`ClaudeEngine(stream=True)` 用 `--output-format stream-json`,逐步把角色输出打到 stderr;`run_demo` 用 `graph.stream(stream_mode="updates")` 做节点级实时。
- **人工引导**:`build_graph(interrupt_after=["ba","architect","developer"])` 在这些节点后暂停,`run_demo` 读取你的输入写入 `state.human_feedback`,由 `engine._build_prompt` 作为「HUMAN GUIDANCE」注入下一个角色。
- **改动隔离/回滚**:`vcs.py` 让 developer 在 `aiteam/<task_id>` 分支上逐次 commit(`vcs_enabled` 开启时)。查看 `scripts/task-changes.sh <id>`,取消 `scripts/task-revert.sh <id>`;手动流程开工前用 `scripts/task-start.sh <id>`。

## 可视化调试(LangGraph Studio,可选)

仅在想看流程图 / 节点 state 时使用,日常 CLI 用法不依赖它。

```bash
pip install "langgraph-cli[inmem]"
cd runtime && langgraph dev      # 浏览器里看图、节点状态、线程、checkpoint
```

OpenADE 是另一条可选可视化路线(看 Diff/快照/Worktree),与本运行时互补,不互相替代。

### LangSmith 追踪(可选)

Studio 提示 `LANGSMITH_API_KEY missing` 只是引导,**不影响本地运行**。要把 runs 上报到 LangSmith:

```bash
cp .env.example .env
# 编辑 .env：
#   LANGSMITH_TRACING=true
#   LANGSMITH_API_KEY=lsv...   # https://smith.langchain.com 设置页获取
#   LANGSMITH_PROJECT=aiteam
```

重启 `langgraph dev` 后,LangSmith 的 `aiteam` 项目即出现 runs。免费 Developer 档每月 5000 条 trace,建议采样限量。`.env` 已被 `.gitignore` 忽略,密钥不进仓库。

## 预算是强制项

`guardrails.new_ledger()` 在 `max_total_tokens` 或 `max_total_cost_usd` 未配置(>0)时**直接报错**,因为正确数值取决于该角色用的是 API Key 还是 CLI 订阅。运行前必须显式设置。

## 接入真实引擎(下一步)

实现 `RoleEngine.run(role, state) -> RoleResult`:
1. 加载对应 `.aiteam/roles/<role>.md` 契约;
2. 通过 `bin/codex` / Claude Code CLI 调用模型(BA/UX/架构/审查偏 Claude,实现偏 Codex);
3. 更新 `docs/` 与 `memory/`,把 token/cost 回填进 `RoleResult` 以驱动预算账本。
