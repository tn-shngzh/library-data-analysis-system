# 图书馆用户借阅行为分析系统 — 设计文档

> **版本 v0.12.0** | 基于 842 万条借阅记录的多维度分析 + 102,237 个读者账户管理

---

## 一、系统总览

```
┌──────────┐      HTTP/JSON       ┌──────────┐      SQL       ┌────────────┐
│  Vue 3   │ ◄──── JWT Auth ────► │  FastAPI │ ◄─────────────► │ PostgreSQL │
│  前端     │                     │  后端     │                 │  数据库     │
│  (5174)  │                     │  (8000)  │                 │            │
└──────────┘                     └──────────┘                 └────────────┘
```

| 层级 | 技术 | 职责 |
|------|------|------|
| **前端** | Vue 3 + TypeScript + Pinia + ECharts | 数据可视化、交互操作、多语言界面 |
| **后端** | FastAPI + psycopg_pool (Poetry) | RESTful API、认证鉴权、数据聚合计算 |
| **数据库** | PostgreSQL + 内存缓存 | 数据存储、索引优化、缓存加速 |
| **工具链** | Poetry (Python) / npm (Node) / Vite (构建) | 依赖管理、构建部署 |

---

## 二、双系统设计

系统按用户角色分为两个独立子系统：

```
                    ┌─────────────────────────────────┐
                    │       登录 (/login)               │
                    │     JWT + 验证码 + bcrypt          │
                    └────────┬──────────────┬───────────┘
                             │              │
                      ┌──────▼──────┐  ┌───▼────────┐
                      │   admin      │  │   user      │
                      │  (数据分析)  │  │  (借阅系统) │
                      └──────┬──────┘  └───┬────────┘
                             │              │
              ┌──────────────▼──┐    ┌──────▼───────────┐
              │  仪表盘 /dashboard│   │ 借阅系统           │
              │  总览 │ 读者 │    │   │ 我的借阅 │ 热门图书 │
              │  图书 │ 借阅 │    │   │ 图书搜索 │ 个人中心 │
              │  趋势 │ 统计 │    │   └──────────────────┘
              │  预测 │ 报表 │    │
              │  智能分析等...   │
              └─────────────────┘
```

---

## 三、后端架构

### 3.1 目录结构

```
library_data_analysis_fastapi/
├── pyproject.toml                   # Poetry 项目配置 (依赖/脚本/元数据)
├── poetry.lock                      # 锁定依赖版本
├── poetry.toml                      # Poetry 本地配置
├── main.py                          # 入口：应用初始化、中间件、路由注册
├── app/
│   ├── config.py                    # 配置：JWT密钥、数据库连接、CORS
│   ├── database.py                  # 数据库：连接池(10~50)、索引创建、异步封装
│   ├── auth.py                      # 认证：JWT签发/校验、bcrypt加密、验证码生成
│   ├── cache.py                     # 缓存：内存缓存(线程安全)、TTL过期、命中率统计
│   ├── tasks.py                     # 任务：后台缓存刷新调度
│   ├── routers/                     # 11个路由模块(共61个API端点)
│   │   ├── auth.py                  #   认证 (5个端点)
│   │   ├── overview.py              #   总览 (10个端点)
│   │   ├── readers.py               #   读者分析 (7个端点)
│   │   ├── books.py                 #   图书分析 (5个端点)
│   │   ├── borrows.py               #   借阅分析 (9个端点)
│   │   ├── analysis.py              #   数据分析 (6个端点)
│   │   ├── statistics.py            #   统计分析 (6个端点)
│   │   ├── insights.py              #   智能洞察 (1个端点)
│   │   ├── intelligence.py          #   智能分析 (2个端点)
│   │   ├── imports.py               #   数据导入 (3个端点)
│   │   ├── report.py                #   AI报告+导出 (7个端点)
│   └── services/
│       ├── llm.py                   # LLM集成服务
│       └── export.py                # Excel/Word导出服务
```

### 3.2 核心机制

| 机制 | 说明 |
|------|------|
| **连接池** | `psycopg_pool`，min=10 / max=50，异步线程桥接 |
| **内存缓存** | 路由层缓存 + SWR 策略，TTL 分级配置 |
| **索引优化** | 启动时自动创建 6 个关键索引 |
| **数据预加载** | 后端启动时预取热点数据到缓存 |
| **健康检查** | `/health` 端点检测 DB / 内存 / 缓存 / 运行时长 |

