# AI Work Assistant

> 个人工作效率 AI 系统 — 面向企业技术岗位人员，减少日常工作时间消耗，自动化产出工作内容。

## 系统概述

AI Work Assistant 是一个基于 RAG（检索增强生成）的智能工作助手系统，专为云计算工程师、售前工程师、技术支持工程师等技术岗位人员设计。

### 核心价值

- **减少认知负担** — 自动检索知识库，提供结构化建议
- **减少准备时间** — 模板化输出，秒级生成工作文档
- **减少重复写作** — 周报、汇报、客户回复一键生成
- **减少信息查找** — RAG 知识库覆盖产品文档、FAQ、故障排查
- **减少技术解释时间** — 根据受众自动调整表达方式
- **减少汇报编写时间** — 结构化汇报材料自动生成

## 系统架构

```
┌─────────────────────────────────────────────────┐
│          Web Frontend (SPA — HTML/CSS/JS)        │
│  工作台 │ 9场景表单 │ 知识库管理 │ 系统状态      │
├─────────────────────────────────────────────────┤
│          Auth Middleware (API Key)                │
├─────────────────────────────────────────────────┤
│                 API Layer (FastAPI)               │
│  /knowledge/*  │  /scenario/*  │  /health        │
├─────────────────────────────────────────────────┤
│              Service Layer                        │
│  knowledge_service  │  scenario_service           │
├─────────────────────────────────────────────────┤
│           Scenario Modules (9个场景)              │
│  排查│问答│客户回复│周报│汇报│培训│演示│PoC│升级   │
├─────────────────────────────────────────────────┤
│         Prompt Templates + Output Modes           │
│  客户模式  │  技术模式  │  领导模式               │
├─────────────────────────────────────────────────┤
│              Knowledge Layer (RAG)                │
│  VectorStore(ChromaDB) │ Embeddings(OpenAI)       │
│  Chunker │ Dedup │ Cleaner                        │
├─────────────────────────────────────────────────┤
│           Ingestion Pipeline                      │
│  File Ingestor │ URL Ingestor │ Bootstrap         │
└─────────────────────────────────────────────────┘
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
cd ai-work-assistant

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env，填入 OpenAI API Key
# OPENAI_API_KEY=sk-your-key-here

# （可选）设置访问密钥，保护 API 不被未授权访问
# AUTH_API_KEY=your-secret-key
```

### 3. 启动服务

```bash
# 启动服务（同时提供 API 和 Web 前端）
python main.py
```

启动后可访问以下地址：

| 地址 | 说明 |
|------|------|
| http://localhost:8000 | **Web 前端界面**（日常使用入口） |
| http://localhost:8000/ui | Web 前端界面（同上） |
| http://localhost:8000/docs | Swagger API 交互文档 |
| http://localhost:8000/redoc | ReDoc API 文档 |
| http://localhost:8000/health | 健康检查 |

> **提示**：如果配置了 `AUTH_API_KEY`，打开 Web 界面后点击右上角 🔑 按钮输入密钥即可正常使用。

### 4. 初始化知识库

```bash
# Bootstrap 导入 ~1000 条初始数据
curl -X POST http://localhost:8000/knowledge/bootstrap
```

### 5. 开始使用

```bash
# 技术问答示例
curl -X POST http://localhost:8000/scenario/tech_qa \
  -H "Content-Type: application/json" \
  -d '{"question": "ZStack支持哪些存储方案？", "product": "ZStack Cloud"}'

# 运行完整示例
python examples/example_requests.py
```

## 项目结构

