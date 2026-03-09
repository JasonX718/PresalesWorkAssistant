# AI Work Assistant — 平台使用指南

---

## 目录

1. [快速上手](#1-快速上手)
2. [知识库管理](#2-知识库管理)
3. [场景模块使用](#3-场景模块使用)
4. [输出模式说明](#4-输出模式说明)
5. [自动场景识别](#5-自动场景识别)
6. [实战案例](#6-实战案例)
7. [进阶用法](#7-进阶用法)
8. [API 接口速查表](#8-api-接口速查表)

---

## 1. 快速上手

### 1.1 启动系统

```bash
# 确保已完成配置（参考《系统配置指南》）
python main.py
```

系统启动后，可以通过以下方式访问：

| 访问方式 | 地址 | 说明 |
|----------|------|------|
| Swagger 文档 | http://localhost:8000/docs | 可视化交互，推荐新手使用 |
| ReDoc 文档 | http://localhost:8000/redoc | 可读性更好的 API 文档 |
| 命令行 curl | http://localhost:8000 | 脚本集成和自动化 |
| Python 脚本 | `examples/` 目录 | 完整调用示例 |

### 1.2 初始化知识库

首次使用 **必须** 先初始化知识库：

```bash
curl -X POST http://localhost:8000/knowledge/bootstrap
```

返回示例：

```json
{
  "total_records": 73,
  "chunks_created": 856,
  "errors": [],
  "duration_seconds": 12.35
}
```

初始化完成后，系统已包含约 1000 条 ZStack 相关的知识记录，覆盖架构、运维、FAQ、存储、网络等 10 个领域。

### 1.3 验证系统状态

```bash
curl http://localhost:8000/health
```

正常响应：

```json
{
  "status": "running",
  "vector_db": {
    "status": "healthy",
    "document_count": 856
  },
  "llm_model": "gpt-4o",
  "embedding_model": "text-embedding-3-small",
  "openai_configured": true
}
```

确认 `openai_configured` 为 `true`、`document_count` 大于 0，即可开始使用。

### 1.4 第一次调用

试一个最简单的技术问答：

```bash
curl -X POST http://localhost:8000/scenario/tech_qa \
  -H "Content-Type: application/json" \
  -d '{
    "question": "ZStack支持哪些存储方案？"
  }'
```

系统会从知识库检索相关内容，结合 LLM 生成结构化回答。

---

## 2. 知识库管理

知识库是系统的核心。所有场景模块在生成内容前，都会先从知识库中检索相关信息，确保输出的准确性。

### 2.1 搜索知识库

**GET 方式**（简单查询）：

```bash
curl "http://localhost:8000/knowledge/search?query=ZStack高可用&top_k=3"
```

**POST 方式**（支持过滤）：

```bash
curl -X POST http://localhost:8000/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Ceph存储故障处理",
    "top_k": 5,
    "document_type": "troubleshooting",
    "source_type": "seed"
  }'
```

参数说明：

| 参数 | 类型 | 说明 |
|------|------|------|
| `query` | string | 搜索关键词（必填） |
| `top_k` | int | 返回结果数，1-20，默认 5 |
| `document_type` | string | 按文档类型过滤（如 `faq`、`troubleshooting`） |
| `source_type` | string | 按来源类型过滤（`seed`、`file`、`url`） |

返回结果中每条包含：`content`（内容片段）、`score`（相似度分数，0-1）、`metadata`（来源信息）。

### 2.2 导入本地文件

将本地的 Markdown、文本、HTML 等文件导入知识库：

```bash
curl -X POST http://localhost:8000/knowledge/ingest/file \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/home/user/docs/zstack-v4.6-release-notes.md",
    "document_type": "release_notes",
    "title": "ZStack v4.6 发布说明"
  }'
```

支持的文件格式：`.md`、`.txt`、`.html`、`.htm`、`.json`、`.yaml`、`.yml`、`.rst`、`.csv`

返回示例：

```json
{
  "total_chunks": 12,
  "new_chunks": 12,
  "duplicate_skipped": 0,
  "errors": [],
  "sources_processed": ["/home/user/docs/zstack-v4.6-release-notes.md"]
}
```

### 2.3 导入网页 URL

从网页自动提取内容并导入知识库：

```bash
curl -X POST http://localhost:8000/knowledge/ingest/url \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://www.zstack.io/help/product_manuals/",
      "https://www.zstack.io/help/tutorials/"
    ],
    "document_type": "product_doc",
    "force_refresh": false
  }'
```

参数说明：

| 参数 | 说明 |
|------|------|
| `urls` | URL 列表，支持一次导入多个 |
| `document_type` | 文档分类标签 |
| `force_refresh` | `false`=跳过已导入的 URL；`true`=强制重新抓取 |

**URL 导入处理流程**：

```
提交 URL → HTTP 抓取网页 → 提取正文(去除导航/广告/脚本)
→ 文本清洗 → 去重检查 → 分块 → 生成向量 → 写入数据库
```

### 2.4 刷新 URL 内容

当网页内容更新后，强制重新抓取并替换旧内容：

```bash
curl -X POST http://localhost:8000/knowledge/refresh/url \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://www.zstack.io/help/product_manuals/"],
    "document_type": "product_doc"
  }'
```

此接口会先删除该 URL 的所有旧数据，然后重新导入。

### 2.5 查看知识库文档列表

```bash
curl http://localhost:8000/knowledge/documents
```

返回所有已导入的文档来源及其分块数：

```json
{
  "total": 15,
  "documents": [
    {
      "source": "seed:synthetic:architecture",
      "title": "ZStack Cloud整体架构概述",
      "source_type": "seed",
      "document_type": "architecture",
      "chunk_count": 23
    },
    {
      "source": "https://www.zstack.io/help/tutorials/",
      "title": "ZStack 教程",
      "source_type": "url",
      "document_type": "product_doc",
      "chunk_count": 8
    }
  ]
}
```

### 2.6 查看知识库统计

```bash
curl http://localhost:8000/knowledge/stats
```

```json
{
  "total_chunks": 856,
  "total_sources": 15,
  "source_types": { "seed": 10, "url": 3, "file": 2 },
  "document_types": { "architecture": 3, "troubleshooting": 2, "faq": 3, ... }
}
```

### 2.7 删除文档

删除某个来源的所有内容：

```bash
# 删除某个文件来源
curl -X DELETE "http://localhost:8000/knowledge/document//home/user/docs/old-doc.md"

# 删除某个 URL 来源
curl -X DELETE "http://localhost:8000/knowledge/document/https://example.com/page"
```

### 2.8 去重机制

系统使用两层去重机制，不必担心重复导入：

| 层级 | 机制 | 说明 |
|------|------|------|
| 来源级 | URL/文件路径检查 | 同一来源不重复导入（除非 `force_refresh=true`） |
| 内容级 | xxhash64 内容哈希 | 相同内容即使来自不同来源也不会重复存储 |

---

## 3. 场景模块使用

系统提供 9 个场景模块，覆盖技术岗位的主要工作场景。

### 3.1 模块一览

| 模块 | 接口 | 用途 | 时间限制 |
|------|------|------|----------|
| 技术问题排查 | `POST /scenario/troubleshooting` | 分析故障，给出排查方案 | 10 分钟 |
| 技术问题回答 | `POST /scenario/tech_qa` | 快速回答技术问题 | 3 分钟 |
| 客户答复 | `POST /scenario/customer_reply` | 生成专业客户回复 | — |
| 周报生成 | `POST /scenario/weekly_report` | 自动生成周报 | 5 分钟 |
| 汇报生成 | `POST /scenario/briefing` | 生成汇报/PPT 材料 | 15 分钟 |
| 培训生成 | `POST /scenario/training` | 生成培训课程内容 | — |
| 演示准备 | `POST /scenario/demo_prep` | 准备产品演示方案 | — |
| PoC 支持 | `POST /scenario/poc_support` | 制定 PoC 计划 | — |
| 问题升级 | `POST /scenario/escalation` | 整理升级材料 | 10 分钟 |

### 3.2 技术问题排查

**场景**：客户报告故障、线上告警、系统异常

```bash
curl -X POST http://localhost:8000/scenario/troubleshooting \
  -H "Content-Type: application/json" \
  -d '{
    "problem_description": "客户环境中云主机创建失败，UI提示存储空间不足，但Ceph集群实际使用率只有60%",
    "environment": "ZStack 4.6.0, CentOS 7.9, Ceph Nautilus 14.2.22, 5个OSD节点",
    "error_logs": "org.zstack.header.storage.primary.PrimaryStorageException: not enough capacity on primary storage",
    "affected_component": "PrimaryStorage / Ceph",
    "urgency_level": "high",
    "output_mode": "technical"
  }'
```

**输入字段**：

| 字段 | 必填 | 说明 |
|------|------|------|
| `problem_description` | 是 | 问题描述，越详细越好 |
| `environment` | 否 | 环境信息（版本号、节点数、操作系统等） |
| `error_logs` | 否 | 相关错误日志片段 |
| `affected_component` | 否 | 受影响的组件 |
| `urgency_level` | 否 | `low` / `medium` / `high` / `critical` |
| `output_mode` | 否 | `technical`(默认) / `customer` / `leadership` |

**输出结构**：
1. 问题概述
2. 可能原因 Top 3
3. 排查步骤（含具体命令）
4. 临时止血方案
5. 需要收集的日志
6. 是否建议升级

### 3.3 技术问题回答

**场景**：同事提问、客户技术咨询、自己查资料

```bash
curl -X POST http://localhost:8000/scenario/tech_qa \
  -H "Content-Type: application/json" \
  -d '{
    "question": "ZStack支持在线迁移吗？需要什么前提条件？本地存储能迁移吗？",
    "context": "客户要求在不停机的情况下进行物理机维护",
    "product": "ZStack Cloud",
    "output_mode": "technical"
  }'
```

**输入字段**：

| 字段 | 必填 | 说明 |
|------|------|------|
| `question` | 是 | 技术问题 |
| `context` | 否 | 补充上下文 |
| `product` | 否 | 相关产品，默认 `ZStack` |
| `output_mode` | 否 | 默认 `technical` |

**输出结构**：结论 → 技术解释 → 适用条件 → 注意事项

### 3.4 客户答复

**场景**：回复客户邮件、微信群答复、售前咨询

```bash
curl -X POST http://localhost:8000/scenario/customer_reply \
  -H "Content-Type: application/json" \
  -d '{
    "customer_question": "我们公司有200台VMware虚拟机，想迁移到ZStack，迁移难度大吗？需要停机吗？",
    "context": "客户是制造业企业，IT团队5人，没有开源云平台经验，预算200万",
    "product": "ZStack Cloud",
    "output_mode": "customer"
  }'
```

**输入字段**：

| 字段 | 必填 | 说明 |
|------|------|------|
| `customer_question` | 是 | 客户原始问题 |
| `context` | 否 | 客户背景、行业、规模等 |
| `product` | 否 | 默认 `ZStack` |
| `output_mode` | 否 | 默认 `customer`（自动切换为客户模式） |

**输出结构**：客户问题复述 → 问题解释 → 适用条件 → 风险说明 → 建议下一步

> **特点**：语气专业友好，避免过度承诺，不暴露内部细节。

### 3.5 周报生成

**场景**：每周五写周报

```bash
curl -X POST http://localhost:8000/scenario/weekly_report \
  -H "Content-Type: application/json" \
  -d '{
    "tasks_completed": [
      "完成客户A的ZStack Cloud PoC环境部署和验收",
      "处理了3个技术支持工单（网络、存储、迁移）",
      "参加ZStack 4.7新版本培训并通过考试",
      "编写了Ceph存储最佳实践文档"
    ],
    "major_results": [
      "客户A PoC成功通过验收，预计下月签约（合同金额80万）",
      "工单平均处理时间从4小时缩短到2.5小时"
    ],
    "issues": [
      "客户B的VPC网络偶现延迟问题，正在与研发排查",
      "测试环境Ceph集群有一个OSD频繁报慢，疑似磁盘问题"
    ],
    "next_week_plan": [
      "准备客户C的技术方案汇报（周三）",
      "跟进客户A的商务流程",
      "完成ZStack 4.7新功能测试报告"
    ],
    "report_version": "leadership"
  }'
```

**输入字段**：

| 字段 | 必填 | 说明 |
|------|------|------|
| `tasks_completed` | 否 | 本周完成的工作列表 |
| `major_results` | 否 | 关键成果列表 |
| `issues` | 否 | 当前问题和风险 |
| `next_week_plan` | 否 | 下周计划列表 |
| `report_version` | 否 | 版本：`standard`(标准) / `leadership`(领导版) / `technical`(技术版) |

**三种版本差异**：

| 版本 | 特点 | 适合对象 |
|------|------|----------|
| `standard` | 完整结构化周报 | 团队内部分享 |
| `leadership` | 精简，300字以内，突出数据 | **给领导看** |
| `technical` | 详细技术内容，含问题跟踪表 | 技术团队 |

### 3.6 汇报生成

**场景**：准备 PPT 汇报、项目进展报告

```bash
curl -X POST http://localhost:8000/scenario/briefing \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "ZStack私有云方案在制造业的应用实践",
    "audience": "客户CTO和IT总监",
    "goal": "说服客户选择ZStack替换VMware，重点强调成本优势和国产化",
    "time_limit": 20,
    "output_mode": "leadership"
  }'
```

**输出**：汇报结构 → 每页核心内容 → 建议图示 → 演讲提示

### 3.7 培训生成

**场景**：准备内部培训、客户培训

```bash
curl -X POST http://localhost:8000/scenario/training \
  -H "Content-Type: application/json" \
  -d '{
    "training_topic": "ZStack Cloud网络架构与VPC配置",
    "audience_level": "intermediate",
    "duration": 90,
    "output_mode": "technical"
  }'
```

**`audience_level` 取值**：`beginner`（入门）/ `intermediate`（中级）/ `advanced`（高级）

**输出**：培训目标 → 核心知识点 → 架构说明 → 培训大纲 → 演示流程 → 常见问题

### 3.8 演示准备

**场景**：给客户做产品 Demo

```bash
curl -X POST http://localhost:8000/scenario/demo_prep \
  -H "Content-Type: application/json" \
  -d '{
    "demo_product": "ZStack Cloud",
    "scenario": "向金融客户演示VPC网络隔离和安全组功能",
    "audience": "银行IT架构师和安全团队",
    "time_limit": 30
  }'
```

**输出**：演示目标 → 演示流程表 → 关键说明点 → 容易出问题的环节 → 备选方案 → 检查清单

### 3.9 PoC 支持

**场景**：为客户设计 PoC 方案

```bash
curl -X POST http://localhost:8000/scenario/poc_support \
  -H "Content-Type: application/json" \
  -d '{
    "customer_requirements": "客户需要验证：50台云主机并发创建、Ceph存储性能达到5000 IOPS、VPC网络隔离、与AD域集成",
    "product_scope": "ZStack Cloud Enterprise 4.6",
    "constraints": "PoC周期2周，客户提供3台服务器，网络环境已就绪"
  }'
```

**输出**：需求分析 → 架构方案 → 实施步骤 → 风险评估 → 验证指标 → 资源需求

### 3.10 问题升级

**场景**：排查不了的问题需要升级给研发/高级支持

```bash
curl -X POST http://localhost:8000/scenario/escalation \
  -H "Content-Type: application/json" \
  -d '{
    "problem": "客户生产环境管理节点每天OOM重启2-3次，已持续一周",
    "environment": "ZStack 4.5.0, 双管理节点HA, MySQL Galera集群, 20台物理机, 300台云主机",
    "logs": "java.lang.OutOfMemoryError: Java heap space\n  at org.zstack.core.thread.ThreadFacadeImpl...\n2025-03-08 14:23:15 管理节点自动重启",
    "attempted_actions": [
      "检查MySQL连接数 — 正常，峰值120/500",
      "增加JVM堆内存从4G到8G — 重启频率降低但未完全解决",
      "排查RabbitMQ消息队列 — 未发现消息堆积",
      "检查定时任务 — 发现每天14点执行全量资源同步",
      "分析heap dump — 发现大量TaskProgress对象未释放"
    ]
  }'
```

**输出**：问题概述 → 环境信息表 → 已排查步骤表 → 未确认问题 → 关键日志 → 升级建议 → 附件清单

---

## 4. 输出模式说明

每个场景模块都支持通过 `output_mode` 参数指定输出风格。同样的输入，不同模式生成的内容完全不同。

### 4.1 三种模式对比

| 模式 | `output_mode` 值 | 面向对象 | 风格特点 |
|------|-------------------|----------|----------|
| 客户模式 | `customer` | 客户 / 合作方 | 专业友好、避免术语、不过度承诺 |
| 技术模式 | `technical` | 工程师 / 技术团队 | 精确术语、含命令和配置、强调原理 |
| 领导模式 | `leadership` | 管理层 / 领导 | 简洁量化、结论先行、突出风险和决策 |

### 4.2 同一问题的三种输出示例

**问题**："ZStack 云主机无法创建，报存储空间不足"

**客户模式** (`output_mode: "customer"`)：
> 关于您反馈的云主机创建问题，经过我们初步分析，该问题与存储系统的容量管理有关。建议您的运维团队先确认存储使用情况，我们也会安排工程师协助远程排查...

**技术模式** (`output_mode: "technical"`)：
> 问题根因：PrimaryStorage 容量校验使用的是 ZStack 管理面的已分配容量而非 Ceph 实际使用容量。
> 排查命令：`zstack-cli QueryPrimaryStorage fields=uuid,totalCapacity,availableCapacity`
> 对比 Ceph 实际：`ceph df`

**领导模式** (`output_mode: "leadership"`)：
> **状态**：客户环境云主机创建受阻
> **影响**：新业务无法上线
> **原因**：存储容量统计偏差
> **预计恢复**：2小时内

### 4.3 各模块的默认输出模式

| 模块 | 默认模式 | 说明 |
|------|----------|------|
| 技术排查 | `technical` | 面向工程师的排查方案 |
| 技术问答 | `technical` | 技术详细回答 |
| 客户答复 | `customer` | 自动切换为客户模式 |
| 周报 | `leadership` | 默认给领导的版本 |
| 汇报 | `leadership` | 面向管理层 |
| 培训 | `technical` | 面向技术学员 |
| 演示准备 | `technical` | 面向演示工程师 |
| PoC | `technical` | 技术方案 |
| 问题升级 | `technical` | 面向高级支持 |

---

## 5. 自动场景识别

当你不确定该用哪个模块时，可以使用自动识别接口，系统会根据输入内容自动选择最合适的场景。

### 5.1 使用方式

```bash
curl -X POST http://localhost:8000/scenario/auto \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "客户问ZStack能不能对接他们现有的VMware vCenter，实现统一管理",
    "output_mode": "customer"
  }'
```

### 5.2 识别逻辑

系统采用两级识别策略：

1. **关键词匹配**（优先、快速）：
   - 包含"故障""报错""排查" → 技术排查
   - 包含"怎么""如何""什么是" → 技术问答
   - 包含"客户""回复""答复" → 客户答复
   - 包含"周报""本周" → 周报生成
   - 包含"升级""转交" → 问题升级
   - ...

2. **LLM 智能判断**（兜底）：当关键词匹配不自信时，调用 LLM 理解语义后判断。

### 5.3 携带额外数据

自动识别也支持传入结构化数据：

```bash
curl -X POST http://localhost:8000/scenario/auto \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "帮我排查一下这个云主机创建失败的问题",
    "additional_data": {
      "environment": "ZStack 4.6, Ceph存储",
      "error_logs": "not enough capacity"
    },
    "output_mode": "technical"
  }'
```

### 5.4 查看所有可用场景

```bash
curl http://localhost:8000/scenario/types
```

```json
{
  "scenarios": [
    { "type": "troubleshooting", "name": "技术问题排查" },
    { "type": "tech_qa", "name": "技术问题回答" },
    { "type": "customer_reply", "name": "客户答复" },
    { "type": "weekly_report", "name": "周报生成" },
    { "type": "briefing", "name": "汇报生成" },
    { "type": "training", "name": "培训生成" },
    { "type": "demo_prep", "name": "演示准备" },
    { "type": "poc_support", "name": "PoC支持" },
    { "type": "escalation", "name": "问题升级" }
  ]
}
```

---

## 6. 实战案例

### 案例一：周五下午 5 点，快速生成周报

```bash
curl -X POST http://localhost:8000/scenario/weekly_report \
  -H "Content-Type: application/json" \
  -d '{
    "tasks_completed": [
      "完成客户A的PoC部署和功能演示",
      "解决客户B的VPC网络延迟问题",
      "编写ZStack v4.7升级指南"
    ],
    "major_results": [
      "客户A PoC通过验收，签约概率90%"
    ],
    "issues": [
      "客户C反馈GPU直通性能不达预期"
    ],
    "next_week_plan": [
      "客户A签约跟进",
      "客户C现场排查GPU问题"
    ],
    "report_version": "leadership"
  }'
```

→ **5分钟内**生成领导版周报，直接复制粘贴到邮件/钉钉。

### 案例二：客户群里突然问了一个技术问题

```bash
curl -X POST http://localhost:8000/scenario/customer_reply \
  -H "Content-Type: application/json" \
  -d '{
    "customer_question": "ZStack的云主机支持在线扩容CPU和内存吗？会不会影响业务？",
    "product": "ZStack Cloud"
  }'
```

→ 生成**专业、克制**的客户回复，不过度承诺，说明适用条件。

### 案例三：凌晨收到告警，快速定位问题

```bash
curl -X POST http://localhost:8000/scenario/troubleshooting \
  -H "Content-Type: application/json" \
  -d '{
    "problem_description": "物理机host-03突然显示Disconnected状态，上面运行着15台云主机",
    "environment": "ZStack 4.6.0, 10台物理机, Ceph存储",
    "urgency_level": "critical"
  }'
```

→ 生成**排查清单**，包含具体命令，按可能性排序。

### 案例四：给新人准备培训材料

```bash
curl -X POST http://localhost:8000/scenario/training \
  -H "Content-Type: application/json" \
  -d '{
    "training_topic": "ZStack Cloud基础运维入门",
    "audience_level": "beginner",
    "duration": 120
  }'
```

→ 生成**完整的培训大纲**，含知识点、动手练习、常见问题。

### 案例五：排查不了的问题整理升级材料

```bash
curl -X POST http://localhost:8000/scenario/escalation \
  -H "Content-Type: application/json" \
  -d '{
    "problem": "在线迁移偶发失败，错误信息不一致",
    "environment": "ZStack 4.5, KVM, Ceph, 混合CPU型号(Intel E5 + AMD EPYC)",
    "logs": "libvirt: error : internal error: QEMU unexpectedly closed the monitor",
    "attempted_actions": [
      "检查了libvirt版本一致性 - 一致",
      "检查了存储连接 - 正常",
      "怀疑CPU兼容性问题但不确定"
    ]
  }'
```

→ 生成**标准格式的升级材料**，直接发给研发或高级支持。

---

## 7. 进阶用法

### 7.1 运行示例脚本

项目提供了完整的示例脚本：

```bash
# 运行所有场景示例
python examples/example_requests.py

# 运行 URL 导入示例
python examples/example_url_import.py
```

### 7.2 使用 Python 调用

```python
import httpx

client = httpx.Client(base_url="http://localhost:8000", timeout=120)

# 技术问答
response = client.post("/scenario/tech_qa", json={
    "question": "ZStack如何配置高可用？",
    "output_mode": "technical",
})

result = response.json()
print(result["content"])
print(f"耗时: {result['processing_time_seconds']}秒")
```

### 7.3 使用 Swagger 交互文档

访问 `http://localhost:8000/docs`，可以在浏览器中直接：
1. 查看所有 API 和参数说明
2. 填写参数并点击 "Try it out" 执行
3. 查看请求和响应示例

这是 **最推荐的入门方式**——无需写任何代码。

### 7.4 批量导入知识

准备一批文档导入知识库：

```bash
# 1. 将文档放到一个目录
mkdir -p /tmp/my_docs
cp *.md /tmp/my_docs/

# 2. 逐个导入（或写脚本批量）
for file in /tmp/my_docs/*.md; do
  curl -X POST http://localhost:8000/knowledge/ingest/file \
    -H "Content-Type: application/json" \
    -d "{\"file_path\": \"$file\", \"document_type\": \"internal_doc\"}"
done
```

### 7.5 定制知识库内容

除了默认的 ZStack 知识外，可以导入任何与你工作相关的内容：

- 公司内部技术文档
- 项目经验总结
- 客户案例汇编
- 竞品分析资料
- 行业白皮书

导入后，所有场景模块都会自动检索和引用这些知识。

---

## 8. API 接口速查表

### 知识库接口

```
POST   /knowledge/bootstrap        初始化知识库（~1000条种子数据）
POST   /knowledge/ingest/file      导入本地文件
POST   /knowledge/ingest/url       导入网页URL
POST   /knowledge/refresh/url      刷新URL内容
GET    /knowledge/search?query=xxx  搜索（GET简化版）
POST   /knowledge/search           搜索（POST完整版，支持过滤）
GET    /knowledge/documents         列出所有文档
GET    /knowledge/stats             统计信息
DELETE /knowledge/document/{source} 删除文档
```

### 场景模块接口

```
GET    /scenario/types              列出所有场景
POST   /scenario/auto               自动识别场景并执行
POST   /scenario/troubleshooting    技术问题排查
POST   /scenario/tech_qa            技术问题回答
POST   /scenario/customer_reply     客户答复
POST   /scenario/weekly_report      周报生成
POST   /scenario/briefing           汇报生成
POST   /scenario/training           培训生成
POST   /scenario/demo_prep          演示准备
POST   /scenario/poc_support        PoC支持
POST   /scenario/escalation         问题升级
```

### 系统接口

```
GET    /                            系统信息
GET    /health                      健康检查
GET    /docs                        Swagger 交互文档
GET    /redoc                       ReDoc API 文档
```

---

> **提示**：遇到任何问题，先通过 `/health` 检查系统状态，再通过 `/knowledge/stats` 确认知识库是否就绪。
