# Architecture — Newworld Backend + Chat App

Status: Draft (awaits human acceptance)

## Context

在 `newworld/projects/backend`（Express + TypeScript + MongoDB + Socket.io）和 `newworld/projects/chat-app`（React + Vite + Capacitor）现有代码基础上，完成一个可用的 MVP 聊天系统。后端需可生产部署，前端需本地可运行、可构建，UI 使用 Ionic UI。

## Existing System Inspection

### Backend 已有能力

- 分层架构：Controllers → Services → Repositories → Mongoose Models
- Auth：register/login/refresh/logout，JWT access + refresh token rotation
- User：GET/PATCH /api/users/me
- Room：POST/GET /api/rooms，GET /api/rooms/:roomId，POST /api/rooms/:roomId/join
- Message：GET/POST /api/rooms/:roomId/messages（cursor 分页）
- Socket.io：room:join/leave, message:send, typing:start/stop, message:read
- Docker Compose + Nginx 生产部署

### Backend 需要改动

- 新增 `POST /api/auth/guest`：接收 `deviceId`，创建或复用 guest 用户，返回 auth tokens
- Room model/validators：移除 `private` 类型支持，只保留 `public`
- User validators：PATCH /api/users/me 只允许 `username`、`avatarUrl`，不允许 `email`
- Guest 用户 model：User roles 加 `guest`，或用 `isGuest` 字段标记

### Chat-app 已有能力

- React 19 + Vite + React Router + TanStack Query + Socket.io client + Capacitor
- AuthProvider：login/register/logout/refresh
- RoomListPage、CreateRoomDialog、ChatPage、ChatInput、MessageBubble
- useSocket、useTyping、socket.ts、api.ts、secure-storage.ts
- 路由：/login, /register, /rooms, /rooms/:roomId, /profile, /settings

### Chat-app 需要改动

- 安装 `@ionic/react` + `@ionic/react-router`，迁移路由到 IonReactRouter
- 所有页面迁移到 Ionic UI 组件
- 登录页新增"游客登录"按钮 + deviceId 生成/读取逻辑
- refresh token 存储改为 native-only（Web 不持久化）
- Socket 断线/重连提示条
- 消息 clientId 去重确认
- Profile 页：email 只读，username/avatarUrl 可编辑

## Proposed Design

### 数据流

```text
Chat-app (Ionic UI)
  ├── REST API ──→ Express :4000 ──→ Services ──→ Repositories ──→ MongoDB
  └── Socket.io ──→ Express :4000 ──→ Socket handlers ──→ Services ──→ MongoDB
```

### 新增接口

| Method | Path | Body | Response | 说明 |
|--------|------|------|----------|------|
| `POST` | `/api/auth/guest` | `{ deviceId: string }` | `{ user, tokens }` | 创建或复用 guest 用户 |

### Guest 用户设计

- User model 新增 `isGuest: boolean` 字段（默认 `false`）
- Guest 用户 `username` 自动生成：`guest_<deviceId前8位>`
- Guest 用户 `email` 自动生成：`<deviceId>@guest.local`
- Guest 用户 `roles`: `["guest"]`
- 同一 `deviceId` 再次调用时复用已有用户
- Guest 用户可加入公开房间、发送消息，与普通用户共用 Socket 鉴权

## Task Breakdown

### T1: Backend — Guest Login API

- **Produces**: `POST /api/auth/guest` 接口，guest 用户创建/复用逻辑
- **Consumes**: User model, Token service, Auth service
- **Boundaries**: 只改 auth 相关文件；不动 room/message/socket
- **Files**: `auth.service.ts`, `auth.controller.ts`, `auth.routes.ts`, `auth.validators.ts`, `user.model.ts`
- **Verification**: `curl -X POST /api/auth/guest -d '{"deviceId":"test123"}'` 返回 user + tokens；重复调用返回同一用户

### T2: Backend — Room 简化为 Public Only

- **Produces**: Room model/validators 只支持 `public` 类型
- **Consumes**: Room model, chat validators
- **Boundaries**: 只改 room model 和 validators；不动 message 逻辑
- **Files**: `room.model.ts`, `chat.validators.ts`
- **Verification**: 创建房间时 type 只接受 `public`；private 返回 400

### T3: Backend — User Profile 限制 email 不可改

- **Produces**: PATCH /api/users/me 只接受 `username`、`avatarUrl`
- **Consumes**: User validators
- **Boundaries**: 只改 user validators
- **Files**: `user.validators.ts`
- **Verification**: `PATCH /api/users/me` 带 `email` 字段返回 400

