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
  <a href="#-技术栈"><img src="https://img.shields.io/badge/React-19-61DAFB" alt="React"></a>
</p>

<p align="center">
  <a href="#-快速开始">快速开始</a> &bull;
  <a href="#-核心功能">核心功能</a> &bull;
  <a href="#-系统架构">系统架构</a> &bull;
  <a href="#-api-文档">API 文档</a> &bull;
  <a href="#-sdk">SDK</a> &bull;
  <a href="https://github.com/Athenavi/fast_blog/blob/main/CONTRIBUTING.md">贡献指南</a>
</p>

---

## 为什么选择 CardedAI？

传统博客系统只有 **写文章 + 发布**。CardedAI 在此之上构建了三大智能引擎：

| 能力 | 传统博客 | CardedAI |
|------|---------|----------|
| 内容管理 | CRUD + SEO | CRUD + SEO + **AI 写作助手** |
| 信息获取 | 手动搜索 | **自动情报采集** (RSS/Web/API) + 情感分析 + 简报生成 |
| 知识利用 | 无 | **RAG 知识引擎** — 向量检索 + LLM 问答 |
| 工作流 | 手动操作 | **DAG 自动化引擎** — 可视化编排 + 定时/事件触发 |
| AI 集成 | 无 | **MCP Server** — 让 AI Agent 直接操作你的博客 |
| 开发者体验 | REST API | **Python/JS SDK** + 完整类型提示 |

## 核心功能

### 1. 博客 CMS (核心)

- **文章管理** — 富文本编辑器 + Markdown，分类/标签/草稿
- **SEO 优化中心** — 站点地图、Schema 结构化数据、面包屑、Hreflang
- **多语言** — 内置翻译管理系统 + 机器翻译集成
- **插件系统** — 热加载/卸载、沙箱隔离、依赖解析、权限控制
- **安全防护** — RBAC + 2FA + CSRF + 敏感词过滤 + 审计日志

### 2. 情报引擎 (Intel)

```
数据源 (RSS/Web/API) → 采集器 → 清洗管道 → AI 分析 → 预警 & 简报
```

- **多源采集** — RSS、Web 爬虫、API 接口，可扩展插件架构
- **智能清洗** — 文本清洗 → 去重 → 富化 (实体提取、关键词)
- **AI 分析** — 情感分析 + 自动分类 + 摘要生成
- **预警系统** — 规则引擎，关键词/情感/频率触发
- **简报生成** — 每日/周/专题简报，一键生成

### 3. 知识引擎 (Knowledge)

```
文档上传 → 解析 → 分块 → 向量化 → 存储 → RAG 检索 + LLM 问答
```

- **文档处理** — PDF/Word/TXT/Markdown 自动解析 + 智能分块
- **向量存储** — Milvus/Qdrant/Chroma 多后端支持
- **RAG 检索** — 语义搜索 + 上下文排序 + 缓存加速
- **知识问答** — 基于文档的 LLM 问答，引用溯源
- **报告生成** — 基于知识库的 AI 报告自动生成

### 4. 工作流引擎 (Workflow)

```
触发器 (Cron/Webhook/Event) → DAG 图 → 节点执行 → 输出
```

- **DAG 引擎** — 拓扑排序 + 并发执行 + 分支条件 + 循环检测
- **节点类型** — LLM / 采集 / RAG 检索 / 条件判断 / 通知推送
- **触发方式** — Cron 定时 / Webhook / 事件驱动 / 手动触发
- **工具注册表** — 动态注册 Agent 工具，支持自定义脚本
- **并发控制** — 工作流级 + 节点级并发限制，Redis 可选

### 5. MCP Server (AI Agent 接口)

```python
# AI Agent 通过 MCP 协议直接操作你的博客
mcp_tool("create_article", {"title": "...", "content": "..."})
mcp_tool("rag_search", {"query": "...", "knowledge_base_id": 1})
mcp_tool("execute_workflow", {"workflow_id": 1, "input": {...}})
```

