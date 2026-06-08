<p align="center">
  <h1 align="center">CardedAI</h1>
  <p align="center"><strong>Information, carded. Insight, delivered.</strong></p>
  <p align="center">
    AI 驱动的全栈内容管理 & 智能情报平台 — 博客 CMS + 情报采集 + RAG 知识引擎 + 工作流自动化
  </p>
</p>

<p align="center">
  <a href="https://github.com/Athenavi/fast_blog/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-AGPL--3.0-blue" alt="License"></a>
  <a href="https://github.com/Athenavi/fast_blog/actions"><img src="https://img.shields.io/github/actions/workflow/status/Athenavi/fast_blog/ci.yml?branch=main" alt="CI"></a>
  <a href="https://github.com/Athenavi/fast_blog/releases"><img src="https://img.shields.io/badge/version-V0.3.26-green" alt="Version"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.14+-blue" alt="Python"></a>
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-0.136-009688" alt="FastAPI"></a>
  <a href="https://astro.build"><img src="https://img.shields.io/badge/Astro-5.x-FF5D01" alt="Astro"></a>
</p>

<p align="center">
  <a href="#-快速开始">快速开始</a> &bull;
  <a href="#-核心功能">核心功能</a> &bull;
  <a href="#-系统架构">系统架构</a> &bull;
  <a href="#-api-文档">API 文档</a> &bull;
  <a href="https://github.com/Athenavi/fast_blog/blob/main/CONTRIBUTING.md">贡献指南</a>
</p>

---

## 为什么选择 CardedAI？

传统博客系统只有 **写文章 + 发布**。CardedAI 在此之上构建了三大智能引擎：

| 能力 | 传统博客 | CardedAI |
|------|---------|----------|
| 内容管理 | CRUD + SEO | CRUD + SEO + **AI 写作助手** |
| 信息获取 | 手动搜索 | **自动情报采集** (RSS/Web/API/搜索引擎) + 情感分析 + 简报生成 |
| 知识利用 | 无 | **RAG 知识引擎** — 向量检索 + LLM 问答 + 报告生成 |
| 工作流 | 手动操作 | **DAG 自动化引擎** — 可视化编排 + 定时/事件触发 |
| AI 集成 | 无 | **MCP Server** — Claude Desktop/Cursor IDE 直接操作站点 |

## 核心功能

### 1. 博客 CMS（核心）

- **文章管理** — 富文本编辑器 + Markdown，分类/标签/草稿/修订历史
- **SEO 优化中心** — 站点地图、Schema 结构化数据、面包屑、Hreflang、元标签
- **多语言** — 内置翻译管理系统 + 机器翻译集成
- **安全防护** — RBAC + 2FA + CSRF + 敏感词过滤 + 审计日志
- **媒体管理** — 图库/文件夹/批量上传/图片编辑/PDF 预览
- **页面建构** — 可视化 Page Builder + 块模式库 + Widget 系统

### 2. 情报引擎 (Intel)

```
数据源 (RSS/Web/API/搜索引擎) → 采集器 → 清洗管道 → AI 分析 → 预警 & 简报
```

- **多源采集** — RSS、Web 爬虫、API 接口、Google/Bing 搜索引擎（可扩展插件架构）
- **智能清洗** — 文本清洗 → SimHash 去重 → 实体/关键词富化
- **AI 分析** — 情感分析 + 自动分类 + 摘要生成（LLM 驱动，有 fallback）
- **预警系统** — 规则引擎，关键词/情感/频率触发，邮件/Webhook 分发
- **简报生成** — 每日/每周/每月/主题简报，一键生成（LLM 驱动）
- **自动调度** — APScheduler 定时采集 + 自动简报生成

### 3. 知识引擎 (Knowledge / RAG)

```
文档上传 → 解析 → 分块 → 向量化 → 存储 → RAG 检索 + LLM 问答 → 报告生成
```

- **文档处理** — PDF/Word/TXT/Markdown/HTML/URL 自动解析 + 智能分块（3 种策略）
- **向量存储** — Milvus / Qdrant 双后端支持
- **Embedding** — Local (sentence-transformers) + OpenAI 双后端
- **RAG 检索** — 语义搜索 + 上下文排序 + 两级缓存加速
- **知识问答** — 基于文档的 LLM 问答，引用溯源
- **报告生成** — 基于知识库的 AI 报告自动生成（4 种模板）

### 4. 工作流引擎 (Workflow)

```
触发器 (Cron/Webhook/Event) → DAG 图 → 节点执行 → 输出
```

- **DAG 引擎** — 拓扑排序 + 并行执行 + 分支条件 + 循环检测 + 超时控制
- **节点类型** — LLM / 采集器 / RAG 检索 / 条件判断 / 通知推送
- **触发方式** — Cron 定时 / Webhook / 事件驱动 / 手动触发
- **工具注册表** — 动态注册 Agent 工具（内置 4 个：采集/检索/通知/发布）
- **可视化编辑器** — SVG 画布 + 拖拽 + 连线 + 节点配置面板 + 执行历史

### 5. MCP Server (AI Agent 接口)

支持 Claude Desktop、Cursor IDE 等 MCP 客户端通过 stdio 直接连接：