### 3.3 认证体系

```
登录流程：
  1. GET  /api/captcha       ← 获取验证码图片 + key
  2. POST /api/login          ← 提交 用户名 + 密码 + 验证码
  3. 服务端校验验证码 → bcrypt校验密码 → 签发JWT(7天)
  4. 前端存储 token 至 localStorage，后续请求携带 Authorization header

安全措施：
  - bcrypt 12轮加密存储
  - 图形验证码 (5分钟过期，一次性使用)
  - JWT 黑名单机制 (登出即失效)
  - Token 自动过期 (7天)
  - 路由守卫拦截未认证请求
```

### 3.4 数据库

```
核心表：
  circulations       —— 流通记录 (842万条)
  borrowers          —— 读者信息 (10.2万人)
  book_categories    —— 图书分类

⚠️ 查询规则：所有 SQL 直接查原始表，禁止引用 mv_* 物化视图

缓存表：
  monthly_history_cache  —— 月度历史预聚合，用于同比/环比计算
  degree_hour_cache      —— 学历-时段预聚合，用于学历热力图

关键索引 (6个)：
  idx_circ_borrow_date         idx_circ_borrow_date_status
  idx_circ_borrower_id         idx_circ_bib_id
  idx_circ_status              idx_borrowers_degree
```

---

## 四、前端架构

### 4.1 目录结构

```
library_data_analysis_vue/src/
├── main.ts            # 入口：应用挂载、插件注册
├── api/               # 数据层：后端API调用封装
│   ├── index.ts       #   基础请求 (get/post/postForm) + SWR缓存 + 自动重试
│   ├── auth.ts        #   认证API
│   ├── overview.ts    #   总览API
│   ├── readers.ts     #   读者API
│   ├── books.ts       #   图书API (+搜索)
│   ├── borrows.ts     #   借阅API
│   ├── analysis.ts    #   分析API
│   ├── statistics.ts  #   统计API
│   ├── insights.ts    #   洞察API
│   ├── intelligence.ts#   智能分析API
│   ├── imports.ts     #   数据导入API
│   └── reports.ts     #   报表API
│
├── composables/       # 业务逻辑层：可复用组合式函数
│   ├── useAuth.ts     #   认证状态管理
│   ├── useTime.ts     #   实时时钟 (每分钟更新)
│   ├── useDropdown.ts #   下拉菜单 (外部点击关闭)
│   ├── useLoading.ts  #   加载状态包装
│   ├── useSearch.ts   #   搜索 (防抖+分页)
│   └── useToast.ts    #   全局通知
│
├── stores/            # 状态管理 (Pinia)
│   ├── data.ts        #   数据仓库：预加载全部数据，页面切换亚秒响应
│   ├── user.ts        #   用户信息
│   └── analysis.ts    #   分析视图状态
│
├── components/        # 可复用UI组件
│   ├── StatCard.vue          统计卡片 (已弃用)
│   ├── TrendChart.vue        趋势图
│   ├── PieChart.vue          饼图
│   ├── RankingList.vue       排行榜
│   ├── RankingCard.vue       排行卡片
│   ├── ChartCard.vue         图表容器 (含stats指标展示)
│   ├── ChartViewSwitcher.vue 图表视图切换
│   ├── PageHeader.vue        页面头部
│   ├── LoadingSpinner.vue    加载动画
│   ├── DetailPanel.vue       详情面板
│   ├── InsightsPanel.vue     洞察面板
│   ├── CategoryList.vue      分类列表
│   └── icons/IconBase.vue    图标基座
│
├── views/             # 页面视图
│   ├── LoginView.vue          登录页
│   ├── RegisterView.vue       注册页
│   ├── DashboardView.vue      仪表盘 (含侧边栏导航)
│   ├── OverviewView.vue      总览 (两行布局：7日趋势(含header指标)+运营预警(含header指标) + 读者活跃度热力图/今日洞察&馆藏健康度 | 毛玻璃卡片)
│   ├── ReaderView.vue         读者分析
│   ├── BookView.vue           图书分析
│   ├── BorrowView.vue         借阅分析
│   ├── CategoryView.vue       分类分析
│   ├── TrendView.vue          趋势分析
│   ├── StatisticsView.vue     统计分析
│   ├── AnalysisView.vue       综合分析
│   ├── PredictView.vue        智能预测
│   ├── IntelligenceView.vue   智能分析
│   ├── HistoricalAnalysisView.vue 历史分析
│   ├── CirculationView.vue    借阅系统
│   ├── ReportView.vue         报表
│   ├── ImportView.vue         数据导入
│   ├── SettingsView.vue       个人设置
│   └── OptimizationList.vue   优化建议
│
├── constants/         # 常量定义
│   └── index.ts       #   全局常量
│
├── assets/            # 静态资源
│   ├── base.css       #   基础样式重置
│   ├── main.css       #   主样式入口
│   └── logo.svg       #   Logo 图标
│
├── i18n/              # 国际化 (4种语言 × 20+模块)
│   ├── index.ts       #   i18n 初始化配置
│   ├── types.ts       #   类型定义
│   └── locales/       #   语言文件 (zh-CN / en / zh-TW / ja)
├── router/index.ts    # 路由配置 + 守卫
├── plugins/echarts.ts # ECharts 全局注册
├── utils/             # 工具函数
│   ├── format.ts      #   数字/日期/百分比格式化
│   ├── cache.ts       #   本地缓存 (TTL)
│   ├── timer.ts       #   防抖/节流
│   └── export.ts      #   数据导出
├── styles/            # 全局样式
│   ├── design-tokens.css  # 设计令牌
│   └── buttons.css        # 按钮样式
└── App.vue            # 根组件 (路由过渡 + Toast)
```

