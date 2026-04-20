# 图书馆数据分析系统

## 版本

**v0.5.0** - 实现用户认证系统

## 功能特性

- JWT 登录认证
- 角色权限控制（admin/user）
- 管理员可登录系统
- 普通用户禁止登录
- 102,235 个用户账号管理

## 项目结构

- `library_data_analysis_fastapi/` - FastAPI 后端
- `library_data_analysis_vue/` - Vue 3 前端

## 启动方式

### 后端
```bash
cd library_data_analysis_fastapi
pip install -r requirements.txt
uvicorn main:app --reload
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
- 普通用户: `user_{id}` / 随机密码（无法登录系统）

## API

- `POST /api/login` - 用户登录
- `GET /api/me` - 获取当前用户信息
