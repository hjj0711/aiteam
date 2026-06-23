# Skills 架构与使用

本文件说明本工作区如何给 agent 装 skill,以及"不同角色用不同 skill"的约定。
面向 Claude Code 的 Agent Skills。术语扫盲见 `README.md` 的「新手必读」。

## 什么是 Skill

一个 skill = 一个文件夹,里面至少有一个 `SKILL.md`。`SKILL.md` 顶部的 YAML
`description` 告诉 Claude "**这件事怎么做 + 什么时候用**",Claude 据此自动按需调用。

```
<skill-name>/
  SKILL.md          # 必需：frontmatter(name/description) + 正文说明
  reference.md      # 可选：详细资料，按需加载
  examples/         # 可选：示例
  scripts/          # 可选：可执行脚本
```

最小 frontmatter:

```markdown
---
name: my-skill
description: 这个技能做什么 + 何时使用（触发依据，务必写清楚）
---
正文……
```

常用可选 frontmatter 字段(来自官方):

- `allowed-tools` / `disallowed-tools` — 限制该 skill 能用的工具。
- `disable-model-invocation: true` — 只允许用户手动 `/name` 触发,不让模型自动调用。
- `context: fork` + `agent: <name>` — 在隔离子代理里运行该 skill。

## 四种添加方式

| 方式 | 位置 / 命令 | 作用范围 | 适合 |
| --- | --- | --- | --- |
| 1. 项目手动 | `.claude/skills/<name>/SKILL.md`(随 Git 共享) | 本仓库 | 团队共享、与项目绑定。**本工作区默认用这种** |
| 2. 个人手动 | `~/.claude/skills/<name>/SKILL.md` | 你电脑上所有项目 | 个人通用习惯 |
| 3. 插件市场 | `/plugin marketplace add <repo>` → `/plugin install <name>` | 装了该插件的会话 | 用社区/官方现成 skill 包 |
| 4. 附加目录 | 启动加 `--add-dir <path>` 或 `/add-dir` | 当前会话 | 复用仓库外已有的 skill 目录 |

说明:
- **官方 / 插件**:Anthropic 与社区通过"插件(plugin)"分发 skill。先 `add` 一个市场仓库,
  再 `install`;插件里的 skill 命名为 `plugin-name:skill-name`。
- **附加目录**:例如复用本机另一个项目的 skill 库,可启动时
  `claude --add-dir /Users/kit/Documents/myself/newworld/.agents/skills`,
  该目录下的 skill 当次会话即可用(不复制进本仓库)。

## 本工作区的架构:每个角色用自己的 skill

Claude Code 会**自动发现 `.claude/skills/` 下的全部 skill**,并按 `description` 自行决定
何时调用——它本身没有"按角色隔离"的概念。本工作区在其之上加一层**约定**:

> 每个角色文件 `.aiteam/roles/<role>.md` 里有一个 `## Skills` 段,列出该角色应优先使用的 skill。
> 你以哪个角色启动任务(在提示里引用对应 role.md),role.md 就告诉 Claude 该用哪些 skill。

```
.claude/skills/            # 所有 skill 的实际存放地(全局可见，随 Git 共享)
  capacitor/SKILL.md
  record-decision/SKILL.md
  ...
.aiteam/roles/<role>.md    # 每个角色的 ## Skills 段 = 该角色的 skill 清单(可手动改)
docs/skills.md             # 本文件：架构与使用
```

这是一种**软映射**:skill 全局可见,role.md 负责"指派与聚焦"。要修改某个角色用哪些 skill,
直接编辑该角色的 `## Skills` 段即可。

### 当前角色 → skill 映射

| 角色 | Skills |
| --- | --- |
| Developer | `capacitor`, `react-dev`, `nodejs-backend-patterns`, `mongodb` |
| QA | `webapp-testing` |
| UX | `web-design-guidelines` |
| Architect | 待定：`codex-brainstorm`（需 Codex MCP） |
| BA / Reviewer | 暂未指派(按需在各自 role.md 添加) |

> 注：`mongodb` 与 `nodejs-backend-patterns` 由 `npx skills add` 安装到 `.agents/skills/`，
> 并以**软链**形式出现在 `.claude/skills/` 供 Claude Code 使用。其余 skill 是直接复制进
> `.claude/skills/` 的实体目录。`mongodb-attack` 在 `wgpsec/AboutSecurity` 中不存在，已跳过。

### 给某个角色加一个 skill(标准步骤)

1. 把 skill 文件夹放进 `.claude/skills/<name>/`(手动新建,或从别处复制)。
2. 打开对应的 `.aiteam/roles/<role>.md`,在 `## Skills` 段加一行说明。
3. 开一个新的 Claude Code 会话使其生效。

### 想要"硬隔离"(可选,进阶)

若需要严格限制"某角色只能用某些 skill",用 Claude Code 的两种原生机制:

- **子代理**:在 `.claude/agents/<role>.md` 定义子代理,配合权限规则
  `Skill(capacitor)` / `Skill(deploy *)` 精确允许或拒绝具体 skill。
- **权限设置**:在 `.claude/settings*.json` 用 `skillOverrides` 把某些 skill 设为
  `off` / `name-only`。

本工作区默认用上面的软映射(role.md 清单),够用且易维护;需要强隔离时再上子代理。

## 来源与版权

从市场/他处引入的 skill 保留其 `_meta.json`(记录 owner、版本、来源 commit)以便追溯。
例:`capacitor` 来自 `capawesome-team`(openclaw 市场)。