### 4.2 分层架构

```
┌───────────────────────────────────────────────────────────┐
│                       视图层 (views/)                      │
│   页面组件，负责布局编排，组合业务逻辑和UI组件                │
├───────────────────────────────────────────────────────────┤
│                    UI组件层 (components/)                   │
│   通用可复用组件，接收 props 渲染，不关心数据来源             │
├───────────────────────────────────────────────────────────┤
│               业务逻辑层 (composables/ + stores/)            │
│   封装跨视图共享的状态与逻辑，处理数据流                     │
├───────────────────────────────────────────────────────────┤
│                 数据层 (api/ + utils/)                     │
│   HTTP请求封装、SWR缓存、数据格式化、本地存储               │
└───────────────────────────────────────────────────────────┘
         ▲ 依赖方向：视图 → 业务 → 数据 (单向依赖)
```

### 4.3 数据流

```
登录成功
    │
    ▼
preloadAll()  ───────────────────────────────────────────────┐
    │  并行加载4大模块                                      │
    ├── overview  (stats / monthlyBorrows / categories / ...)  │
    ├── readers   (stats / types / trend / top / ...)       │
    ├── books     (stats / categories / hotBooks / ...)     │
    └── borrows   (stats / actionStats / degreeStats / ...) │
    │                                                        │
    ▼                                                        │
Pinia Store ──── 页面切换读取缓存 ──── 亚秒级渲染              │
(data.ts)                                                     │
    │                                                        │
    └── refreshModule(moduleName) ──── 按需刷新热点数据        │
```

### 4.4 SWR 缓存策略

```
请求流程：
  ① 检查 SWR 缓存 staleTime 内 → 直接返回 (毫秒)
  ② 超过 staleTime 未达 maxAge → 返回旧数据 + 后台静默刷新
  ③ 超过 maxAge → 发起新请求

分级配置：
  /api/overview/stats          stale: 60s    maxAge: 5min
  /api/overview/categories     stale: 5min   maxAge: 10min
  /api/borrows/daily-trend     stale: 5min   maxAge: 10min
  /api/readers/monthly-trend   stale: 5min   maxAge: 10min
  默认                        stale: 30s    maxAge: 5min

其他特性：
  - 请求去重：同一URL多个请求等待同一个Promise
  - 自动重试：服务端错误最多重试2次
  - 超时控制：60秒强制中断
  - 401处理：自动跳转登录页
```

### 4.5 导航系统