```
ai-work-assistant/
├── main.py                          # 应用入口（API + 前端静态服务）
├── config.py                        # 全局配置
├── requirements.txt                 # Python 依赖
├── .env.example                     # 环境变量模板
├── .gitignore
│
├── web/                             # Web 前端（SPA）
│   ├── index.html                   # 主页面
│   ├── style.css                    # 样式
│   └── app.js                       # 前端逻辑
│
├── app/
│   ├── auth.py                      # API Key 认证中间件
│   ├── api/                         # FastAPI 路由
│   │   ├── knowledge.py             # 知识库 API（含文件上传）
│   │   ├── scenarios.py             # 场景模块 API
│   │   └── health.py                # 健康检查
│   │
│   ├── services/                    # 业务逻辑层
│   │   ├── knowledge_service.py     # 知识库服务
│   │   └── scenario_service.py      # 场景调度服务
│   │
│   ├── knowledge/                   # 知识库核心
│   │   ├── vector_store.py          # ChromaDB 向量存储
│   │   ├── embeddings.py            # OpenAI Embedding
│   │   ├── chunker.py               # 文档分块
│   │   └── dedup.py                 # 去重逻辑
│   │
│   ├── ingestion/                   # 数据导入
│   │   ├── file_ingestor.py         # 文件导入
│   │   ├── url_ingestor.py          # URL 导入
│   │   ├── cleaner.py               # 内容清洗
│   │   └── bootstrap.py             # 初始数据导入
│   │
│   ├── scenario_modules/            # 9 个场景模块
│   │   ├── base.py                  # 基类
│   │   ├── troubleshooting.py       # 技术排查
│   │   ├── tech_qa.py               # 技术问答
│   │   ├── customer_reply.py        # 客户答复
│   │   ├── weekly_report.py         # 周报生成
│   │   ├── briefing.py              # 汇报生成
│   │   ├── training.py              # 培训生成
│   │   ├── demo_prep.py             # 演示准备
│   │   ├── poc_support.py           # PoC 支持
│   │   └── escalation.py            # 问题升级
│   │
│   ├── prompt_templates/            # Prompt 模板
│   │   ├── output_modes.py          # 输出模式定义
│   │   ├── troubleshooting.py
│   │   ├── tech_qa.py
│   │   ├── customer_reply.py
│   │   ├── weekly_report.py
│   │   ├── briefing.py
│   │   ├── training.py
│   │   ├── demo_prep.py
│   │   ├── poc_support.py
│   │   └── escalation.py
│   │
│   ├── models/                      # 数据模型
│   │   ├── common.py                # 通用模型
│   │   ├── knowledge.py             # 知识库模型
│   │   └── scenarios.py             # 场景输入模型
│   │
│   └── router/                      # 场景路由
│       └── scenario_router.py       # 自动识别+路由
│
├── data/
│   ├── seed/                        # 种子数据
│   │   ├── zstack_docs.json
│   │   ├── troubleshooting.json
│   │   └── faq.json
│   └── chroma_db/                   # ChromaDB 持久化
│
├── examples/                        # 使用示例
│   ├── example_requests.py
│   └── example_url_import.py
│
└── tests/                           # 测试
```

## API 接口

### 知识库 API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/knowledge/ingest/file` | 导入本地文件（服务器路径） |
| POST | `/knowledge/ingest/upload` | 浏览器上传文件 |
| POST | `/knowledge/ingest/url` | 导入 URL 内容 |
| POST | `/knowledge/bootstrap` | 初始化知识库（~1000条） |
| POST | `/knowledge/refresh/url` | 刷新 URL 内容 |
| GET/POST | `/knowledge/search` | 搜索知识库 |
| GET | `/knowledge/documents` | 列出所有文档（支持分页） |
| GET | `/knowledge/stats` | 知识库统计 |
| DELETE | `/knowledge/document/{source}` | 删除文档 |

### 场景模块 API

| 方法 | 路径 | 说明 | 时间限制 |
|------|------|------|----------|
| POST | `/scenario/auto` | 自动识别场景 | — |
| POST | `/scenario/troubleshooting` | 技术问题排查 | 10分钟 |
| POST | `/scenario/tech_qa` | 技术问题回答 | 3分钟 |
| POST | `/scenario/customer_reply` | 客户答复 | — |
| POST | `/scenario/weekly_report` | 周报生成 | 5分钟 |
| POST | `/scenario/briefing` | 汇报生成 | 15分钟 |
| POST | `/scenario/training` | 培训内容生成 | — |
| POST | `/scenario/demo_prep` | 演示准备 | — |
| POST | `/scenario/poc_support` | PoC 方案 | — |
| POST | `/scenario/escalation` | 问题升级 | 10分钟 |
| GET | `/scenario/types` | 列出所有场景 | — |

