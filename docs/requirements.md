# Requirements

Status: Accepted

## Task

NEWWORLD-CHAT-001: 完成 `/Users/kit/Documents/myself/newworld/projects/backend` 与 `/Users/kit/Documents/myself/newworld/projects/chat-app` 的聊天系统开发。

## Problem

`newworld` 已有一个 Express + TypeScript + MongoDB + Socket.io 后端骨架，以及一个 React + Vite + Capacitor 聊天前端骨架。后端文档描述了认证、房间、消息、Socket.io、Docker 和生产部署能力；前端已具备登录/注册、房间列表、聊天页、Socket 连接和安全存储基础。但当前需求尚未被明确成可验收的产品范围，`chat-app` 的 README 仍是 Vite 模板，开发前需要先确认目标能力、边界和验收标准。

## Users

- **普通聊天用户**：注册/登录后创建或加入聊天室，发送消息，查看历史消息，看到实时消息和输入状态。
- **个人站点所有者/维护者**：需要在本地和生产环境可运行、可部署、可排查问题的 backend + chat-app。

## Current Facts From Existing Docs And Code

- Backend 技术栈：Node.js 20+、TypeScript、Express、Socket.io、MongoDB + Mongoose、JWT access/refresh token、Zod、Winston、Docker Compose。
- Backend 已规划公开入口：`https://malou.site/health`、`https://malou.site/api`、`https://malou.site/socket.io`。
- Backend 文档声明支持：注册/登录/登出/个人资料、refresh token hash + rotation、房间与消息 REST API、Socket.io 实时聊天、日志、Docker 部署。
- Backend HTTP API 文档列出：`POST /api/auth/register|login|refresh|logout`，`GET/PATCH /api/users/me`，`POST/GET /api/rooms`，`GET /api/rooms/:roomId`，`POST /api/rooms/:roomId/join`，`GET/POST /api/rooms/:roomId/messages`。
- Backend Socket.io 事件文档列出：客户端 `room:join|leave`、`message:send`、`typing:start|stop`、`message:read`；服务端 `room:user_joined|left`、`message:created`、`typing:started|stopped`、`message:read`。
- Chat-app 技术栈：React 19、Vite、React Router、TanStack Query、Socket.io client、Capacitor、Capacitor secure storage。
- Chat-app UI 目标是 H5 WebView / Capacitor App，前端界面优先使用 Ionic UI 组件与移动端交互模式。
- Chat-app 路由现状：`/login`、`/register`、`/rooms`、`/rooms/:roomId`、`/profile`、`/settings`。

## In Scope

### 1. Authentication And Session

用户可以注册、登录、自动恢复会话、登出。

Acceptance criteria:
- **AC1.1**: 用户可通过 username/email/password 注册；重复 email 或 username 返回可理解错误。
- **AC1.2**: 用户可通过 email/password 登录；失败时显示错误且不进入聊天室。
- **AC1.3**: 登录成功后保存 access token；refresh token 只在 native/Capacitor 环境持久化到 secure storage。
- **AC1.4**: native 环境重启 app 后能用 refresh token 恢复会话；Web 浏览器环境不要求持久化 refresh token。
- **AC1.5**: access token 过期且 native storage 中存在 refresh token 时，前端自动调用 refresh 接口并重试原请求。
- **AC1.6**: 登出后清除本地 token，并回到登录页；后端作废对应 refresh token。
- **AC1.7**: 未登录访问 `/rooms`、`/rooms/:roomId`、`/profile`、`/settings` 会跳转到 `/login`。
- **AC1.8**: 支持游客登录：客户端生成或读取稳定 `deviceId`，在 native local storage / secure storage 中保存；游客无需填写账号密码即可进入聊天室。

### 2. Profile And Settings

用户可查看和更新自己的基础资料。

Acceptance criteria:
- **AC2.1**: 用户可查看当前用户名、邮箱、头像 URL 和创建时间。
- **AC2.2**: 用户资料字段均为可选填写；用户可更新允许变更的资料字段，非法字段或非法格式被前后端拒绝。
- **AC2.3**: 支持更新 `username`、`avatarUrl`；本轮不允许更新 `email`。
- **AC2.4**: 更新成功后前端立即展示最新资料。

### 3. Room Management

用户可浏览、创建、加入聊天室。

Acceptance criteria:
- **AC3.1**: `/rooms` 展示房间列表，包括名称、描述、类型和成员数量。
- **AC3.2**: 房间列表为空时显示空状态。
- **AC3.3**: 本轮只支持公开房间；不实现 private 房间规则。
- **AC3.4**: 用户可创建公开房间；名称必填并有长度限制。
- **AC3.5**: 已登录用户或游客用户可加入公开房间。
- **AC3.6**: 创建或加入房间后，房间列表自动刷新。

### 4. Chat Messages

用户可查看历史消息并发送新消息。

Acceptance criteria:
- **AC4.1**: 打开房间页后展示房间名称和最近消息。
- **AC4.2**: 用户可发送 1-2000 字符文本消息；空白消息不可发送。
- **AC4.3**: 成功发送的消息持久化到 MongoDB，并包含 sender、room、content、clientId、createdAt、status。
- **AC4.4**: 消息列表支持分页加载历史消息。
- **AC4.5**: 用户无房间访问权限时，REST 和 Socket 发送/读取都被拒绝。
- **AC4.6**: 使用 `clientId` 避免同一条消息在本地提交和 Socket 广播后重复显示。

