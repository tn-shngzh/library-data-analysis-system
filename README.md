# 图书馆数据分析系统

## 版本

**v0.6.0** - 数据预加载优化、移除分馆功能、数据库清理

## 更新日志

### v0.6.0 (2026-04-20)
- ✨ 新增数据预加载功能，进入系统时自动获取所有数据
- 🗑️ 移除分馆相关功能和数据列
- 🧹 清理数据库中的 `imported_at` 无用列
- 📊 导出完整数据集到 CSV 格式（6.2M+ 记录）
- 🚀 优化页面切换体验，实现秒级响应
- 📦 更新版本号至 0.6.0

### v0.5.0 - Dashboard 与性能优化
- 核心仪表板页面（总览、读者、图书、借阅）
- 标签导航功能
- 物化视图优化查询性能（1000x 提升）
- 毫秒级响应速度

### v0.4.0 - 登录验证
- 验证码验证功能
- 登录界面样式优化
- 增强用户体验

### v0.3.0 - JWT 认证
- JWT 身份认证
- 基于角色的访问控制（RBAC）
- 管理员/普通用户权限分离

### v0.2.0 - 架构重构
- 前后端分离架构
- FastAPI 后端
- Vue 3 前端

### v0.1.0 - 初始版本
- 项目初始化
- 基础功能搭建

## 功能特性

- JWT 登录认证
- 角色权限控制（admin/user）
- 管理员可登录系统
- 普通用户禁止登录
- 102,235 个用户账号管理
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

- 管理员: `admin` / `admin123`
- 普通用户（测试）：user / user123
- 普通用户:（无法登录系统）

## API

### 认证
- `GET /api/captcha` - 获取验证码
- `POST /api/login` - 用户登录
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