## 场景模块详解

### 1. 技术问题排查 (Troubleshooting)

快速分析技术故障并提供排查方案。

```json
POST /scenario/troubleshooting
{
  "problem_description": "云主机创建失败，提示存储空间不足",
  "environment": "ZStack 4.6.0, Ceph存储, 3节点",
  "error_logs": "Error: not enough space on primary storage",
  "affected_component": "PrimaryStorage",
  "urgency_level": "high",
  "output_mode": "technical"
}
```

**输出包含**：问题概述 → 可能原因Top3 → 排查步骤 → 临时方案 → 需收集日志 → 是否升级

### 2. 技术问答 (Tech Q&A)

```json
POST /scenario/tech_qa
{
  "question": "ZStack支持在线迁移吗？有什么前提条件？",
  "product": "ZStack Cloud",
  "output_mode": "technical"
}
```

### 3. 客户答复 (Customer Reply)

```json
POST /scenario/customer_reply
{
  "customer_question": "我们想用ZStack替换VMware，迁移难度大吗？",
  "context": "客户有200台VMware虚拟机",
  "output_mode": "customer"
}
```

### 4. 周报生成 (Weekly Report)

支持三种版本：`standard` / `leadership` / `technical`

```json
POST /scenario/weekly_report
{
  "tasks_completed": ["完成客户A的PoC", "处理3个技术工单"],
  "major_results": ["PoC通过验收"],
  "issues": ["客户B网络延迟问题"],
  "next_week_plan": ["准备方案汇报"],
  "report_version": "leadership"
}
```

### 5. 问题升级 (Escalation)

```json
POST /scenario/escalation
{
  "problem": "管理节点OOM频繁重启",
  "environment": "ZStack 4.5.0, 双管理节点",
  "logs": "OutOfMemoryError: Java heap space",
  "attempted_actions": ["增加JVM内存到8G", "检查MySQL连接数"]
}
```

## 输出模式

每个场景支持三种输出模式：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `customer` | 客户模式 | 对外沟通，专业易懂 |
| `technical` | 技术模式 | 内部技术文档，详细精确 |
| `leadership` | 领导模式 | 管理汇报，简洁量化 |

## 知识库管理

### URL 导入

```json
POST /knowledge/ingest/url
{
  "urls": ["https://example.com/docs/page1", "https://example.com/docs/page2"],
  "document_type": "product_doc",
  "force_refresh": false
}
```

**处理流程**：
```
URL → Fetch → HTML清洗 → 文本提取 → 标准化 → 去重检查 → 分块 → Embedding → 写入ChromaDB
```

**返回信息**：
- 总chunk数量
- 新增chunk数量
- 重复跳过数量
- 元数据（标题、URL、抓取时间）

### 去重策略

系统使用双层去重机制：

1. **Source 级别**：同一 URL/文件路径不重复导入（除非 `force_refresh=true`）
2. **Content 级别**：基于 xxhash64 内容哈希，相同内容不重复存储

### Bootstrap 初始化

```bash
curl -X POST http://localhost:8000/knowledge/bootstrap
```

自动导入流程：
1. 加载 `data/seed/` 目录下的 JSON 文件
2. 生成合成知识数据（架构、运维、FAQ 等 10 个类别）
3. 分块 → Embedding → 写入数据库
4. 目标：~1000 条记录

## Ingestion Pipeline

