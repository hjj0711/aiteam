# aiteam LangGraph 运行时(骨架)

把 `.aiteam/roles/` 里的角色契约变成一个**受控的多 Agent 图**:复杂度路由、覆盖度评估、QA 有界返工、Fix-Loop 护栏,以及作为图状态强制的**预算账本**。

默认使用确定性 **Stub 引擎**,无需任何 API Key 就能跑通和单测;将来把 `engine.RoleEngine` 换成真实的 Codex / Claude Code CLI 适配器即可上线。

> 这是骨架:节点目前返回占位产物、不写 `docs/`。真实引擎才会读取角色契约 + 调模型 + 更新 `docs/` 与 `memory/`。

## 目录

```
runtime/
  aiteam_runtime/
    state.py        # 图状态(可 checkpoint/恢复)
    guardrails.py   # 预算账本 + 确定性护栏(token/cost 强制配置)
    engine.py       # RoleEngine 接口 + StubEngine + 复杂度分类
    nodes.py        # 各角色节点 + 条件路由
    graph.py        # 图编排 + 人工审批中断 + 编译入口
  run_demo.py       # 本地端到端跑一个任务
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

# 端到端 demo(stub 引擎)
python runtime/run_demo.py "Add user auth with sessions"
python runtime/run_demo.py "Fix a typo in the footer"        # 简单分支

# 单测
pip install pytest
cd runtime && python -m pytest -q
```

## 可视化调试(LangGraph Studio,可选)

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
