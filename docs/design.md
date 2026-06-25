# UX And UI Design — Newworld Chat App

Status: Draft (awaits human acceptance)

## Design System

- **UI 框架**: Ionic UI (React 版) — `@ionic/react` + `@ionic/react-router`
- **目标形态**: H5 WebView / Capacitor App，移动端优先
- **设计语言**: Ionic Motion + Material Design 阴影/波纹，iOS/Android 自适应模式
- **色调**: Ionic 默认主题色，可后续自定义
- **字体**: 系统默认字体栈，Ionic 推荐

## User Flows

### Flow 1: 认证入口

```text
App 启动
  │
  ├─ 有 access token → 进入 /rooms
  │
  ├─ native 有 refresh token → 调用 /auth/refresh
  │    ├─ 成功 → 进入 /rooms
  │    └─ 失败 → 跳转 /login
  │
  └─ 无 token → 跳转 /login
       │
       ├─ 输入 email + password → 登录 → /rooms
       ├─ 点击"注册" → /register → 注册成功 → /rooms
       └─ 点击"游客登录" → 生成/读取 deviceId → 后端创建 guest → /rooms
```

### Flow 2: 房间列表 → 聊天

```text
/rooms
  │
  ├─ 点击房间 → /rooms/:roomId → 加载消息 → 实时聊天
  │
  ├─ 点击"创建房间" → Ionic Modal → 填写名称/描述 → 创建 → 列表刷新
  │
  └─ 点击"加入" → 加入房间 → 列表刷新
```

### Flow 3: 聊天页

```text
/rooms/:roomId
  │
  ├─ 加载历史消息（分页，向上滚动加载更多）
  │
  ├─ 输入消息 → 发送 → 消息出现在底部
  │
  ├─ 收到 message:created → 新消息出现在底部
  │
  ├─ 输入时 → typing:start → 其他用户看到"正在输入"
  │
  └─ 返回 → room:leave → 回到 /rooms
```

### Flow 4: 个人资料

```text
/rooms → 点击用户名 → /profile
  │
  ├─ 查看用户名、邮箱、头像、创建时间
  ├─ 编辑 username / avatarUrl → 保存 → 更新显示
  └─ 返回 /rooms
```

## Screens And States

### Screen 1: 登录页 `/login`

```
┌────────────────────────┐
│     Newworld Chat       │
│                          │
│  ┌──────────────────┐   │
│  │ Email             │   │
│  └──────────────────┘   │
│  ┌──────────────────┐   │
│  │ Password          │   │
│  └──────────────────┘   │
│  [    登录    ]          │
│  [   注册账号  ]          │
│  [  游客登录  ]           │
└────────────────────────┘
```

| 状态 | 表现 |
|------|------|
| **默认** | Email + Password 输入框，登录/注册/游客按钮 |
| **加载中** | 按钮禁用 + Ionic Spinner |
| **登录失败** | IonToast 红色提示"邮箱或密码错误" |
| **网络错误** | IonToast "网络错误，请重试" |

### Screen 2: 注册页 `/register`

```
┌────────────────────────┐
│     创建账号             │
│                          │
│  ┌──────────────────┐   │
│  │ 用户名            │   │
│  └──────────────────┘   │
│  ┌──────────────────┐   │
│  │ Email             │   │
│  └──────────────────┘   │
│  ┌──────────────────┐   │
│  │ Password          │   │
│  └──────────────────┘   │
│  [    注册    ]          │
│  [  返回登录  ]          │
└────────────────────────┘
```

| 状态 | 表现 |
|------|------|
| **默认** | 用户名 + Email + Password 输入框 |
| **加载中** | 按钮禁用 + Ionic Spinner |
| **注册失败** | IonToast 提示具体错误（用户名/邮箱已存在等） |
| **注册成功** | 自动跳转 /rooms |

### Screen 3: 房间列表 `/rooms`

```
┌────────────────────────┐
│ ☰  聊天室        👤 用户 │
│────────────────────────│
│  ┌──────────────────┐  │
│  │ # 闲聊大厅        │  │
│  │ 12 名成员          │  │
│  └──────────────────┘  │
│  ┌──────────────────┐  │
│  │ # 技术分享        │  │
│  │ 5 名成员           │  │
│  └──────────────────┘  │
│                          │
│  [ + 创建房间 ]          │
└────────────────────────┘
```

| 状态 | 表现 |
|------|------|
| **加载中** | IonSpinner 居中 |
| **有房间** | IonList + IonItem 展示房间卡片 |
| **空列表** | 居中灰色文字"暂无聊天室，创建一个吧！" |
| **加载失败** | IonToast "加载失败" + 重试按钮 |
| **创建房间** | IonModal 弹出表单 |
| **加入房间** | 点击"加入"按钮，成功后列表刷新 |

### Screen 4: 聊天页 `/rooms/:roomId`