### 6. 性能优化层

- **RAG 缓存** — 搜索结果缓存 + 文档变更自动失效
- **并发管理** — 信号量控制，防止资源耗尽
- **批量 Embedding** — 异步队列 + 自动分批 + 后台处理
- **任务队列** — Redis Streams 采集队列，可选降级为内存

## 系统架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Frontend (Astro + React)                    │
│  ┌──────────┐  ┌──────────────┐  ┌───────────┐  ┌───────────────┐  │
│  │ 博客前台  │  │ 情报看板      │  │ 知识工作台 │  │ 工作流编辑器  │  │
│  └──────────┘  └──────────────┘  └───────────┘  └───────────────┘  │
└──────────────────────────┬───────────────────────────────────────────┘
                           │ HTTP / WebSocket
┌──────────────────────────┴───────────────────────────────────────────┐
│                        Backend (FastAPI)                              │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                      API v2 (RESTful)                           │ │
│  │  /articles  /intel  /knowledge  /workflow  /dashboard  /mcp     │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ 情报引擎    │  │ 知识引擎      │  │ 工作流引擎│  │ MCP Server   │  │
│  │ Collector   │  │ RAG Chain    │  │ DAG      │  │ AI Agent     │  │
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

### 使用 Docker (推荐)

```bash
# 1. 克隆仓库
git clone https://github.com/Athenavi/fast_blog.git
cd fast_blog

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 设置 SECRET_KEY、数据库密码等

# 3. 一键启动
docker-compose up -d

# 4. 访问
# 前台: http://localhost:4321
# 后台: http://localhost:4321/admin
# API:  http://localhost:9421/api/v2/docs
```

### 本地开发

```bash
# 1. Python 环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. 数据库 (需要 PostgreSQL + Redis)
# 或修改 .env 使用 SQLite 开发模式

# 3. 启动后端
python main.py

# 4. 启动前端 (另一个终端)
cd frontend-astro
npm install
npm run dev
```

### 使用 SDK

**Python SDK:**

```python
from fastblog_sdk import FastBlogClient

client = FastBlogClient("http://localhost:9421/api/v2")
client.login("admin@example.com", "password")

# 博客操作
articles = client.get_articles(page=1, per_page=10)
client.create_article({"title": "Hello", "content": "World", "status": "published"})

# 情报引擎
sources = client.get_intel_sources()
client.trigger_collection(source_id=1)
intel = client.search_intelligence(query="AI", category="tech")

# 知识引擎
bases = client.get_knowledge_bases()
client.upload_document(base_id=1, file_path="paper.pdf")
answer = client.rag_qa(question="What is RAG?", knowledge_base_id=1)

# 工作流
workflows = client.get_workflow_definitions()
client.execute_workflow(def_id=1, input_data={"topic": "AI"})
```

**JavaScript SDK:**

```typescript
import { FastBlogSDK } from '@fastblog/sdk';

const sdk = new FastBlogSDK({ baseUrl: 'http://localhost:9421/api/v2' });
await sdk.login('admin@example.com', 'password');

// 情报
const sources = await sdk.getIntelSources();
const intel = await sdk.searchIntelligence('AI news');

// 知识库
const answer = await sdk.knowledgeQA(1, 'What is RAG?');

// 工作流
await sdk.executeWorkflow(1, { topic: 'AI' });
```

## API 文档

启动后端后访问自动生成的 API 文档：

| 文档类型 | URL |
|---------|-----|
| Swagger UI | `http://localhost:9421/api/v2/docs` |
| ReDoc | `http://localhost:9421/api/v2/redoc` |
| OpenAPI JSON | `http://localhost:9421/api/v2/openapi.json` |

### API 模块