```json
// Claude Desktop 配置
{
  "mcpServers": {
    "fastblog": {
      "command": "python",
      "args": ["-m", "src.mcp.cli"]
    }
  }
}
```

- **资源** — articles / categories / users / media / settings / intel / knowledge / workflow
- **工具** — 文章 CRUD / 情报采集/搜索 / 知识库问答 / 工作流触发（15+ 工具）
- **提示模板** — 写作 / SEO / 内容审计 / 情报分析 / 知识 QA（6 个）

### 6. 性能优化层

- **RAG 缓存** — 两级缓存（内存 + Redis），TTL 控制，自动失效
- **并发管理** — 信号量控制，防止资源耗尽
- **批量 Embedding** — 异步队列 + 自动分批 + 后台处理
- **任务队列** — Redis Streams + 内存 fallback

## 系统架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Frontend (Astro + React)                    │
│  博客前台 / 管理后台 / 情报看板 / 知识工作台 / 工作流编辑器          │
└──────────────────────────┬───────────────────────────────────────────┘
                           │ HTTP / WebSocket
┌──────────────────────────┴───────────────────────────────────────────┐
│                        Backend (FastAPI)                              │
│  /articles  /intel  /knowledge  /workflow  /dashboard  /mcp         │
│                                                                      │
│  ┌────────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ 情报引擎    │  │ 知识引擎      │  │ 工作流引擎│  │ MCP Server   │  │
│  │ Collector   │  │ RAG Chain    │  │ DAG      │  │ stdio/SSE    │  │
│  │ Cleaner     │  │ Embedding    │  │ Triggers │  │ Tools        │  │
│  │ Analyzer    │  │ VectorStore  │  │ Executors│  │ Resources    │  │
│  │ Briefing    │  │ ReportGen    │  │ ToolReg  │  │ Prompts      │  │
│  └────────────┘  └──────────────┘  └──────────┘  └──────────────┘  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                    性能优化层                                    │ │
│  │  RAG Cache  │  Concurrency Mgr  │  Batch Embedding  │  Task Q  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└───────────────┬──────────────────┬──────────────────┬────────────────┘
                │                  │                  │
        ┌───────┴──────┐  ┌───────┴──────┐  ┌───────┴──────┐
        │ PostgreSQL   │  │    Redis     │  │   Milvus     │
        │ (主数据库)    │  │ (缓存/队列)  │  │ (向量存储)   │
        └──────────────┘  └──────────────┘  └──────────────┘
```

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/Athenavi/fast_blog.git
cd fast_blog

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 设置 SECRET_KEY、数据库密码等

# 3. 启动后端
pip install -r requirements.txt
python main.py --port 9421 --env dev

# 4. 启动前端（另一个终端）
cd frontend-astro
npm install
npm run dev

# 访问: http://localhost:4321/admin
# API:  http://localhost:9421/api/v2/docs
```

## 技术栈

**后端:** FastAPI + SQLAlchemy 2.0 + PostgreSQL + Redis + Milvus/Qdrant

**前端:** Astro + React 19 + Tailwind CSS + Framer Motion + TanStack Query

**AI:** sentence-transformers + OpenAI API + MCP Protocol

## API 文档

启动后端后访问:
- Swagger UI: `http://localhost:9421/api/v2/docs`
- ReDoc: `http://localhost:9421/api/v2/redoc`

### API 模块

| 模块 | 前缀 | 端点数 | 说明 |
|------|------|--------|------|
| 博客 | `/api/v2/articles` | 20+ | 文章 CRUD、分类、评论等 |
| 情报 | `/api/v2/intel` | 18 | 数据源、采集、情报、简报、预警 |
| 知识 | `/api/v2/knowledge` | 16 | 知识库、文档、RAG 搜索、报告 |
| 工作流 | `/api/v2/workflow` | 19 | 定义、执行、工具、触发器 |
| MCP | `/api/v2/mcp` | 8 | JSON-RPC + SSE + 信息端点 |

## 项目结构

```
CardedAI/
├── src/                          # 后端源码
│   ├── api/v2/                   # REST API 端点 (30+ 模块)
│   │   ├── intel/                #   情报 API
│   │   ├── knowledge/            #   知识 API
│   │   ├── workflow/             #   工作流 API
│   │   └── mcp/                  #   MCP 协议端点
│   ├── mcp/                      # MCP Server (stdio/SSE)
│   ├── auth/                     # 认证 & 安全
│   └── middleware/               # 中间件
├── shared/                       # 共享层
│   ├── models/                   # 数据模型 (65 ORM 表)
│   └── services/                 # 业务服务
│       ├── intel/                #   情报引擎
│       ├── knowledge/            #   知识引擎 (RAG)
│       ├── workflow/             #   工作流引擎 (DAG)
│       └── performance/          #   性能优化
├── frontend-astro/               # 前端 (Astro + React)
│   └── src/
│       ├── pages/admin/          # 管理后台页面 (35+)
│       └── components/           # React 组件
├── sdk/                          # SDK
│   ├── python/                   # Python SDK
│   └── javascript/               # JavaScript SDK
├── tests/                        # 测试套件
├── docker-compose.yml            # Docker 编排
└── Makefile                      # 开发命令