```
┌────────────────────────┐
│ ←  # 闲聊大厅            │
│────────────────────────│
│  Alice: 大家好！         │
│  You:  你好 👋           │
│  Bob:  今天聊什么？       │
│  Alice 正在输入…         │
│────────────────────────│
│ ┌────────────┐ ┌─────┐  │
│ │ 输入消息…   │ │发送  │  │
│ └────────────┘ └─────┘  │
└────────────────────────┘
```

| 状态 | 表现 |
|------|------|
| **加载消息中** | 消息区居中 IonSpinner |
| **有消息** | 消息列表，自己的消息靠右高亮，他人靠左 |
| **空消息** | 居中灰色"还没有消息，发一条吧！" |
| **加载历史** | 向上滚动到顶部时加载更多 |
| **正在输入** | 输入区上方显示"XX 正在输入…" |
| **发送中** | 发送按钮禁用 |
| **发送失败** | IonToast "发送失败" |
| **Socket 断线** | 顶部黄色提示条"连接中断，正在重连…" |
| **Socket 重连成功** | 提示条消失 |
| **无权限** | IonToast "无权访问此房间" + 跳回 /rooms |

### Screen 5: 个人资料 `/profile`

```
┌────────────────────────┐
│ ←  个人资料              │
│────────────────────────│
│  ┌────┐                 │
│  │头像 │                 │
│  └────┘                 │
│  用户名: [可编辑]        │
│  Email:  alice@xx.com   │
│  注册于: 2026-01-01      │
│  [    保存    ]          │
└────────────────────────┘
```

| 状态 | 表现 |
|------|------|
| **加载中** | IonSpinner |
| **加载失败** | IonToast "加载失败" |
| **保存中** | 按钮禁用 + Spinner |
| **保存成功** | IonToast "已保存" + 更新显示 |
| **保存失败** | IonToast 显示错误信息 |

## Reusable Components

| 组件 | Ionic 基础 | 描述 |
|------|-----------|------|
| **AppHeader** | IonHeader + IonToolbar | 各页面顶部导航栏，含返回按钮和标题 |
| **AuthForm** | IonList + IonInput + IonButton | 登录/注册共用表单结构 |
| **RoomList** | IonList + IonItem | 房间列表，每项含名称、描述、成员数 |
| **RoomCard** | IonItem | 单个房间卡片 |
| **CreateRoomModal** | IonModal + IonInput | 创建房间的模态弹窗 |
| **MessageList** | IonContent + 自定义 scroll | 消息列表，支持无限向上滚动 |
| **MessageBubble** | 自定义 div | 单条消息气泡，区分自己/他人 |
| **ChatInput** | IonFooter + IonInput + IonButton | 底部消息输入栏 |
| **TypingIndicator** | 自定义 div | "XX 正在输入…" 提示 |
| **ErrorToast** | IonToast | 全局错误/成功提示 |
| **LoadingSpinner** | IonSpinner | 加载中占位 |
| **EmptyState** | 自定义 div | 空列表/空消息占位 |
| **ConnectionBanner** | 自定义 div | Socket 断线/重连提示条 |

## Navigation Structure

```text
IonReactRouter
├── /login          (公开)
├── /register       (公开)
├── AuthGuard
│   ├── /rooms              → RoomListPage
│   ├── /rooms/:roomId      → ChatPage
│   ├── /profile            → ProfilePage
│   └── /settings           → SettingsPage
└── 重定向: / → /rooms (已登录) 或 /login (未登录)
```

## Responsive And Accessibility

- **移动端优先**：所有页面按手机屏幕宽度设计，WebView 内自适应
- **iOS/Android 自适应**：Ionic 自动根据平台切换交互模式（如返回按钮位置）
- **触摸友好**：按钮最小 44px 触摸区域，输入框高度适配软键盘
- **软键盘**：聊天页输入框在键盘弹出时保持可见（Ionic Keyboard API）
- **对比度**：Ionic 默认主题满足 WCAG AA 对比度
- **语义标签**：使用 Ionic 组件内置 ARIA 属性
- **加载状态**：所有异步操作有明确的 loading 指示
- **错误状态**：所有失败有可理解的错误提示

## Exit Gate Checklist

- [x] US-1 (Auth): 登录/注册/游客/会话恢复/登出/路由守卫 — 全部有交互路径和状态
- [x] US-2 (Profile): 查看/编辑/保存 — 有交互路径和状态
- [x] US-3 (Rooms): 列表/创建/加入/空状态 — 有交互路径和状态
- [x] US-4 (Messages): 历史/发送/分页/权限/去重 — 有交互路径和状态
- [x] US-5 (Realtime): Socket 鉴权/加入离开/实时消息/typing/断线重连 — 有交互路径和状态
- [x] US-6 (Mobile/Ionic): Ionic UI/Vite/secure storage/CORS — 有组件和约束
- [x] US-7 (DevOps): 不涉及 UX 交互