### T4: Backend — Typecheck/Lint/Build 通过

- **Produces**: 后端代码质量验证通过
- **Consumes**: T1, T2, T3
- **Boundaries**: 不改功能代码，只修 lint/type 错误
- **Verification**: `npm run typecheck && npm run lint && npm run build` 全部通过

### T5: Chat-app — 安装 Ionic + 路由迁移

- **Produces**: Ionic React 集成，IonReactRouter 替换 react-router-dom
- **Consumes**: 现有路由结构
- **Boundaries**: 只改路由和 app 入口；页面组件后续迁移
- **Files**: `package.json`, `main.tsx`, `app/router.tsx`, `app/providers.tsx`
- **Verification**: `npm run dev` 启动后 Ionic 框架生效，路由可导航

### T6: Chat-app — 登录/注册页迁移 Ionic + 游客登录

- **Produces**: Ionic 登录/注册页，游客登录按钮 + deviceId 逻辑
- **Consumes**: T5, AuthProvider, secure-storage
- **Boundaries**: 只改 auth 页面和 AuthProvider；不改后端
- **Files**: `LoginPage.tsx`, `RegisterPage.tsx`, `AuthProvider.tsx`, `useAuth.ts`
- **Verification**: 登录/注册/游客登录均可工作；游客 deviceId 在 native 中持久化

### T7: Chat-app — 房间列表页迁移 Ionic

- **Produces**: Ionic RoomListPage + CreateRoomModal
- **Consumes**: T5, rooms.query.ts
- **Boundaries**: 只改房间列表页；不改聊天页
- **Files**: `RoomListPage.tsx`, `CreateRoomDialog.tsx`
- **Verification**: 房间列表展示、创建、加入均工作；空状态显示

### T8: Chat-app — 聊天页迁移 Ionic

- **Produces**: Ionic ChatPage + MessageBubble + ChatInput + TypingIndicator
- **Consumes**: T5, chat.query.ts, useSocket, useTyping
- **Boundaries**: 只改聊天页组件；不改 Socket 逻辑
- **Files**: `ChatPage.tsx`, `ChatInput.tsx`, `MessageBubble.tsx`
- **Verification**: 消息展示、发送、历史分页、typing 指示器均工作

### T9: Chat-app — Profile 页迁移 Ionic + email 只读

- **Produces**: Ionic ProfilePage，email 只读，username/avatarUrl 可编辑
- **Consumes**: T5, AuthProvider
- **Boundaries**: 只改 profile 页
- **Files**: `ProfilePage.tsx`, `SettingsPage.tsx`
- **Verification**: 查看资料、编辑 username/avatarUrl、保存均工作

### T10: Chat-app — Refresh Token Native-Only + Socket 重连提示

- **Produces**: Web 不持久化 refresh token；native 持久化；Socket 断线/重连提示条
- **Consumes**: T5, api.ts, socket.ts, secure-storage.ts
- **Boundaries**: 只改 api.ts, socket.ts, secure-storage.ts
- **Files**: `api.ts`, `socket.ts`, `secure-storage.ts`, `AuthProvider.tsx`
- **Verification**: Web 刷新页面后不自动恢复；native 重启后恢复；Socket 断线显示提示条

### T11: Chat-app — Lint/Build 通过

- **Produces**: 前端代码质量验证通过
- **Consumes**: T5-T10
- **Boundaries**: 不改功能代码，只修 lint/type 错误
- **Verification**: `npm run lint && npm run build` 全部通过

### T12: Backend — 生产部署验证

- **Produces**: 后端部署到生产环境并验证
- **Consumes**: T4
- **Boundaries**: 只验证部署，不改代码
- **Verification**: `curl https://malou.site/health` 返回 ok；`/api` 和 `/socket.io` 可访问

## Coverage Evaluation

### Pass 1: AC → Task Mapping