### 5. Realtime Chat

用户在同一房间内实时看到消息和输入状态。

Acceptance criteria:
- **AC5.1**: Socket.io 连接必须使用当前 access token 鉴权。
- **AC5.2**: 用户进入房间时触发 `room:join`，离开时触发 `room:leave`。
- **AC5.3**: 一名用户发送消息后，同房间其他在线用户无需刷新即可看到 `message:created`。
- **AC5.4**: 输入框内容变化时发送 typing start/stop，同房间其他用户可看到“正在输入”。
- **AC5.5**: Socket 断线后自动重连；重连后仍能继续加入当前房间或提示重新登录。

### 6. Mobile / Capacitor / Ionic UI Readiness

Chat-app 应作为 Web + Capacitor App 双形态可运行，UI 按 H5 WebView 场景设计，优先使用 Ionic UI 组件和移动端交互模式。

Acceptance criteria:
- **AC6.1**: Web 本地开发通过 Vite 运行，API 走 `/api` 代理或同源反代。
- **AC6.2**: Chat-app 主要 UI 使用 Ionic UI（React 版）组件实现移动端 WebView 友好的页面、表单、列表、导航和输入体验。
- **AC6.3**: 原生 Capacitor 环境使用 secure storage/native storage 保存 refresh token 与游客 `deviceId`。
- **AC6.4**: Web 浏览器环境不持久化 refresh token；Web 可用于开发调试，但会话恢复以 native 为准。
- **AC6.5**: 生产环境的 API、Socket、CORS、Cookie/SameSite 配置能支持 `https://malou.site` 与 Capacitor origin。
- **AC6.6**: 本轮 Web 与 native/Capacitor 都应可运行；后端生产部署优先级高于 chat-app 生产发布。

### 7. Local Development, Deployment, And Operations

系统应可本地启动、检查、部署，并有基本运维文档。

Acceptance criteria:
- **AC7.1**: Backend 可通过 Docker Compose 启动 backend + MongoDB。
- **AC7.2**: Backend 可通过宿主机 `npm run dev` 连接 Docker MongoDB 开发。
- **AC7.3**: Backend 提供 `npm run typecheck`、`npm run lint`、`npm run build` 且应通过。
- **AC7.4**: Chat-app 提供 `npm run lint`、`npm run build` 且应通过。
- **AC7.5**: 后端需要可部署到生产环境，并通过 `https://malou.site/health`、`/api`、`/socket.io` 验证。
- **AC7.6**: Chat-app 本轮不要求生产部署，但必须本地可运行、可构建，并能连接后端。
- **AC7.7**: 文档说明本地启动、后端生产入口、Nginx 反代、数据库备份/同步和常见排查。
- **AC7.8**: `.env` 不提交到 git；生产环境不能使用默认 JWT secret。

## Out Of Scope For This Iteration

- 私密房间、多人私聊 / 好友系统 / 群成员邀请审批。
- 管理后台、封禁、举报、审计后台。
- 图片、文件、语音、表情包等富媒体消息。
- 端到端加密。
- 推送通知。
- 多 backend 实例横向扩展与 Redis Socket.io adapter。
- 托管 MongoDB、副本集、自动化云备份。
- App Store / TestFlight / Android 发布流程。
- Chat-app 生产部署。
- 自研完整移动端 UI 组件库（本轮优先使用 Ionic UI）。

## Constraints

- 不硬编码任何生产密钥、数据库密码、SSH key 或 token。
- 不删除或覆盖 `newworld` 中已有未提交改动。
- Backend 保持现有分层：Controllers → Services → Repositories → Mongoose Models。
- Backend 输入校验继续使用 Zod。
- Backend 认证继续使用 JWT access token + refresh token rotation。
- Chat-app 保持 React + Vite + TypeScript + TanStack Query + Socket.io client。
- Chat-app UI 优先使用 Ionic UI（React 版），避免重造基础移动端组件。
- 移动端相关实现优先遵循 Capacitor 约定。

## Assumptions

- 目标是先完成可用的 MVP 聊天系统，而不是社交产品完整形态。
- `backend` 是 `chat-app` 的唯一后端。
- 生产域名继续使用 `malou.site`。
- 本轮只有 backend 需要生产部署；chat-app 只需本地可运行和可构建。
- MongoDB 仍运行在 Docker Compose 中，且不直接暴露公网。
- 当前 `newworld` 工作树的大量未提交文件是用户已有工作，应保留。

## Resolved Decisions

1. **游客登录后端语义**：后端创建真实 `guest` 用户并返回普通 auth tokens，复用现有用户体系（消息 sender、房间成员、Socket 鉴权）。
2. **游客 deviceId 规则**：同一 deviceId 再次游客登录时复用同一游客用户，不重复创建。
3. **email 不可改**：本轮不允许更新 email，降低认证复杂度。
4. **已读回执**：本轮不做已读回执 UI，`message:read` 事件保留但不实现 UI。
5. **测试最低门槛**：backend `typecheck` + `lint` + `build`；chat-app `lint` + `build`；关键 backend API/Socket 手动或自动验证；Playwright E2E 有时间再加。

## Acceptance Gate Before Development

- 用户确认或修改本需求。
- Open Questions 中影响架构或验收的项已回答。
- Architect 需要把每条 acceptance criterion 映射到实现任务和验证路径。
