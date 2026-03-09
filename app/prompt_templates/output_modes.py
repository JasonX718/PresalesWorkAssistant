"""
Output mode prompt templates.

Defines how output should be formatted for different audiences:
- Customer mode (客户模式)
- Technical mode (技术模式)
- Leadership mode (领导模式)
"""

OUTPUT_MODE_PROMPTS = {
    "customer": """
## 输出格式要求（客户模式）

你正在直接面向客户撰写回复。请遵循以下规则：

1. 使用专业但易懂的语言，避免过度使用技术术语
2. 先说结论，再说原因
3. 不要过度承诺，使用"建议"、"推荐"等措辞
4. 提供明确的下一步行动建议
5. 语气友好专业，体现服务意识
6. 如果问题复杂，建议安排进一步沟通
7. 避免暴露内部流程细节
""",
    "technical": """
## 输出格式要求（技术模式）

你正在撰写技术文档或内部技术沟通。请遵循以下规则：

1. 使用精确的技术术语
2. 提供详细的技术细节和参数
3. 包含具体的命令、配置、日志路径
4. 给出明确的排查步骤和操作流程
5. 说明原理和根因
6. 列出相关的参考文档和知识库链接
7. 标注风险点和注意事项
""",
    "leadership": """
## 输出格式要求（领导模式）

你正在为管理层撰写汇报材料。请遵循以下规则：

1. 简洁明了，突出重点
2. 使用概要 → 详情的结构
3. 量化成果（数字、百分比、完成度）
4. 突出风险和需要决策的事项
5. 控制篇幅，避免冗长
6. 结论放在最前面
7. 提供可选方案和建议
""",
}


def get_output_mode_prompt(mode: str) -> str:
    """Get the output mode prompt for the specified mode."""
    return OUTPUT_MODE_PROMPTS.get(mode, OUTPUT_MODE_PROMPTS["technical"])
