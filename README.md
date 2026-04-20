# 图书馆用户借阅行为分析系统

## 版本

**v0.10.0** - 借阅功能完善、系统稳定性提升、用户设置独立页面

## 更新日志

### v0.10.0 (2026-04-20) - 借阅接口修复与数据完善
- 🛠️ 修复 `/api/borrows/my` 接口 SQL 查询错误，解决页面空白问题
- 🛠️ 修复 `/api/borrows/borrow` 接口 SQL 查询错误，确保借阅功能正常
- 🛠️ 修复 `/api/borrows/return` 接口 SQL 查询错误，确保归还功能正常
- 🔧 修正 borrowers 表字段名查询（`WHERE username = %s` → `WHERE name = %s`）
- 👤 为 admin 账号创建对应的 borrowers 记录（id: 102236）

### v0.9.0 (2026-04-20) - 安全修复与密码加密
- 🔐 修复 admin 账号密码存储问题（从明文 `admin123` 改为 bcrypt 12 轮加密）
- 🔑 使用 `bcrypt.hashpw()` 生成密码哈希，符合安全最佳实践
- 🛡️ 验证登录接口 `/api/login` 密码验证逻辑，确保 bcrypt 验证正常
- 📝 更新 README 默认账号说明，标注密码已加密存储

### v0.8.0 (2026-04-20) - 用户设置独立页面
- ✨ 新增 `SettingsView.vue` 独立设置页面，包含三个功能模块：
  - 个人信息（昵称、邮箱、电话）
  - 修改密码（当前密码、新密码、确认密码）
  - 安全设置（加密方式、密码强度提示）
- 🎨 采用专属侧边栏导航，包含菜单项：个人信息、修改密码、安全设置
- 🗑️ 从 `LibraryView.vue` 移除设置标签页，不再与图书相关标签混放
- 🔄 新增路由配置 `/settings`，支持独立访问设置页面
- 📱 改进导航体验：
  - 用户菜单新增"用户设置"选项，点击跳转至 `/settings`
  - 新增 `goToSettings()` 方法处理路由跳转
  - 新增 `goToMyBooks()` 快捷方式，从用户菜单直接跳转我的借阅
  - 新增 `goToHotBooks()` 快捷方式，从用户菜单直接跳转热门图书
- 🎨 优化 UI 设计：移除原卡片设计，采用现代化面板布局
- ⏰ 新增实时时钟显示，每分钟更新一次

### v0.7.0 (2026-04-20) - 用户注册与借阅系统界面
- ✨ 新增用户注册功能，支持在线创建账户（`/api/register`）
- 🔐 优化密码加密机制，使用 bcrypt 直接加密（12 轮加密）
- 🎨 实现借阅系统界面，与数据分析系统风格统一（侧边栏导航）
- 📝 完善输入验证机制（用户名 3-20 字符，密码 6-50 字符）
- 🔄 实现用户 ID 自增机制，确保唯一性和连续性
- 📦 更新版本号至 0.7.0
- 🛠️ 技术栈：移除 passlib，添加 python-multipart

### v0.6.0 (2026-04-20) - 数据预加载与架构简化
- ✨ 新增数据预加载功能，进入系统时自动获取所有数据
- 🗑️ 移除分馆相关功能和数据列，简化系统架构
- 🧹 清理数据库中的 `imported_at` 无用列，优化存储
- 📊 导出完整数据集到 CSV 格式（9.8M+ 记录，便于分析）
- 🚀 优化页面切换体验，实现秒级响应
- 📦 更新版本号至 0.6.0

### v0.5.0 (2026-04-19) - Dashboard 与性能优化
- 📊 新增四个核心仪表板页面（总览、读者、图书、借阅）
- ️ 实现标签导航功能，支持快速切换
- 🗄️ 引入物化视图优化查询性能（提升约 1000 倍）
- ⚡ 实现毫秒级响应速度，用户体验大幅提升
- 📈 完善数据可视化，支持多维度分析

### v0.4.0 (2026-04-19) - 登录验证
- 🔐 新增验证码验证功能，提升系统安全性
- 🎨 优化登录界面样式，采用现代化设计
- 💡 增强用户体验，添加错误提示和反馈
- 🔒 实现验证码一次性使用机制

### v0.3.0 (2026-04-19) - JWT 认证
- 🔑 实现 JWT 身份认证机制
- 👥 引入基于角色的访问控制（RBAC）
- 🛡️ 实现管理员/普通用户权限分离
- 🚪 添加登录守卫，保护路由安全
- 🎫 Token 有效期管理（7 天）

### v0.2.0 (2026-04-19) - 架构重构
- 🏗️ 实现前后端分离架构
- ⚙️ 采用 FastAPI 作为后端框架
- 🖥️ 使用 Vue 3 构建前端界面
- 📦 引入 Poetry 进行依赖管理
- 🔄 重构代码结构，提升可维护性

### v0.1.0 (2026-04-18) - 初始版本
- 🎉 项目初始化完成
- 📁 搭建基础项目结构
- 🔧 配置开发环境和工具链
- 📝 编写项目文档和说明

## 功能特性

- JWT 登录认证
- 角色权限控制（admin/user）
- 用户注册功能
- 双系统设计（借阅系统 + 数据分析系统）
- 管理员可登录数据分析系统
- 普通用户可登录借阅系统
- 102,237 个用户账号管理
- 6,232,387 条流通记录分析
- 数据预加载，秒级响应
- 多维度数据分析（总览、读者、图书、借阅）

## 项目结构

- `library_data_analysis_fastapi/` - FastAPI 后端
- `library_data_analysis_vue/` - Vue 3 前端
- `data/` - 导出的 CSV 数据集

## 启动方式

### 后端
```bash
cd library_data_analysis_fastapi
pip install poetry
poetry install
poetry run uvicorn main:app --reload
```

### 前端
```bash
cd library_data_analysis_vue
npm install
npm run dev
```

## 默认账号

- 管理员：`admin` / `admin123`（登录数据分析系统）
- 普通用户：可注册新账号（登录借阅系统）
- 测试用户：`user` / `user123`（借阅系统）

## API

### 认证
- `GET /api/captcha` - 获取验证码
- `POST /api/login` - 用户登录
- `POST /api/register` - 用户注册
- `GET /api/me` - 获取当前用户信息

### 总览
- `GET /api/overview/stats` - 获取总览统计数据
- `GET /api/overview/categories` - 获取图书分类统计
- `GET /api/overview/recent-books` - 获取最近借阅记录

### 读者
- `GET /api/readers/stats` - 读者统计
- `GET /api/readers/types` - 读者类型分布
- `GET /api/readers/monthly-trend` - 月度注册趋势
- `GET /api/readers/top` - 活跃读者排行

### 图书
- `GET /api/books/stats` - 图书统计
- `GET /api/books/categories` - 图书分类统计
- `GET /api/books/hot` - 热门图书排行

### 借阅
- `GET /api/borrows/stats` - 借阅统计
- `GET /api/borrows/action-stats` - 流通类型统计
- `GET /api/borrows/degree-stats` - 读者学历分布
- `GET /api/borrows/daily-trend` - 每日借阅趋势
- `GET /api/borrows/top-borrowers` - 借阅达人排行
- `GET /api/borrows/top-books` - 热门图书排行
- `GET /api/borrows/recent` - 最近借阅记录
