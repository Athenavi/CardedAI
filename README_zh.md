<div align="center">

<img src="docs/assets/fastblog-logo.svg" alt="FastBlog Logo" width="120" height="120" onerror="this.style.display='none'">

# FastBlog

### ⚡ 面向开发者的现代化高性能博客平台

[![CI Status](https://github.com/Athenavi/fast_blog/actions/workflows/ci.yml/badge.svg)](https://github.com/Athenavi/fast_blog/actions/workflows/ci.yml)
[![Release](https://github.com/Athenavi/fast_blog/actions/workflows/release.yml/badge.svg)](https://github.com/Athenavi/fast_blog/actions/workflows/release.yml)
[![Python Version](https://img.shields.io/badge/python-3.14+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Astro](https://img.shields.io/badge/Astro-5.x-BC52EE.svg?logo=astro&logoColor=white)](https://astro.build/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](./LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/Athenavi/fast_blog?style=social)](https://github.com/Athenavi/fast_blog/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/Athenavi/fast_blog?style=social)](https://github.com/Athenavi/fast_blog/network/members)
[![Docker](https://img.shields.io/badge/docker-ready-blue?logo=docker&logoColor=white)](https://github.com/Athenavi/fast_blog/pkgs/container/fastblog)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Athenavi/fast_blog/blob/main/CONTRIBUTING.md)

[English](README.md) | **中文**

[🚀 快速开始](#-快速开始) · [📖 文档](#-文档) · [🎯 特性](#-特性) · [🗺️ 路线图](#%EF%B8%8F-路线图) · [🤝 参与贡献](#-参与贡献)

</div>

---

## ✨ 为什么选择 FastBlog？

FastBlog 是一个**新一代博客平台**，将 **FastAPI** 的极致性能与 **Astro** 的现代前端架构完美结合。专为追求性能、可扩展性和开发体验的开发者打造。

| 特性        | FastBlog | WordPress | Ghost | Strapi |
|-----------|----------|-----------|-------|--------|
| API 优先    | ✅        | ❌         | ✅     | ✅      |
| 静态生成      | ✅        | ❌         | ❌     | ❌      |
| 插件系统      | ✅        | ✅         | ❌     | ✅      |
| 移动端 App   | ✅        | ❌         | ❌     | ❌      |
| 零 JS 前端   | ✅        | ❌         | ❌     | ❌      |
| Docker 支持 | ✅        | ✅         | ✅     | ✅      |

---

## 🎯 特性

### 🚀 极致性能

- **Astro 岛屿架构** — 默认零 JavaScript，首屏加载速度提升 80%+
- **全异步** — FastAPI + asyncpg 非阻塞数据库操作
- **智能缓存** — 多层 Redis 缓存 + 智能失效机制
- **CDN 友好** — 静态资源优化 + 缓存头配置

### 🔌 可扩展

- **插件系统** — Hook 机制（`do_action` / `apply_filters`），无需修改核心代码即可扩展
- **主题引擎** — 热插拔 Astro 主题 + React Islands 组件
- **RESTful API** — 完整 v2 API + 自动生成 Swagger/ReDoc 文档
- **SDK 支持** — Python & JavaScript SDK 编程访问

### 🔒 企业级安全

- **JWT + OAuth2** — Cookie/Bearer 双模式认证 + 双因素认证 (TOTP)
- **RBAC 权限** — 细粒度的基于能力的权限管理系统
- **零信任安全** — IP 追踪、异常检测、内容审批工作流
- **审计日志** — 追踪所有敏感操作
- **速率限制** — 可配置的端点级限流

### 📱 现代化体验

- **响应式设计** — 完美适配桌面、平板、手机
- **深色模式** — 跟随系统主题自动切换
- **SEO 优化** — 自动生成 Sitemap、Meta 标签、结构化数据
- **PWA 支持** — 可安装为原生应用，支持离线访问
- **移动端 App** — Capacitor 封装的原生 Android/iOS 应用

### 🛠️ 开发者体验

- **热重载** — 开发时即时反馈
- **CLI 工具** — 强大的命令行管理工具（`python scripts/cli.py`）
- **类型安全** — 全代码库类型注解
- **MCP Server** — AI 集成，支持 Claude Desktop & Cursor IDE

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx / CDN                          │
├────────────────────────┬────────────────────────────────────┤
│    Astro 前端           │         FastAPI 后端               │
│   (静态 SSG)           │    (异步 REST API 服务器)          │
│                        │                                    │
│  ┌──────────────┐      │  ┌───────────┐  ┌──────────────┐  │
│  │  React 19    │      │  │  路由层    │  │   中间件     │  │
│  │  岛屿组件    │      │  │ (v2/v3)   │  │              │  │
│  └──────────────┘      │  └─────┬─────┘  └──────────────┘  │
│                        │        │                          │
│  ┌──────────────┐      │  ┌─────▼─────┐  ┌──────────────┐  │
│  │ TailwindCSS  │      │  │  服务层    │  │  插件钩子    │  │
│  └──────────────┘      │  └─────┬─────┘  └──────────────┘  │
│                        │        │                          │
│  ┌──────────────┐      │  ┌─────▼─────┐  ┌──────────────┐  │
│  │ TanStack     │      │  │  模型层    │  │   缓存层     │  │
│  │ React Query  │      │  │(SQLAlchemy)│  │   (Redis)    │  │
│  └──────────────┘      │  └─────┬─────┘  └──────────────┘  │
│                        │        │                          │
│                        │  ┌─────▼─────┐                    │
│                        │  │PostgreSQL │                    │
│                        │  └───────────┘                    │
├────────────────────────┴────────────────────────────────────┤
│                    共享模型 & 工具库                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 技术栈

<table>
<tr>
<td valign="top" width="50%">

**后端**

- [FastAPI](https://fastapi.tiangolo.com/) 0.128 — 异步 Web 框架
- [SQLAlchemy](https://www.sqlalchemy.org/) 2.0 — ORM 数据库工具
- [PostgreSQL](https://www.postgresql.org/) — 主数据库 (asyncpg)
- [Redis](https://redis.io/) — 缓存 & 会话存储
- [Alembic](https://alembic.sqlalchemy.org/) — 数据库迁移
- [Uvicorn](https://www.uvicorn.org/) — ASGI 服务器
- [APScheduler](https://apscheduler.readthedocs.io/) — 后台任务调度

</td>
<td valign="top" width="50%">

**前端**

- [Astro](https://astro.build/) 5.7 — 静态站点生成器 (SSG)
- [React](https://react.dev/) 19 — UI 组件（岛屿架构）
- [TailwindCSS](https://tailwindcss.com/) — 工具优先 CSS
- [TypeScript](https://www.typescriptlang.org/) — 类型安全
- [TanStack React Query](https://tanstack.com/query) — 数据获取
- [TipTap](https://tiptap.dev/) — 富文本编辑器
- [Radix UI](https://www.radix-ui.com/) — 无障碍组件库

</td>
</tr>
<tr>
<td valign="top">

**基础设施**

- [Docker](https://www.docker.com/) — 容器化部署
- [Nginx](https://nginx.org/) — 反向代理
- [Capacitor](https://capacitorjs.com/) — 移动端 App (Android/iOS)

</td>
<td valign="top">

**集成服务**

- [Meilisearch](https://www.meilisearch.com/) — 全文搜索引擎
- [Sentry](https://sentry.io/) — 错误追踪
- [S3 兼容存储](https://aws.amazon.com/s3/) — 对象存储
- [MCP Server](https://modelcontextprotocol.io/) — AI 集成

</td>
</tr>
</table>

---

## 🚀 快速开始

### Docker 一键部署（推荐）

```bash
git clone https://github.com/Athenavi/fast_blog.git
cd fast_blog
cp .env_example .env
# 编辑 .env 配置数据库等信息

docker-compose up -d
```

访问 `http://localhost:4321` 查看前端，`http://localhost:9421/docs` 查看 API 文档。

### 手动安装

<details>
<summary><b>前置要求</b></summary>

- Python 3.14+
- Node.js 18+
- PostgreSQL 17+
- Redis 7+（可选，用于缓存）

</details>

```bash
# 1. 克隆 & 设置后端
git clone https://github.com/Athenavi/fast_blog.git
cd fast_blog
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 2. 配置环境
cp .env_example .env
# 编辑 .env 文件

# 3. 运行数据库迁移
alembic upgrade head

# 4. 启动后端
python main.py --backend fastapi

# 5. 设置前端（新终端）
cd frontend-astro
npm install
npm run dev
```

### CLI 快速开始

```bash
# 使用内置 CLI
python scripts/cli.py create my-blog   # 初始化项目
python scripts/cli.py user create admin --admin  # 创建管理员
python scripts/cli.py dev --port 9421  # 启动开发服务器
```

---

## 📖 文档

| 文档                                       | 说明             |
|------------------------------------------|----------------|
| [快速开始](docs/QUICK_START.md)              | 安装和配置指南        |
| [技术架构](docs/TECHNICAL.md)                | 系统设计与决策        |
| [API 参考](docs/API_REFERENCE.md)          | 完整 REST API 文档 |
| [插件开发](docs/PLUGIN_DEVELOPMENT_GUIDE.md) | 开发自定义插件        |
| [主题开发](docs/THEME_DEVELOPMENT_GUIDE.md)  | 创建自定义主题        |
| [部署指南](docs/DEPLOYMENT_GUIDE.md)         | 生产环境部署         |
| [故障排查](docs/TROUBLESHOOTING_FAQ.md)      | 常见问题解答         |
| [更新日志](CHANGELOG.md)                     | 版本历史           |
| [安全策略](SECURITY.md)                      | 漏洞报告           |

---

## 📊 性能对比

基于包含 1000 篇文章的博客进行测试：

| 指标            | FastBlog (Astro) | 典型 SSR | 提升      |
|---------------|------------------|--------|---------|
| 首次内容绘制        | **~0.5s**        | ~1.5s  | ⬇️ 67%  |
| 最大内容绘制        | **~0.8s**        | ~2.5s  | ⬇️ 68%  |
| 可交互时间         | **~0.5s**        | ~3.0s  | ⬇️ 83%  |
| 首页 JS 大小      | **~0KB**         | ~250KB | ⬇️ 100% |
| Lighthouse 分数 | **98-100**       | 60-80  | ⬆️ 25%+ |

---

## 🗺️ 路线图

### ✅ 已完成

- [x] FastAPI 异步后端，100+ 数据模型
- [x] Astro SSG 前端 + React 19 岛屿架构
- [x] 插件系统（Hook 机制，18 个内置插件）
- [x] 主题引擎（热切换，3 个主题：default, magazine, modern-minimal）
- [x] RESTful API v2 + 自动 Swagger 文档
- [x] JWT 认证 + 双因素认证 (TOTP) + 零信任安全
- [x] TipTap 富文本编辑器文章管理
- [x] 嵌套评论系统
- [x] S3 兼容媒体管理
- [x] 全文搜索（Meilisearch）
- [x] SEO 优化工具集（Sitemap、Meta、结构化数据）
- [x] Docker 部署支持
- [x] PWA 支持 + 离线访问
- [x] 实时协作（基于 Yjs）
- [x] AI 集成（MCP Server）
- [x] 移动端 App（Capacitor Android/iOS）
- [x] 电商模块（商品、订单、购物车）
- [x] 国际化（i18n）+ 翻译管理

### 🚧 进行中

- [ ] 多租户支持
- [ ] GraphQL API
- [ ] 高级数据分析仪表板

### 📅 计划中

- [ ] Webhook 系统
- [ ] 内容版本对比视图

查看 [开放 Issues](https://github.com/Athenavi/fast_blog/issues) 获取完整的功能列表和已知问题。

---

## 🤝 参与贡献

我们欢迎各种形式的贡献！无论是修复错别字、添加功能还是改进文档，每一份贡献都很重要。

**快捷链接：**

- 🐛 [报告 Bug](https://github.com/Athenavi/fast_blog/issues/new?template=bug_report.md)
- 💡 [功能建议](https://github.com/Athenavi/fast_blog/issues/new?template=feature_request.md)
- 💬 [社区讨论](https://github.com/Athenavi/fast_blog/discussions)
- 📖 [贡献指南](CONTRIBUTING.md)

请在贡献前阅读 [贡献指南](CONTRIBUTING.md) 和 [行为准则](CODE_OF_CONDUCT.md)。

---

## 🌟 贡献者

<a href="https://github.com/Athenavi/fast_blog/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Athenavi/fast_blog" alt="贡献者" />
</a>

---

## 📄 开源协议

本项目采用 [Apache License 2.0](LICENSE) 开源协议。

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) — 优秀的异步 Web 框架
- [Astro](https://astro.build/) — 现代化静态站点构建工具
- [SQLAlchemy](https://www.sqlalchemy.org/) — Python SQL 工具包
- 所有 [贡献者](https://github.com/Athenavi/fast_blog/graphs/contributors)

---

<div align="center">

**如果 FastBlog 对你有帮助，请在 GitHub 上给我们一个 ⭐！**

Made with ❤️ by FastBlog Team

[⬆ 回到顶部](#fastblog)

</div>