```
仪表盘侧边栏导航 (11个功能入口)：

┌──────────────────────┐
│ 总览  (Overview)     │  ← 默认首页
├──────────────────────┤
│ 历史分析 (Historical)│
├──────────────────────┤
│ 智能预测 (Predict)   │  ← AI预测分析
├──────────────────────┤
│ 智能分析 (Analysis)  │  ← 关联分析
├──────────────────────┤
│ 统计分析 (Statistics)│  ← 描述性统计/回归/聚类
├──────────────────────┤
│ 借阅分析 (Borrows)   │
├──────────────────────┤
│ 读者分析 (Readers)   │
├──────────────────────┤
│ 趋势分析 (Trends)    │
├──────────────────────┤
│ 图书分析 (Books)     │
├──────────────────────┤
│ 报表 (Reports)       │  ← AI生成报告/导出
├──────────────────────┤
│ 数据导入 (Import)    │  ← CSV上传
└──────────────────────┘
```

---

## 五、API 列表 (61个端点)

### 认证 `/api`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/captcha` | 获取验证码 |
| POST | `/api/register` | 用户注册 |
| POST | `/api/login` | 登录 (返回JWT) |
| GET | `/api/me` | 当前用户信息 |
| POST | `/api/logout` | 注销 |

### 总览 `/api/overview`
| GET | `/stats` | 核心指标 (总借阅/活跃读者/同比环比/日环比) |
| GET | `/historical-stats` | 历史统计 (年均/月均/周转率/留存率/峰值/年度趋势) |
| GET | `/historical-detail` | 月度明细 (借出/归还/活跃读者按月) |
| GET | `/recent-books` | 最近借阅 (5条) |
| GET | `/top-books` | 热门图书排行 |
| GET | `/book-categories` | 分类统计 |
| GET | `/monthly-borrows` | 月度借阅趋势 (用于趋势图) |
| GET | `/trend-7d` | 7日全维度趋势 (借出/归还/流通量/借书人数) |
| GET | `/collection-health` | 馆藏健康度 (利用率/零借阅/曾借出) |
| GET | `/reader-activity-heatmap` | 读者活跃度热力图 (星期×时段) |

### 读者 `/api/readers`
| GET | `/stats` | 读者统计 (总数/活跃/新增) |
| GET | `/types` | 学历分布 |
| GET | `/monthly-trend` | 月度活跃趋势 |
| GET | `/top` | 活跃读者排行 |
| GET | `/degree-stats` | 学历统计 |
| GET | `/degree-hour-heatmap` | 学历-时段热力图 |
| GET | `/frequency-distribution` | 借阅频次分布 |

### 图书 `/api/books`
| GET | `/stats` | 图书统计 (总数/借阅率/零借阅) |
| GET | `/categories` | 分类统计 |
| GET | `/hot` | 热门图书 |
| GET | `/search` | 图书搜索 (关键词+分类+分页) |
| GET | `/categories-list` | 分类列表 |

### 借阅 `/api/borrows`
| GET | `/stats` | 借阅统计 |
| GET | `/action-stats` | 操作类型分布 |
| GET | `/degree-stats` | 学历-借阅量 |
| GET | `/daily-trend` | 每日趋势 |
| GET | `/top-borrowers` | 借阅者排行 |
| GET | `/top-books` | 图书排行 |
| GET | `/recent` | 最近借阅 |
| GET | `/monthly-trend` | 月度借出 |
| GET | `/monthly-returns` | 月度归还 |

### 分析 `/api/analysis`
| GET | `/correlation` | 关联分析 |
| GET | `/period-comparison` | 时段对比 |
| GET | `/category-heatmap` | 分类热力图 |
| GET | `/degree-monthly-trend` | 学历-月度趋势 |
| GET | `/daily-trend` | 每日趋势 |
| GET | `/category-period-comparison` | 分类时段对比 |

### 统计 `/api/stats`
| GET | `/frequency` | 频数分析 |
| GET | `/descriptive` | 描述性统计 (均值/方差/偏度/峰度) |
| GET | `/crosstab` | 交叉分析 |
| GET | `/correlation-matrix` | 相关性矩阵 (Pearson) |
| GET | `/clustering/reader` | 读者聚类 (K-Means) |
| GET | `/regression/forecast` | 借阅量预测 (线性回归) |

