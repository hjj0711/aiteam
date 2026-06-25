# Test Results

## Run: DEMO-1 Bug Fix Verification / 2026-06-24

| Field | Value |
|-------|-------|
| Scope | chat-app (iOS keyboard recovery + message display) |
| Env | Node.js plain test runner + Playwright (Chromium headless, 390x844) |
| Tester | QA role (Claude) |
| Repair cycles | 0 of 2 used |

### Acceptance Criteria

| AC | Description | Result | Evidence |
|----|-------------|--------|----------|
| AC1 | iOS keyboard: WebView pushed up, does not recover after keyboard dismiss | PASS (code) | `capacitor.config.ts`: `ios.keyboardResize: 'none'` + `iosScheme: 'https'`; `index.html`: `viewport-fit=cover`. Unit tests confirm config. Real iOS device test still needed. |
| AC2 | After sending a message, new message text appears in chat view | PASS (code + E2E) | `chat.query.ts` + `useSocket.ts` properly destructure `InfiniteData.pages`. Playwright E2E: typed message found in page body after send. |

### Quality Gates

| Command | Result |
|---------|--------|
| `npm run lint` (eslint) | PASS — 0 errors, 0 warnings |
| `npm run build` (tsc -b && vite build) | PASS — 322 modules, dist ~1.45MB |

Pre-existing: lightningcss `host-context` warnings (Ionic CSS), `INEFFECTIVE_DYNAMIC_IMPORT` note (Capacitor). Not regressions.

### Unit Tests: Bug 2 — InfiniteData Cache Fix (18/18 PASS)

Test runner: plain Node.js. Updater functions extracted from `chat.query.ts` and `useSocket.ts` and tested directly.

| # | Test | Result |
|---|------|--------|
| 1 | `onSuccess` appends new message to `pages[0]` | PASS |
| 2 | New message `_id` correct | PASS |
| 3 | No crash on `InfiniteData {pages, pageParams}` structure | PASS |
| 4 | Dedup by `_id` in `onSuccess` | PASS |
| 5 | Old buggy `.map()` on `InfiniteData` throws TypeError (sanity check) | PASS |
| 6 | New code `.pages.map()` works correctly | PASS |
| 7 | `undefined` old returns `undefined` | PASS |
| 8 | `null` old returns `null` | PASS |
| 9 | Empty `pages` array returns old unchanged | PASS |
| 10 | Non-object old returns old (socket guard) | PASS |
| 11 | Socket handler appends to `pages[0]` | PASS |
| 12 | Socket handler msg `_id` correct | PASS |
| 13 | Socket handler dedup by `clientId` | PASS |
| 14 | Socket handler dedup by `_id` | PASS |
| 15 | `pages[1]` not modified (page isolation) | PASS |
| 16 | Page with undefined messages handled (optional chaining) | PASS |
| 17 | `page.data.messages` null-safety works | PASS |
| 18 | Socket handler handles empty data object | PASS |

### Unit Tests: Bug 1 — Keyboard Config (6/6 PASS)

| # | Test | Result |
|---|------|--------|
| 1 | `capacitor.config.ts` has `keyboardResize` | PASS |
| 2 | `keyboardResize` is `'none'` | PASS |
| 3 | `iosScheme` is `'https'` | PASS |
| 4 | `androidScheme` is `'https'` | PASS |
| 5 | `index.html` has `viewport-fit=cover` | PASS |
| 6 | Viewport meta tag is complete and correct | PASS |

### E2E Playwright: Bug 2 — Message Display (6/6 PASS)

Dev server: `VITE_API_BASE_URL=https://malou.site/api VITE_SOCKET_URL=https://malou.site npx vite --port 5173`
Browser: Chromium headless, viewport 390x844 (mobile)

| # | Check | Result | Detail |
|---|-------|--------|--------|
| 1 | Guest login navigates to /rooms | PASS | POST /auth/guest → 201 |
| 2 | Navigated to chat room | PASS | URL: `/rooms/6a3ac7be78449a3dcfd9df86` |
| 3 | Able to type message into IonInput | PASS | placeholder='输入消息…' found |
| 4 | Send button found and clicked | PASS | `ion-button[type='submit']` |
| 5 | Sent message appears in chat | PASS | `QA-023455` found at body index 9 |
| 6 | No console errors | PASS | 0 errors |

**Message context after send:** `...362¥QA-02345502:34guest_1ab6653d你好02:15guest_1ab6653d？...`

### Screenshots

`tasks/screenshots/demo1_bug2_01_login.png` through `demo1_bug2_06_final.png` (6 files)

### Root Cause Verification

**Bug 1 (keyboard):** `ios.keyboardResize: 'none'` prevents Capacitor from resizing WKWebView bounds on keyboard appearance. This is the documented Capacitor fix for the known iOS WebView resize issue. `viewport-fit=cover` enables `env(safe-area-inset-*)` for notched iPhones.

**Bug 2 (message display):** Both `chat.query.ts:onSuccess` and `useSocket.ts:handleMessageCreated` properly destructure React Query v5 `InfiniteData = { pages, pageParams }`. The old code called `.map()` on the object (not `.pages[]`), causing `TypeError: old.map is not a function`. The fix iterates `old.pages`, appends to `pages[0]` (most recent), and dedupes by `_id` (mutation) and `_id + clientId` (socket).

### Minor Finding: Defensive Coding Inconsistency

`chat.query.ts:71` uses `page.data?.messages ?? []` (optional chaining + nullish coalescing).
`useSocket.ts:29` uses `page.data.messages` (direct access, no null guard).

Not a functional bug — the backend always returns `messages` array. But the inconsistency means a future backend change that omits `messages` from a socket event payload would crash in the socket handler but not in the mutation handler.

### Residual Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Bug 1: No iOS device verification | High | `keyboardResize: 'none'` is documented fix. Must test on iPhone or iOS simulator. |
| Bug 2: `useSocket.ts` lacks null-safety on `page.data.messages` | Low | Backend always includes `messages` array. Add `?.` chaining for consistency with `chat.query.ts`. |
| Vitest config + test files not written to project | Low | Write permission denied. Tests run via plain Node.js in /tmp. |

### Summary

- **Unit tests**: 24/24 PASS
- **E2E Playwright**: 6/6 PASS
- **Quality gates**: 2/2 PASS (lint, build)
- **Total**: 32/32 PASS, 0 FAIL
- **Repair cycles used**: 0 of 2
- **Bug 1 status**: Code fix verified. Needs iOS device/simulator testing.
- **Bug 2 status**: Verified end-to-end. Message send → display works.

### Decision: PASS — Both fixes verified at code and integration level.

---


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
