# 部署指南 — AI Work Assistant

> 将 AI Work Assistant 部署到 CPU 云服务器，通过浏览器远程访问。

---

## 目录

1. [服务器要求](#1-服务器要求)
2. [服务器初始化](#2-服务器初始化)
3. [项目部署](#3-项目部署)
4. [配置环境变量](#4-配置环境变量)
5. [初始化知识库](#5-初始化知识库)
6. [Systemd 服务管理](#6-systemd-服务管理)
7. [Nginx 反向代理](#7-nginx-反向代理)
8. [SSL 证书 (HTTPS)](#8-ssl-证书-https)
9. [防火墙配置](#9-防火墙配置)
10. [ZStack 内部文档接入](#10-zstack-内部文档接入)
11. [网络架构总览](#11-网络架构总览)
12. [运维管理](#12-运维管理)
13. [常见问题排查](#13-常见问题排查)

---

## 1. 服务器要求

### 最低配置（CPU 云服务器）

| 项目 | 要求 | 说明 |
|------|------|------|
| CPU | 2 核+ | 所有 AI 推理由 OpenAI API 完成，服务器仅做 API 转发 |
| 内存 | 4 GB+ | ChromaDB + FastAPI 运行所需 |
| 磁盘 | 40 GB+ | 系统 + 项目 + ChromaDB 数据 + 日志 |
| 操作系统 | Ubuntu 22.04 LTS / CentOS 8+ / Debian 12 | 推荐 Ubuntu 22.04 |
| Python | 3.12+ | 必须（推荐通过 mise 管理版本） |
| 网络 | 公网 IP + 开放 80/443 端口 | 浏览器访问需要 |

### 网络要求

- **入站**：80（HTTP）、443（HTTPS）开放给用户
- **出站**：443（HTTPS）可达 `api.openai.com`（或你的 OpenAI 兼容 API 地址）
- **内部**：8000 端口仅 localhost 监听，由 Nginx 代理

> **重要**：系统的 AI 推理通过 OpenAI API 远程完成，服务器本身不需要 GPU。需确保服务器能访问 OpenAI API。

---

## 2. 服务器初始化

### Ubuntu 22.04

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y build-essential curl wget git nginx certbot python3-certbot-nginx

# 安装 Python 3.12+
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip

# 验证版本
python3.12 --version
nginx -v
```

### CentOS 8+ / Rocky Linux

```bash
sudo dnf update -y
sudo dnf install -y gcc make curl wget git nginx certbot python3-certbot-nginx
sudo dnf install -y python3.12 python3.12-devel python3.12-pip
```

### 创建应用用户（推荐）

```bash
# 创建专用用户，避免用 root 运行服务
sudo useradd -m -s /bin/bash aiassist
sudo passwd aiassist

# 将用户加入 www-data 组（Nginx 需要读取静态文件）
sudo usermod -aG www-data aiassist
```

---

## 3. 项目部署

### 方式一：从 Git 拉取

```bash
# 切换到应用用户
sudo su - aiassist

# 克隆项目
git clone <your-repo-url> ~/ai-work-assistant
cd ~/ai-work-assistant
```

### 方式二：手动上传

```bash
# 从本地机器打包上传
# （在本地执行）
tar czf ai-work-assistant.tar.gz --exclude='data/chroma_db' --exclude='__pycache__' --exclude='.env' --exclude='venv' .
scp ai-work-assistant.tar.gz user@your-server-ip:~/

# （在服务器执行）
sudo su - aiassist
mkdir -p ~/ai-work-assistant
cd ~/ai-work-assistant
tar xzf ~/ai-work-assistant.tar.gz
rm ~/ai-work-assistant.tar.gz
```

### 安装 Python 依赖

```bash
cd ~/ai-work-assistant

# 方式一：使用 uv（推荐，更快）
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# 方式二：传统 pip
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 验证安装
python -c "import fastapi; import chromadb; print('OK')"
```

---

## 4. 配置环境变量

```bash
cd ~/ai-work-assistant

# 复制模板
cp .env.example .env

# 编辑配置
nano .env
```

### 必须配置

```env
# OpenAI API Key（必填）
OPENAI_API_KEY=sk-your-actual-key-here

# 如果使用代理或兼容 API（如 Azure OpenAI、国内中转等）
OPENAI_BASE_URL=https://api.openai.com/v1

# 生产环境设置
APP_DEBUG=false
LOG_LEVEL=INFO
```

### 生产环境推荐配置

```env
# OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small

# App
APP_HOST=127.0.0.1
APP_PORT=8000
APP_DEBUG=false
LOG_LEVEL=INFO

# ChromaDB
CHROMA_PERSIST_DIR=./data/chroma_db
CHROMA_COLLECTION_NAME=ai_work_assistant

# Knowledge Base
CHUNK_SIZE=800
CHUNK_OVERLAP=200
MAX_SEARCH_RESULTS=5

# Bootstrap
SEED_DATA_DIR=./data/seed
BOOTSTRAP_RECORD_COUNT=1000
```

> **关键**：生产环境 `APP_HOST` 应设为 `127.0.0.1`，仅监听本地，由 Nginx 反向代理对外服务。

### 验证配置

```bash
source venv/bin/activate
python -c "from config import get_settings; s = get_settings(); print(f'API Key: {s.openai_api_key[:8]}...' if s.openai_api_key else 'NO KEY SET')"
```

---

## 5. 初始化知识库

```bash
cd ~/ai-work-assistant
source venv/bin/activate

# 先测试启动
python main.py &

# 等待 2 秒启动完成
sleep 2

# 初始化种子数据（~1000 条）
curl -X POST http://127.0.0.1:8000/knowledge/bootstrap

# 验证
curl http://127.0.0.1:8000/knowledge/stats

# 验证健康状态
curl http://127.0.0.1:8000/health

# 停止测试进程
kill %1
```

---

## 6. Systemd 服务管理

### 创建服务文件

```bash
sudo tee /etc/systemd/system/ai-work-assistant.service << 'EOF'
[Unit]
Description=AI Work Assistant - Personal AI Work Assistant System
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=aiassist
Group=aiassist
WorkingDirectory=/home/aiassist/ai-work-assistant
Environment="PATH=/home/aiassist/ai-work-assistant/venv/bin:/usr/bin:/bin"
ExecStart=/home/aiassist/ai-work-assistant/venv/bin/python main.py
Restart=always
RestartSec=5

# 日志
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ai-work-assistant

# 安全限制
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/home/aiassist/ai-work-assistant/data
ProtectHome=read-only

# 资源限制
MemoryMax=2G
CPUQuota=150%

[Install]
WantedBy=multi-user.target
EOF
```

### 启动服务

```bash
# 重载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start ai-work-assistant

# 设置开机自启
sudo systemctl enable ai-work-assistant

# 查看状态
sudo systemctl status ai-work-assistant

# 查看日志
sudo journalctl -u ai-work-assistant -f
```

### 常用管理命令

```bash
# 重启
sudo systemctl restart ai-work-assistant

# 停止
sudo systemctl stop ai-work-assistant

# 查看最近 100 行日志
sudo journalctl -u ai-work-assistant -n 100

# 查看今日日志
sudo journalctl -u ai-work-assistant --since today
```

---

## 7. Nginx 反向代理

### 创建 Nginx 配置

```bash
sudo tee /etc/nginx/sites-available/ai-work-assistant << 'EOF'
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名或公网IP

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 上传文件大小限制
    client_max_body_size 50M;

    # 请求超时（场景生成可能较慢）
    proxy_connect_timeout 60s;
    proxy_send_timeout 120s;
    proxy_read_timeout 300s;  # 5 分钟 — 某些场景如汇报生成需要较长时间
    send_timeout 120s;

    # 反向代理到 FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 支持 WebSocket（如后续扩展）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 静态文件缓存（CSS/JS/图片）
    location /static/ {
        proxy_pass http://127.0.0.1:8000/static/;
        proxy_cache_valid 200 1d;
        add_header Cache-Control "public, max-age=86400";
    }

    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
EOF
```

### 启用配置

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/ai-work-assistant /etc/nginx/sites-enabled/

# 删除默认配置（可选）
sudo rm -f /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
sudo systemctl enable nginx
```

### 如果使用 IP 直接访问（无域名）

将 `server_name your-domain.com` 改为 `server_name _;` 或改为你的公网 IP：

```nginx
server_name 123.45.67.89;  # 你的公网IP
```

---

## 8. SSL 证书 (HTTPS)

### 方式一：Let's Encrypt（免费，需要域名）

```bash
# 申请证书（自动修改 Nginx 配置）
sudo certbot --nginx -d your-domain.com

# 测试自动续期
sudo certbot renew --dry-run

# 自动续期由 certbot 的 systemd timer 管理
sudo systemctl status certbot.timer
```

### 方式二：自签名证书（适合内网 / IP 访问）

```bash
# 生成自签名证书
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/ai-assistant.key \
  -out /etc/nginx/ssl/ai-assistant.crt \
  -subj "/CN=AI Work Assistant"
```

然后修改 Nginx 配置：

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/ai-assistant.crt;
    ssl_certificate_key /etc/nginx/ssl/ai-assistant.key;

    # ... 其余配置同上 ...
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}
```

---

## 9. 防火墙配置

### UFW（Ubuntu 默认）

```bash
# 启用防火墙
sudo ufw enable

# 允许 SSH（重要！先加这条，否则可能被锁在外面）
sudo ufw allow 22/tcp

# 允许 HTTP 和 HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 不要暴露 8000 端口（由 Nginx 代理，仅本地监听）
# sudo ufw deny 8000/tcp  # 可选，因为 APP_HOST=127.0.0.1 已经限制了

# 查看状态
sudo ufw status verbose
```

### 预期的开放端口

```
端口    协议    来源        用途
22      TCP     管理 IP     SSH 远程管理
80      TCP     所有        HTTP（重定向到 HTTPS）
443     TCP     所有        HTTPS（主要访问入口）
```

> **注意**：8000 端口不对外暴露。FastAPI 绑定 `127.0.0.1:8000`，仅接受来自 Nginx 的本地转发请求。

### 云服务商安全组

除了服务器防火墙，还需要在云服务商控制台配置安全组（入站规则）：

| 方向 | 端口 | 协议 | 来源 | 说明 |
|------|------|------|------|------|
| 入站 | 22 | TCP | 你的 IP | SSH 管理 |
| 入站 | 80 | TCP | 0.0.0.0/0 | HTTP |
| 入站 | 443 | TCP | 0.0.0.0/0 | HTTPS |
| 出站 | 443 | TCP | 0.0.0.0/0 | 访问 OpenAI API |

---

## 10. ZStack 内部文档接入

系统部署到云服务器后，有多种方式导入 ZStack 内部文档：

### 方式一：通过 Web 界面上传文件

1. 浏览器打开 `https://your-domain.com/ui`
2. 点击左侧「知识库」
3. 选择「文件上传」标签页
4. 拖拽或选择文件（支持 `.md` `.txt` `.html` `.json` `.yaml` `.rst` `.csv`）
5. 选择文档类型（如 `product_doc`、`faq`、`troubleshooting`）
6. 点击「上传」

### 方式二：通过 URL 导入在线文档

```bash
# 使用 API 导入 ZStack 在线文档
curl -X POST https://your-domain.com/knowledge/ingest/url \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://www.zstack.io/help/product_manuals/V4/4/5.html",
      "https://www.zstack.io/help/product_manuals/V4/4/6.html"
    ],
    "document_type": "product_doc",
    "force_refresh": false
  }'
```

或使用 Web 界面的「URL 导入」功能。

### 方式三：批量上传文件到服务器

```bash
# 本地准备文档目录
# docs/
#   ├── zstack-architecture.md
#   ├── zstack-storage-guide.md
#   └── ...

# SCP 上传到服务器
scp -r docs/ aiassist@your-server:~/ai-work-assistant/data/docs/

# 在服务器上使用 API 批量导入
ssh aiassist@your-server
cd ~/ai-work-assistant
source venv/bin/activate

# 使用文件导入 API（逐个）
for f in data/docs/*.md; do
  curl -X POST http://127.0.0.1:8000/knowledge/ingest/file \
    -H "Content-Type: application/json" \
    -d "{\"file_path\": \"$f\", \"document_type\": \"product_doc\"}"
done
```

### 方式四：定时刷新 URL 文档

创建 cron 定时任务，定期更新 ZStack 在线文档内容：

```bash
# 编辑 crontab
crontab -e

# 每周日凌晨 3 点刷新知识库中的 URL 内容
0 3 * * 0 curl -X POST http://127.0.0.1:8000/knowledge/refresh/url -H "Content-Type: application/json" -d '{"urls": ["https://www.zstack.io/help/..."], "force_refresh": true}' >> /home/aiassist/refresh.log 2>&1
```

### 文档读取验证

部署后，验证知识库中的 ZStack 文档可以被正确检索：

```bash
# 搜索测试
curl -X POST https://your-domain.com/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query": "ZStack 存储架构", "top_k": 3}'

# 技术问答测试（会自动检索知识库）
curl -X POST https://your-domain.com/scenario/tech_qa \
  -H "Content-Type: application/json" \
  -d '{"question": "ZStack支持哪些存储方案？", "product": "ZStack Cloud"}'
```

---

## 11. 网络架构总览

```
                        ┌─────────────────┐
  用户浏览器  ──HTTPS──▶ │   Nginx (:443)  │
  (任意位置)             │   反向代理       │
                        └────────┬────────┘
                                 │ proxy_pass
                                 ▼
                        ┌─────────────────┐
                        │ FastAPI (:8000)  │──▶ 静态文件 (web/)
                        │ 127.0.0.1 only  │──▶ API 路由
                        └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼             ▼
            ┌──────────┐  ┌──────────┐  ┌───────────┐
            │ ChromaDB │  │ OpenAI   │  │ URL Fetch │
            │ 本地文件  │  │ API      │  │ 外部文档  │
            │ 向量存储  │  │ GPT-4o   │  │ ZStack等  │
            └──────────┘  └──────────┘  └───────────┘
```

### 请求流转

1. 用户通过浏览器访问 `https://your-domain.com/ui`
2. Nginx 接收请求，SSL 终止
3. Nginx 将请求转发到 `127.0.0.1:8000`
4. FastAPI 处理请求：
   - 访问 `/ui` → 返回 `web/index.html`
   - 访问 `/static/*` → 返回 CSS/JS 静态文件
   - API 请求 → 执行业务逻辑
5. 场景模块调用 OpenAI API（出站 HTTPS）
6. 知识库检索从本地 ChromaDB 获取
7. 结果返回浏览器渲染

---

## 12. 运维管理

### 日志查看

```bash
# 实时日志
sudo journalctl -u ai-work-assistant -f

# 最近错误
sudo journalctl -u ai-work-assistant -p err --since "1 hour ago"

# Nginx 访问日志
sudo tail -f /var/log/nginx/access.log

# Nginx 错误日志
sudo tail -f /var/log/nginx/error.log
```

### 数据备份

```bash
# 备份知识库
tar czf backup-chroma-$(date +%Y%m%d).tar.gz -C /home/aiassist/ai-work-assistant/data chroma_db

# 备份配置
cp /home/aiassist/ai-work-assistant/.env backup-env-$(date +%Y%m%d)

# 自动备份 cron（每天凌晨 2 点）
echo "0 2 * * * tar czf /home/aiassist/backups/chroma-\$(date +\%Y\%m\%d).tar.gz -C /home/aiassist/ai-work-assistant/data chroma_db" | crontab -
```

### 更新部署

```bash
# 方式一：Git 拉取更新
cd ~/ai-work-assistant
git pull origin main
source venv/bin/activate
pip install -r requirements.txt    # 或 uv sync
sudo systemctl restart ai-work-assistant

# 方式二：手动上传更新
# 本地打包 → scp → 解压 → 重启服务
```

### 监控建议

- **系统资源**：可安装 `htop`、`iotop` 监控 CPU / 内存 / 磁盘
- **服务状态**：`systemctl status ai-work-assistant`
- **API 健康**：定时 `curl https://your-domain.com/health`
- **磁盘空间**：`df -h`（关注 ChromaDB 数据增长）

---

## 13. 常见问题排查

### 问题：访问页面显示 502 Bad Gateway

**原因**：FastAPI 服务未启动或崩溃

```bash
# 检查服务状态
sudo systemctl status ai-work-assistant

# 查看最近日志
sudo journalctl -u ai-work-assistant -n 50

# 常见原因：
# 1. .env 文件缺失或 OpenAI API Key 未配置
# 2. Python 依赖未安装
# 3. 端口被占用

# 尝试手动启动查看详细错误
cd ~/ai-work-assistant
source venv/bin/activate
python main.py
```

### 问题：场景请求超时

**原因**：OpenAI API 响应慢或 Nginx 超时配置过短

```bash
# 确认 Nginx proxy_read_timeout 已设为 300s
sudo grep proxy_read_timeout /etc/nginx/sites-available/ai-work-assistant

# 如果仍然超时，可以增加到 600s
```

### 问题：知识库搜索无结果

```bash
# 检查知识库是否初始化
curl http://127.0.0.1:8000/knowledge/stats

# 如果 total_chunks 为 0，需要初始化
curl -X POST http://127.0.0.1:8000/knowledge/bootstrap
```

### 问题：无法访问 OpenAI API

```bash
# 测试网络连通性
curl -v https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 如果被墙，考虑：
# 1. 使用代理：在 .env 中配置 OPENAI_BASE_URL 指向代理地址
# 2. 使用国内兼容 API（如 Azure OpenAI）
# 3. 服务器使用境外节点
```

### 问题：文件上传失败

```bash
# 检查 Nginx 上传限制
sudo grep client_max_body_size /etc/nginx/sites-available/ai-work-assistant
# 应为 50M 或更大

# 检查文件格式是否支持
# 支持: .md .txt .html .htm .json .yaml .yml .rst .csv
```

### 问题：服务器重启后服务未自动启动

```bash
# 确认 enable 了自启动
sudo systemctl is-enabled ai-work-assistant
# 应输出 "enabled"

# 如果不是
sudo systemctl enable ai-work-assistant
```

---

## 快速部署检查清单

部署完成后，逐项验证：

- [ ] Python 3.12+ 已安装
- [ ] 依赖已安装（`uv sync` 或 `pip install -r requirements.txt`）
- [ ] `.env` 文件已配置（OpenAI API Key）
- [ ] `APP_HOST=127.0.0.1`（生产环境）
- [ ] Systemd 服务已创建并 enabled
- [ ] 服务正常运行：`systemctl status ai-work-assistant`
- [ ] Nginx 配置已创建并启用
- [ ] Nginx 配置测试通过：`nginx -t`
- [ ] SSL 证书已配置（HTTPS）
- [ ] 防火墙仅开放 22/80/443
- [ ] 云安全组规则已配置
- [ ] 知识库已初始化（bootstrap）
- [ ] 浏览器可访问：`https://your-domain.com/ui`
- [ ] 场景模块可正常使用
- [ ] ZStack 文档已导入且可搜索
- [ ] 自动备份已配置
