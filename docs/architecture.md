# Architecture

Status: Draft (awaits human acceptance)

## Context

一个零依赖的 Node.js 单页待办事项 Web 应用。无数据库，无框架，纯标准库。

## Proposed Design

```text
浏览器                     Node.js Server
┌──────────┐    HTTP       ┌──────────────┐
│ index.html│ ←────────── │  server.js   │
│  (内嵌CSS  │  GET /      │              │
│   + JS)   │             │  REST API    │
│           │ ←─────────→ │  /api/todos  │
│  fetch()  │  JSON       │              │
└──────────┘             │  内存 []     │
                         └──────────────┘
```

### 文件结构

```text
project/
  server.js    # HTTP 服务 + API 路由 + 静态文件服务
  index.html   # 单页应用 (HTML + CSS + JS 全部内嵌)
```

**两个文件**，零 `node_modules`。

### 运行时

```
node server.js
# => 输出: Server running at http://localhost:3000
```

## Interfaces And Data

### REST API

| Method | Path | Body | Response | 说明 |
|--------|------|------|----------|------|
| `GET` | `/` | - | `text/html` | 返回 `index.html` |
| `GET` | `/api/todos` | - | `Todo[]` | 获取全部待办 |
| `POST` | `/api/todos` | `{ text: string }` | `Todo` (201) | 创建待办 |
| `PATCH` | `/api/todos/:id` | `{ done: boolean }` | `Todo` | 切换完成状态 |
| `DELETE` | `/api/todos/:id` | - | `204 No Content` | 删除待办 |

### 数据模型 (Todo)

```json
{
  "id": "string (crypto.randomUUID())",
  "text": "string",
  "done": false,
  "createdAt": "ISO 8601 string"
}
```

### 前端状态

```javascript
// 全局变量
let todos = [];       // 当前列表
let loading = false;  // 加载中
let error = null;     // 错误信息
```

## Delivery Plan

### Step 1: 搭建服务端骨架
- 创建 `server.js`：HTTP Server，URL 路由，JSON 解析，静态文件服务
- 文件：`server.js`
- 验收：`curl localhost:3000` 返回 HTML；`curl localhost:3000/api/todos` 返回 `[]`

### Step 2: 实现 REST API
- 完整的 CRUD 操作（Create/Read/Update/Delete）
- 内存数组存储，请求体解析，错误处理
- 文件：`server.js`
- 验收：用 curl 测试全部 4 个接口，验证响应格式

### Step 3: 创建前端页面
- `index.html`：输入框、按钮、列表、空状态、错误状态
- 内嵌 CSS（极简风格）和 JS（fetch API 交互）
- 文件：`index.html`
- 验收：浏览器打开页面，完整操作一遍 add → toggle → delete

### Step 4: 联调验证
- 启动 server，浏览器访问 localhost:3000
- 全面覆盖所有验收标准

## Risks And Tradeoffs

| 风险 / 取舍 | 影响 | 缓解 |
|-------------|------|------|
| 内存存储，重启丢失 | 练手项目可接受 | 不做处理 |
| 无并发控制 | 单用户场景无影响 | 不做处理 |
| 无前端路由 | 单页面不需要 | 不做处理 |
| 无构建工具 | CSS/JS 写在一起稍显杂乱 | 项目够小，可接受 |
| 无自动化测试框架 | 手动验证为主 | QA 阶段用 curl + 浏览器手动测试 |

## Verification Strategy

| 层级 | 方法 |
|------|------|
| API | `curl` 命令逐一验证 4 个接口 + 边界（空文本、不存在的 id） |
| UI | 浏览器手动测试所有用户故事和状态（空列表、添加、标记、删除） |
| 交叉审查 | Reviewer 用不同模型检查代码和测试结果 |