### 其他
| 模块 | 端点 | 说明 |
|------|------|------|
| 洞察 | GET `/api/insights/auto` | 自动智能洞察 (增长/预警/趋势) |
| 智能 | GET `/api/intelligence/correlation` | 图书关联分析 (共现网络) |
| 智能 | GET `/api/intelligence/collection-optimization` | 馆藏优化建议 |
| 导入 | POST `/api/imports/upload` | CSV上传导入 |
| 导入 | GET `/api/imports/history` | 导入历史 |
| 导入 | POST `/api/imports/validate` | CSV格式校验 |
| 报表 | GET `/api/reports/status` | LLM 服务状态检查 |
| 报表 | GET `/api/reports/overview\|reader\|book\|borrow` | AI生成报告 |
| 报表 | GET `/api/reports/export/excel/{type}` | 导出Excel |
| 报表 | GET `/api/reports/export/word` | 导出Word |

---

## 六、国际化 (i18n)

```
4种语言 × 21模块 = 84翻译文件

├── zh-CN (简体中文)   ├── zh-TW (繁体中文)
├── en    (English)    └── ja    (日本語)

每个语言包含：
  common.ts    — 通用词汇      nav.ts        — 导航菜单
  login.ts     — 登录页        register.ts   — 注册页
  overview.ts  — 总览页        reader.ts     — 读者分析
  book.ts      — 图书分析      borrow.ts     — 借阅分析
  analysis.ts  — 综合分析      stats.ts      — 统计分析
  trend.ts     — 趋势分析      predict.ts    — 智能预测
  insights.ts  — 智能洞察      intelligence.ts— 智能分析
  report.ts    — 报表          settings.ts   — 设置
  category.ts  — 分类          degree.ts     — 学历
  months.ts    — 月份          import.ts     — 导入
```

---

## 七、技术栈全景

### 前端
| 技术 | 用途 |
|------|------|
| Vue 3 (Composition API) | 前端框架 |
| TypeScript | 类型安全 |
| Pinia | 状态管理 |
| Vue Router | 路由 (History模式 + 路由守卫) |
| ECharts + vue-echarts | 图表可视化 |
| D3.js | 高级数据可视化 |
| vue-i18n | 国际化 |
| Vite | 构建工具 |
| Vitest | 单元测试 |

### 后端
| 技术 | 用途 |
|------|------|
| Poetry | 依赖管理与打包 (pyproject.toml) |
| FastAPI | Web 框架 |
| Uvicorn | ASGI 服务器 |
| psycopg / psycopg_pool | PostgreSQL 驱动 + 连接池 |
| PyJWT + python-jose | JWT 认证 + 加密 |
| bcrypt | 密码哈希 (12轮) |
| Pillow | 验证码图片生成 |
| python-multipart | 文件上传 |
| python-dotenv | 环境变量管理 |
| python-docx | Word 文档导出 |
| scipy | 统计分析 (回归/聚类) |
| psutil | 系统监控 (健康检查) |

### 数据库
| 特性 | 说明 |
|------|------|
| PostgreSQL | 关系型数据库 |
| 内存缓存 | 后端 MemoryCache + TTL 分级，替代物化视图 |
| 连接池 | min=10, max=50 |

---

## 八、性能保障体系

| 手段 | 实现 | 效果 |
|------|------|------|
| **内存缓存** | 后端 MemoryCache + TTL | 减少重复计算，替代物化视图 |
| **SWR 缓存** | 前端分级缓存 + 后台刷新 | 页面切换无需等待 |
| **数据预加载** | 登录后并行拉取全部数据 | 后续操作亚秒响应 |
| **请求去重** | pendingRequests Map | 相同请求只发一次 |
| **连接池** | 50个并发连接 | 高并发下稳定 |
| **自动重试** | 服务端错误重试2次 | 容错性提升 |
| **索引** | 6个关键索引 | 过滤/排序/SQL加速 |

---

## 九、启动方式

```bash
# 后端
cd library_data_analysis_fastapi
poetry install
poetry run uvicorn main:app --reload --port 8000

# 前端
cd library_data_analysis_vue
npm install
npm run dev

# 默认账号
#   admin / admin123  → 数据分析系统
#   user  / user123   → 借阅系统
```