| AC | Task | Verification |
|----|------|-------------|
| AC1.1 (注册) | T4 (现有) | curl POST /api/auth/register |
| AC1.2 (登录) | T4 (现有) | curl POST /api/auth/login |
| AC1.3 (token 存储 native) | T10 | native 重启恢复会话 |
| AC1.4 (refresh native only) | T10 | Web 不持久化 refresh |
| AC1.5 (auto refresh) | T10 | access token 过期后自动 refresh |
| AC1.6 (登出) | T4 (现有) | curl POST /api/auth/logout |
| AC1.7 (路由守卫) | T5, T6 | 未登录跳转 /login |
| AC1.8 (游客登录) | T1, T6 | 游客登录 → /rooms |
| AC2.1 (查看资料) | T9 | Profile 页展示 |
| AC2.2 (可选字段) | T3, T9 | 空字段不报错 |
| AC2.3 (username/avatarUrl 可改) | T3, T9 | PATCH 成功 |
| AC2.4 (更新后展示) | T9 | 保存后页面刷新 |
| AC3.1 (房间列表) | T7 | /rooms 展示列表 |
| AC3.2 (空状态) | T7 | 无房间时显示提示 |
| AC3.3 (只支持公开) | T2 | private 返回 400 |
| AC3.4 (创建公开房间) | T7 | 创建成功 |
| AC3.5 (加入公开房间) | T7 | 加入成功 |
| AC3.6 (列表刷新) | T7 | 创建/加入后列表更新 |
| AC4.1 (房间名+消息) | T8 | 聊天页展示 |
| AC4.2 (发送消息) | T8 | 发送成功 |
| AC4.3 (消息持久化) | T4 (现有) | curl POST message |
| AC4.4 (分页) | T8 | 向上滚动加载更多 |
| AC4.5 (权限拒绝) | T4 (现有) | 无权限返回 403 |
| AC4.6 (clientId 去重) | T8 | 不重复显示 |
| AC5.1 (Socket 鉴权) | T4 (现有) | Socket 连接需 token |
| AC5.2 (join/leave) | T8 | 进入/离开房间 |
| AC5.3 (实时消息) | T8 | 多客户端实时收到 |
| AC5.4 (typing) | T8 | 输入提示显示 |
| AC5.5 (断线重连) | T10 | 断线后自动重连 |
| AC6.1 (Vite 开发) | T5 | npm run dev |
| AC6.2 (Ionic UI) | T5-T9 | 页面使用 Ionic 组件 |
| AC6.3 (native storage) | T10 | secure storage 存储 |
| AC6.4 (CORS) | T4 (现有) | 生产 CORS 配置 |
| AC6.5 (Web+native 可运行) | T11 | lint/build 通过 |
| AC6.6 (后端部署优先) | T12 | 生产验证 |
| AC7.1 (Docker Compose) | T4 (现有) | docker compose up |
| AC7.2 (宿主机 dev) | T4 (现有) | npm run dev |
| AC7.3 (backend 检查) | T4 | typecheck/lint/build |
| AC7.4 (chat-app 检查) | T11 | lint/build |
| AC7.5 (后端生产部署) | T12 | malou.site 验证 |
| AC7.6 (chat-app 本地可运行) | T11 | npm run dev |
| AC7.7 (文档) | T4 (现有) | 文档已有 |
| AC7.8 (.env 不提交) | T4 (现有) | .gitignore 检查 |

### Coverage Score

- Total ACs: 41
- Mapped to task: 41/41 (100%)
- Mapped to verification: 41/41 (100%)
- **Coverage: 100% — no critical gaps**

## Risks And Tradeoffs

| 风险 / 取舍 | 影响 | 缓解 |
|-------------|------|------|
| Ionic UI 引入增加包体积 | WebView 加载稍慢 | Ionic 按需导入 + tree-shaking |
| Guest 用户无密码保护 | deviceId 被猜到可冒充 | deviceId 使用 UUID，足够随机 |
| Web 不持久化 refresh token | Web 刷新页面需重新登录 | 本轮 Web 主要用于开发调试 |
| 现有代码有未提交改动 | 可能与新改动冲突 | 先 git stash 或基于现有代码增量改 |
| 无自动化测试 | 回归靠手动验证 | 本轮最低门槛：typecheck/lint/build + 手动 API 验证 |

## Verification Strategy

| 层级 | 方法 |
|------|------|
| Backend API | curl 逐一验证所有接口 + 边界 |
| Backend 质量 | `npm run typecheck && npm run lint && npm run build` |
| Chat-app 质量 | `npm run lint && npm run build` |
| Chat-app UI | 浏览器手动测试所有页面和状态 |
| 实时聊天 | 两个浏览器窗口测试实时消息和 typing |
| 生产部署 | `curl https://malou.site/health` + Socket.io 连接验证 |

## Execution Order

```text
T1 (guest API) ──→ T4 (backend checks) ──→ T12 (deploy)
T2 (room simplify) ──→ T4
T3 (profile limit) ──→ T4

T5 (Ionic setup) ──→ T6 (auth pages) ──→ T7 (rooms) ──→ T8 (chat) ──→ T9 (profile) ──→ T10 (storage/socket) ──→ T11 (chat-app checks)
```

Backend (T1-T4) 和 Chat-app (T5-T11) 可并行，T12 依赖 T4。
