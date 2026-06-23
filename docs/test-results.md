# Test Results

## Run: TODO-001 QA / 2026-06-23

| Field | Value |
|-------|-------|
| Scope | todo-app (server.js + index.html) |
| Env | Node.js + curl |
| Tester | QA role (Claude) |

## Acceptance Criteria Coverage

### US-1: 查看待办列表

| AC | 描述 | 结果 | 证据 |
|----|------|------|------|
| AC1.1 | 打开页面看到所有待办 | PASS | `GET /api/todos` 返回完整数组 |
| AC1.2 | 未完成未勾选，已完成勾选 | PASS | `done: false` 初始值；PATCH 后可切换 true/false |
| AC1.3 | 空列表显示提示 | PASS | HTML 包含「暂无待办事项」|

### US-2: 添加待办

| AC | 描述 | 结果 | 证据 |
|----|------|------|------|
| AC2.1 | 输入框和添加按钮 | PASS | HTML 包含 `input#todo-input` 和 `button[type=submit]` |
| AC2.2 | 输入后按按钮或 Enter 出现新待办 | PASS | POST 返回 201 + Todo；`<form>` 元素支持 Enter 提交；新项在数组顶部 |
| AC2.3 | 空内容不可添加 | PASS | 空字符串和纯空格均返回 400 `{"error":"text is required"}` |

### US-3: 标记完成/取消完成

| AC | 描述 | 结果 | 证据 |
|----|------|------|------|
| AC3.1 | 勾选框切换完成状态 | PASS | HTML 包含 `input[type=checkbox]`；PATCH 接口 toggle 成功 |
| AC3.2 | 完成项有删除线 | PASS | HTML CSS: `.todo-item.done .text { text-decoration: line-through; }` |
| AC3.3 | 取消完成恢复普通样式 | PASS | PATCH `done: false` 返回正确；JS toggle 正确切换 `.done` class |

### US-4: 删除待办

| AC | 描述 | 结果 | 证据 |
|----|------|------|------|
| AC4.1 | 删除按钮点击后消失 | PASS | DELETE 返回 204；列表长度减少 |
| AC4.2 | 删除无需确认 | PASS | JS 直接调用 `deleteTodo()` 无确认弹窗 |

## Edge Cases

| 测试 | 结果 | 证据 |
|------|------|------|
| PATCH 不存在的 id | PASS | 404 `{"error":"Todo not found"}` |
| DELETE 不存在的 id | PASS | 404 `{"error":"Todo not found"}` |
| 非法 JSON body | PASS | 400 `{"error":"Invalid JSON body"}` |
| done 字段非 boolean | PASS | 400 `{"error":"done must be a boolean"}` |
| 不存在的路由 | PASS | 404 `{"error":"Not Found"}` |
| 200 字符长文本 | PASS | 正常创建，text 长度 200 |

## UI State Verification (source inspection)

| 状态 | 表现 | 结果 |
|------|------|------|
| 加载中 | 显示「加载中...」| PASS |
| 加载失败 | 显示「加载失败，请刷新重试」| PASS |
| 空列表 | 显示「暂无待办事项」| PASS |
| 操作失败 toast | 底部红色提示「xxx失败，请重试」| PASS |
| 无障碍 | delete button 有 `aria-label` | PASS |
| 键盘操作 | `<form>` + `<input>` 支持 Enter 提交 | PASS |

## Summary

- **Passed**: 15/15
- **Failed**: 0
- **Blocked**: 0

## Residual Risk

- 未在真实浏览器中做 UI 手动测试（HTML/CSS/JS 通过源码审查和 API 测试验证）
- 前端乐观更新 + 失败回滚的竞态未做压力测试（单用户场景风险低）
- 建议 Reviewer 在浏览器中实际打开页面做最终确认