```
数据源 (File / URL / Seed)
    ↓
┌───────────────┐
│   Fetch       │  文件读取 / HTTP请求 / JSON加载
└───────┬───────┘
        ↓
┌───────────────┐
│   Clean       │  去除HTML标签/广告/导航/脚本
└───────┬───────┘  trafilatura (主) + BeautifulSoup (备)
        ↓
┌───────────────┐
│  Normalize    │  统一编码/去除控制字符/标准化空白
└───────┬───────┘
        ↓
┌───────────────┐
│  Deduplicate  │  xxhash64 内容哈希去重
└───────┬───────┘
        ↓
┌───────────────┐
│    Chunk      │  RecursiveCharacterTextSplitter
└───────┬───────┘  size=800, overlap=200
        ↓
┌───────────────┐
│   Embed       │  OpenAI text-embedding-3-small
└───────┬───────┘  1536维, 批量100条/次
        ↓
┌───────────────┐
│    Store      │  ChromaDB PersistentClient
└───────────────┘  cosine距离, HNSW索引
```

## Web 前端

系统内置一个 SPA 前端，启动后通过浏览器直接访问 `http://localhost:8000` 即可使用，无需额外构建步骤。

前端包含：

- **工作台** — 概览面板 + 快速跳转
- **9 个场景模块表单** — 填写参数后一键生成，结果以 Markdown 渲染展示
- **知识库管理** — 搜索、上传文件、导入网页、查看文档列表、一键 Bootstrap
- **系统状态** — 查看服务运行状态、知识库统计、OpenAI 配置状态

### 前端访问认证

如果在 `.env` 中配置了 `AUTH_API_KEY`，所有 API 请求都需要携带密钥：

- **Web 界面**：点击右上角 🔑 按钮输入密钥（自动保存到浏览器 localStorage）
- **curl / SDK**：通过 Header 传递 `X-API-Key: your-key` 或 Query 参数 `?api_key=your-key`

```bash
# 启用认证的 curl 示例
curl -X POST http://localhost:8000/scenario/tech_qa \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{"question": "ZStack支持哪些存储方案？"}'
```

> 不设置 `AUTH_API_KEY` 则无需认证，适合本地开发使用。生产环境强烈建议配置。

## 云服务器部署

如需将系统部署到云服务器通过公网访问，参考 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)，包含：

- Systemd 服务管理
- Nginx 反向代理 + SSL
- 防火墙 & 安全组配置
- ZStack 内部文档接入方式

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| Web框架 | FastAPI | 异步高性能 API + 静态文件服务 |
| 前端 | HTML/CSS/JS + marked.js | 内置 SPA，无需构建 |
| 向量数据库 | ChromaDB | 轻量级向量存储 |
| LLM | OpenAI GPT-4o | 生成结构化内容 |
| Embedding | text-embedding-3-small | 1536维文本向量 |
| 文档处理 | trafilatura + BeautifulSoup | 网页内容提取 |
| 文本分块 | LangChain TextSplitter | 递归字符分块 |
| HTTP客户端 | httpx | 异步 HTTP 请求 |
| 配置管理 | pydantic-settings | 类型安全配置 |
| 去重 | xxhash | 高性能内容哈希 |

## 设计原则

1. **优先减少工作时间** — 所有输出可直接使用
2. **结论先行** — 先给结论，再给解释
3. **模板化输出** — 结构化、可复用
4. **时间限制** — 每个模块有明确的时间约束
5. **升级机制** — 问题无法解决时支持升级
6. **知识驱动** — 基于 RAG 确保回答准确

## 扩展指南

### 添加新的场景模块

1. 在 `app/prompt_templates/` 创建 prompt 模板
2. 在 `app/scenario_modules/` 创建模块（继承 `BaseScenarioModule`）
3. 在 `app/models/scenarios.py` 添加输入模型
4. 在 `app/models/common.py` 的 `ScenarioType` 枚举添加类型
5. 在 `app/router/scenario_router.py` 注册模块
6. 在 `app/api/scenarios.py` 添加 API 端点

### 添加新的知识来源

1. 在 `data/seed/` 添加 JSON 文件（格式：`[{title, content, document_type}]`）
2. 调用 `POST /knowledge/bootstrap` 重新导入
3. 或使用 `POST /knowledge/ingest/url` 导入网页

## License

MIT