| 模块 | 前缀 | 说明 |
|------|------|------|
| 博客 | `/api/v2/articles` | 文章 CRUD、分类、评论 |
| 情报 | `/api/v2/intel/sources` | 数据源、采集、情报、简报、预警 |
| 知识 | `/api/v2/knowledge` | 知识库、文档、RAG 搜索、报告 |
| 工作流 | `/api/v2/workflow` | 定义、执行、工具、触发器 |
| 仪表盘 | `/api/v2/dashboard` | 统计、分析、活动 |
| MCP | `/mcp` | AI Agent 协议端点 |

## 技术栈

**后端:**
- **FastAPI** — 高性能异步 Web 框架
- **SQLAlchemy 2.0** — 异步 ORM + Alembic 迁移
- **PostgreSQL** — 主数据库 (支持 asyncpg)
- **Redis** — 缓存 / 任务队列 / 会话存储
- **Milvus / Qdrant** — 向量数据库 (RAG)

**前端:**
- **Astro** — 静态站点生成 + 岛屿架构
- **React 19** — 交互式组件
- **Tailwind CSS** — 原子化 CSS
- **Framer Motion** — 动画库
- **TanStack Query** — 数据获取

**AI / ML:**
- **sentence-transformers** — 本地 Embedding
- **OpenAI API** — Embedding + LLM (可选)
- **MCP Protocol** — AI Agent 标准协议

## 项目结构

```
CardedAI/
├── src/                          # 后端源码
│   ├── api/v2/                   # REST API 端点
│   │   ├── intel/                #   情报 API
│   │   ├── knowledge/            #   知识 API
│   │   ├── workflow/             #   工作流 API
│   │   └── dashboard/            #   仪表盘 API
│   ├── mcp/                      # MCP Server
│   │   ├── server.py             #   核心 MCP 服务器
│   │   └── extensions.py         #   情报/知识/工作流 MCP 扩展
│   ├── auth/                     # 认证 & 安全
│   └── middleware/               # 中间件
├── shared/                       # 共享层
│   ├── models/                   # 数据模型 (SQLAlchemy)
│   │   ├── intel/                #   情报模型
│   │   ├── knowledge/            #   知识模型
│   │   └── workflow/             #   工作流模型
│   └── services/                 # 业务服务
│       ├── intel/                #   情报引擎 (采集/清洗/分析)
│       ├── knowledge/            #   知识引擎 (RAG/Embedding)
│       ├── workflow/             #   工作流引擎 (DAG/触发器)
│       └── performance/          #   性能优化 (缓存/并发/批量)
├── frontend-astro/               # 前端 (Astro + React)
│   └── src/
│       ├── pages/                # 路由页面
│       └── components/           # React 组件
├── sdk/
│   ├── python/                   # Python SDK
│   └── javascript/               # JavaScript SDK
├── plugins/                      # 插件目录
├── tests/                        # 测试套件
├── alembic_migrations/           # 数据库迁移
├── docker-compose.yml            # Docker 编排
├── Dockerfile                    # 后端镜像
└── Makefile                      # 开发命令
```

## 测试

```bash
# 运行全部测试
python -m pytest tests/ -v

# 各阶段集成测试
python debug/test_phase2_imports.py   # 情报引擎 (40 tests)
python debug/test_phase3_imports.py   # 知识引擎 (38 tests)
python debug/test_phase4_imports.py   # 自动化引擎 (90 tests)
python debug/test_phase6_imports.py   # 集成验证 (63 tests)

# 带覆盖率
python -m pytest tests/ --cov=src --cov-report=html
```

## 参与贡献

我们欢迎所有形式的贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解：

- 如何报告 Bug
- 如何提交新功能
- 代码规范和提交约定
- Pull Request 流程

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史。

## 开源协议

本项目采用 [AGPL-3.0](LICENSE) 协议开源。

---

<p align="center">
  <strong>CardedAI</strong> — 让信息流动，让洞察抵达。<br>
  <sub>Built with FastAPI + Astro + React + AI</sub>
</p>
