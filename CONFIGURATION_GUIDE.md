# AI Work Assistant — 系统配置指南

---

## 目录

1. [环境要求](#1-环境要求)
2. [安装部署](#2-安装部署)
3. [环境变量配置详解](#3-环境变量配置详解)
4. [OpenAI 模型配置](#4-openai-模型配置)
5. [向量数据库配置](#5-向量数据库配置)
6. [知识库参数调优](#6-知识库参数调优)
7. [应用服务配置](#7-应用服务配置)
8. [场景模块时间限制配置](#8-场景模块时间限制配置)
9. [URL 抓取配置](#9-url-抓取配置)
10. [种子数据与 Bootstrap 配置](#10-种子数据与-bootstrap-配置)
11. [生产环境部署建议](#11-生产环境部署建议)
12. [常见配置问题排查](#12-常见配置问题排查)

---

## 1. 环境要求

### 1.1 操作系统

| 系统 | 支持状态 |
|------|----------|
| macOS 12+ | 完全支持 |
| Ubuntu 20.04 / 22.04 | 完全支持 |
| CentOS 7.9 / 8 | 完全支持 |
| Windows 10/11 | 支持（需 WSL2 或原生 Python） |

### 1.2 Python 版本

- **最低要求**：Python 3.10
- **推荐版本**：Python 3.11 或 3.12

检查版本：

```bash
python --version
# 或
python3 --version
```

### 1.3 硬件要求

| 场景 | CPU | 内存 | 磁盘 |
|------|-----|------|------|
| 开发/测试 | 2 核 | 4 GB | 10 GB |
| 生产（小规模知识库 <5000 条） | 4 核 | 8 GB | 50 GB SSD |
| 生产（大规模知识库 >10000 条） | 8 核 | 16 GB | 100 GB SSD |

> 磁盘空间主要由 ChromaDB 向量数据库和日志占用。每 1000 条向量记录约占 50-100 MB。

### 1.4 网络要求

- 必须能访问 OpenAI API（或兼容 API 的代理/私有部署地址）
- 如需 URL 导入功能，需能访问目标网站
- 默认服务端口：`8000`

---

## 2. 安装部署

### 2.1 第一步：创建虚拟环境

```bash
# 进入项目目录
cd ai-work-assistant

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows CMD
# venv\Scripts\Activate.ps1     # Windows PowerShell
```

### 2.2 第二步：安装依赖

```bash
pip install -r requirements.txt
```

依赖清单概要：

| 类别 | 包名 | 用途 |
|------|------|------|
| Web 框架 | `fastapi`, `uvicorn` | API 服务 |
| LLM | `openai`, `langchain` | 大模型调用 |
| 向量数据库 | `chromadb` | 向量存储与检索 |
| 文档处理 | `trafilatura`, `beautifulsoup4` | 网页内容提取 |
| 网络 | `httpx` | 异步 HTTP 客户端 |
| 配置 | `pydantic-settings`, `python-dotenv` | 环境变量管理 |
| 去重 | `xxhash` | 内容哈希 |

### 2.3 第三步：创建配置文件

```bash
cp .env.example .env
```

然后按照下方说明编辑 `.env` 文件。

### 2.4 第四步：启动服务

```bash
python main.py
```

启动成功后，终端会输出：

```
AI Work Assistant starting...
  LLM Model: gpt-4o
  Embedding Model: text-embedding-3-small
  ChromaDB Path: ./data/chroma_db
  OpenAI Configured: True
Vector store ready. 0 documents loaded.
```

访问地址：

| 地址 | 说明 |
|------|------|
| `http://localhost:8000` | API 根路径 |
| `http://localhost:8000/docs` | Swagger 交互文档 |
| `http://localhost:8000/redoc` | ReDoc API 文档 |
| `http://localhost:8000/health` | 健康检查 |

---

## 3. 环境变量配置详解

所有配置通过项目根目录的 `.env` 文件管理。系统启动时自动读取。

### 3.1 完整配置项一览

```bash
# =============================================================================
# AI Work Assistant - 完整配置
# =============================================================================

# ---- OpenAI 配置 ----
OPENAI_API_KEY=sk-your-openai-api-key-here     # [必填] OpenAI API 密钥
OPENAI_BASE_URL=https://api.openai.com/v1       # [可选] API 基地址
LLM_MODEL=gpt-4o                                # [可选] 对话模型
EMBEDDING_MODEL=text-embedding-3-small           # [可选] 向量模型
EMBEDDING_DIMENSION=1536                         # [可选] 向量维度

# ---- ChromaDB 配置 ----
CHROMA_PERSIST_DIR=./data/chroma_db              # [可选] 数据库存储路径
CHROMA_COLLECTION_NAME=ai_work_assistant         # [可选] 集合名称

# ---- 应用配置 ----
APP_HOST=0.0.0.0                                 # [可选] 监听地址
APP_PORT=8000                                    # [可选] 监听端口
APP_DEBUG=true                                   # [可选] 调试模式
LOG_LEVEL=INFO                                   # [可选] 日志级别

# ---- 知识库配置 ----
CHUNK_SIZE=800                                   # [可选] 分块大小
CHUNK_OVERLAP=200                                # [可选] 分块重叠
MAX_SEARCH_RESULTS=5                             # [可选] 搜索返回数

# ---- Bootstrap 配置 ----
SEED_DATA_DIR=./data/seed                        # [可选] 种子数据目录
BOOTSTRAP_RECORD_COUNT=1000                      # [可选] 初始化记录数

# ---- URL 抓取配置 ----
URL_FETCH_TIMEOUT=30                             # [可选] 抓取超时(秒)
URL_USER_AGENT=AIWorkAssistant/1.0               # [可选] 请求 User-Agent

# ---- 时间限制配置(秒) ----
TROUBLESHOOTING_TIME_LIMIT=600                   # [可选] 技术排查
TECH_QA_TIME_LIMIT=180                           # [可选] 技术问答
WEEKLY_REPORT_TIME_LIMIT=300                     # [可选] 周报生成
BRIEFING_TIME_LIMIT=900                          # [可选] 汇报生成
ESCALATION_TIME_LIMIT=600                        # [可选] 问题升级
```

### 3.2 必填 vs 可选

| 参数 | 是否必填 | 说明 |
|------|----------|------|
| `OPENAI_API_KEY` | **必填** | 没有此配置系统无法调用 LLM 和生成 Embedding |
| 其他所有参数 | 可选 | 均有合理默认值，可按需调整 |

---

## 4. OpenAI 模型配置

### 4.1 API 密钥

```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
```

获取方式：
1. 访问 [OpenAI Platform](https://platform.openai.com/api-keys)
2. 创建新的 API Key
3. 将密钥粘贴到 `.env` 文件

> **安全提示**：`.env` 文件已在 `.gitignore` 中，不会被提交到代码仓库。请勿将密钥写入代码中。

### 4.2 API 基地址（支持兼容接口）

```bash
OPENAI_BASE_URL=https://api.openai.com/v1
```

如果你使用的是 OpenAI 兼容的第三方服务（如 Azure OpenAI、本地部署的 vLLM / Ollama 等），修改此地址即可：

| 场景 | 配置值 |
|------|--------|
| OpenAI 官方 | `https://api.openai.com/v1` |
| Azure OpenAI | `https://your-resource.openai.azure.com/openai/deployments/your-deployment` |
| 本地 Ollama | `http://localhost:11434/v1` |
| 其他兼容 API | 对应服务的地址 |

### 4.3 对话模型选择

```bash
LLM_MODEL=gpt-4o
```

推荐模型及适用场景：

| 模型 | 特点 | 推荐场景 |
|------|------|----------|
| `gpt-4o` | 最强能力，速度快 | **推荐**，适合所有场景 |
| `gpt-4o-mini` | 成本低，速度快 | 预算有限时使用 |
| `gpt-4-turbo` | 能力强，较贵 | 需要长上下文时 |
| `gpt-3.5-turbo` | 成本最低 | 仅用于简单问答 |

> **建议**：默认使用 `gpt-4o`，如需控制成本可切换为 `gpt-4o-mini`。

### 4.4 向量模型选择

```bash
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
```

可选模型：

| 模型 | 维度 | 价格 | 推荐度 |
|------|------|------|--------|
| `text-embedding-3-small` | 1536 | $0.02/百万 token | **推荐**，性价比最高 |
| `text-embedding-3-large` | 3072 | $0.13/百万 token | 需要更高精度时使用 |

> **注意**：更换向量模型后，需要清空并重建知识库（旧向量与新向量不兼容）。
>
> 清空方法：删除 `data/chroma_db/` 目录，然后重新执行 Bootstrap。

---

## 5. 向量数据库配置

### 5.1 存储路径

```bash
CHROMA_PERSIST_DIR=./data/chroma_db
```

- 此目录存放 ChromaDB 的持久化数据（SQLite 元数据 + HNSW 向量索引）
- 支持相对路径和绝对路径
- 确保运行用户对该路径有读写权限

**生产环境建议**：使用 SSD 存储，配置绝对路径：

```bash
CHROMA_PERSIST_DIR=/data/ai-assistant/chroma_db
```

### 5.2 集合名称

```bash
CHROMA_COLLECTION_NAME=ai_work_assistant
```

- 一个 ChromaDB 实例可以有多个集合（类似数据库中的表）
- 默认集合名 `ai_work_assistant` 通常无需修改
- 如果在同一台机器上运行多个实例，可通过不同集合名隔离数据

### 5.3 数据备份

ChromaDB 数据存储在 `CHROMA_PERSIST_DIR` 指定的目录中。备份只需复制该目录：

```bash
# 备份
cp -r ./data/chroma_db ./backup/chroma_db_$(date +%Y%m%d)

# 恢复
cp -r ./backup/chroma_db_20250309 ./data/chroma_db
```

---

## 6. 知识库参数调优

### 6.1 分块大小

```bash
CHUNK_SIZE=800
CHUNK_OVERLAP=200
```

| 参数 | 含义 | 默认值 | 调优建议 |
|------|------|--------|----------|
| `CHUNK_SIZE` | 每个文本块的最大字符数 | 800 | 500-1500 |
| `CHUNK_OVERLAP` | 相邻块之间的重叠字符数 | 200 | CHUNK_SIZE 的 15%-25% |

**调优原则**：

- **块太小**（< 300）：上下文不完整，检索质量下降
- **块太大**（> 1500）：检索不精确，包含过多无关内容
- **重叠太小**（< 50）：跨块信息容易丢失
- **重叠太大**（> 400）：存储冗余，浪费 Embedding 开销

**场景推荐**：

| 场景 | CHUNK_SIZE | CHUNK_OVERLAP |
|------|-----------|---------------|
| FAQ / 简短问答 | 500 | 100 |
| 技术文档（默认） | 800 | 200 |
| 长篇白皮书 / 架构文档 | 1200 | 300 |

### 6.2 搜索返回数量

```bash
MAX_SEARCH_RESULTS=5
```

- 每次知识库检索最多返回的结果数
- 更多结果 → 更全面的上下文，但增加 LLM 输入 token 消耗
- 推荐范围：3-10

---

## 7. 应用服务配置

### 7.1 监听地址和端口

```bash
APP_HOST=0.0.0.0
APP_PORT=8000
```

| 参数 | 说明 |
|------|------|
| `APP_HOST=0.0.0.0` | 监听所有网络接口（允许外部访问） |
| `APP_HOST=127.0.0.1` | 仅监听本地（更安全，适合开发） |
| `APP_PORT=8000` | 服务端口号，避免与其他服务冲突 |

### 7.2 调试模式

```bash
APP_DEBUG=true
```

| 值 | 效果 |
|----|------|
| `true` | 开启热重载（代码修改后自动重启），适合开发 |
| `false` | 关闭热重载，适合生产环境 |

> **生产环境务必设置为 `false`**。

### 7.3 日志级别

```bash
LOG_LEVEL=INFO
```

| 级别 | 说明 | 使用场景 |
|------|------|----------|
| `DEBUG` | 最详细，包含每次检索和 LLM 调用 | 排查问题 |
| `INFO` | 标准信息（启动、请求、导入） | **推荐日常使用** |
| `WARNING` | 仅警告和错误 | 生产环境（最小日志） |
| `ERROR` | 仅错误信息 | 生产环境（仅报错） |

---

## 8. 场景模块时间限制配置

每个场景模块有独立的时间限制设置。时间限制用于追踪处理耗时（记录在响应中的 `processing_time_seconds` 字段）。

```bash
TROUBLESHOOTING_TIME_LIMIT=600    # 技术排查：10 分钟
TECH_QA_TIME_LIMIT=180            # 技术问答：3 分钟
WEEKLY_REPORT_TIME_LIMIT=300      # 周报生成：5 分钟
BRIEFING_TIME_LIMIT=900           # 汇报生成：15 分钟
ESCALATION_TIME_LIMIT=600         # 问题升级：10 分钟
```

单位为秒。可按实际需要调整：

| 场景 | 默认限制 | 建议范围 | 说明 |
|------|----------|----------|------|
| 技术排查 | 600s (10min) | 300-900 | 复杂问题可适当延长 |
| 技术问答 | 180s (3min) | 60-300 | 简单问答可缩短 |
| 周报生成 | 300s (5min) | 120-600 | 内容多时可延长 |
| 汇报生成 | 900s (15min) | 300-1800 | PPT 内容较多时可延长 |
| 问题升级 | 600s (10min) | 300-900 | 日志多时可延长 |

---

## 9. URL 抓取配置

### 9.1 超时设置

```bash
URL_FETCH_TIMEOUT=30
```

- 单位：秒
- 指从发起请求到获得响应的最大等待时间
- 国内网络访问国外网站时，建议增大到 `60`

### 9.2 User-Agent

```bash
URL_USER_AGENT=AIWorkAssistant/1.0
```

- 部分网站会根据 User-Agent 过滤爬虫请求
- 如果导入失败（返回 403），可尝试改为浏览器 User-Agent：

```bash
URL_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
```

---

## 10. 种子数据与 Bootstrap 配置

### 10.1 种子数据目录

```bash
SEED_DATA_DIR=./data/seed
```

系统在 Bootstrap 时会读取此目录下所有 `.json` 文件。

### 10.2 JSON 文件格式

每个 JSON 文件是一个数组，每条记录包含：

```json
[
  {
    "title": "文档标题",
    "content": "文档正文内容，可以很长...",
    "document_type": "faq"
  }
]
```

`document_type` 可选值：`faq`、`troubleshooting`、`architecture`、`deployment`、`api`、`overview`、`whitepaper`、`general` 等。

### 10.3 初始化记录数

```bash
BOOTSTRAP_RECORD_COUNT=1000
```

- 系统会先加载种子文件，再生成合成数据
- 所有内容经分块后，截取前 `BOOTSTRAP_RECORD_COUNT` 条写入数据库
- 增大此数字可以获得更丰富的初始知识库

### 10.4 添加自定义种子数据

在 `data/seed/` 目录下创建新的 JSON 文件，例如 `my_company_docs.json`：

```json
[
  {
    "title": "公司内部部署规范",
    "content": "详细内容...",
    "document_type": "deployment"
  },
  {
    "title": "常见客户问题汇总",
    "content": "详细内容...",
    "document_type": "faq"
  }
]
```

然后调用 Bootstrap 接口重新初始化：

```bash
# 先清空旧数据（可选）
rm -rf ./data/chroma_db

# 重新初始化
curl -X POST http://localhost:8000/knowledge/bootstrap
```

---

## 11. 生产环境部署建议

### 11.1 推荐配置

```bash
# .env — 生产环境配置

OPENAI_API_KEY=sk-your-production-key
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536

CHROMA_PERSIST_DIR=/data/ai-assistant/chroma_db
CHROMA_COLLECTION_NAME=ai_work_assistant

APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=false
LOG_LEVEL=WARNING

CHUNK_SIZE=800
CHUNK_OVERLAP=200
MAX_SEARCH_RESULTS=5

SEED_DATA_DIR=./data/seed
BOOTSTRAP_RECORD_COUNT=1000

URL_FETCH_TIMEOUT=60
URL_USER_AGENT=AIWorkAssistant/1.0
```

### 11.2 使用 Gunicorn 多 Worker 部署

```bash
pip install gunicorn

gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 300 \
  --access-logfile /var/log/ai-assistant/access.log \
  --error-logfile /var/log/ai-assistant/error.log
```

### 11.3 Systemd 服务文件

创建 `/etc/systemd/system/ai-work-assistant.service`：

```ini
[Unit]
Description=AI Work Assistant
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/ai-work-assistant
EnvironmentFile=/opt/ai-work-assistant/.env
ExecStart=/opt/ai-work-assistant/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用并启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-work-assistant
sudo systemctl start ai-work-assistant
sudo systemctl status ai-work-assistant
```

### 11.4 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name ai-assistant.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;    # 场景模块可能耗时较长
        proxy_send_timeout 300s;
    }
}
```

### 11.5 定时备份

```bash
# crontab -e
# 每天凌晨 2 点备份 ChromaDB 数据
0 2 * * * cp -r /data/ai-assistant/chroma_db /backup/chroma_db_$(date +\%Y\%m\%d)
# 保留最近 7 天备份
0 3 * * * find /backup -name "chroma_db_*" -mtime +7 -exec rm -rf {} \;
```

---

## 12. 常见配置问题排查

### 12.1 启动报错 `OPENAI_API_KEY` 为空

**现象**：`/health` 返回 `"openai_configured": false`

**原因**：`.env` 文件未创建或 Key 未填写

**解决**：
```bash
cp .env.example .env
# 编辑 .env，填入真实的 OPENAI_API_KEY
```

### 12.2 ChromaDB 权限错误

**现象**：`PermissionError: [Errno 13] Permission denied: './data/chroma_db'`

**解决**：
```bash
mkdir -p ./data/chroma_db
chmod 755 ./data/chroma_db
```

### 12.3 Embedding 模型更换后搜索不准

**原因**：旧向量和新向量维度/空间不一致

**解决**：清空重建知识库
```bash
rm -rf ./data/chroma_db
python main.py
curl -X POST http://localhost:8000/knowledge/bootstrap
```

### 12.4 URL 导入返回空内容

**可能原因**：
1. 目标网站需要 JavaScript 渲染（SPA 页面）— trafilatura 无法处理
2. 网站反爬封禁了默认 User-Agent
3. 网络超时

**解决**：
- 更换 `URL_USER_AGENT` 为浏览器 UA
- 增大 `URL_FETCH_TIMEOUT`
- 对于 SPA 页面，手动复制内容保存为 `.md` 文件后通过文件导入

### 12.5 端口被占用

**现象**：`Address already in use`

**解决**：
```bash
# 查看占用进程
lsof -i :8000
# 修改端口
# .env 中设置 APP_PORT=8001
```

### 12.6 LLM 调用超时

**现象**：场景模块响应时间很长或超时

**解决**：
- 确认网络到 OpenAI API 的连通性
- 如使用代理，确认代理配置正确
- 可尝试切换到 `gpt-4o-mini` 获取更快的响应速度

---

> **下一步**：配置完成后，请参阅 [《平台使用指南》](./USAGE_GUIDE.md) 了解如何使用各项功能。
