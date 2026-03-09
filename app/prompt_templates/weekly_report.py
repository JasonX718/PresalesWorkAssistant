"""
Prompt template for weekly report generation (周报生成).
"""

WEEKLY_REPORT_SYSTEM_PROMPT = """你是一名工作汇报撰写专家，帮助技术人员快速生成结构化周报。

原则：
- 结构清晰，重点突出
- 量化成果
- 突出价值和影响
- 控制篇幅
- 时间限制：5分钟
"""

WEEKLY_REPORT_STANDARD_PROMPT = """请根据以下信息生成周报：

## 本周完成工作
{tasks_completed}

## 关键成果
{major_results}

## 当前问题
{issues}

## 下周计划
{next_week_plan}

## 相关知识库信息
{knowledge_context}

---

请按以下结构输出**标准版周报**：

### 本周工作总结

#### 完成工作
（列出已完成的工作，按重要性排序）

#### 关键成果
（量化描述关键成果）

#### 当前问题与风险
（列出当前存在的问题和风险，标注影响和紧急程度）

### 下周工作计划
（按优先级列出下周计划）
"""

WEEKLY_REPORT_LEADERSHIP_PROMPT = """请根据以下信息生成**领导汇报版**周报（简洁版）：

## 本周完成工作
{tasks_completed}

## 关键成果
{major_results}

## 当前问题
{issues}

## 下周计划
{next_week_plan}

## 相关知识库信息
{knowledge_context}

---

请按以下结构输出**领导版周报**（控制在300字以内）：

**本周概要：**（一句话总结本周工作）

**关键成果：**
- （量化的关键数据）

**风险提示：**
- （需要关注的风险项）

**下周重点：**
- （最重要的2-3项计划）
"""

WEEKLY_REPORT_TECHNICAL_PROMPT = """请根据以下信息生成**技术版**周报：

## 本周完成工作
{tasks_completed}

## 关键成果
{major_results}

## 当前问题
{issues}

## 下周计划
{next_week_plan}

## 相关知识库信息
{knowledge_context}

---

请按以下结构输出**技术版周报**：

### 技术工作详情

#### 已完成事项
（详细的技术工作内容，包含技术细节）

#### 技术成果
（技术指标和成果）

#### 技术问题跟踪
| 问题 | 状态 | 影响 | 计划 |
|------|------|------|------|
（列出各技术问题）

#### 下周技术计划
（详细的技术计划和目标）
"""
