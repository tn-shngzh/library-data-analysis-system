# 模块化架构文档

## 目录结构

```
src/
├── api/                    # 数据层 - API 服务
│   ├── index.ts            # 基础请求封装（get/post/postForm）
│   ├── auth.ts             # 认证 API（登录/注册/验证码/登出）
│   ├── overview.ts         # 总览数据 API
│   ├── readers.ts          # 读者数据 API
│   ├── books.ts            # 图书数据 API（含搜索）
│   ├── borrows.ts          # 借阅数据 API
│   └── library.ts          # 图书馆首页 API（首页数据/借阅操作）
│
├── composables/            # 业务逻辑层 - 可复用组合式函数
│   ├── useAuth.ts          # 认证状态管理（用户名/角色/登录检查/登出）
│   ├── useTime.ts          # 时间管理（实时时钟更新）
│   ├── useDropdown.ts      # 下拉菜单管理（显示/隐藏/外部点击关闭）
│   ├── useLoading.ts       # 加载状态管理（loading 状态/异步操作包装）
│   └── useSearch.ts        # 搜索功能（关键词/结果/防抖/分页）
│
├── utils/                  # 工具函数层
│   ├── format.ts           # 数据格式化（数字/日期/百分比）
│   ├── timer.ts            # 定时器工具（防抖/节流）
│   └── cache.ts            # 本地缓存（getCache/setCache/clearCache/TTL）
│
├── constants/              # 常量配置层
│   └── index.ts            # 应用常量（API 路径/分页配置/角色定义等）
│
├── components/             # 公共组件层
│   ├── StatCard.vue        # 统计卡片组件
│   ├── LoadingSpinner.vue  # 加载动画组件
│   ├── PageHeader.vue      # 页面标题组件
│   ├── CategoryList.vue    # 分类列表组件
│   └── icons/
│       └── IconBase.vue    # 图标基础组件
│
├── styles/                 # 样式层
│   ├── design-tokens.css   # 设计令牌（颜色/排版/间距/阴影/动画）
│   └── login.css           # 登录/注册页样式
│
├── views/                  # 视图层 - 页面组件
│   ├── LoginView.vue       # 登录页
│   ├── RegisterView.vue    # 注册页
│   ├── DashboardView.vue   # 管理后台主页
│   ├── OverviewView.vue    # 总览视图
│   ├── ReaderView.vue      # 读者视图
│   ├── BookView.vue        # 图书视图
│   ├── BorrowView.vue      # 借阅视图
│   ├── LibraryView.vue     # 图书馆用户界面
│   └── SettingsView.vue    # 用户设置页
│
├── router/                 # 路由层
│   └── index.ts            # 路由配置
│
├── App.vue                 # 根组件
└── main.ts                 # 应用入口
```

---

## 分层架构说明

### 1. 数据层（api/）

所有与后端 API 的交互都通过此层完成，视图层不直接调用 `fetch`。

**基础请求封装** (`api/index.ts`)：
- `get(url)` — GET 请求，自动携带 Authorization 头
- `post(url, body)` — POST JSON 请求
- `postForm(url, formData)` — POST FormData 请求

**各 API 模块**：
| 模块 | 文件 | 提供方法 |
|------|------|----------|
| 认证 | auth.ts | getCaptcha, login, register, logout |
| 总览 | overview.ts | getAll |
| 读者 | readers.ts | getAll |
| 图书 | books.ts | getAll, search |
| 借阅 | borrows.ts | getAll |
| 图书馆 | library.ts | getHomeData, getMyBorrows, borrowBook |

**使用示例**：
```typescript
import { overviewApi } from '@/api/overview'
const data = await overviewApi.getAll()
```

### 2. 业务逻辑层（composables/）

可复用的组合式函数，封装跨视图共享的业务逻辑。

| Composable | 导出 | 说明 |
|------------|------|------|
| useAuth | username, role, checkAuth, logout | 认证状态与操作 |
| useTime | currentTime | 每分钟自动更新的时间字符串 |
| useDropdown | showDropdown, dropdownRef, toggleDropdown, closeDropdown | 下拉菜单状态管理，自动处理外部点击关闭 |
| useLoading | loading, withLoading | 加载状态包装，withLoading 自动管理 loading 状态 |
| useSearch | searchKeyword, searchResults, searchLoading, performSearch, resetSearch | 搜索功能，内置防抖 |

**使用示例**：
```typescript
import { useAuth } from '@/composables/useAuth'
const { username, role, checkAuth, logout } = useAuth()
```

### 3. 工具函数层（utils/）

纯函数工具，无副作用，无状态依赖。

| 模块 | 函数 | 说明 |
|------|------|------|
| format | formatNumber, formatDate, formatPercent | 数据格式化 |
| timer | debounce(fn, delay), throttle(fn, limit) | 防抖与节流 |
| cache | getCache, setCache, clearCache | localStorage 缓存，支持 TTL |

### 4. 常量配置层（constants/）

集中管理应用级常量，避免魔法值散落在代码中。

### 5. 公共组件层（components/）

可复用的 UI 组件，遵循统一的设计令牌系统。

| 组件 | Props | 说明 |
|------|-------|------|
| StatCard | title, value, icon, color | 统计数据展示卡片 |
| LoadingSpinner | size, color | 加载动画 |
| PageHeader | title, subtitle | 页面标题区域 |
| CategoryList | categories | 分类数据列表 |

### 6. 视图层（views/）

页面级组件，负责组合使用各层模块完成页面渲染。

**重构后的视图依赖关系**：

```
LoginView ──────→ authApi
RegisterView ───→ authApi
DashboardView ──→ overviewApi, readerApi, bookApi, borrowApi, useAuth, useTime
OverviewView ───→ overviewApi, useAuth
ReaderView ─────→ readerApi, useAuth
BookView ───────→ bookApi, useAuth
BorrowView ─────→ borrowApi, useAuth
LibraryView ────→ libraryApi, useAuth, useTime, useDropdown, useSearch, cache
SettingsView ───→ useAuth, useTime, useDropdown
```

---

## 设计原则

1. **单一职责**：每个模块只负责一个明确的功能领域
2. **低耦合高内聚**：模块间通过明确的接口交互，内部实现独立
3. **分层架构**：数据层 → 业务逻辑层 → 视图层，依赖方向单向向下
4. **统一命名**：
   - API 模块：`xxxApi`，文件名对应业务域
   - Composables：`useXxx` 命名约定
   - 工具函数：语义化命名，如 `formatNumber`
   - 组件：PascalCase 命名
5. **缓存策略**：通过 `utils/cache.ts` 统一管理，支持 TTL 过期
6. **错误处理**：API 层统一处理认证失败，视图层处理业务错误
